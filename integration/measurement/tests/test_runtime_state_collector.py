"""런타임 상태 수집기 단위 테스트."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# 경로 설정
_MEASUREMENT_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "integration" / "measurement"))
sys.path.insert(0, str(_REPO_ROOT / "mac_mini" / "code"))

from runtime_state_collector import (
    CollectorConfig,
    collect_all_states,
    collect_docker_service,
    collect_host_ping,
    collect_mqtt_broker,
    collect_ollama_api,
    collect_sqlite_db,
)


# ── Docker 서비스 수집 테스트 ─────────────────────────────────────────────────


class TestCollectDockerService:
    @pytest.mark.asyncio
    async def test_running_service_returns_ready(self):
        """실행 중인 서비스는 READY를 반환한다."""
        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(b"abc123\n", b""))

        with patch(
            "asyncio.create_subprocess_exec",
            AsyncMock(return_value=mock_proc),
        ):
            result = await collect_docker_service("mosquitto")

        assert result == "READY"

    @pytest.mark.asyncio
    async def test_stopped_service_returns_blocked(self):
        """중지된 서비스는 BLOCKED를 반환한다."""
        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))

        with patch(
            "asyncio.create_subprocess_exec",
            AsyncMock(return_value=mock_proc),
        ):
            result = await collect_docker_service("edge_controller_app")

        assert result == "BLOCKED"

    @pytest.mark.asyncio
    async def test_docker_not_found_returns_unknown(self):
        """docker 명령어 없으면 UNKNOWN을 반환한다."""
        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("docker not found"),
        ):
            result = await collect_docker_service("mosquitto")

        assert result == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_timeout_returns_unknown(self):
        """타임아웃 시 UNKNOWN을 반환한다."""
        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=asyncio.TimeoutError(),
        ):
            result = await collect_docker_service("ollama", timeout=0.001)

        assert result == "UNKNOWN"


# ── MQTT 브로커 수집 테스트 ───────────────────────────────────────────────────


class TestCollectMqttBroker:
    @pytest.mark.asyncio
    async def test_successful_connection_returns_ready(self):
        """TCP 연결 성공 시 READY를 반환한다."""
        mock_writer = AsyncMock()
        mock_writer.wait_closed = AsyncMock()

        with patch(
            "asyncio.open_connection",
            AsyncMock(return_value=(AsyncMock(), mock_writer)),
        ):
            result = await collect_mqtt_broker("127.0.0.1", 1883)

        assert result == "READY"

    @pytest.mark.asyncio
    async def test_connection_refused_returns_blocked(self):
        """연결 거부 시 BLOCKED를 반환한다."""
        with patch(
            "asyncio.open_connection",
            side_effect=ConnectionRefusedError(),
        ):
            result = await collect_mqtt_broker("127.0.0.1", 1883)

        assert result == "BLOCKED"

    @pytest.mark.asyncio
    async def test_timeout_returns_unknown(self):
        """타임아웃 시 UNKNOWN을 반환한다."""
        with patch(
            "asyncio.open_connection",
            side_effect=asyncio.TimeoutError(),
        ):
            result = await collect_mqtt_broker("127.0.0.1", 1883)

        assert result == "UNKNOWN"


# ── Ollama API 수집 테스트 ────────────────────────────────────────────────────


class TestCollectOllamaApi:
    @pytest.mark.asyncio
    async def test_api_with_models_returns_ready(self):
        """모델이 있는 경우 READY를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": [{"name": "llama3.1"}]}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await collect_ollama_api("http://127.0.0.1:11434")

        assert result == "READY"

    @pytest.mark.asyncio
    async def test_api_without_models_returns_degraded(self):
        """모델이 없는 경우 DEGRADED를 반환한다."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"models": []}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await collect_ollama_api("http://127.0.0.1:11434")

        assert result == "DEGRADED"

    @pytest.mark.asyncio
    async def test_connection_error_returns_blocked(self):
        """연결 오류 시 BLOCKED를 반환한다."""
        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await collect_ollama_api("http://127.0.0.1:11434")

        assert result == "BLOCKED"


# ── SQLite DB 수집 테스트 ─────────────────────────────────────────────────────


class TestCollectSqliteDb:
    @pytest.mark.asyncio
    async def test_missing_db_file_returns_blocked(self, tmp_path):
        """DB 파일이 없으면 BLOCKED를 반환한다."""
        missing_path = tmp_path / "nonexistent.db"
        result = await collect_sqlite_db(missing_path)
        assert result == "BLOCKED"

    @pytest.mark.asyncio
    async def test_valid_db_returns_ready(self, tmp_path):
        """유효한 WAL DB는 READY를 반환한다."""
        import sqlite3

        db_path = tmp_path / "audit_log.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        # 7개 필수 테이블 생성
        for table in [
            "routing_events",
            "validator_results",
            "deferral_events",
            "timeout_events",
            "escalation_events",
            "caregiver_actions",
            "actuation_ack_events",
        ]:
            conn.execute(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY);")
        conn.commit()
        conn.close()

        result = await collect_sqlite_db(db_path)
        assert result == "READY"

    @pytest.mark.asyncio
    async def test_missing_tables_returns_degraded(self, tmp_path):
        """테이블이 일부 없으면 DEGRADED를 반환한다."""
        import sqlite3

        db_path = tmp_path / "partial.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        # 일부 테이블만 생성
        conn.execute("CREATE TABLE routing_events (id INTEGER PRIMARY KEY);")
        conn.commit()
        conn.close()

        result = await collect_sqlite_db(db_path)
        assert result == "DEGRADED"


# ── 호스트 Ping 수집 테스트 ───────────────────────────────────────────────────


class TestCollectHostPing:
    @pytest.mark.asyncio
    async def test_successful_ping_returns_ready(self):
        """ping 성공 시 READY를 반환한다."""
        mock_proc = MagicMock()
        mock_proc.wait = AsyncMock(return_value=0)

        with patch(
            "asyncio.create_subprocess_exec",
            AsyncMock(return_value=mock_proc),
        ):
            result = await collect_host_ping("192.168.1.100")

        assert result == "READY"

    @pytest.mark.asyncio
    async def test_failed_ping_returns_blocked(self):
        """ping 실패 시 BLOCKED를 반환한다."""
        mock_proc = MagicMock()
        mock_proc.wait = AsyncMock(return_value=1)

        with patch(
            "asyncio.create_subprocess_exec",
            AsyncMock(return_value=mock_proc),
        ):
            result = await collect_host_ping("192.168.1.200")

        assert result == "BLOCKED"

    @pytest.mark.asyncio
    async def test_ping_not_found_returns_unknown(self):
        """ping 명령어 없으면 UNKNOWN을 반환한다."""
        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("ping not found"),
        ):
            result = await collect_host_ping("192.168.1.100")

        assert result == "UNKNOWN"


# ── collect_all_states 통합 테스트 ───────────────────────────────────────────


class TestCollectAllStates:
    @pytest.mark.asyncio
    async def test_always_includes_mac_mini_ready(self):
        """collect_all_states는 항상 mac_mini=READY를 포함한다."""
        config = CollectorConfig(
            docker_services=[],
            rpi_host=None,
            sqlite_db_path=None,
        )

        with (
            patch(
                "runtime_state_collector.collect_mqtt_broker",
                AsyncMock(return_value="READY"),
            ),
            patch(
                "runtime_state_collector.collect_ollama_api",
                AsyncMock(return_value="READY"),
            ),
        ):
            states = await collect_all_states(config)

        assert states["mac_mini"] == "READY"

    @pytest.mark.asyncio
    async def test_measurement_nodes_always_unknown(self):
        """측정 노드는 항상 UNKNOWN 상태다."""
        config = CollectorConfig(
            docker_services=[],
            rpi_host=None,
            sqlite_db_path=None,
        )

        with (
            patch(
                "runtime_state_collector.collect_mqtt_broker",
                AsyncMock(return_value="READY"),
            ),
            patch(
                "runtime_state_collector.collect_ollama_api",
                AsyncMock(return_value="READY"),
            ),
        ):
            states = await collect_all_states(config)

        assert states["stm32_time_probe_01"] == "UNKNOWN"
        assert states["stm32_time_probe_02"] == "UNKNOWN"
        assert states["esp32_button_node"] == "UNKNOWN"
        assert states["esp32_sensor_node"] == "UNKNOWN"

    @pytest.mark.asyncio
    async def test_collector_exception_does_not_propagate(self):
        """수집기 예외가 전체 결과에 영향을 주지 않는다."""
        config = CollectorConfig(
            docker_services=["mosquitto"],
            rpi_host=None,
            sqlite_db_path=None,
        )

        with (
            patch(
                "runtime_state_collector.collect_docker_service",
                AsyncMock(return_value="UNKNOWN"),
            ),
            patch(
                "runtime_state_collector.collect_mqtt_broker",
                AsyncMock(side_effect=RuntimeError("unexpected")),
            ),
            patch(
                "runtime_state_collector.collect_ollama_api",
                AsyncMock(return_value="BLOCKED"),
            ),
        ):
            # 예외가 전파되지 않고 정상적으로 완료되어야 한다
            states = await collect_all_states(config)

        assert "mac_mini" in states
        assert all(v in ("READY", "DEGRADED", "BLOCKED", "UNKNOWN") for v in states.values())

    @pytest.mark.asyncio
    async def test_collector_config_from_env(self, monkeypatch):
        """환경변수에서 CollectorConfig를 생성한다."""
        monkeypatch.setenv("MQTT_HOST", "192.168.1.10")
        monkeypatch.setenv("MQTT_PORT", "1884")
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://192.168.1.10:11434")
        monkeypatch.setenv("RPI_HOST", "192.168.1.50")

        config = CollectorConfig.from_env()

        assert config.mqtt_host == "192.168.1.10"
        assert config.mqtt_port == 1884
        assert config.ollama_base_url == "http://192.168.1.10:11434"
        assert config.rpi_host == "192.168.1.50"

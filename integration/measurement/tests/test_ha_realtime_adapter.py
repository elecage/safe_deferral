"""HA 리얼타임 어댑터 단위 테스트."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# 경로 설정
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "integration" / "measurement"))

from ha_realtime_adapter import (
    AdapterService,
    MQTTPrefightPublisher,
    StateSnapshotBuilder,
    app,
)
from runtime_state_collector import CollectorConfig


# ── StateSnapshotBuilder 테스트 ──────────────────────────────────────────────


class TestStateSnapshotBuilder:
    def test_build_returns_correct_structure(self):
        """raw_states에서 aggregator 호환 snapshot dict를 생성한다."""
        builder = StateSnapshotBuilder()
        raw_states = {
            "mac_mini": "READY",
            "mosquitto": "READY",
            "stm32_time_probe_01": "UNKNOWN",
        }

        snapshot = builder.build(raw_states)

        assert snapshot["version"] == StateSnapshotBuilder.VERSION
        assert snapshot["snapshot_type"] == StateSnapshotBuilder.SNAPSHOT_TYPE
        assert "nodes" in snapshot
        assert snapshot["nodes"]["mac_mini"] == "READY"
        assert snapshot["nodes"]["stm32_time_probe_01"] == "UNKNOWN"

    def test_build_preserves_all_states(self):
        """모든 노드 상태가 snapshot에 포함된다."""
        builder = StateSnapshotBuilder()
        raw_states = {
            "mac_mini": "READY",
            "homeassistant": "DEGRADED",
            "ollama": "BLOCKED",
            "rpi": "UNKNOWN",
        }

        snapshot = builder.build(raw_states)

        assert len(snapshot["nodes"]) == 4
        assert snapshot["nodes"]["homeassistant"] == "DEGRADED"
        assert snapshot["nodes"]["ollama"] == "BLOCKED"

    def test_build_with_empty_states(self):
        """빈 상태 딕셔너리도 정상 처리한다."""
        builder = StateSnapshotBuilder()
        snapshot = builder.build({})

        assert snapshot["nodes"] == {}
        assert snapshot["version"] == StateSnapshotBuilder.VERSION

    def test_build_includes_description(self):
        """snapshot에 description 필드가 포함된다."""
        builder = StateSnapshotBuilder()
        snapshot = builder.build({"mac_mini": "READY"})

        assert "description" in snapshot
        assert len(snapshot["description"]) > 0


# ── MQTTPrefightPublisher 테스트 ──────────────────────────────────────────────


class TestMQTTPrefightPublisher:
    def test_publish_report_without_client_does_not_raise(self):
        """MQTT 클라이언트 없이도 예외 없이 동작한다."""
        publisher = MQTTPrefightPublisher()
        publisher._client = None  # 강제로 클라이언트 제거

        # 예외 없이 실행되어야 한다
        publisher.publish_report("exp_001", {"final_state": "READY"})

    def test_publish_snapshot_without_client_does_not_raise(self):
        """MQTT 클라이언트 없이 snapshot 발행도 예외 없이 동작한다."""
        publisher = MQTTPrefightPublisher()
        publisher._client = None

        publisher.publish_snapshot({"nodes": {"mac_mini": "READY"}})

    def test_publish_report_with_mock_client(self):
        """mock 클라이언트로 정상 발행 흐름을 검증한다."""
        publisher = MQTTPrefightPublisher()
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.rc = 0
        mock_client.publish.return_value = mock_result
        publisher._client = mock_client

        publisher.publish_report("exp_001", {"final_state": "READY"})

        # publish가 올바른 토픽으로 호출되었는지 확인
        call_args = mock_client.publish.call_args
        assert "experiment/preflight/result/exp_001" in call_args[0][0]

    def test_connect_failure_sets_client_to_none(self):
        """MQTT 연결 실패 시 클라이언트가 None이 된다."""
        publisher = MQTTPrefightPublisher()
        if publisher._client is not None:
            publisher._client.connect = MagicMock(side_effect=ConnectionRefusedError("refused"))
            publisher.connect()
            # 연결 실패 시 _client가 None으로 처리됨
            assert publisher._client is None


# ── FastAPI 엔드포인트 테스트 ──────────────────────────────────────────────────


def _make_mock_adapter_service() -> MagicMock:
    """테스트용 AdapterService mock을 생성한다."""
    mock_service = MagicMock(spec=AdapterService)
    mock_service.get_last_snapshot.return_value = {
        "version": "1.0",
        "snapshot_type": "node_state_snapshot",
        "description": "test snapshot",
        "nodes": {"mac_mini": "READY", "mosquitto": "READY"},
    }
    mock_service.get_last_report.return_value = {
        "experiment_id": "exp_e2e_light_control_001",
        "final_state": "READY",
        "blocked_if_missing": False,
        "dependency_results": [],
        "reasons": [],
    }
    mock_service.get_all_reports.return_value = {
        "exp_e2e_light_control_001": {
            "experiment_id": "exp_e2e_light_control_001",
            "final_state": "READY",
            "blocked_if_missing": False,
            "dependency_results": [],
            "reasons": [],
        }
    }
    mock_service.list_experiment_ids.return_value = ["exp_e2e_light_control_001"]
    mock_service.run_once = AsyncMock(
        return_value={
            "exp_e2e_light_control_001": {
                "experiment_id": "exp_e2e_light_control_001",
                "final_state": "READY",
                "blocked_if_missing": False,
                "dependency_results": [],
                "reasons": [],
            }
        }
    )
    return mock_service


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        """GET /health는 status ok를 반환한다."""
        import ha_realtime_adapter as adapter_module

        mock_service = _make_mock_adapter_service()

        with patch.object(adapter_module, "_adapter_service", mock_service):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "ha_realtime_adapter"

    def test_health_has_snapshot_status(self):
        """GET /health는 has_snapshot 필드를 포함한다."""
        import ha_realtime_adapter as adapter_module

        mock_service = _make_mock_adapter_service()

        with patch.object(adapter_module, "_adapter_service", mock_service):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.get("/health")

        assert "has_snapshot" in response.json()
        assert response.json()["has_snapshot"] is True


class TestReadinessEndpoint:
    def test_known_experiment_returns_report(self):
        """GET /readiness/{id}는 알려진 실험의 리포트를 반환한다."""
        import ha_realtime_adapter as adapter_module

        mock_service = _make_mock_adapter_service()

        with patch.object(adapter_module, "_adapter_service", mock_service):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.get("/readiness/exp_e2e_light_control_001")

        assert response.status_code == 200
        data = response.json()
        assert data["experiment_id"] == "exp_e2e_light_control_001"
        assert "final_state" in data

    def test_unknown_experiment_returns_404(self):
        """GET /readiness/{id}는 알 수 없는 실험 ID에 404를 반환한다."""
        import ha_realtime_adapter as adapter_module

        mock_service = _make_mock_adapter_service()
        # 알 수 없는 실험 ID → None 반환
        mock_service.get_last_report.return_value = None

        with patch.object(adapter_module, "_adapter_service", mock_service):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.get("/readiness/nonexistent_experiment")

        assert response.status_code == 404

    def test_list_readiness_returns_all_reports(self):
        """GET /readiness는 모든 실험의 리포트를 반환한다."""
        import ha_realtime_adapter as adapter_module

        mock_service = _make_mock_adapter_service()

        with patch.object(adapter_module, "_adapter_service", mock_service):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.get("/readiness")

        assert response.status_code == 200
        data = response.json()
        assert "experiments" in data
        assert "snapshot" in data


class TestRefreshEndpoint:
    def test_force_refresh_triggers_run_once(self):
        """POST /readiness/refresh는 즉시 상태 수집을 실행한다."""
        import ha_realtime_adapter as adapter_module

        mock_service = _make_mock_adapter_service()

        with patch.object(adapter_module, "_adapter_service", mock_service):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.post("/readiness/refresh")

        assert response.status_code == 200
        data = response.json()
        assert data["refreshed"] is True
        assert "experiments" in data
        mock_service.run_once.assert_called_once()

    def test_force_refresh_exception_returns_500(self):
        """POST /readiness/refresh 예외 시 500을 반환한다."""
        import ha_realtime_adapter as adapter_module

        mock_service = _make_mock_adapter_service()
        mock_service.run_once = AsyncMock(side_effect=RuntimeError("collector failure"))

        with patch.object(adapter_module, "_adapter_service", mock_service):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/readiness/refresh")

        assert response.status_code == 500


class TestSnapshotEndpoint:
    def test_snapshot_returns_current_state(self):
        """GET /snapshot는 현재 state snapshot을 반환한다."""
        import ha_realtime_adapter as adapter_module

        mock_service = _make_mock_adapter_service()

        with patch.object(adapter_module, "_adapter_service", mock_service):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.get("/snapshot")

        assert response.status_code == 200
        data = response.json()
        assert "snapshot" in data
        assert data["snapshot"]["nodes"]["mac_mini"] == "READY"

    def test_snapshot_no_data_returns_message(self):
        """GET /snapshot는 데이터 없을 때 message를 반환한다."""
        import ha_realtime_adapter as adapter_module

        mock_service = _make_mock_adapter_service()
        mock_service.get_last_snapshot.return_value = None

        with patch.object(adapter_module, "_adapter_service", mock_service):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.get("/snapshot")

        assert response.status_code == 200
        data = response.json()
        assert data["snapshot"] is None
        assert "message" in data

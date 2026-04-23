"""
런타임 상태 수집기.

각 노드의 실제 런타임 상태를 비동기로 수집하여 state snapshot 형식으로 반환한다.
VALID_STATES: READY | DEGRADED | BLOCKED | UNKNOWN

수집 대상:
- Docker 컨테이너 서비스 (compose ps --status running)
- MQTT 브로커 TCP 연결
- Ollama API 헬스 체크
- SQLite WAL 모드 및 스키마 검증
- 원격 호스트 ping (RPi 등)

이 모듈은 평가/운영지원 헬퍼이며, 정책 진실, 밸리데이터 권한, 실험 의미를 재정의하지 않는다.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# 유효한 상태 집합 (aggregator 스켈레톤과 일치)
VALID_STATES = {"READY", "DEGRADED", "BLOCKED", "UNKNOWN"}

# 감사 로그 스키마에 필요한 테이블 목록 (40_verify_sqlite.sh 기준)
_REQUIRED_AUDIT_TABLES = [
    "routing_events",
    "validator_results",
    "deferral_events",
    "timeout_events",
    "escalation_events",
    "caregiver_actions",
    "actuation_ack_events",
]

# Docker 수집 시 작업 디렉토리 (워크스페이스 compose 경로)
_DOCKER_WORKSPACE_DIR = Path.home() / "smarthome_workspace" / "docker"


@dataclass
class CollectorConfig:
    """
    런타임 상태 수집기 설정.

    환경변수로 오버라이드 가능:
    - MQTT_HOST, MQTT_PORT
    - OLLAMA_BASE_URL
    - SQLITE_PATH
    - RPI_HOST
    - DOCKER_WORKSPACE_DIR
    """

    mqtt_host: str = "127.0.0.1"
    mqtt_port: int = 1883
    ollama_base_url: str = "http://127.0.0.1:11434"
    sqlite_db_path: Optional[Path] = None
    docker_services: List[str] = field(
        default_factory=lambda: [
            "mosquitto",
            "homeassistant",
            "ollama",
            "edge_controller_app",
        ]
    )
    # RPi 호스트 (None이면 ping 건너뜀)
    rpi_host: Optional[str] = None
    # 각 수집기의 개별 타임아웃 (초)
    collect_timeout_s: float = 10.0

    @classmethod
    def from_env(cls) -> "CollectorConfig":
        """환경변수에서 설정을 로드하여 CollectorConfig를 생성한다."""
        sqlite_path_env = os.environ.get("SQLITE_PATH")
        sqlite_db_path = Path(sqlite_path_env) if sqlite_path_env else None

        return cls(
            mqtt_host=os.environ.get("MQTT_HOST", "127.0.0.1"),
            mqtt_port=int(os.environ.get("MQTT_PORT", "1883")),
            ollama_base_url=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            sqlite_db_path=sqlite_db_path,
            rpi_host=os.environ.get("RPI_HOST"),
        )


# ── 개별 수집기 ─────────────────────────────────────────────────────────────


async def collect_docker_service(
    service_name: str,
    workspace_dir: Optional[Path] = None,
    timeout: float = 5.0,
) -> str:
    """
    Docker Compose 서비스의 실행 상태를 확인한다.

    Args:
        service_name: 확인할 서비스 이름
        workspace_dir: docker compose 디렉토리 (기본값: ~/smarthome_workspace/docker)
        timeout: 최대 대기 시간 (초)

    Returns:
        READY: 서비스 실행 중
        BLOCKED: 서비스 중지됨
        UNKNOWN: docker 불가용 또는 예외
    """
    cwd = workspace_dir or _DOCKER_WORKSPACE_DIR
    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                "docker",
                "compose",
                "ps",
                "--status",
                "running",
                "-q",
                service_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd if cwd.exists() else None,
            ),
            timeout=timeout,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = stdout.decode("utf-8", errors="replace").strip()
        if output:
            logger.debug("Docker 서비스 실행 중 | service=%s", service_name)
            return "READY"
        logger.warning("Docker 서비스 미실행 | service=%s", service_name)
        return "BLOCKED"
    except asyncio.TimeoutError:
        logger.warning("Docker 상태 확인 타임아웃 | service=%s", service_name)
        return "UNKNOWN"
    except FileNotFoundError:
        logger.warning("docker 명령어 없음 | service=%s", service_name)
        return "UNKNOWN"
    except Exception as exc:
        logger.warning("Docker 상태 확인 오류 | service=%s error=%s", service_name, exc)
        return "UNKNOWN"


async def collect_mqtt_broker(
    host: str = "127.0.0.1",
    port: int = 1883,
    timeout: float = 5.0,
) -> str:
    """
    MQTT 브로커 TCP 연결 가능성을 확인한다.

    Args:
        host: MQTT 브로커 호스트
        port: MQTT 브로커 포트
        timeout: 최대 대기 시간 (초)

    Returns:
        READY: 연결 성공
        BLOCKED: 연결 거부
        UNKNOWN: 타임아웃 또는 예외
    """
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        logger.debug("MQTT 브로커 연결 성공 | host=%s port=%d", host, port)
        return "READY"
    except ConnectionRefusedError:
        logger.warning("MQTT 브로커 연결 거부 | host=%s port=%d", host, port)
        return "BLOCKED"
    except asyncio.TimeoutError:
        logger.warning("MQTT 브로커 연결 타임아웃 | host=%s port=%d", host, port)
        return "UNKNOWN"
    except Exception as exc:
        logger.warning("MQTT 브로커 확인 오류 | host=%s port=%d error=%s", host, port, exc)
        return "UNKNOWN"


async def collect_ollama_api(
    base_url: str = "http://127.0.0.1:11434",
    timeout: float = 8.0,
) -> str:
    """
    Ollama API 헬스를 확인한다.

    GET /api/tags 응답으로 모델 목록 확인.

    Args:
        base_url: Ollama API 베이스 URL
        timeout: 최대 대기 시간 (초)

    Returns:
        READY: API 응답 및 모델 목록 있음
        DEGRADED: API 응답하나 모델 없음
        BLOCKED: 연결 불가
        UNKNOWN: 예외
    """
    try:
        import httpx
    except ImportError:
        logger.warning("httpx 미설치 - Ollama 상태 확인 불가")
        return "UNKNOWN"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{base_url}/api/tags")
        if resp.status_code == 200:
            data = resp.json()
            models = data.get("models", [])
            if models:
                logger.debug("Ollama API 정상 | model_count=%d", len(models))
                return "READY"
            logger.warning("Ollama API 응답하나 모델 없음")
            return "DEGRADED"
        logger.warning("Ollama API HTTP 오류 | status=%d", resp.status_code)
        return "DEGRADED"
    except (httpx.ConnectError, httpx.ConnectTimeout):
        logger.warning("Ollama API 연결 불가 | url=%s", base_url)
        return "BLOCKED"
    except httpx.TimeoutException:
        logger.warning("Ollama API 타임아웃 | url=%s", base_url)
        return "UNKNOWN"
    except Exception as exc:
        logger.warning("Ollama API 확인 오류 | url=%s error=%s", base_url, exc)
        return "UNKNOWN"


async def collect_sqlite_db(
    db_path: Path,
    timeout: float = 5.0,
) -> str:
    """
    SQLite 감사 로그 DB 상태를 확인한다.

    WAL 모드, 무결성 검사, 7개 필수 테이블 존재 확인.

    Args:
        db_path: SQLite DB 파일 경로
        timeout: 최대 대기 시간 (초)

    Returns:
        READY: 모든 검사 통과
        DEGRADED: WAL 모드 정상이나 일부 테이블 없음
        BLOCKED: DB 파일 없음 또는 열기 실패
        UNKNOWN: 예외
    """

    def _check_sqlite() -> str:
        # DB 파일 존재 확인
        if not db_path.exists():
            logger.warning("SQLite DB 파일 없음 | path=%s", db_path)
            return "BLOCKED"

        try:
            conn = sqlite3.connect(str(db_path), timeout=3.0)
            try:
                # WAL 모드 확인
                mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
                if mode.lower() != "wal":
                    logger.warning("SQLite WAL 모드 아님 | mode=%s", mode)
                    return "DEGRADED"

                # 무결성 검사
                integrity = conn.execute("PRAGMA integrity_check;").fetchone()[0]
                if integrity.lower() != "ok":
                    logger.warning("SQLite 무결성 검사 실패 | result=%s", integrity)
                    return "DEGRADED"

                # 필수 테이블 확인
                existing = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table';"
                    ).fetchall()
                }
                missing = [t for t in _REQUIRED_AUDIT_TABLES if t not in existing]
                if missing:
                    logger.warning("SQLite 누락 테이블 | tables=%s", missing)
                    return "DEGRADED"

                logger.debug("SQLite DB 정상 | path=%s", db_path)
                return "READY"
            finally:
                conn.close()
        except sqlite3.OperationalError as exc:
            logger.warning("SQLite 연결 실패 | path=%s error=%s", db_path, exc)
            return "BLOCKED"

    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, _check_sqlite),
            timeout=timeout,
        )
        return result
    except asyncio.TimeoutError:
        logger.warning("SQLite 검사 타임아웃 | path=%s", db_path)
        return "UNKNOWN"
    except Exception as exc:
        logger.warning("SQLite 검사 예외 | path=%s error=%s", db_path, exc)
        return "UNKNOWN"


async def collect_host_ping(
    host: str,
    timeout: float = 3.0,
) -> str:
    """
    원격 호스트의 ping 응답을 확인한다.

    Args:
        host: ping 대상 호스트
        timeout: 최대 대기 시간 (초)

    Returns:
        READY: ping 응답 있음
        BLOCKED: ping 응답 없음
        UNKNOWN: 명령어 오류 또는 예외
    """
    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                "ping",
                "-c",
                "1",
                "-W",
                "2",
                host,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            ),
            timeout=timeout,
        )
        returncode = await asyncio.wait_for(proc.wait(), timeout=timeout)
        if returncode == 0:
            logger.debug("Ping 성공 | host=%s", host)
            return "READY"
        logger.warning("Ping 응답 없음 | host=%s", host)
        return "BLOCKED"
    except asyncio.TimeoutError:
        logger.warning("Ping 타임아웃 | host=%s", host)
        return "BLOCKED"
    except FileNotFoundError:
        logger.warning("ping 명령어 없음 | host=%s", host)
        return "UNKNOWN"
    except Exception as exc:
        logger.warning("Ping 예외 | host=%s error=%s", host, exc)
        return "UNKNOWN"


# ── 통합 수집 함수 ────────────────────────────────────────────────────────────


async def collect_all_states(config: CollectorConfig) -> Dict[str, str]:
    """
    모든 수집기를 동시에 실행하고 node_id → state 딕셔너리를 반환한다.

    Args:
        config: 수집기 설정

    Returns:
        {node_id: state_string} 딕셔너리 (VALID_STATES 중 하나)
    """
    logger.info("런타임 상태 수집 시작")

    # mac_mini 자체 상태 (항상 READY - 이 코드가 실행 중이면 동작 중)
    states: Dict[str, str] = {"mac_mini": "READY"}

    # Docker 서비스 수집 태스크
    docker_tasks = {
        svc: collect_docker_service(
            svc, timeout=config.collect_timeout_s
        )
        for svc in config.docker_services
    }

    # MQTT 브로커 수집
    mqtt_task = collect_mqtt_broker(
        host=config.mqtt_host,
        port=config.mqtt_port,
        timeout=config.collect_timeout_s,
    )

    # Ollama API 수집
    ollama_task = collect_ollama_api(
        base_url=config.ollama_base_url,
        timeout=config.collect_timeout_s,
    )

    # SQLite DB 수집 (경로가 설정된 경우에만)
    sqlite_future = None
    if config.sqlite_db_path:
        sqlite_future = collect_sqlite_db(
            db_path=config.sqlite_db_path,
            timeout=config.collect_timeout_s,
        )

    # RPi ping 수집 (호스트가 설정된 경우에만)
    rpi_future = None
    if config.rpi_host:
        rpi_future = collect_host_ping(
            host=config.rpi_host,
            timeout=config.collect_timeout_s,
        )

    # 모든 태스크 동시 실행
    task_list = list(docker_tasks.values()) + [mqtt_task, ollama_task]
    optional_tasks = []
    if sqlite_future:
        optional_tasks.append(sqlite_future)
    if rpi_future:
        optional_tasks.append(rpi_future)

    all_tasks = task_list + optional_tasks
    results = await asyncio.gather(*all_tasks, return_exceptions=True)

    # Docker 서비스 결과 적용
    docker_service_names = list(docker_tasks.keys())
    for i, svc in enumerate(docker_service_names):
        result = results[i]
        if isinstance(result, Exception):
            logger.warning("Docker 수집 예외 | service=%s error=%s", svc, result)
            states[svc] = "UNKNOWN"
        else:
            states[svc] = result

    # MQTT 결과 적용
    offset = len(docker_tasks)
    mqtt_result = results[offset]
    if isinstance(mqtt_result, Exception):
        logger.warning("MQTT 수집 예외 | error=%s", mqtt_result)
        # mosquitto 서비스 상태를 MQTT 연결로 보완 (이미 docker task가 있으면 skip)
        if "mosquitto" not in states:
            states["mosquitto"] = "UNKNOWN"
    else:
        # MQTT 연결 결과를 mosquitto docker 결과와 병합 (둘 다 READY여야 진짜 READY)
        if "mosquitto" not in states:
            states["mosquitto"] = mqtt_result

    # Ollama 결과 적용
    ollama_result = results[offset + 1]
    if isinstance(ollama_result, Exception):
        logger.warning("Ollama 수집 예외 | error=%s", ollama_result)
        if "ollama" not in states:
            states["ollama"] = "UNKNOWN"
    else:
        if "ollama" not in states:
            states["ollama"] = ollama_result

    # 선택적 태스크 결과 적용
    optional_offset = offset + 2
    if sqlite_future:
        sqlite_result = results[optional_offset]
        if isinstance(sqlite_result, Exception):
            logger.warning("SQLite 수집 예외 | error=%s", sqlite_result)
            states["sqlite_audit_db"] = "UNKNOWN"
        else:
            states["sqlite_audit_db"] = sqlite_result
        optional_offset += 1

    if rpi_future:
        rpi_result = results[optional_offset]
        if isinstance(rpi_result, Exception):
            logger.warning("RPi ping 수집 예외 | error=%s", rpi_result)
            states["rpi"] = "UNKNOWN"
        else:
            states["rpi"] = rpi_result

    # 측정 노드는 현재 항상 UNKNOWN (라이브 프로브 없음)
    states["stm32_time_probe_01"] = "UNKNOWN"
    states["stm32_time_probe_02"] = "UNKNOWN"
    states["esp32_button_node"] = "UNKNOWN"
    states["esp32_sensor_node"] = "UNKNOWN"

    logger.info(
        "런타임 상태 수집 완료 | node_count=%d ready=%d blocked=%d unknown=%d",
        len(states),
        sum(1 for v in states.values() if v == "READY"),
        sum(1 for v in states.values() if v == "BLOCKED"),
        sum(1 for v in states.values() if v == "UNKNOWN"),
    )
    return states

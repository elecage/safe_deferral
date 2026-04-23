"""
Home Assistant 리얼타임 어댑터.

런타임 상태를 주기적으로 수집하여 aggregator를 통해 실험 준비도를 평가하고
MQTT 및 REST API로 결과를 노출한다.

흐름:
  1. collect_all_states() → {node_id: state}
  2. StateSnapshotBuilder → aggregator 호환 snapshot dict
  3. aggregate_report() → PreflightReport
  4. MQTT 발행 (experiment/preflight/result/{experiment_id})
  5. REST API로 on-demand 조회 가능

이 어댑터는 평가/운영지원 레이어이며, 정책 진실, 밸리데이터 권한을 재정의하지 않는다.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

# runtime_state_collector 및 aggregator 스켈레톤 import
# 패키지로 실행될 때와 직접 실행될 때 모두 동작하도록 경로 설정
_REPO_ROOT = Path(__file__).resolve().parents[2]
_MEASUREMENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_MEASUREMENT_DIR))
sys.path.insert(0, str(_REPO_ROOT / "integration" / "measurement"))

from runtime_state_collector import CollectorConfig, collect_all_states  # noqa: E402

from preflight_readiness_aggregator_skeleton import (  # noqa: E402
    aggregate_report,
    find_repo_root,
    index_experiments,
    index_nodes,
    load_registry,
    load_state_snapshot,
    PreflightError,
    PreflightReport,
)

logger = logging.getLogger(__name__)

# 레지스트리 기본 경로 (repo-relative)
_EXP_REGISTRY_REL = "integration/measurement/experiment_registry_skeleton.yaml"
_NODE_REGISTRY_REL = "integration/measurement/node_registry_skeleton.yaml"

# MQTT 선택적 import
try:
    import paho.mqtt.client as _mqtt_module  # type: ignore[no-redef]
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False
    logger.warning("paho-mqtt 미설치 - MQTT 발행 비활성화")


# ── State Snapshot Builder ────────────────────────────────────────────────────


class StateSnapshotBuilder:
    """
    런타임 수집 결과를 aggregator 호환 state snapshot dict로 변환한다.

    aggregator의 load_state_snapshot()이 기대하는 형식:
      {nodes: {node_id: "READY" | "DEGRADED" | "BLOCKED" | "UNKNOWN"}}
    """

    VERSION = "1.0"
    SNAPSHOT_TYPE = "node_state_snapshot"

    def build(self, raw_states: Dict[str, str]) -> Dict[str, Any]:
        """
        raw_states 딕셔너리에서 aggregator 호환 snapshot을 생성한다.

        Args:
            raw_states: {node_id: state_string} 딕셔너리

        Returns:
            aggregator가 기대하는 YAML 호환 딕셔너리
        """
        return {
            "version": self.VERSION,
            "snapshot_type": self.SNAPSHOT_TYPE,
            "description": "Live runtime state snapshot from ha_realtime_adapter",
            "nodes": dict(raw_states),
        }


# ── MQTT Publisher ────────────────────────────────────────────────────────────


class MQTTPrefightPublisher:
    """
    Preflight 결과를 MQTT로 발행한다.

    paho-mqtt 미설치 시 자동으로 no-op 모드로 동작한다.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 1883) -> None:
        self.host = host
        self.port = port
        self._client = None

        if HAS_MQTT:
            self._client = _mqtt_module.Client()
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect

    def connect(self) -> None:
        """MQTT 브로커에 연결."""
        if not self._client:
            return
        try:
            self._client.connect(self.host, self.port, keepalive=60)
            self._client.loop_start()
            logger.info("MQTT 발행 클라이언트 연결 | host=%s port=%d", self.host, self.port)
        except Exception as exc:
            logger.warning("MQTT 발행 클라이언트 연결 실패 (계속 진행) | error=%s", exc)
            self._client = None

    def disconnect(self) -> None:
        """MQTT 연결 해제."""
        if self._client:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception as exc:
                logger.warning("MQTT 연결 해제 오류 | error=%s", exc)

    def publish_report(self, experiment_id: str, report: Dict[str, Any]) -> None:
        """
        Preflight 리포트를 MQTT 토픽에 발행한다.

        토픽: experiment/preflight/result/{experiment_id}

        Args:
            experiment_id: 실험 ID
            report: PreflightReport.to_dict() 결과
        """
        if not self._client:
            logger.debug("MQTT 발행 건너뜀 (클라이언트 없음) | experiment=%s", experiment_id)
            return
        topic = f"experiment/preflight/result/{experiment_id}"
        payload = json.dumps(report, ensure_ascii=False)
        try:
            result = self._client.publish(topic, payload, qos=1)
            if result.rc == 0:
                logger.debug("MQTT 발행 성공 | topic=%s", topic)
            else:
                logger.warning("MQTT 발행 실패 | topic=%s rc=%d", topic, result.rc)
        except Exception as exc:
            logger.warning("MQTT 발행 예외 | topic=%s error=%s", topic, exc)

    def publish_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """
        현재 state snapshot을 디버그 토픽에 발행한다.

        토픽: experiment/preflight/snapshot
        """
        if not self._client:
            return
        try:
            payload = json.dumps(snapshot, ensure_ascii=False)
            self._client.publish("experiment/preflight/snapshot", payload, qos=0)
        except Exception as exc:
            logger.warning("MQTT 스냅샷 발행 예외 | error=%s", exc)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT 발행 연결 성공")
        else:
            logger.warning("MQTT 발행 연결 실패 | rc=%d", rc)

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning("MQTT 발행 예상치 못한 연결 해제 | rc=%d", rc)


# ── Adapter Service ───────────────────────────────────────────────────────────


class AdapterService:
    """
    메인 어댑터 서비스.

    주기적으로 상태를 수집하고 aggregator를 호출하여 결과를 발행한다.
    """

    def __init__(
        self,
        repo_root: Path,
        collector_config: CollectorConfig,
        publisher: MQTTPrefightPublisher,
    ) -> None:
        self._repo_root = repo_root
        self._collector_config = collector_config
        self._publisher = publisher
        self._snapshot_builder = StateSnapshotBuilder()
        self._last_snapshot: Optional[Dict[str, Any]] = None
        self._last_reports: Dict[str, Dict[str, Any]] = {}

        # 레지스트리 로드
        try:
            exp_registry = load_registry(repo_root, _EXP_REGISTRY_REL, "experiment_registry")
            node_registry = load_registry(repo_root, _NODE_REGISTRY_REL, "node_registry")
            self._experiment_index = index_experiments(exp_registry)
            self._node_index = index_nodes(node_registry)
            logger.info(
                "레지스트리 로드 완료 | experiments=%d nodes=%d",
                len(self._experiment_index),
                len(self._node_index),
            )
        except PreflightError as exc:
            logger.error("레지스트리 로드 실패 | error=%s", exc)
            self._experiment_index = {}
            self._node_index = {}

    async def run_once(self) -> Dict[str, Dict[str, Any]]:
        """
        상태 수집 → 스냅샷 생성 → 모든 실험에 대해 aggregator 호출 → 발행.

        Returns:
            {experiment_id: report_dict} 결과 딕셔너리
        """
        # 1. 런타임 상태 수집
        raw_states = await collect_all_states(self._collector_config)

        # 2. State snapshot 생성
        snapshot = self._snapshot_builder.build(raw_states)
        self._last_snapshot = snapshot
        self._publisher.publish_snapshot(snapshot)

        # aggregator가 사용할 수 있는 형식으로 변환
        state_for_aggregator: Dict[str, str] = {
            k: v for k, v in snapshot["nodes"].items()
        }

        # 3. 각 실험에 대해 aggregator 실행
        reports: Dict[str, Dict[str, Any]] = {}
        for exp_id, experiment in self._experiment_index.items():
            try:
                report: PreflightReport = aggregate_report(
                    experiment=experiment,
                    node_index=self._node_index,
                    state_snapshot=state_for_aggregator,
                )
                report_dict = report.to_dict()
                reports[exp_id] = report_dict
                self._publisher.publish_report(exp_id, report_dict)
                logger.info(
                    "Preflight 평가 완료 | experiment=%s final_state=%s",
                    exp_id,
                    report.final_state,
                )
            except PreflightError as exc:
                logger.error("Preflight 평가 오류 | experiment=%s error=%s", exp_id, exc)
                reports[exp_id] = {
                    "experiment_id": exp_id,
                    "final_state": "UNKNOWN",
                    "error": str(exc),
                }

        self._last_reports = reports
        return reports

    async def run(self, interval_s: float = 30.0) -> None:
        """
        주기적 수집 루프.

        Args:
            interval_s: 수집 간격 (초)
        """
        logger.info("어댑터 서비스 시작 | interval_s=%.1f", interval_s)
        while True:
            try:
                await self.run_once()
            except Exception as exc:
                logger.error("수집 루프 예외 | error=%s", exc, exc_info=True)
            await asyncio.sleep(interval_s)

    def get_last_snapshot(self) -> Optional[Dict[str, Any]]:
        """마지막 수집 state snapshot을 반환한다."""
        return self._last_snapshot

    def get_last_report(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """특정 실험의 마지막 Preflight 리포트를 반환한다."""
        return self._last_reports.get(experiment_id)

    def get_all_reports(self) -> Dict[str, Dict[str, Any]]:
        """모든 실험의 마지막 Preflight 리포트를 반환한다."""
        return dict(self._last_reports)

    def list_experiment_ids(self):
        """등록된 실험 ID 목록을 반환한다."""
        return list(self._experiment_index.keys())


# ── FastAPI App ───────────────────────────────────────────────────────────────

# 모듈 레벨 캐시
_adapter_service: Optional[AdapterService] = None
_publisher: Optional[MQTTPrefightPublisher] = None
_bg_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 앱 생명주기 - 시작/종료 처리."""
    global _adapter_service, _publisher, _bg_task

    logger.info("HA 리얼타임 어댑터 서비스 시작")

    # 설정 로드
    collector_config = CollectorConfig.from_env()
    repo_root = find_repo_root(_REPO_ROOT)

    # MQTT 발행 클라이언트 초기화
    _publisher = MQTTPrefightPublisher(
        host=collector_config.mqtt_host,
        port=collector_config.mqtt_port,
    )
    _publisher.connect()

    # 어댑터 서비스 초기화
    _adapter_service = AdapterService(
        repo_root=repo_root,
        collector_config=collector_config,
        publisher=_publisher,
    )

    # 초기 수집 실행 (시작 시)
    try:
        await _adapter_service.run_once()
        logger.info("초기 상태 수집 완료")
    except Exception as exc:
        logger.warning("초기 수집 실패 (계속 진행) | error=%s", exc)

    # 백그라운드 수집 루프 시작
    interval_s = float(os.environ.get("ADAPTER_INTERVAL_S", "30"))
    _bg_task = asyncio.create_task(
        _adapter_service.run(interval_s=interval_s)
    )
    logger.info("백그라운드 수집 루프 시작 | interval_s=%.1f", interval_s)

    yield

    # 종료 처리
    logger.info("HA 리얼타임 어댑터 서비스 종료")
    if _bg_task:
        _bg_task.cancel()
        try:
            await _bg_task
        except asyncio.CancelledError:
            pass
    if _publisher:
        _publisher.disconnect()


# FastAPI 앱 정의
app = FastAPI(
    title="HA Realtime Adapter",
    description="Home Assistant realtime preflight readiness adapter",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict:
    """헬스 체크 엔드포인트."""
    return {
        "status": "ok",
        "service": "ha_realtime_adapter",
        "has_snapshot": _adapter_service is not None and _adapter_service.get_last_snapshot() is not None,
    }


@app.get("/readiness/{experiment_id}")
async def get_readiness(experiment_id: str) -> dict:
    """
    특정 실험의 Preflight 준비도를 반환한다.

    Args:
        experiment_id: 실험 ID

    Returns:
        PreflightReport JSON

    Raises:
        404: 실험 ID를 찾을 수 없는 경우
    """
    if _adapter_service is None:
        raise HTTPException(status_code=503, detail="Adapter service not ready")

    report = _adapter_service.get_last_report(experiment_id)
    if report is None:
        known_ids = _adapter_service.list_experiment_ids()
        raise HTTPException(
            status_code=404,
            detail=f"Experiment '{experiment_id}' not found. Known: {known_ids}",
        )
    return report


@app.get("/readiness")
async def list_readiness() -> dict:
    """모든 실험의 Preflight 준비도를 반환한다."""
    if _adapter_service is None:
        raise HTTPException(status_code=503, detail="Adapter service not ready")
    return {
        "experiments": _adapter_service.get_all_reports(),
        "snapshot": _adapter_service.get_last_snapshot(),
    }


@app.post("/readiness/refresh")
async def force_refresh() -> dict:
    """
    즉시 상태 수집 및 Preflight 평가를 강제 실행한다.

    Returns:
        모든 실험의 최신 PreflightReport
    """
    if _adapter_service is None:
        raise HTTPException(status_code=503, detail="Adapter service not ready")
    try:
        reports = await _adapter_service.run_once()
        return {"refreshed": True, "experiments": reports}
    except Exception as exc:
        logger.error("강제 새로고침 오류 | error=%s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/snapshot")
async def get_snapshot() -> dict:
    """현재 state snapshot을 반환한다 (디버그용)."""
    if _adapter_service is None:
        raise HTTPException(status_code=503, detail="Adapter service not ready")
    snapshot = _adapter_service.get_last_snapshot()
    if snapshot is None:
        return {"snapshot": None, "message": "No snapshot collected yet"}
    return {"snapshot": snapshot}


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)

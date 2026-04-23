"""
엣지 컨트롤러 메인 진입점.

FastAPI 애플리케이션 정의 및 MQTT 리스너 통합.
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError
from starlette.responses import JSONResponse

from policy_router.models import PolicyRouterInput

from .mqtt_client import create_mqtt_client, MQTTClient
from .models import OrchestratorOutput
from .orchestrator import orchestrate
from .policy_loader import load_fault_rules, load_low_risk_actions, load_policy_table

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# 모듈 레벨 캐시
_policy_cache: dict = {}
_mqtt_client: MQTTClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리.

    시작: 정책 파일 로드, MQTT 연결
    종료: MQTT 정리
    """
    logger.info("엣지 컨트롤러 서비스 시작")

    # 정책 파일 로드
    try:
        _policy_cache["policy_table"] = load_policy_table()
        _policy_cache["low_risk_actions"] = load_low_risk_actions()
        _policy_cache["fault_rules"] = load_fault_rules()
        logger.info("모든 정책 파일 로드 완료")
    except Exception as exc:
        logger.error("정책 파일 로드 실패: %s", exc, exc_info=True)
        raise

    # MQTT 클라이언트 초기화
    global _mqtt_client
    try:
        _mqtt_client = create_mqtt_client(on_message_callback=_on_mqtt_message)
        if _mqtt_client:
            _mqtt_client.connect()
            _mqtt_client.start()
            logger.info("MQTT 클라이언트 시작됨")
        else:
            logger.warning("MQTT 클라이언트 미초기화 - MQTT 기능 비활성화")
    except Exception as exc:
        logger.warning("MQTT 초기화 실패 (계속 진행): %s", exc)
        _mqtt_client = None

    yield

    # 종료 정리
    logger.info("엣지 컨트롤러 서비스 종료")
    if _mqtt_client:
        try:
            _mqtt_client.stop()
            _mqtt_client.disconnect()
            logger.info("MQTT 클라이언트 정지됨")
        except Exception as exc:
            logger.error("MQTT 정리 오류: %s", exc)


# FastAPI 앱 정의
app = FastAPI(
    title="Edge Controller App",
    description="Policy-driven deterministic routing and validation orchestrator",
    version="1.0.0",
    lifespan=lifespan,
)


# 예외 핸들러
@app.exception_handler(ValidationError)
async def _validation_error_handler(request: Request, exc: ValidationError):
    """Pydantic 검증 오류 핸들러."""
    logger.warning("검증 오류: %s", exc)
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


# 헬스 체크
@app.get("/health")
async def health_check() -> dict:
    """헬스 체크 엔드포인트."""
    return {
        "status": "ok",
        "service": "edge_controller_app",
        "policy_loaded": len(_policy_cache) > 0,
    }


# 오케스트레이션 엔드포인트 (테스트/직접 호출용)
@app.post("/orchestrate")
async def orchestrate_endpoint(
    router_input: PolicyRouterInput,
) -> OrchestratorOutput:
    """
    정책 라우팅 및 검증 오케스트레이션 엔드포인트.

    Args:
        router_input: 정책 라우터 입력

    Returns:
        오케스트레이션 결과

    Raises:
        HTTPException: 처리 오류
    """
    try:
        result = await orchestrate(router_input)
        logger.info(
            "오케스트레이션 성공 | correlation_id=%s route_class=%s",
            result.audit_correlation_id,
            result.route_class,
        )
        return result

    except ValueError as exc:
        logger.error("검증 오류: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except Exception as exc:
        logger.error("처리 오류: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


# MQTT 메시지 콜백
def _on_mqtt_message(payload_str: str) -> None:
    """
    MQTT 메시지 수신 콜백.

    JSON을 파싱하여 오케스트레이션을 수행하고 결과를 퍼블리시한다.

    Args:
        payload_str: JSON 문자열 페이로드
    """
    try:
        # JSON 파싱
        payload_dict = json.loads(payload_str)
        logger.debug("MQTT 메시지 파싱: correlation_id=%s", payload_dict.get("routing_metadata", {}).get("audit_correlation_id"))

        # PolicyRouterInput 검증
        router_input = PolicyRouterInput(**payload_dict)

        # 오케스트레이션 실행 (동기 호출을 위해 asyncio.run 필요)
        import asyncio

        result = asyncio.run(orchestrate(router_input))

        # 결과 퍼블리시
        if _mqtt_client:
            result_json = json.dumps(result.model_dump(), default=str)
            _mqtt_client.publish(
                "smarthome/audit/validator_output",
                result_json,
            )
            logger.info(
                "MQTT 결과 퍼블리시 | correlation_id=%s route_class=%s",
                result.audit_correlation_id,
                result.route_class,
            )
        else:
            logger.warning("MQTT 결과 퍼블리시 불가 - 클라이언트 미초기화")

    except json.JSONDecodeError as exc:
        logger.error("JSON 파싱 오류: %s", exc)

    except ValidationError as exc:
        logger.error("입력 검증 오류: %s", exc)

    except Exception as exc:
        logger.error("MQTT 메시지 처리 오류: %s", exc, exc_info=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )

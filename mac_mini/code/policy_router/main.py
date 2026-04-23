"""
Policy Router FastAPI 서비스.

/route  : PolicyRouterInput → PolicyRouterOutput (결정론적 라우팅)
/health : 헬스 체크

LLM 을 직접 호출하지 않는다.
freshness, fault status, validation metadata 를 LLM 실행 컨텍스트에 포함하지 않는다.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .models import PolicyRouterInput, PolicyRouterOutput
from .policy_loader import load_low_risk_actions, load_policy_table
from .router import _POLICY_TABLE, _LOW_RISK_ACTIONS, route

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 frozen 정책 파일을 미리 로드해 응답 지연을 줄인다."""
    logger.info("Policy Router 시작: frozen 정책 파일 로드 중...")
    _POLICY_TABLE.update(load_policy_table())
    _LOW_RISK_ACTIONS.update(load_low_risk_actions())
    logger.info(
        "정책 파일 로드 완료 | policy_table=%s low_risk_actions=%s",
        _POLICY_TABLE.get("version"),
        _LOW_RISK_ACTIONS.get("version"),
    )
    yield
    logger.info("Policy Router 종료")


app = FastAPI(
    title="Policy Router",
    description="결정론적 라우팅 서비스 - CLASS_0 / CLASS_1 / CLASS_2 분기",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(ValidationError)
async def _validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Pydantic 검증 오류를 422 로 반환한다."""
    logger.warning("입력 검증 실패: %s", exc)
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.post("/route", response_model=PolicyRouterOutput)
async def route_event(router_input: PolicyRouterInput) -> PolicyRouterOutput:
    """
    이벤트/컨텍스트 JSON 을 받아 CLASS_0 / CLASS_1 / CLASS_2 로 결정론적 라우팅한다.
    LLM 을 직접 호출하지 않는다.
    """
    try:
        return route(router_input)
    except Exception as exc:
        logger.error("라우팅 중 예상치 못한 오류: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="내부 라우터 오류")


@app.get("/health")
async def health_check() -> dict:
    """서비스 헬스 체크."""
    return {"status": "ok", "service": "policy_router"}

"""
Context-Integrity Safe Deferral Handler FastAPI 서비스.

엔드포인트:
  POST /deferral/start        : clarification session 시작 (WAITING 상태 반환)
  POST /deferral/button_input : 버튼 입력 처리 (RESOLVED or WAITING)
  POST /deferral/timeout      : 타임아웃 처리 (C201 emit → CLASS_2 에스컬레이션)
  GET  /health                : 헬스 체크

자유 대화 생성은 절대 금지한다.
clarification flow 는 버튼 기반으로만 동작한다.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .handler import emit_timeout_event, resolve_button_input, start_clarification_session
from .models import ButtonInput, DeferralHandlerInput, DeferralHandlerOutput
from .policy_loader import load_policy_table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

_policy_cache: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 frozen 정책 파일을 미리 로드한다."""
    logger.info("Safe Deferral Handler 시작: frozen 정책 파일 로드 중...")
    _policy_cache["policy_table"] = load_policy_table()
    logger.info(
        "정책 파일 로드 완료 | version=%s",
        _policy_cache["policy_table"].get("version"),
    )
    yield
    logger.info("Safe Deferral Handler 종료")


app = FastAPI(
    title="Context-Integrity Safe Deferral Handler",
    description="버튼 기반 bounded clarification flow - 자유 대화 생성 금지",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(ValidationError)
async def _validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Pydantic 검증 오류를 422 로 반환한다."""
    logger.warning("입력 검증 실패: %s", exc)
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.post("/deferral/start", response_model=DeferralHandlerOutput)
async def start_session(handler_input: DeferralHandlerInput) -> DeferralHandlerOutput:
    """
    clarification session 을 시작한다.
    WAITING 상태와 함께 버튼 매핑이 포함된 옵션 목록을 반환한다.
    """
    try:
        return start_clarification_session(handler_input)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("clarification session 시작 오류: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="내부 핸들러 오류")


@app.post("/deferral/button_input", response_model=DeferralHandlerOutput)
async def handle_button(
    handler_input: DeferralHandlerInput,
    button_input: ButtonInput,
) -> DeferralHandlerOutput:
    """
    버튼 입력을 받아 후보 옵션을 resolve 한다.
    유효한 hit_count 이면 RESOLVED, 범위 초과이면 WAITING 을 반환한다.
    """
    try:
        return resolve_button_input(handler_input, button_input)
    except Exception as exc:
        logger.error("버튼 입력 처리 오류: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="내부 핸들러 오류")


@app.post("/deferral/timeout", response_model=DeferralHandlerOutput)
async def handle_timeout(handler_input: DeferralHandlerInput) -> DeferralHandlerOutput:
    """
    타임아웃을 처리한다.
    C201 timeout_event 를 emit 하고 TIMEOUT 상태를 반환한다.
    호출자는 이 결과를 보고 CLASS_2 에스컬레이션을 진행해야 한다.
    """
    try:
        return emit_timeout_event(handler_input)
    except Exception as exc:
        logger.error("타임아웃 처리 오류: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="내부 핸들러 오류")


@app.get("/health")
async def health_check() -> dict:
    """서비스 헬스 체크."""
    return {"status": "ok", "service": "safe_deferral_handler"}

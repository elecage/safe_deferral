"""
Caregiver Confirmation Backend FastAPI 서비스.

엔드포인트:
  POST /confirm            : ConfirmationRequest 직접 처리
  POST /confirm/telegram   : Telegram inline button callback 처리
  GET  /health             : 헬스 체크

확인 결과는 audit_logging_service 채널로만 기록한다.
직접 SQLite 에 쓰지 않는다.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .confirmer import confirm, parse_telegram_callback
from .models import ConfirmationRequest, ConfirmationResponse, TelegramCallbackUpdate
from .policy_loader import load_low_risk_actions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

_policy_cache: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 frozen 정책 파일을 미리 로드한다."""
    logger.info("Caregiver Confirmation Backend 시작: frozen 정책 파일 로드 중...")
    _policy_cache["low_risk_actions"] = load_low_risk_actions()
    logger.info(
        "정책 파일 로드 완료 | version=%s",
        _policy_cache["low_risk_actions"].get("version"),
    )
    yield
    logger.info("Caregiver Confirmation Backend 종료")


app = FastAPI(
    title="Caregiver Confirmation Backend",
    description="보호자 bounded 원격 액션 확인 - 허용 목록 외 액션 거부",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(ValidationError)
async def _validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    logger.warning("입력 검증 실패: %s", exc)
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.post("/confirm", response_model=ConfirmationResponse)
async def confirm_action(req: ConfirmationRequest) -> ConfirmationResponse:
    """
    보호자 확인 요청을 처리한다.
    허용 목록 내 저위험 액션만 승인하며, 그 외는 거부한다.
    """
    try:
        return confirm(req)
    except Exception as exc:
        logger.error("확인 처리 오류: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="내부 확인 처리 오류")


@app.post("/confirm/telegram", response_model=ConfirmationResponse)
async def confirm_telegram(update: TelegramCallbackUpdate) -> ConfirmationResponse:
    """
    Telegram inline button callback_data 를 파싱하여 확인 요청으로 처리한다.
    callback_data 포맷: "confirm:<action>:<target_device>:<correlation_id>"
    """
    try:
        req = parse_telegram_callback(update)
        return confirm(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Telegram 콜백 처리 오류: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="내부 확인 처리 오류")


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "service": "caregiver_confirmation_backend"}

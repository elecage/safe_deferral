"""
Caregiver Confirmation Backend 입력/출력 Pydantic 모델.

보호자는 notification_backend 가 보낸 Telegram 인라인 버튼 또는
mock API 엔드포인트를 통해 확인 요청을 보낸다.

반환값은 세 가지 중 하나:
  - CONFIRMED_LOW_RISK_ACTION   : 허용 목록 내 저위험 액션 확인 완료
  - REJECTED_HIGH_RISK_ACTION   : 허용 목록 밖 액션 - 거부
  - INVALID_CONFIRMATION        : 형식 오류 / 필수 필드 누락 등
"""
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ConfirmationStatus(str, Enum):
    CONFIRMED_LOW_RISK_ACTION = "CONFIRMED_LOW_RISK_ACTION"
    REJECTED_HIGH_RISK_ACTION = "REJECTED_HIGH_RISK_ACTION"
    INVALID_CONFIRMATION = "INVALID_CONFIRMATION"


class ConfirmationRequest(BaseModel):
    """
    보호자 확인 요청.
    notification_backend 가 보낸 알림에서 보호자가 선택한 액션 정보를 담는다.
    """

    model_config = ConfigDict(extra="forbid")

    audit_correlation_id: str = Field(..., min_length=1)
    # 보호자가 확인하려는 액션과 타겟 기기
    action: str = Field(..., min_length=1)
    target_device: str = Field(..., min_length=1)
    # Telegram callback_data 또는 mock API 에서 전달되는 확인자 식별자 (선택)
    confirmed_by: Optional[str] = None


class ConfirmationResponse(BaseModel):
    """보호자 확인 결과."""

    status: ConfirmationStatus
    audit_correlation_id: str
    action: Optional[str] = None
    target_device: Optional[str] = None
    reason: str = ""


class TelegramCallbackUpdate(BaseModel):
    """
    Telegram inline keyboard callback_data 를 파싱한 update.
    callback_data 포맷: "confirm:<action>:<target_device>:<correlation_id>"
    """

    model_config = ConfigDict(extra="forbid")

    callback_data: str = Field(..., min_length=1)
    from_user_id: Optional[int] = None
    message_id: Optional[int] = None

"""
Notification Backend 페이로드 Pydantic 모델.

class_2_notification_payload_schema_v1_0_0_FROZEN.json 을 따른다.
스키마에 없는 ad hoc 필드를 임의로 추가하지 않는다.

CLASS_0 긴급 알림과 CLASS_2 보호자 에스컬레이션 두 가지 페이로드를 정의한다.
"""
import time
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


def _now_ms() -> int:
    return int(time.time() * 1000)


class Class2NotificationPayload(BaseModel):
    """
    CLASS_2 보호자 에스컬레이션 페이로드.
    class_2_notification_payload_schema_v1_0_0_FROZEN.json 준수.
    required: event_summary, context_summary, unresolved_reason, manual_confirmation_path
    """

    model_config = ConfigDict(extra="forbid")

    # ── required ──
    event_summary: str = Field(..., min_length=1, max_length=300)
    context_summary: str = Field(..., min_length=1, max_length=800)
    unresolved_reason: str = Field(..., min_length=1, max_length=200)
    manual_confirmation_path: str = Field(..., min_length=1, max_length=300)

    # ── schema_governed (optional) ──
    audit_correlation_id: Optional[str] = Field(None, max_length=120)
    timestamp_ms: int = Field(default_factory=_now_ms)
    notification_channel: Optional[Literal["telegram", "local_dashboard", "sms", "other"]] = None
    source_layer: Optional[
        Literal[
            "policy_router",
            "validator",
            "context_integrity_safe_deferral_handler",
            "dispatcher",
            "system",
        ]
    ] = None
    exception_trigger_id: Optional[
        Literal["C201", "C202", "C203", "C204", "C205"]
    ] = None


class Class0AlertPayload(BaseModel):
    """
    CLASS_0 응급 알림 페이로드.
    응급 상황에서 즉시 보내는 알림이므로 간결하게 유지한다.
    class_2_notification_payload_schema 를 기반으로 하되
    CLASS_0 필수 필드를 추가한다.
    """

    model_config = ConfigDict(extra="forbid")

    event_summary: str = Field(..., min_length=1, max_length=300)
    context_summary: str = Field(..., min_length=1, max_length=800)
    emergency_trigger_id: str = Field(..., description="E001~E005")
    emergency_actions: list = Field(default_factory=list)
    audit_correlation_id: Optional[str] = Field(None, max_length=120)
    timestamp_ms: int = Field(default_factory=_now_ms)
    notification_channel: Optional[Literal["telegram", "local_dashboard", "sms", "other"]] = None


class NotificationResult(BaseModel):
    """알림 전송 결과."""

    success: bool
    channel: str
    dry_run: bool = False
    error_message: Optional[str] = None
    sent_at_ms: int = Field(default_factory=_now_ms)

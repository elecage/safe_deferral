"""
Audit Logging Service 이벤트 Pydantic 모델.

각 이벤트 타입은 MQTT topic audit/log/<type> 으로 publish 되고
audit_logging_service 가 단독으로 SQLite 에 persist 한다.

테이블별 이벤트:
  - routing_events       : policy_router 라우팅 결정
  - validator_results    : deterministic_validator 검증 결과
  - deferral_events      : safe_deferral_handler 세션 시작/resolve
  - timeout_events       : safe_deferral_handler C201 타임아웃
  - escalation_events    : CLASS_2 에스컬레이션
  - caregiver_actions    : 보호자 확인/개입 기록
  - actuation_ack_events : actuator dispatcher ACK 결과
"""
import time
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


def _now_ms() -> int:
    return int(time.time() * 1000)


# ── 공통 베이스 ──────────────────────────────────────────────────────────────


class AuditEventBase(BaseModel):
    """모든 감사 이벤트 공통 필드."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(..., min_length=1, description="이벤트 고유 ID (UUID 권장)")
    audit_correlation_id: str = Field(..., min_length=1)
    timestamp_ms: int = Field(default_factory=_now_ms)
    class_label: str = Field(..., description="CLASS_0 / CLASS_1 / CLASS_2")
    reason: str = Field(..., description="이벤트 발생 이유 요약")
    payload_summary: Optional[str] = Field(None, max_length=500)


# ── 테이블별 이벤트 모델 ─────────────────────────────────────────────────────


class RoutingEvent(AuditEventBase):
    """routing_events 테이블 - policy_router 의 라우팅 결정."""

    source_node_id: Optional[str] = None
    route_class: str = Field(..., description="CLASS_0 / CLASS_1 / CLASS_2")
    llm_invocation_allowed: bool = False
    emergency_trigger_id: Optional[str] = None


class ValidatorResult(AuditEventBase):
    """validator_results 테이블 - deterministic_validator 의 검증 결과."""

    validation_status: str = Field(
        ..., description="approved / safe_deferral / rejected_escalation"
    )
    routing_target: str
    exception_trigger_id: str = "none"
    deferral_reason: Optional[str] = None


class DeferralEvent(AuditEventBase):
    """deferral_events 테이블 - safe_deferral_handler 의 세션 시작/resolve."""

    deferral_status: str = Field(..., description="waiting / resolved")
    deferral_reason: Optional[str] = None
    resolved_action: Optional[str] = None
    resolved_target: Optional[str] = None
    options_count: int = 0


class TimeoutEvent(AuditEventBase):
    """timeout_events 테이블 - C201 타임아웃."""

    timeout_trigger_id: str = "C201"
    options_presented: int = 0


class EscalationEvent(AuditEventBase):
    """escalation_events 테이블 - CLASS_2 에스컬레이션."""

    exception_trigger_id: str
    source_layer: str
    notification_channel: Optional[str] = None


class CaregiverAction(AuditEventBase):
    """caregiver_actions 테이블 - 보호자 확인/개입."""

    action_type: str = Field(..., description="confirmed / rejected / timed_out")
    confirmed_action: Optional[str] = None
    confirmed_target: Optional[str] = None


class ActuationAckEvent(AuditEventBase):
    """actuation_ack_events 테이블 - actuator dispatcher ACK."""

    action: str
    target_device: str
    ack_status: str = Field(..., description="success / timeout / failure")
    ack_latency_ms: Optional[int] = None

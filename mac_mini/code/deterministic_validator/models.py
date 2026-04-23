"""
Deterministic Validator 입력/출력 Pydantic 모델.

입력은 CLASS_1 경로에서만 허용된다.

출력 모델은 다음 frozen 스키마를 따른다.
- validator_output_schema_v1_1_0_FROZEN.json

후보 액션 입력은 다음 frozen 스키마를 따른다.
- candidate_action_schema_v1_0_0_FROZEN.json
"""
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── candidate_action_schema_v1_0_0_FROZEN.json 기반 ─────────────────────────


class CandidateAction(BaseModel):
    """
    LLM 이 제안하는 단일 후보 액션.
    proposed_action 이 safe_deferral 인 경우 target_device 는 반드시 'none',
    deferral_reason 이 필수이다.
    """

    model_config = ConfigDict(extra="forbid")

    proposed_action: Literal["light_on", "light_off", "safe_deferral"]
    target_device: Literal["living_room_light", "bedroom_light", "none"]
    deferral_reason: Optional[
        Literal[
            "ambiguous_target",
            "insufficient_context",
            "policy_restriction",
            "unresolved_multi_candidate",
        ]
    ] = None
    rationale_summary: Optional[str] = Field(
        None, max_length=160, description="로깅/디버깅 전용 - 안전 라우팅에 사용 금지"
    )


# ── Validator 입력 모델 ──────────────────────────────────────────────────────


class DeviceState(BaseModel):
    """검증 시점의 단일 기기 상태."""

    model_config = ConfigDict(extra="forbid")

    device_id: str
    state: str


class ValidatorInput(BaseModel):
    """
    Deterministic Validator 입력.
    CLASS_1 경로에서만 허용된다.
    """

    model_config = ConfigDict(extra="forbid")

    audit_correlation_id: str = Field(..., min_length=1)
    # LLM 이 제안한 후보 액션 목록 (1~N개)
    candidate_actions: List[CandidateAction] = Field(..., min_length=1)
    # 현재 기기 상태 목록 (ACK 검증에도 사용)
    current_device_states: List[DeviceState]


# ── validator_output_schema_v1_1_0_FROZEN.json 기반 출력 모델 ───────────────


class ValidationStatus(str, Enum):
    APPROVED = "approved"
    SAFE_DEFERRAL = "safe_deferral"
    REJECTED_ESCALATION = "rejected_escalation"


class RoutingTarget(str, Enum):
    ACTUATOR_DISPATCHER = "actuator_dispatcher"
    CONTEXT_INTEGRITY_SAFE_DEFERRAL_HANDLER = "context_integrity_safe_deferral_handler"
    CLASS_2_ESCALATION = "class_2_escalation"


class ExceptionTriggerID(str, Enum):
    NONE = "none"
    C201 = "C201"
    C202 = "C202"
    C203 = "C203"
    C204 = "C204"
    C205 = "C205"


class DeferralReason(str, Enum):
    AMBIGUOUS_TARGET = "ambiguous_target"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    POLICY_RESTRICTION = "policy_restriction"
    UNRESOLVED_MULTI_CANDIDATE = "unresolved_multi_candidate"


class ExecutablePayload(BaseModel):
    """
    validation_status == approved 일 때만 존재한다.
    actuator_dispatcher 가 이 페이로드를 실행하고 ACK 를 기다린다.
    """

    model_config = ConfigDict(extra="forbid")

    action: Literal["light_on", "light_off"]
    target_device: Literal["living_room_light", "bedroom_light"]
    requires_ack: bool = Field(..., description="정책 기반 폐루프 제어 플래그")


class ValidatorOutput(BaseModel):
    """
    Deterministic Validator 출력.
    validator_output_schema_v1_1_0_FROZEN.json 준수.

    - approved       → routing_target=actuator_dispatcher, executable_payload 필수
    - safe_deferral  → routing_target=context_integrity_safe_deferral_handler, deferral_reason 필수
    - rejected_escalation → routing_target=class_2_escalation, exception_trigger_id 필수
    """

    validation_status: ValidationStatus
    routing_target: RoutingTarget
    exception_trigger_id: ExceptionTriggerID = ExceptionTriggerID.NONE
    executable_payload: Optional[ExecutablePayload] = None
    deferral_reason: Optional[DeferralReason] = None
    # 감사 추적용 (스키마 외 필드이나 로깅에 필요)
    audit_correlation_id: str = ""
    # safe_deferral 시 bounded clarification 에 전달할 후보 목록 (최대 3개)
    deferral_candidates: Optional[List[CandidateAction]] = None

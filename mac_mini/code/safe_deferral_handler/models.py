"""
Context-Integrity Safe Deferral Handler 입력/출력 Pydantic 모델.

이 핸들러는 Deterministic Validator 가 SAFE_DEFERRAL 을 결정한 후 호출된다.
입력으로 bounded candidate option 목록(2~3개)을 받아
버튼 기반 clarification flow 를 구성한다.

clarification 모달리티:
  1 hit  = 옵션 A
  2 hits = 옵션 B
  3 hits = 옵션 C (선택적)

자유 대화 생성은 절대 금지한다.
타임아웃 시 CLASS_2 에스컬레이션을 위한 timeout_event 를 emit 한다.
"""
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ButtonMapping(str, Enum):
    """버튼 입력 → 후보 옵션 매핑."""

    ONE_HIT = "1_hit"
    TWO_HITS = "2_hits"
    THREE_HITS = "3_hits"


class ClarificationOption(BaseModel):
    """단일 clarification 옵션 (버튼 매핑 + 후보 액션 요약)."""

    model_config = ConfigDict(extra="forbid")

    button_mapping: ButtonMapping
    action: str  # 예: "light_on"
    target_device: str  # 예: "living_room_light"
    display_label: str = Field(..., max_length=60, description="사용자에게 보여줄 짧은 레이블")


class DeferralHandlerInput(BaseModel):
    """
    Safe Deferral Handler 입력.
    Deterministic Validator 의 deferral_candidates (2~3개) 를 받는다.
    """

    model_config = ConfigDict(extra="forbid")

    audit_correlation_id: str = Field(..., min_length=1)
    deferral_reason: str
    # 2~3개의 bounded 후보 옵션 (action, target_device 쌍)
    candidate_options: List[ClarificationOption] = Field(..., min_length=2, max_length=3)


class ClarificationFlowStatus(str, Enum):
    WAITING = "waiting"
    RESOLVED = "resolved"
    TIMEOUT = "timeout"


class DeferralHandlerOutput(BaseModel):
    """
    Safe Deferral Handler 출력.
    - WAITING: clarification 대기 중 (버튼 입력 기다리는 상태)
    - RESOLVED: 사용자가 버튼으로 옵션을 선택함
    - TIMEOUT: 제한 시간 내 선택 없음 → CLASS_2 에스컬레이션 필요
    """

    status: ClarificationFlowStatus
    audit_correlation_id: str
    # RESOLVED 시: 선택된 옵션
    resolved_option: Optional[ClarificationOption] = None
    # TIMEOUT 시: CLASS_2 에스컬레이션을 위한 트리거 ID
    timeout_trigger_id: Optional[Literal["C201"]] = None
    # clarification 에 사용된 옵션 목록 (로깅/감사 목적)
    presented_options: Optional[List[ClarificationOption]] = None


class ButtonInput(BaseModel):
    """버튼 입력 이벤트 - clarification flow 에서 사용자 응답을 나타낸다."""

    model_config = ConfigDict(extra="forbid")

    hit_count: int = Field(..., ge=1, le=3, description="버튼 타격 횟수 (1~3)")
    timestamp_ms: int


class TimeoutEvent(BaseModel):
    """타임아웃 이벤트 - CLASS_2 에스컬레이션 트리거로 사용된다."""

    model_config = ConfigDict(extra="forbid")

    audit_correlation_id: str
    trigger_id: Literal["C201"] = "C201"
    reason: str = "context_integrity_safe_deferral_timeout"
    timestamp_ms: int

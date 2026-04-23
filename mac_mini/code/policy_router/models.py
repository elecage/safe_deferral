"""
Policy Router 입력/출력 Pydantic 모델.

입력 모델은 다음 frozen 스키마를 따른다.
- policy_router_input_schema_v1_1_1_FROZEN.json (최상위 래퍼)
- context_schema_v1_0_0_FROZEN.json (pure_context_payload 내부)

출력 모델(PolicyRouterOutput)은 Prompt 1 요구사항을 충족한다.
"""
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── context_schema_v1_0_0_FROZEN.json 기반 ──────────────────────────────────


class EventType(str, Enum):
    BUTTON = "button"
    SENSOR = "sensor"
    SYSTEM = "system"


class TriggerEvent(BaseModel):
    """
    trigger_event 섹션.
    timestamp_ms 는 staleness 판단 전용이며 LLM 프롬프트에 전달해서는 안 된다.
    """

    model_config = ConfigDict(extra="forbid")

    event_type: EventType
    event_code: str
    timestamp_ms: int = Field(..., description="staleness 판단 전용 - LLM 프롬프트 전달 금지")


class EnvironmentalContext(BaseModel):
    """순수 물리 환경 정보. 모든 필드가 required (missing-state fault 감지를 위해)."""

    model_config = ConfigDict(extra="forbid")

    temperature: float
    illuminance: float
    occupancy_detected: bool
    smoke_detected: bool
    gas_detected: bool


class DeviceStates(BaseModel):
    """제어 대상 기기의 현재 상태. context_schema 의 device_states 섹션."""

    model_config = ConfigDict(extra="forbid")

    living_room_light: Literal["on", "off"]
    bedroom_light: Literal["on", "off"]
    living_room_blind: Literal["open", "closed"]
    tv_main: Literal["on", "off", "playing", "standby"]


class PureContextPayload(BaseModel):
    """
    LLM 프롬프트 조합에 전달 가능한 유일한 순수 컨텍스트 페이로드.
    routing_metadata(네트워크 상태, ingest 타임스탬프 등)는 포함하지 않는다.
    """

    model_config = ConfigDict(extra="forbid")

    trigger_event: TriggerEvent
    environmental_context: EnvironmentalContext
    device_states: DeviceStates


# ── policy_router_input_schema_v1_1_1_FROZEN.json 기반 ──────────────────────


class NetworkStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


class RoutingMetadata(BaseModel):
    """
    라우팅 메타데이터 - LLM 실행 컨텍스트에서 분리되는 운영 정보.
    ingest_timestamp_ms 와 network_status 는 안전 fallback 판단에만 사용한다.
    """

    model_config = ConfigDict(extra="forbid")

    audit_correlation_id: str = Field(..., min_length=1)
    ingest_timestamp_ms: int
    network_status: NetworkStatus


class PolicyRouterInput(BaseModel):
    """Policy Router 최상위 입력 래퍼. policy_router_input_schema_v1_1_1_FROZEN.json 준수."""

    model_config = ConfigDict(extra="forbid")

    source_node_id: str = Field(..., min_length=1)
    routing_metadata: RoutingMetadata
    pure_context_payload: PureContextPayload


# ── Policy Router 출력 모델 ──────────────────────────────────────────────────


class RouteClass(str, Enum):
    CLASS_0 = "CLASS_0"
    CLASS_1 = "CLASS_1"
    CLASS_2 = "CLASS_2"


class Class2TriggerID(str, Enum):
    """CLASS_2 에스컬레이션 트리거 ID. policy_table 의 class_2_escalation.triggers 와 정합."""

    NONE = "none"
    C201 = "C201"
    C202 = "C202"
    C203 = "C203"
    C204 = "C204"
    C205 = "C205"


class PolicyRouterOutput(BaseModel):
    """
    Policy Router 출력.
    - route_class: CLASS_0 / CLASS_1 / CLASS_2
    - route_reason: 라우팅 결정 이유 (로깅/감사용)
    - llm_invocation_allowed: CLASS_1 이고 조건 충족 시에만 True
    - policy_constraints: 다음 단계(validator, deferral handler 등)가 참조할 정책 제약 값
    - exception_trigger_id: CLASS_2 시 해당 트리거 ID, 나머지는 "none"
    - emergency_actions: CLASS_0 시 즉시 실행할 액션 목록
    - emergency_trigger_id: CLASS_0 시 발동된 트리거 ID (E001~E005)
    """

    route_class: RouteClass
    route_reason: str
    llm_invocation_allowed: bool
    policy_constraints: Dict[str, Any]
    audit_correlation_id: str
    exception_trigger_id: Class2TriggerID = Class2TriggerID.NONE
    emergency_actions: Optional[List[str]] = None
    emergency_trigger_id: Optional[str] = None

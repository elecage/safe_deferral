"""
Policy Router 핵심 라우팅 로직.

모든 판단 기준(임계값, 트리거 조건, 타임아웃)은
policy_table_v1_1_2_FROZEN.json 에서 읽어온다. 하드코딩 금지.

라우팅 우선순위:
  1. CLASS_0 응급 트리거 확인 (E001~E005) - staleness 검사보다 우선
  2. staleness 검사 → CLASS_2 (C204)
  3. 나머지 → CLASS_1

CLASS_0 을 staleness 보다 먼저 검사하는 이유:
  응급 상황(화재, 가스 누출, 낙상 등)에서 이벤트 지연을 이유로
  보호 조치를 생략하는 것은 더 위험하기 때문이다.
"""
import logging
from typing import Any, Dict, Optional

from .models import (
    Class2TriggerID,
    PolicyRouterInput,
    PolicyRouterOutput,
    RouteClass,
)
from .policy_loader import load_low_risk_actions, load_policy_table

logger = logging.getLogger(__name__)

# 모듈 수준 정책 캐시 (최초 호출 시 로드, 이후 재사용)
_POLICY_TABLE: Dict[str, Any] = {}
_LOW_RISK_ACTIONS: Dict[str, Any] = {}


def _ensure_policy_loaded() -> None:
    """정책 파일이 아직 로드되지 않았으면 로드한다."""
    global _POLICY_TABLE, _LOW_RISK_ACTIONS
    if not _POLICY_TABLE:
        _POLICY_TABLE = load_policy_table()
        logger.info(
            "policy_table 로드 완료 | version=%s", _POLICY_TABLE.get("version")
        )
    if not _LOW_RISK_ACTIONS:
        _LOW_RISK_ACTIONS = load_low_risk_actions()
        logger.info(
            "low_risk_actions 로드 완료 | version=%s",
            _LOW_RISK_ACTIONS.get("version"),
        )


def _get_global_constraints() -> Dict[str, Any]:
    return _POLICY_TABLE.get("global_constraints", {})


def _get_class0_triggers() -> list:
    return (
        _POLICY_TABLE.get("routing_policies", {})
        .get("class_0_emergency", {})
        .get("triggers", [])
    )


def _get_class0_actions() -> list:
    return (
        _POLICY_TABLE.get("routing_policies", {})
        .get("class_0_emergency", {})
        .get("actions", [])
    )


def _get_class1_constraints() -> Dict[str, Any]:
    return (
        _POLICY_TABLE.get("routing_policies", {})
        .get("class_1_low_risk", {})
        .get("constraints", {})
    )


def _check_staleness(router_input: PolicyRouterInput) -> bool:
    """
    trigger_event.timestamp_ms 와 ingest_timestamp_ms 의 차이가
    freshness_threshold_ms(정책 기준) 를 초과하면 stale 로 판단한다.
    """
    threshold_ms = _get_global_constraints().get("freshness_threshold_ms", 3000)
    event_ts = router_input.pure_context_payload.trigger_event.timestamp_ms
    ingest_ts = router_input.routing_metadata.ingest_timestamp_ms
    age_ms = ingest_ts - event_ts
    return age_ms > threshold_ms


def _check_class0_emergency(
    router_input: PolicyRouterInput,
) -> Optional[Dict[str, Any]]:
    """
    E001~E005 중 하나라도 충족하면 해당 trigger dict 를 반환한다.
    아무것도 해당하지 않으면 None 을 반환한다.
    트리거 리스트 순서대로 평가하며 첫 번째 매칭에서 즉시 반환한다.
    """
    ctx = router_input.pure_context_payload
    env = ctx.environmental_context
    trig = ctx.trigger_event

    for trigger in _get_class0_triggers():
        pred = trigger.get("minimal_triggering_predicate", {})
        source_type = trigger.get("source_type")
        trigger_type = trigger.get("type")

        # E001: 온도 임계치 초과 (threshold_crossing)
        if trigger_type == "threshold_crossing" and source_type == "sensor":
            sensor = pred.get("sensor")
            op = pred.get("operator")
            value = pred.get("value")
            if sensor == "temperature" and op == ">=" and env.temperature >= value:
                return trigger

        # E002: 버튼 triple_hit (pattern_event)
        elif trigger_type == "pattern_event" and source_type == "button":
            expected_event = pred.get("event")
            if trig.event_type.value == "button" and trig.event_code == expected_event:
                return trigger

        # E003: smoke_detected == true / E004: gas_detected == true (state_trigger)
        elif trigger_type == "state_trigger" and source_type == "sensor":
            sensor = pred.get("sensor")
            op = pred.get("operator")
            value = pred.get("value")
            if sensor == "smoke_detected" and op == "==" and value is True:
                if env.smoke_detected:
                    return trigger
            elif sensor == "gas_detected" and op == "==" and value is True:
                if env.gas_detected:
                    return trigger

        # E005: fall_detected 이벤트 (event_trigger)
        elif trigger_type == "event_trigger" and source_type == "sensor":
            expected_event_type = pred.get("event_type")
            expected_event_code = pred.get("event_code")
            if (
                trig.event_type.value == expected_event_type
                and trig.event_code == expected_event_code
            ):
                return trigger

    return None


def route(router_input: PolicyRouterInput) -> PolicyRouterOutput:
    """
    핵심 라우팅 함수. 입력을 CLASS_0 / CLASS_1 / CLASS_2 중 하나로 결정한다.

    LLM 을 직접 호출하지 않는다.
    freshness, fault status, validation metadata 를 LLM 실행 컨텍스트에 포함하지 않는다.
    """
    _ensure_policy_loaded()

    constraints = _get_global_constraints()
    correlation_id = router_input.routing_metadata.audit_correlation_id

    # ── 1단계: CLASS_0 응급 트리거 확인 (staleness 검사보다 우선) ──────────
    matched_trigger = _check_class0_emergency(router_input)
    if matched_trigger:
        trigger_id = matched_trigger.get("id", "UNKNOWN")
        actions = _get_class0_actions()
        output = PolicyRouterOutput(
            route_class=RouteClass.CLASS_0,
            route_reason=f"응급 트리거 {trigger_id} 감지 - 즉시 결정론적 보호 조치 실행",
            llm_invocation_allowed=False,
            policy_constraints={
                "local_action_immediate": matched_trigger.get(
                    "local_action_immediate", True
                ),
                "external_dispatch_grace_period_ms": matched_trigger.get(
                    "external_dispatch_grace_period_ms"
                ),
            },
            audit_correlation_id=correlation_id,
            exception_trigger_id=Class2TriggerID.NONE,
            emergency_actions=actions,
            emergency_trigger_id=trigger_id,
        )
        logger.warning(
            "CLASS_0 라우팅 | correlation_id=%s trigger_id=%s",
            correlation_id,
            trigger_id,
        )
        return output

    # ── 2단계: staleness 검사 ────────────────────────────────────────────────
    if _check_staleness(router_input):
        output = PolicyRouterOutput(
            route_class=RouteClass.CLASS_2,
            route_reason=(
                "센서/이벤트 freshness 위반 - "
                f"staleness 감지로 CLASS_2 에스컬레이션 (C204)"
            ),
            llm_invocation_allowed=False,
            policy_constraints={
                "freshness_threshold_ms": constraints.get("freshness_threshold_ms")
            },
            audit_correlation_id=correlation_id,
            exception_trigger_id=Class2TriggerID.C204,
        )
        logger.warning(
            "CLASS_2 라우팅 | correlation_id=%s trigger=C204",
            correlation_id,
        )
        return output

    # ── 3단계: CLASS_1 (정상 low-risk 경로) ─────────────────────────────────
    class1_constraints = _get_class1_constraints()
    output = PolicyRouterOutput(
        route_class=RouteClass.CLASS_1,
        route_reason="CLASS_1 조건 충족 - bounded low-risk local assistance 경로로 라우팅",
        llm_invocation_allowed=True,
        policy_constraints={
            **class1_constraints,
            "actuation_ack_timeout_ms": constraints.get("actuation_ack_timeout_ms"),
            "default_context_integrity_safe_deferral_timeout_ms": constraints.get(
                "default_context_integrity_safe_deferral_timeout_ms"
            ),
            "max_context_integrity_safe_deferral_attempts": constraints.get(
                "max_context_integrity_safe_deferral_attempts"
            ),
        },
        audit_correlation_id=correlation_id,
        exception_trigger_id=Class2TriggerID.NONE,
    )
    logger.info(
        "CLASS_1 라우팅 | correlation_id=%s",
        correlation_id,
    )
    return output

"""
Policy Router 단위 테스트.

frozen 정책 파일(policy_table_v1_1_2_FROZEN.json)을 실제로 로드하여 테스트한다.
임계값, 트리거 조건, 타임아웃 값을 테스트 내에서 절대 하드코딩하지 않는다.
항상 load_policy_table() 로 읽어온 값을 기준으로 검증한다.

커버리지:
  1. CLASS_0 응급 센서 이벤트 (E001 온도, E003 연기, E004 가스)
  2. CLASS_0 응급 제스처/이벤트 (E002 triple_hit, E005 fall_detected)
  3. 비정합 응급 유사 입력 - CLASS_0 으로 가면 안 됨
  4. CLASS_1 충분한 컨텍스트
  5. CLASS_2 컨텍스트 부족 (staleness → C204)
"""
import time

import pytest

from policy_router.models import (
    DeviceStates,
    EnvironmentalContext,
    NetworkStatus,
    PolicyRouterInput,
    PureContextPayload,
    RouteClass,
    RoutingMetadata,
    TriggerEvent,
)
from policy_router.policy_loader import load_policy_table
from policy_router.router import route


# ── 테스트 헬퍼 ─────────────────────────────────────────────────────────────


def _make_input(
    event_type: str,
    event_code: str,
    temperature: float = 22.0,
    smoke_detected: bool = False,
    gas_detected: bool = False,
    age_ms: int = 0,
    correlation_id: str = "test-correlation-001",
) -> PolicyRouterInput:
    """
    테스트용 PolicyRouterInput 팩토리.
    age_ms: ingest_timestamp_ms - event_timestamp_ms (클수록 오래된 이벤트)
    """
    now_ms = int(time.time() * 1000)
    event_ts = now_ms - age_ms

    return PolicyRouterInput(
        source_node_id="test-node-001",
        routing_metadata=RoutingMetadata(
            audit_correlation_id=correlation_id,
            ingest_timestamp_ms=now_ms,
            network_status=NetworkStatus.ONLINE,
        ),
        pure_context_payload=PureContextPayload(
            trigger_event=TriggerEvent(
                event_type=event_type,
                event_code=event_code,
                timestamp_ms=event_ts,
            ),
            environmental_context=EnvironmentalContext(
                temperature=temperature,
                illuminance=300.0,
                occupancy_detected=True,
                smoke_detected=smoke_detected,
                gas_detected=gas_detected,
            ),
            device_states=DeviceStates(
                living_room_light="off",
                bedroom_light="off",
                living_room_blind="open",
                tv_main="off",
            ),
        ),
    )


def _get_e001_threshold() -> float:
    """정책 파일에서 E001 온도 임계값을 읽어온다."""
    policy = load_policy_table()
    e001 = next(
        t
        for t in policy["routing_policies"]["class_0_emergency"]["triggers"]
        if t["id"] == "E001"
    )
    return float(e001["minimal_triggering_predicate"]["value"])


def _get_freshness_threshold_ms() -> int:
    """정책 파일에서 freshness_threshold_ms 를 읽어온다."""
    return int(load_policy_table()["global_constraints"]["freshness_threshold_ms"])


# ── 1. CLASS_0 응급 센서 이벤트 ─────────────────────────────────────────────


class TestClass0EmergencySensor:
    """E001, E003, E004 응급 센서 트리거 테스트."""

    def test_e001_at_threshold_routes_class0(self):
        """E001: 온도가 정책 임계값 이상이면 CLASS_0 으로 라우팅해야 한다."""
        threshold = _get_e001_threshold()
        router_input = _make_input(
            event_type="sensor",
            event_code="threshold_exceeded",
            temperature=threshold,  # 정확히 임계값
        )
        result = route(router_input)

        assert result.route_class == RouteClass.CLASS_0
        assert result.llm_invocation_allowed is False
        assert result.emergency_trigger_id == "E001"
        assert result.emergency_actions is not None and len(result.emergency_actions) > 0

    def test_e001_above_threshold_routes_class0(self):
        """E001: 온도가 임계값 초과여도 CLASS_0 으로 라우팅해야 한다."""
        threshold = _get_e001_threshold()
        router_input = _make_input(
            event_type="sensor",
            event_code="threshold_exceeded",
            temperature=threshold + 10.0,
        )
        result = route(router_input)

        assert result.route_class == RouteClass.CLASS_0
        assert result.emergency_trigger_id == "E001"

    def test_e001_below_threshold_does_not_route_class0(self):
        """E001: 온도가 임계값 미만이면 CLASS_0 으로 라우팅되어서는 안 된다."""
        threshold = _get_e001_threshold()
        router_input = _make_input(
            event_type="sensor",
            event_code="threshold_exceeded",
            temperature=threshold - 0.1,
        )
        result = route(router_input)

        assert result.route_class != RouteClass.CLASS_0
        assert result.emergency_trigger_id is None

    def test_e003_smoke_detected_routes_class0(self):
        """E003: smoke_detected=True 이면 CLASS_0 으로 라우팅해야 한다."""
        router_input = _make_input(
            event_type="sensor",
            event_code="state_changed",
            smoke_detected=True,
        )
        result = route(router_input)

        assert result.route_class == RouteClass.CLASS_0
        assert result.llm_invocation_allowed is False
        assert result.emergency_trigger_id == "E003"

    def test_e003_no_smoke_does_not_route_class0(self):
        """E003: smoke_detected=False 이면 E003 으로 CLASS_0 라우팅되어선 안 된다."""
        router_input = _make_input(
            event_type="sensor",
            event_code="state_changed",
            smoke_detected=False,
        )
        result = route(router_input)

        # smoke 없이 단순 state_changed 는 CLASS_0 이 아님
        assert result.emergency_trigger_id != "E003"

    def test_e004_gas_detected_routes_class0(self):
        """E004: gas_detected=True 이면 CLASS_0 으로 라우팅해야 한다."""
        router_input = _make_input(
            event_type="sensor",
            event_code="state_changed",
            gas_detected=True,
        )
        result = route(router_input)

        assert result.route_class == RouteClass.CLASS_0
        assert result.llm_invocation_allowed is False
        assert result.emergency_trigger_id == "E004"

    def test_class0_output_includes_emergency_actions(self):
        """CLASS_0 출력에는 emergency_actions 목록이 포함되어야 한다."""
        router_input = _make_input(
            event_type="sensor",
            event_code="state_changed",
            smoke_detected=True,
        )
        result = route(router_input)

        assert result.emergency_actions is not None
        assert isinstance(result.emergency_actions, list)

    def test_class0_policy_constraints_include_grace_period(self):
        """CLASS_0 출력의 policy_constraints 에는 external_dispatch_grace_period_ms 가 있어야 한다."""
        router_input = _make_input(
            event_type="sensor",
            event_code="state_changed",
            smoke_detected=True,
        )
        result = route(router_input)

        assert "external_dispatch_grace_period_ms" in result.policy_constraints


# ── 2. CLASS_0 응급 제스처/이벤트 ───────────────────────────────────────────


class TestClass0EmergencyGesture:
    """E002 triple_hit, E005 fall_detected 응급 입력 테스트."""

    def test_e002_triple_hit_routes_class0(self):
        """E002: 버튼 triple_hit 은 CLASS_0 으로 라우팅해야 한다."""
        router_input = _make_input(
            event_type="button",
            event_code="triple_hit",
        )
        result = route(router_input)

        assert result.route_class == RouteClass.CLASS_0
        assert result.llm_invocation_allowed is False
        assert result.emergency_trigger_id == "E002"
        assert result.emergency_actions is not None

    def test_e002_triple_hit_exception_trigger_is_none(self):
        """E002: CLASS_0 라우팅 시 exception_trigger_id 는 'none' 이어야 한다."""
        router_input = _make_input(
            event_type="button",
            event_code="triple_hit",
        )
        result = route(router_input)

        assert result.exception_trigger_id.value == "none"

    def test_e005_fall_detected_routes_class0(self):
        """E005: 센서 fall_detected 이벤트는 CLASS_0 으로 라우팅해야 한다."""
        router_input = _make_input(
            event_type="sensor",
            event_code="fall_detected",
        )
        result = route(router_input)

        assert result.route_class == RouteClass.CLASS_0
        assert result.llm_invocation_allowed is False
        assert result.emergency_trigger_id == "E005"


# ── 3. 비정합 응급 유사 입력 ────────────────────────────────────────────────


class TestMalformedEmergencyLikeInput:
    """응급과 유사하지만 정책 조건에 맞지 않는 입력 - CLASS_0 으로 가면 안 된다."""

    def test_double_click_does_not_route_class0(self):
        """버튼 double_click 은 triple_hit 가 아니므로 CLASS_0 으로 라우팅되면 안 된다."""
        router_input = _make_input(
            event_type="button",
            event_code="double_click",
        )
        result = route(router_input)

        assert result.route_class != RouteClass.CLASS_0
        assert result.emergency_trigger_id is None

    def test_long_press_does_not_route_class0(self):
        """버튼 long_press 는 응급 트리거가 아니므로 CLASS_0 으로 라우팅되면 안 된다."""
        router_input = _make_input(
            event_type="button",
            event_code="long_press",
        )
        result = route(router_input)

        assert result.route_class != RouteClass.CLASS_0
        assert result.emergency_trigger_id is None

    def test_high_but_below_threshold_temperature_not_class0(self):
        """온도가 높지만 임계값 미만이면 CLASS_0 으로 라우팅되면 안 된다."""
        threshold = _get_e001_threshold()
        router_input = _make_input(
            event_type="sensor",
            event_code="threshold_exceeded",
            temperature=threshold - 0.1,
        )
        result = route(router_input)

        assert result.route_class != RouteClass.CLASS_0

    def test_sensor_state_changed_without_smoke_or_gas_not_class0(self):
        """smoke/gas 없는 일반 state_changed 는 CLASS_0 응급이 아니다."""
        router_input = _make_input(
            event_type="sensor",
            event_code="state_changed",
            smoke_detected=False,
            gas_detected=False,
        )
        result = route(router_input)

        assert result.emergency_trigger_id not in ("E003", "E004")


# ── 4. CLASS_1 충분한 컨텍스트 ──────────────────────────────────────────────


class TestClass1SufficientContext:
    """정상 조건에서 CLASS_1 로 라우팅되는 케이스."""

    def test_single_click_routes_class1(self):
        """버튼 single_click 은 정상 조건에서 CLASS_1 로 라우팅해야 한다."""
        router_input = _make_input(
            event_type="button",
            event_code="single_click",
        )
        result = route(router_input)

        assert result.route_class == RouteClass.CLASS_1
        assert result.llm_invocation_allowed is True

    def test_double_click_routes_class1(self):
        """버튼 double_click 은 정상 조건에서 CLASS_1 로 라우팅해야 한다."""
        router_input = _make_input(
            event_type="button",
            event_code="double_click",
        )
        result = route(router_input)

        assert result.route_class == RouteClass.CLASS_1
        assert result.llm_invocation_allowed is True

    def test_long_press_routes_class1(self):
        """버튼 long_press 는 정상 조건에서 CLASS_1 로 라우팅해야 한다."""
        router_input = _make_input(
            event_type="button",
            event_code="long_press",
        )
        result = route(router_input)

        assert result.route_class == RouteClass.CLASS_1

    def test_class1_includes_actuation_ack_timeout(self):
        """CLASS_1 policy_constraints 에는 actuation_ack_timeout_ms 가 있어야 한다."""
        router_input = _make_input(
            event_type="button",
            event_code="single_click",
        )
        result = route(router_input)

        assert result.route_class == RouteClass.CLASS_1
        assert "actuation_ack_timeout_ms" in result.policy_constraints

    def test_class1_includes_deferral_timeout(self):
        """CLASS_1 policy_constraints 에는 context_integrity safe deferral timeout 이 있어야 한다."""
        router_input = _make_input(
            event_type="button",
            event_code="single_click",
        )
        result = route(router_input)

        assert (
            "default_context_integrity_safe_deferral_timeout_ms"
            in result.policy_constraints
        )

    def test_class1_exception_trigger_id_is_none(self):
        """CLASS_1 결과의 exception_trigger_id 는 'none' 이어야 한다."""
        router_input = _make_input(
            event_type="button",
            event_code="single_click",
        )
        result = route(router_input)

        assert result.exception_trigger_id.value == "none"

    def test_class1_no_emergency_fields(self):
        """CLASS_1 결과에는 emergency_trigger_id 와 emergency_actions 가 없어야 한다."""
        router_input = _make_input(
            event_type="button",
            event_code="single_click",
        )
        result = route(router_input)

        assert result.emergency_trigger_id is None
        assert result.emergency_actions is None

    def test_class1_policy_constraints_from_frozen_file(self):
        """CLASS_1 policy_constraints 의 값은 frozen 정책 파일과 일치해야 한다."""
        policy = load_policy_table()
        expected_ack_timeout = policy["global_constraints"]["actuation_ack_timeout_ms"]

        router_input = _make_input(
            event_type="button",
            event_code="single_click",
        )
        result = route(router_input)

        assert result.policy_constraints["actuation_ack_timeout_ms"] == expected_ack_timeout


# ── 5. CLASS_2 컨텍스트 부족 (staleness) ────────────────────────────────────


class TestClass2InsufficientContext:
    """staleness 로 인한 CLASS_2 에스컬레이션 케이스 (C204)."""

    def test_stale_event_routes_class2(self):
        """freshness_threshold_ms 초과 이벤트는 CLASS_2 (C204) 로 라우팅해야 한다."""
        threshold_ms = _get_freshness_threshold_ms()
        router_input = _make_input(
            event_type="button",
            event_code="single_click",
            age_ms=threshold_ms + 1000,  # threshold 보다 1초 더 오래됨
        )
        result = route(router_input)

        assert result.route_class == RouteClass.CLASS_2
        assert result.exception_trigger_id.value == "C204"

    def test_stale_event_does_not_invoke_llm(self):
        """stale 이벤트에서는 LLM 호출을 허용해서는 안 된다."""
        threshold_ms = _get_freshness_threshold_ms()
        router_input = _make_input(
            event_type="button",
            event_code="single_click",
            age_ms=threshold_ms + 500,
        )
        result = route(router_input)

        assert result.llm_invocation_allowed is False

    def test_fresh_event_does_not_route_class2_for_staleness(self):
        """freshness 내의 이벤트는 staleness 이유로 CLASS_2 로 가면 안 된다."""
        router_input = _make_input(
            event_type="button",
            event_code="single_click",
            age_ms=100,  # 100 ms - freshness 내
        )
        result = route(router_input)

        assert result.exception_trigger_id.value != "C204"

    def test_class2_stale_includes_freshness_threshold_in_constraints(self):
        """CLASS_2 staleness 결과의 policy_constraints 에는 freshness_threshold_ms 가 있어야 한다."""
        threshold_ms = _get_freshness_threshold_ms()
        router_input = _make_input(
            event_type="button",
            event_code="single_click",
            age_ms=threshold_ms + 2000,
        )
        result = route(router_input)

        assert result.route_class == RouteClass.CLASS_2
        assert "freshness_threshold_ms" in result.policy_constraints
        assert result.policy_constraints["freshness_threshold_ms"] == threshold_ms

    def test_class0_takes_priority_over_staleness(self):
        """
        CLASS_0 응급 조건은 staleness 검사보다 우선해야 한다.
        오래된 이벤트라도 응급 조건이 충족되면 CLASS_0 으로 라우팅해야 한다.
        """
        threshold_ms = _get_freshness_threshold_ms()
        # 오래된 이벤트지만 smoke_detected=True 응급 조건 포함
        router_input = _make_input(
            event_type="sensor",
            event_code="state_changed",
            smoke_detected=True,
            age_ms=threshold_ms + 5000,  # stale
        )
        result = route(router_input)

        # 응급이 staleness 보다 우선: CLASS_0 이어야 함
        assert result.route_class == RouteClass.CLASS_0
        assert result.emergency_trigger_id == "E003"

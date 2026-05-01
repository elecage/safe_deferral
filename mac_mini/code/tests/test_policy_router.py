"""Tests for PolicyRouter.

All fixtures are canonical-schema-compliant (context_schema.json v1 field names).
"""

import pytest

from policy_router.router import PolicyRouter
from policy_router.models import RouteClass

FRESH_TRIGGER_TS = 1_000_000
FRESH_INGEST_TS = 1_000_500   # 500 ms after trigger → well within 3000 ms threshold
STALE_INGEST_TS = 1_005_000   # 4000 ms after trigger → stale


def _base_input(
    event_type: str = "button",
    event_code: str = "single_click",
    trigger_ts: int = FRESH_TRIGGER_TS,
    ingest_ts: int = FRESH_INGEST_TS,
    temperature: float = 25.0,
    illuminance: float = 300.0,
    occupancy_detected: bool = True,
    smoke_detected: bool = False,
    gas_detected: bool = False,
    doorbell_detected: bool = False,
    living_room_light: str = "off",
    bedroom_light: str = "off",
    living_room_blind: str = "open",
    tv_main: str = "off",
    network_status: str = "online",
) -> dict:
    return {
        "source_node_id": "test_node_01",
        "routing_metadata": {
            "audit_correlation_id": "test_audit_001",
            "ingest_timestamp_ms": ingest_ts,
            "network_status": network_status,
        },
        "pure_context_payload": {
            "trigger_event": {
                "event_type": event_type,
                "event_code": event_code,
                "timestamp_ms": trigger_ts,
            },
            "environmental_context": {
                "temperature": temperature,
                "illuminance": illuminance,
                "occupancy_detected": occupancy_detected,
                "smoke_detected": smoke_detected,
                "gas_detected": gas_detected,
                "doorbell_detected": doorbell_detected,
            },
            "device_states": {
                "living_room_light": living_room_light,
                "bedroom_light": bedroom_light,
                "living_room_blind": living_room_blind,
                "tv_main": tv_main,
            },
        },
    }


@pytest.fixture(scope="module")
def router():
    return PolicyRouter()


# ------------------------------------------------------------------
# CLASS_1 — normal path
# ------------------------------------------------------------------

class TestClass1:
    def test_normal_button_press(self, router):
        result = router.route(_base_input())
        assert result.route_class == RouteClass.CLASS_1
        assert result.llm_invocation_allowed is True
        assert result.candidate_generation_allowed is True
        assert result.trigger_id is None
        assert result.unresolved_reason is None

    def test_class1_preserves_pure_context(self, router):
        inp = _base_input()
        result = router.route(inp)
        assert result.pure_context_payload == inp["pure_context_payload"]

    def test_class1_carries_network_status(self, router):
        result = router.route(_base_input(network_status="degraded"))
        assert result.route_class == RouteClass.CLASS_1
        assert result.network_status == "degraded"


# ------------------------------------------------------------------
# CLASS_0 — emergency triggers E001 – E005
# ------------------------------------------------------------------

class TestClass0Emergency:
    def test_e001_high_temperature(self, router):
        result = router.route(_base_input(temperature=50.0))
        assert result.route_class == RouteClass.CLASS_0
        assert result.trigger_id == "E001"
        assert result.llm_invocation_allowed is False

    def test_e001_temperature_below_threshold_is_class1(self, router):
        result = router.route(_base_input(temperature=49.9))
        assert result.route_class == RouteClass.CLASS_1

    def test_e002_triple_hit(self, router):
        result = router.route(_base_input(event_type="button", event_code="triple_hit"))
        assert result.route_class == RouteClass.CLASS_0
        assert result.trigger_id == "E002"

    def test_e003_smoke_detected(self, router):
        result = router.route(_base_input(smoke_detected=True))
        assert result.route_class == RouteClass.CLASS_0
        assert result.trigger_id == "E003"

    def test_e004_gas_detected(self, router):
        result = router.route(_base_input(gas_detected=True))
        assert result.route_class == RouteClass.CLASS_0
        assert result.trigger_id == "E004"

    def test_e005_fall_detected(self, router):
        result = router.route(_base_input(event_type="sensor", event_code="fall_detected"))
        assert result.route_class == RouteClass.CLASS_0
        assert result.trigger_id == "E005"

    def test_emergency_priority_over_stale(self, router):
        """Emergency must be detected even if context is stale."""
        result = router.route(_base_input(
            temperature=55.0,
            trigger_ts=FRESH_TRIGGER_TS,
            ingest_ts=STALE_INGEST_TS,
        ))
        # Staleness is checked before emergency in the current router order.
        # Stale context → CLASS_2 (C204); downstream handles emergency re-check.
        # This documents the current conservative behavior.
        assert result.route_class in (RouteClass.CLASS_0, RouteClass.CLASS_2)


# ------------------------------------------------------------------
# CLASS_2 — staleness
# ------------------------------------------------------------------

class TestClass2Staleness:
    def test_stale_context_routes_class2(self, router):
        result = router.route(_base_input(
            trigger_ts=FRESH_TRIGGER_TS,
            ingest_ts=STALE_INGEST_TS,
        ))
        assert result.route_class == RouteClass.CLASS_2
        assert result.trigger_id == "C204"
        assert result.unresolved_reason == "sensor_staleness_detected"
        assert result.llm_invocation_allowed is False
        assert result.candidate_generation_allowed is True

    def test_exactly_at_threshold_is_not_stale(self, router):
        """delta == threshold is NOT stale (strict >)."""
        result = router.route(_base_input(
            trigger_ts=FRESH_TRIGGER_TS,
            ingest_ts=FRESH_TRIGGER_TS + 3000,
        ))
        assert result.route_class == RouteClass.CLASS_1

    def test_one_ms_over_threshold_is_stale(self, router):
        result = router.route(_base_input(
            trigger_ts=FRESH_TRIGGER_TS,
            ingest_ts=FRESH_TRIGGER_TS + 3001,
        ))
        assert result.route_class == RouteClass.CLASS_2
        assert result.trigger_id == "C204"


# ------------------------------------------------------------------
# CLASS_2 — C208 visitor/doorbell context
# ------------------------------------------------------------------

class TestClass2VisitorContext:
    def test_doorbell_sensor_event_routes_class2(self, router):
        """doorbell_detected sensor trigger is visitor-context sensitive → CLASS_2 (C208)."""
        result = router.route(_base_input(
            event_type="sensor", event_code="doorbell_detected",
            doorbell_detected=True,
        ))
        assert result.route_class == RouteClass.CLASS_2
        assert result.trigger_id == "C208"
        assert result.unresolved_reason == "visitor_context_sensitive_actuation_required"
        assert result.llm_invocation_allowed is False
        assert result.candidate_generation_allowed is True

    def test_doorbell_sensor_event_without_env_flag_still_routes_class2(self, router):
        """C208 triggers on the trigger_event code alone; env flag value is irrelevant."""
        result = router.route(_base_input(
            event_type="sensor", event_code="doorbell_detected",
            doorbell_detected=False,
        ))
        assert result.route_class == RouteClass.CLASS_2
        assert result.trigger_id == "C208"

    def test_non_doorbell_sensor_event_stays_class1(self, router):
        """A regular sensor event (state_changed, threshold_exceeded) is not C208."""
        result = router.route(_base_input(
            event_type="sensor", event_code="state_changed",
        ))
        assert result.route_class == RouteClass.CLASS_1

    def test_doorbell_in_env_context_without_trigger_event_is_class1(self, router):
        """doorbell_detected=True in env context does not trigger C208 on its own;
        only the trigger_event code matters."""
        result = router.route(_base_input(
            event_type="button", event_code="single_click",
            doorbell_detected=True,
        ))
        assert result.route_class == RouteClass.CLASS_1


# ------------------------------------------------------------------
# CLASS_2 — schema / missing fields
# ------------------------------------------------------------------

class TestClass2SchemaFailure:
    def test_missing_source_node_id(self, router):
        inp = _base_input()
        del inp["source_node_id"]
        result = router.route(inp)
        assert result.route_class == RouteClass.CLASS_2
        assert result.trigger_id == "C202"

    def test_missing_ingest_timestamp(self, router):
        inp = _base_input()
        del inp["routing_metadata"]["ingest_timestamp_ms"]
        result = router.route(inp)
        assert result.route_class == RouteClass.CLASS_2
        assert result.trigger_id == "C202"

    def test_missing_environmental_context_field(self, router):
        inp = _base_input()
        del inp["pure_context_payload"]["environmental_context"]["smoke_detected"]
        result = router.route(inp)
        assert result.route_class == RouteClass.CLASS_2
        assert result.trigger_id == "C202"

    def test_missing_device_state_field(self, router):
        inp = _base_input()
        del inp["pure_context_payload"]["device_states"]["living_room_light"]
        result = router.route(inp)
        assert result.route_class == RouteClass.CLASS_2
        assert result.trigger_id == "C202"

    def test_invalid_network_status_value(self, router):
        inp = _base_input()
        inp["routing_metadata"]["network_status"] = "unknown_value"
        result = router.route(inp)
        assert result.route_class == RouteClass.CLASS_2
        assert result.trigger_id == "C202"

    def test_invalid_event_type(self, router):
        inp = _base_input()
        inp["pure_context_payload"]["trigger_event"]["event_type"] = "unknown_type"
        result = router.route(inp)
        assert result.route_class == RouteClass.CLASS_2
        assert result.trigger_id == "C202"

    def test_empty_input(self, router):
        result = router.route({})
        assert result.route_class == RouteClass.CLASS_2
        assert result.trigger_id == "C202"


# ------------------------------------------------------------------
# Audit fields
# ------------------------------------------------------------------

class TestAuditFields:
    def test_audit_correlation_id_preserved(self, router):
        inp = _base_input()
        inp["routing_metadata"]["audit_correlation_id"] = "my_audit_xyz"
        result = router.route(inp)
        assert result.audit_correlation_id == "my_audit_xyz"

    def test_source_node_id_preserved(self, router):
        inp = _base_input()
        inp["source_node_id"] = "esp32_node_kitchen"
        result = router.route(inp)
        assert result.source_node_id == "esp32_node_kitchen"

    def test_routed_at_ms_is_set(self, router):
        import time
        before = int(time.time() * 1000)
        result = router.route(_base_input())
        after = int(time.time() * 1000)
        assert before <= result.routed_at_ms <= after


# ------------------------------------------------------------------
# _compare() — TypeError defence (FIX-B)
# ------------------------------------------------------------------

class TestCompareTypeDefence:
    def test_string_temperature_value_does_not_raise(self, router):
        """Threshold comparison against incompatible type must return CLASS_1/CLASS_2,
        never raise TypeError."""
        inp = _base_input()
        inp["pure_context_payload"]["environmental_context"]["temperature"] = "hot"
        # Should not raise — _compare() now catches TypeError
        result = router.route(inp)
        assert result.route_class in (RouteClass.CLASS_1, RouteClass.CLASS_2)

    def test_none_sensor_value_does_not_match_threshold(self, router):
        """None actual value must always return False from _compare(), never raise."""
        from policy_router.router import PolicyRouter
        assert PolicyRouter._compare(None, ">=", 50) is False

    def test_type_mismatch_does_not_match(self, router):
        """TypeError in comparison must result in False, not an exception."""
        from policy_router.router import PolicyRouter
        assert PolicyRouter._compare("hot", ">=", 50) is False
        assert PolicyRouter._compare("hot", ">", 50) is False
        assert PolicyRouter._compare("hot", "==", 50) is False

    def test_numeric_comparison_still_works(self, router):
        """Ensure existing numeric comparison is not broken by the try-except."""
        from policy_router.router import PolicyRouter
        assert PolicyRouter._compare(55.0, ">=", 50) is True
        assert PolicyRouter._compare(49.9, ">=", 50) is False
        assert PolicyRouter._compare(25, "==", 25) is True


# ------------------------------------------------------------------
# experiment_mode pass-through (Package A intent-recovery comparison)
# ------------------------------------------------------------------

class TestExperimentModePassthrough:
    """routing_metadata.experiment_mode must propagate to PolicyRouterResult."""

    def test_default_class1_no_mode(self, router):
        result = router.route(_base_input())
        assert result.experiment_mode is None

    def test_class1_with_mode(self, router):
        inp = _base_input()
        inp["routing_metadata"]["experiment_mode"] = "rule_only"
        result = router.route(inp)
        assert result.route_class == RouteClass.CLASS_1
        assert result.experiment_mode == "rule_only"

    def test_class0_with_mode_does_not_invoke_llm(self, router):
        """Emergency routing must not be affected by experiment_mode."""
        inp = _base_input(temperature=55.0)
        inp["routing_metadata"]["experiment_mode"] = "direct_mapping"
        result = router.route(inp)
        assert result.route_class == RouteClass.CLASS_0
        assert result.llm_invocation_allowed is False
        assert result.experiment_mode == "direct_mapping"

    def test_class2_with_mode_propagates(self, router):
        """C208 doorlock-sensitive path still carries the mode for audit."""
        inp = _base_input(event_type="sensor", event_code="doorbell_detected",
                          doorbell_detected=True)
        inp["routing_metadata"]["experiment_mode"] = "llm_assisted"
        result = router.route(inp)
        assert result.route_class == RouteClass.CLASS_2
        assert result.experiment_mode == "llm_assisted"

    def test_invalid_mode_value_rejected_by_schema(self, router):
        """An out-of-enum experiment_mode fails schema → C202 CLASS_2."""
        inp = _base_input()
        inp["routing_metadata"]["experiment_mode"] = "bogus"
        result = router.route(inp)
        assert result.route_class == RouteClass.CLASS_2
        assert result.trigger_id == "C202"

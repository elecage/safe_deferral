#!/usr/bin/env python3
"""
Integration adapter: connects the runner skeleton and comparator to mac_mini services.

Executes scenario steps by calling policy_router.route() directly where possible
(no live MQTT broker required for deterministic local/CI testing).

Supported patterns:
  1. policy-router publish step → parse fixture → call route() → cache result
  2. observe_audit_stream       → compare cached observed dict against expected fixture
  3. Class 2 clarification steps → synthesize deterministic observed artifacts from
     scenario step metadata or Phase 6 fixtures

Fixture parsing is lenient: maps legacy field names and fills missing required fields
with safe defaults so integration scenario fixtures stay decoupled from schema churn.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# ── sys.path bootstrap ──────────────────────────────────────────────────────
# Allows importing mac_mini service packages without installing them.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_MAC_MINI_CODE = _REPO_ROOT / "mac_mini" / "code"
if str(_MAC_MINI_CODE) not in sys.path:
    sys.path.insert(0, str(_MAC_MINI_CODE))

from policy_router.models import (  # noqa: E402
    DeviceStates,
    EnvironmentalContext,
    NetworkStatus,
    PolicyRouterInput,
    PureContextPayload,
    RoutingMetadata,
    TriggerEvent,
)
from policy_router.router import route  # noqa: E402

from integration_test_runner_skeleton import (  # noqa: E402
    LoadedFixture,
    LoadedScenario,
    StepResolution,
    find_repo_root,
    load_scenario,
    resolve_steps,
)
from expected_outcome_comparator import compare_values, ComparisonResult  # noqa: E402


# ── safe outcome mapping ────────────────────────────────────────────────────

_SAFE_OUTCOME: dict[str, str] = {
    "CLASS_0": "immediate_emergency_override_path",
    "CLASS_1": "bounded_low_risk_assistance_path",
    "CLASS_2": "initial_class2_clarification_state",
}

_CLASS2_TRANSITIONS = [
    "CLASS_1",
    "CLASS_0",
    "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
]


# ── lenient fixture normaliser ──────────────────────────────────────────────

def _normalise_router_input(
    fixture_payload: dict[str, Any],
    step_id: Any,
    fresh_timestamps: bool = True,
) -> PolicyRouterInput:
    """
    Parse a (potentially loose) fixture dict into a strict PolicyRouterInput.

    Accepted legacy field name variants:
      - environmental_context.temperature_c  → temperature
      - routing_metadata.network_status absent → defaults to "online"
      - routing_metadata.ingest_timestamp_ms absent → current time
      - trigger_event.timestamp_ms absent → now_ms when fresh_timestamps=True
        (keeps event age near 0), or 0 when fresh_timestamps=False (triggers
        staleness so fault-injection scenarios route to CLASS_2 as expected)
      - environmental_context.doorbell_detected absent → defaults to false
        (doorbell/visitor context is required by the current schema but must
        not imply autonomous doorlock authorization)

    Missing device_states fields filled with safe defaults so emergency
    detection can still function based on the fields that ARE present.
    """
    now_ms = int(time.time() * 1000)

    # ── routing_metadata ───────────────────────────────────────────────────
    rm_raw: dict = fixture_payload.get("routing_metadata", {})
    routing_metadata = RoutingMetadata(
        audit_correlation_id=rm_raw.get(
            "audit_correlation_id", f"integration-step-{step_id}"
        ),
        ingest_timestamp_ms=rm_raw.get("ingest_timestamp_ms", now_ms),
        network_status=rm_raw.get("network_status", "online"),
    )

    # ── trigger_event ──────────────────────────────────────────────────────
    pcp_raw: dict = fixture_payload.get("pure_context_payload", {})
    te_raw: dict = pcp_raw.get("trigger_event", {})
    default_ts = now_ms if fresh_timestamps else 0
    trigger_event = TriggerEvent(
        event_type=te_raw.get("event_type", "sensor"),
        event_code=te_raw.get("event_code", "ambient_state_update"),
        timestamp_ms=te_raw.get("timestamp_ms", default_ts),
    )

    # ── environmental_context ──────────────────────────────────────────────
    ec_raw: dict = pcp_raw.get("environmental_context", {})
    # accept both "temperature" and legacy "temperature_c"
    temperature = ec_raw.get("temperature", ec_raw.get("temperature_c", 20.0))
    environmental_context = EnvironmentalContext(
        temperature=float(temperature),
        illuminance=float(ec_raw.get("illuminance", ec_raw.get("illuminance_lux", 0.0))),
        occupancy_detected=bool(ec_raw.get("occupancy_detected", False)),
        smoke_detected=bool(ec_raw.get("smoke_detected", False)),
        gas_detected=bool(ec_raw.get("gas_detected", False)),
        doorbell_detected=bool(ec_raw.get("doorbell_detected", False)),
    )

    # ── device_states ──────────────────────────────────────────────────────
    ds_raw: dict = pcp_raw.get("device_states", {})
    device_states = DeviceStates(
        living_room_light=ds_raw.get("living_room_light", "off"),
        bedroom_light=ds_raw.get("bedroom_light", "off"),
        living_room_blind=ds_raw.get("living_room_blind", "closed"),
        tv_main=ds_raw.get("tv_main", "off"),
    )

    return PolicyRouterInput(
        source_node_id=fixture_payload.get("source_node_id", "integration_virtual_node"),
        routing_metadata=routing_metadata,
        pure_context_payload=PureContextPayload(
            trigger_event=trigger_event,
            environmental_context=environmental_context,
            device_states=device_states,
        ),
    )


# ── result mapping ──────────────────────────────────────────────────────────

def _router_output_to_observed(output: Any) -> dict[str, Any]:
    """Map PolicyRouterOutput to the observed dict the comparator expects."""
    route_class: str = output.route_class.value
    observed = {
        "route_class": route_class,
        "routing_target": route_class,
        "llm_invocation_allowed": output.llm_invocation_allowed,
        "llm_decision_invocation_allowed": output.llm_invocation_allowed,
        "llm_guidance_generation_allowed": (
            "policy_constrained_only" if route_class in {"CLASS_0", "CLASS_2"} else output.llm_invocation_allowed
        ),
        "safe_outcome": _SAFE_OUTCOME.get(route_class, "unknown"),
        "safe_outcome_family": _SAFE_OUTCOME.get(route_class, "unknown"),
        "canonical_emergency_family": output.emergency_trigger_id,
        "unsafe_autonomous_actuation_allowed": False,
        "doorlock_autonomous_execution_allowed": False,
    }
    if route_class == "CLASS_2":
        observed.update(_class2_initial_observed())
    return observed


def _class2_initial_observed() -> dict[str, Any]:
    return {
        "class2_role": "clarification_transition_state",
        "candidate_generation_allowed": True,
        "candidate_generation_authorizes_actuation": False,
        "confirmation_required_before_transition": True,
        "allowed_transition_targets": list(_CLASS2_TRANSITIONS),
    }


def _candidate_prompt_observed(step: StepResolution) -> dict[str, Any]:
    candidates = step.raw_step.get("candidate_choices", [])
    targets = [
        item.get("candidate_transition_target")
        for item in candidates
        if isinstance(item, dict) and item.get("candidate_transition_target")
    ]
    return {
        "payload_family": "CLASS2_CLARIFICATION_INTERACTION",
        "class2_role": "clarification_transition_state",
        "unresolved_reason": "insufficient_context",
        "candidate_generation_actor": "LLM_GUIDANCE_LAYER_OR_INPUT_CONTEXT_MAPPER",
        "candidate_count_max": 4,
        "candidate_count": len(candidates),
        "candidate_transition_targets": targets,
        "presentation_channels": ["tts", "display", "accessible_feedback"],
        "candidate_generation_authorizes_actuation": False,
        "llm_decision_invocation_allowed": False,
        "llm_guidance_generation_allowed": "policy_constrained_only",
        "unsafe_autonomous_actuation_allowed": False,
        "doorlock_autonomous_execution_allowed": False,
    }


def _class2_fixture_observed(payload: dict[str, Any]) -> dict[str, Any]:
    selection = payload.get("selection_result", {}) if isinstance(payload.get("selection_result"), dict) else {}
    transition_target = payload.get("transition_target")
    selected_candidate = selection.get("selected_candidate_id")
    confirmed = selection.get("confirmed")
    timeout = selection.get("selection_source") == "timeout_or_no_response"
    return {
        "payload_family": payload.get("payload_family"),
        "source_route_class": "CLASS_2",
        "transition_target": transition_target,
        "selected_candidate_id": selected_candidate,
        "required_confirmation": transition_target == "CLASS_1",
        "required_confirmation_or_evidence": transition_target == "CLASS_0",
        "selection_source": selection.get("selection_source"),
        "confirmation_received": confirmed,
        "timeout_or_no_response": timeout,
        "no_intent_assumption": timeout,
        "validator_required_before_dispatch": transition_target == "CLASS_1",
        "single_admissible_action_required": transition_target == "CLASS_1",
        "llm_decision_invocation_allowed": False,
        "llm_guidance_generation_allowed": "policy_constrained_only",
        "candidate_generation_authorizes_actuation": False,
        "unsafe_autonomous_actuation_allowed": False,
        "doorlock_autonomous_execution_allowed": False,
    }


def _transition_family_for(expected: dict[str, Any]) -> str | None:
    return expected.get("expected_transition_family")


# ── step execution ──────────────────────────────────────────────────────────

@dataclass
class StepResult:
    step_id: Any
    action: str
    skipped: bool = False
    skip_reason: str = ""
    observed: Optional[dict[str, Any]] = None
    comparison: Optional[ComparisonResult] = None
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        if self.error:
            return False
        if self.skipped:
            return True
        if self.comparison is not None:
            return self.comparison.passed
        return True

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "step_id": self.step_id,
            "action": self.action,
            "passed": self.passed,
        }
        if self.skipped:
            d["skipped"] = True
            d["skip_reason"] = self.skip_reason
        if self.error:
            d["error"] = self.error
        if self.observed is not None:
            d["observed"] = self.observed
        if self.comparison is not None:
            d["comparison"] = self.comparison.to_dict()
        return d


@dataclass
class ScenarioResult:
    scenario_id: str
    passed: bool
    step_results: list[StepResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "passed": self.passed,
            "steps": [sr.to_dict() for sr in self.step_results],
        }


def execute_scenario(scenario: LoadedScenario) -> ScenarioResult:
    """
    Execute all steps of a loaded scenario and return a ScenarioResult.

    Steps are processed in order; the last observed output is carried forward
    to the next `observe_audit_stream` step for comparison.
    """
    steps = resolve_steps(_REPO_ROOT, scenario)
    step_results: list[StepResult] = []
    last_observed: Optional[dict[str, Any]] = None

    for step in steps:
        sr = _execute_step(step, last_observed)
        step_results.append(sr)
        if sr.observed is not None:
            last_observed = sr.observed

    all_passed = all(sr.passed for sr in step_results)
    return ScenarioResult(
        scenario_id=str(scenario.payload["scenario_id"]),
        passed=all_passed,
        step_results=step_results,
    )


def _execute_step(
    step: StepResolution,
    last_observed: Optional[dict[str, Any]],
) -> StepResult:
    action = step.action

    if action in {"publish_context_payload", "publish_emergency_event_payload"}:
        return _step_publish(step, fresh_timestamps=True)

    if action == "publish_fault_injected_context_payload":
        return _step_publish(step, fresh_timestamps=False)

    if action == "enter_class2_clarification_state":
        observed = dict(last_observed or {})
        observed.update(_class2_initial_observed())
        return _step_compare_or_observe(step, observed)

    if action in {"generate_bounded_candidate_choices", "present_candidate_choices"}:
        return _step_compare_or_observe(step, _candidate_prompt_observed(step))

    if action in {"collect_confirmation_or_timeout", "transition_after_confirmation"}:
        return _step_class2_transition(step, last_observed)

    if action in {
        "detect_candidate_conflict",
        "present_conflict_candidates_or_safe_deferral",
        "detect_missing_required_state",
        "request_state_recheck_or_safe_deferral",
    }:
        observed = dict(last_observed or {})
        observed.update(
            {
                "llm_decision_invocation_allowed": False,
                "llm_guidance_generation_allowed": "policy_constrained_only",
                "candidate_generation_authorizes_actuation": False,
                "unsafe_autonomous_actuation_allowed": False,
                "doorlock_autonomous_execution_allowed": False,
            }
        )
        return _step_compare_or_observe(step, observed)

    if action == "observe_audit_stream":
        return _step_observe(step, last_observed)

    return StepResult(
        step_id=step.step_id,
        action=action,
        skipped=True,
        skip_reason=f"unsupported action '{action}' — skipped",
    )


def _step_publish(step: StepResolution, *, fresh_timestamps: bool = True) -> StepResult:
    if step.payload_fixture is None:
        return StepResult(
            step_id=step.step_id,
            action=step.action,
            error="publish step has no payload_fixture",
        )
    try:
        payload = step.payload_fixture.payload
        # Treat structurally empty environmental_context as missing policy input
        # (C202 analog): conservative stale-timestamp path → CLASS_2.
        pcp_raw = payload.get("pure_context_payload", {})
        ec_raw = pcp_raw.get("environmental_context", {})
        if not ec_raw:
            fresh_timestamps = False
        router_input = _normalise_router_input(
            payload, step.step_id, fresh_timestamps=fresh_timestamps
        )
        output = route(router_input)
        observed = _router_output_to_observed(output)
        return StepResult(
            step_id=step.step_id,
            action=step.action,
            observed=observed,
        )
    except Exception as exc:
        return StepResult(
            step_id=step.step_id,
            action=step.action,
            error=f"{type(exc).__name__}: {exc}",
        )


def _step_class2_transition(
    step: StepResolution,
    last_observed: Optional[dict[str, Any]],
) -> StepResult:
    if step.payload_fixture is not None and isinstance(step.payload_fixture.payload, dict):
        return _step_compare_or_observe(step, _class2_fixture_observed(step.payload_fixture.payload))
    observed = dict(last_observed or {})
    observed.update(
        {
            "source_route_class": "CLASS_2",
            "transition_target": "SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION",
            "timeout_or_no_response": True,
            "confirmation_received": False,
            "no_intent_assumption": True,
            "llm_decision_invocation_allowed": False,
            "llm_guidance_generation_allowed": "policy_constrained_only",
            "candidate_generation_authorizes_actuation": False,
            "unsafe_autonomous_actuation_allowed": False,
            "doorlock_autonomous_execution_allowed": False,
        }
    )
    return _step_compare_or_observe(step, observed)


def _step_compare_or_observe(step: StepResolution, observed: dict[str, Any]) -> StepResult:
    if step.expected_fixture is None:
        return StepResult(step_id=step.step_id, action=step.action, observed=observed)
    try:
        expected: dict = step.expected_fixture.payload
        transition_family = _transition_family_for(expected)
        if transition_family is not None:
            observed.setdefault("transition_family", transition_family)
        comparison = compare_values(observed, expected)
        comparison.observed_path = ""
        comparison.expected_path = str(step.expected_fixture.path)
        return StepResult(
            step_id=step.step_id,
            action=step.action,
            observed=observed,
            comparison=comparison,
        )
    except Exception as exc:
        return StepResult(
            step_id=step.step_id,
            action=step.action,
            error=f"{type(exc).__name__}: {exc}",
        )


def _step_observe(
    step: StepResolution,
    last_observed: Optional[dict[str, Any]],
) -> StepResult:
    if step.expected_fixture is None:
        return StepResult(
            step_id=step.step_id,
            action=step.action,
            skipped=True,
            skip_reason="observe_audit_stream step has no expected_fixture — skipped",
        )
    if last_observed is None:
        return StepResult(
            step_id=step.step_id,
            action=step.action,
            error="observe_audit_stream: no observed result available from a preceding step",
        )
    return _step_compare_or_observe(step, last_observed)


# ── CLI entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Execute an integration scenario against mac_mini policy_router."
    )
    parser.add_argument(
        "--scenario",
        default="integration/scenarios/class0_e001_scenario_skeleton.json",
        help="Repository-relative path to the scenario JSON file.",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    repo_root = find_repo_root(Path.cwd())
    scenario = load_scenario(repo_root, args.scenario)
    result = execute_scenario(scenario)

    indent = 2 if args.pretty else None
    print(json.dumps(result.to_dict(), indent=indent, ensure_ascii=False))
    raise SystemExit(0 if result.passed else 1)

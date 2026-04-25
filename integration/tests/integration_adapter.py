#!/usr/bin/env python3
"""
Integration adapter: connects the runner skeleton and comparator to mac_mini services.

Executes scenario steps by calling policy_router.route() directly
(no live MQTT broker required for deterministic local/CI testing).

Two-step pattern per scenario:
  1. publish_context_payload  → parse fixture → call route() → cache result
  2. observe_audit_stream     → map result to observed dict → compare against expected fixture

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
    "CLASS_2": "caregiver_or_high_safety_escalation_path",
}


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
    return {
        "route_class": route_class,
        "routing_target": route_class,
        "llm_invocation_allowed": output.llm_invocation_allowed,
        "safe_outcome": _SAFE_OUTCOME.get(route_class, "unknown"),
        "canonical_emergency_family": output.emergency_trigger_id,
    }


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

    if action == "publish_context_payload":
        return _step_publish(step, fresh_timestamps=True)

    if action == "publish_fault_injected_context_payload":
        return _step_publish(step, fresh_timestamps=False)

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
            error="publish_context_payload step has no payload_fixture",
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
            error="observe_audit_stream: no observed result available from a preceding publish step",
        )
    try:
        expected: dict = step.expected_fixture.payload
        comparison = compare_values(last_observed, expected)
        comparison.observed_path = ""
        comparison.expected_path = str(step.expected_fixture.path)
        return StepResult(
            step_id=step.step_id,
            action=step.action,
            observed=last_observed,
            comparison=comparison,
        )
    except Exception as exc:
        return StepResult(
            step_id=step.step_id,
            action=step.action,
            error=f"{type(exc).__name__}: {exc}",
        )


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

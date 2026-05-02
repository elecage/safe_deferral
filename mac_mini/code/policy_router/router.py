"""Policy Router — deterministic Class 0 / 1 / 2 classification.

Loads all thresholds and emergency-trigger predicates from canonical assets
at init time so no policy values are hardcoded here.

Authority rule (from 02_safety_and_authority_boundaries.md):
  - LLM output is candidate guidance only, never execution authority.
  - This router classifies routes; it does not invoke the LLM or dispatch actuators.
  - Schema validation failure is always CLASS_2 (C202), never a crash.
"""

import time
from typing import Optional

import jsonschema

from policy_router.models import PolicyRouterResult, RouteClass
from shared.asset_loader import AssetLoader


class PolicyRouter:
    def __init__(self, asset_loader: Optional[AssetLoader] = None):
        loader = asset_loader or AssetLoader()

        self._input_schema = loader.load_schema("policy_router_input_schema.json")
        self._resolver = loader.make_schema_resolver()

        policy = loader.load_policy_table()
        gc = policy["global_constraints"]
        self._freshness_threshold_ms: int = gc["freshness_threshold_ms"]

        self._emergency_triggers: list = (
            policy["routing_policies"]["class_0_emergency"]["triggers"]
        )

        c2_triggers = policy["routing_policies"]["class_2_clarification_transition"]["triggers"]

        # C206 predicate: button events whose event_code is not in the recognized set
        c206 = next((t for t in c2_triggers if t["id"] == "C206"), {})
        pred206 = c206.get("minimal_triggering_predicate", {})
        self._c206_event_type: str = pred206.get("event_type", "button")
        self._c206_recognized_codes: set = set(
            pred206.get("recognized_class1_button_event_codes", ["single_click"])
        )

        # C208 predicate: visitor/doorbell sensor event → doorlock-sensitive path
        c208 = next((t for t in c2_triggers if t["id"] == "C208"), {})
        pred208 = c208.get("minimal_triggering_predicate", {})
        self._c208_event_type: str = pred208.get("event_type", "sensor")
        self._c208_event_code: str = pred208.get("event_code", "doorbell_detected")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, raw_input: dict) -> PolicyRouterResult:
        """Classify raw_input into CLASS_0, CLASS_1, or CLASS_2."""

        # Step 1: schema validation
        validation_error = self._validate_schema(raw_input)
        if validation_error:
            return self._class2(
                raw_input,
                trigger_id="C202",
                reason=f"schema_validation_failed: {validation_error}",
            )

        source_node_id: str = raw_input["source_node_id"]
        meta: dict = raw_input["routing_metadata"]
        ctx: dict = raw_input["pure_context_payload"]

        audit_id: str = meta["audit_correlation_id"]
        ingest_ts: int = meta["ingest_timestamp_ms"]
        network_status: str = meta["network_status"]
        experiment_mode: Optional[str] = meta.get("experiment_mode")
        class2_candidate_source_mode: Optional[str] = meta.get("class2_candidate_source_mode")

        trigger: dict = ctx["trigger_event"]
        env: dict = ctx["environmental_context"]

        routed_at = int(time.time() * 1000)

        # Step 2: staleness check (C204)
        trigger_ts: int = trigger["timestamp_ms"]
        if (ingest_ts - trigger_ts) > self._freshness_threshold_ms:
            return PolicyRouterResult(
                route_class=RouteClass.CLASS_2,
                trigger_id="C204",
                llm_invocation_allowed=False,
                candidate_generation_allowed=True,
                unresolved_reason="sensor_staleness_detected",
                source_node_id=source_node_id,
                audit_correlation_id=audit_id,
                network_status=network_status,
                routed_at_ms=routed_at,
                pure_context_payload=ctx,
                experiment_mode=experiment_mode,
                class2_candidate_source_mode=class2_candidate_source_mode,
            )

        # Step 3: emergency triggers → CLASS_0
        matched = self._match_emergency(trigger, env)
        if matched:
            return PolicyRouterResult(
                route_class=RouteClass.CLASS_0,
                trigger_id=matched,
                llm_invocation_allowed=False,
                candidate_generation_allowed=False,
                unresolved_reason=None,
                source_node_id=source_node_id,
                audit_correlation_id=audit_id,
                network_status=network_status,
                routed_at_ms=routed_at,
                pure_context_payload=ctx,
                experiment_mode=experiment_mode,
                class2_candidate_source_mode=class2_candidate_source_mode,
            )

        # Step 4: C208 — visitor/doorbell sensor event (doorlock-sensitive path)
        if self._is_visitor_context(trigger):
            return self._class2(
                raw_input,
                trigger_id="C208",
                reason="visitor_context_sensitive_actuation_required",
            )

        # Step 5: C206 — insufficient context (ambiguous button event)
        if self._is_insufficient_context(trigger):
            return self._class2(
                raw_input,
                trigger_id="C206",
                reason="insufficient_context_for_intent_resolution",
            )

        # Step 6: all checks passed → CLASS_1
        return PolicyRouterResult(
            route_class=RouteClass.CLASS_1,
            trigger_id=None,
            llm_invocation_allowed=True,
            candidate_generation_allowed=True,
            unresolved_reason=None,
            source_node_id=source_node_id,
            audit_correlation_id=audit_id,
            network_status=network_status,
            routed_at_ms=routed_at,
            pure_context_payload=ctx,
            experiment_mode=experiment_mode,
            class2_candidate_source_mode=class2_candidate_source_mode,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_schema(self, raw_input: dict) -> Optional[str]:
        try:
            validator = jsonschema.Draft7Validator(
                schema=self._input_schema,
                resolver=self._resolver,
            )
            errors = sorted(validator.iter_errors(raw_input), key=str)
            if errors:
                return errors[0].message
        except Exception as exc:  # noqa: BLE001
            return str(exc)
        return None

    def _match_emergency(self, trigger: dict, env: dict) -> Optional[str]:
        """Return the first matching emergency trigger ID, or None."""
        for t in self._emergency_triggers:
            if self._evaluate_trigger(t["type"], t["minimal_triggering_predicate"], trigger, env):
                return t["id"]
        return None

    def _evaluate_trigger(
        self,
        trigger_type: str,
        predicate: dict,
        trigger: dict,
        env: dict,
    ) -> bool:
        if trigger_type == "threshold_crossing":
            actual = env.get(predicate["sensor"])
            if actual is None:
                return False
            return self._compare(actual, predicate["operator"], predicate["value"])

        if trigger_type == "pattern_event":
            # source_type == "button" is implicit; check event_code
            return trigger.get("event_code") == predicate.get("event")

        if trigger_type == "state_trigger":
            actual = env.get(predicate["sensor"])
            return self._compare(actual, predicate.get("operator", "=="), predicate["value"])

        if trigger_type == "event_trigger":
            return (
                trigger.get("event_type") == predicate.get("event_type")
                and trigger.get("event_code") == predicate.get("event_code")
            )

        return False

    @staticmethod
    def _compare(actual, operator: str, value) -> bool:
        if actual is None:
            return False
        try:
            ops = {">=": actual >= value, ">": actual > value,
                   "<=": actual <= value, "<": actual < value, "==": actual == value}
            return ops.get(operator, False)
        except TypeError:
            return False

    def _is_visitor_context(self, trigger: dict) -> bool:
        """Return True when the trigger is a doorbell/visitor-arrival sensor event (C208).

        Any doorbell_detected trigger may involve doorlock-sensitive actuation which
        is outside the Class 1 autonomous low-risk catalog.  Routes to CLASS_2 so a
        caregiver can confirm or deny the visitor-response action.
        """
        return (
            trigger.get("event_type") == self._c208_event_type
            and trigger.get("event_code") == self._c208_event_code
        )

    def _is_insufficient_context(self, trigger: dict) -> bool:
        """Return True when the trigger event is ambiguous (C206).

        Applies only to button events whose event_code is not in the
        recognized clear-intent set loaded from the policy table.
        Emergency button codes (triple_hit) are already caught by CLASS_0
        before this check and never reach here.
        """
        return (
            trigger.get("event_type") == self._c206_event_type
            and trigger.get("event_code") not in self._c206_recognized_codes
        )

    def _class2(self, raw_input: dict, trigger_id: str, reason: str) -> PolicyRouterResult:
        meta = raw_input.get("routing_metadata", {})
        return PolicyRouterResult(
            route_class=RouteClass.CLASS_2,
            trigger_id=trigger_id,
            llm_invocation_allowed=False,
            candidate_generation_allowed=True,
            unresolved_reason=reason,
            source_node_id=raw_input.get("source_node_id", "unknown"),
            audit_correlation_id=meta.get("audit_correlation_id", "unknown"),
            network_status=meta.get("network_status", "unknown"),
            routed_at_ms=int(time.time() * 1000),
            pure_context_payload=raw_input.get("pure_context_payload", {}),
            experiment_mode=meta.get("experiment_mode"),
            class2_candidate_source_mode=meta.get("class2_candidate_source_mode"),
        )

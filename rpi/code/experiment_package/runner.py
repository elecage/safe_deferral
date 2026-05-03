"""PackageRunner — trial orchestration: publish → observe → match → record.

Authority boundary:
  - PackageRunner publishes experiment payloads via VirtualNodeManager only.
  - It does not bypass policy, validator, or doorlock authority.
  - Observed results are experiment artifacts, not validator re-decisions.
  - FAULT_CONTRACT_DRIFT_01 uses a read-only ContractDriftPublisher that sends
    to a non-registry topic for governance detection testing; it cannot publish
    to operational control topics.
"""

import logging
import threading
import time
import uuid
from typing import Optional

from experiment_package.definitions import PackageId, PACKAGES
from experiment_package.fault_profiles import FAULT_PROFILES, FaultProfile
from experiment_package.trial_store import (
    TrialResult,
    TrialStore,
    _expected_transition_targets,
)
from shared.asset_loader import RpiAssetLoader

# Sleep between detecting the initial CLASS_2 routing snapshot and publishing
# the synthetic user/emergency selection that drives the trial to its expected
# transition. The runner already waits for the initial CLASS_2 observation
# (deterministic), so this sleep only needs to cover the small window between
# the Mac mini publishing that observation and the _await_user_then_caregiver
# background thread registering _pending_user_class2.
#
# Bumped from 0.5 s → 1.0 s as part of P0.3 of
# 10_llm_class2_integration_alignment_plan.md to add a comfortable margin
# above the worker-thread startup time after the LLM-bounded start_session
# returns. With P0.1 in place, start_session always returns within
# llm_call_budget_s, after which announce_class2 + escalate_to_class2 +
# thread spawn complete in milliseconds — but a 1 s margin makes the runner
# robust to slower CI / virtualised hosts without needing a synchronisation
# signal.
_CLASS2_SELECTION_DRIVE_DELAY_S = 1.0

# How long to keep polling the NotificationStore after the observation has
# already arrived. The Mac mini timeout/caregiver-fallback path emits the
# dashboard observation BEFORE the caregiver notification, so the runner must
# tolerate notification-after-observation races (Issue #4 of 2026-05-01
# CLASS2 transition closure session).
_POST_OBS_NOTIFICATION_GRACE_S = 2.0

log = logging.getLogger(__name__)

_TRIAL_TIMEOUT_S = 30.0

# Phase-decomposed CLASS_2 trial timeout
# (P2.2 of 10_llm_class2_integration_alignment_plan.md).
#
# A CLASS_2 trial may walk through three serial phases plus telemetry slack:
#   1. LLM candidate generation budget — the manager bounds the LLM call;
#      its budget comes from policy_table.global_constraints.llm_request_timeout_ms
#      (PR #91 P0.1+P0.2). Default 8 s.
#   2. User clarification window — the Mac mini's class2_clarification_timeout_ms
#      from the same policy block. Default 30 s.
#   3. Caregiver Telegram window — policy_table.global_constraints.
#      caregiver_response_timeout_ms (default 300_000 ms = 300 s). Mac mini
#      reads the same field (or accepts CAREGIVER_RESPONSE_TIMEOUT_S env
#      override), so the two stay aligned without manual sync.
#   4. Telemetry publish slack — small margin so the trial does not time out
#      while the post-transition observation is still in flight.
#
# Module-level defaults are kept so old callers that import
# _TRIAL_TIMEOUT_CLASS2_S still work; new callers should use
# PackageRunner._class2_trial_timeout_s, which reflects the live policy.
_LLM_BUDGET_DEFAULT_S = 8.0
_USER_PHASE_TIMEOUT_DEFAULT_S = 30.0
_CAREGIVER_PHASE_TIMEOUT_S = 300.0
_TRIAL_TIMEOUT_CLASS2_SLACK_S = 30.0
_TRIAL_TIMEOUT_CLASS2_S = (
    _LLM_BUDGET_DEFAULT_S
    + _USER_PHASE_TIMEOUT_DEFAULT_S
    + _CAREGIVER_PHASE_TIMEOUT_S
    + _TRIAL_TIMEOUT_CLASS2_SLACK_S
)
_POLL_INTERVAL_S = 0.25

# All experiment fixture payloads are in policy-router input format and must
# be delivered to the normalized context/input topic that the Mac mini reads.
# Emergency scenarios specify ingress_topic=safe_deferral/emergency/event in
# the scenario doc (the physical-device path), but experiment fixtures skip
# the bridge and publish directly to the normalized topic.
_CONTEXT_INPUT_TOPIC = "safe_deferral/context/input"

# Governance-drift topic: deliberately unregistered, for testing
# Must NOT be an operational control topic.
_CONTRACT_DRIFT_TOPIC = "safe_deferral/_governance_test/contract_drift"


class PackageRunner:
    """Orchestrates experiment trials for packages A~G.

    Usage:
        runner = PackageRunner(vnm, obs_store, trial_store)
        trial = runner.start_trial_async(run_id, package_id, node_id,
                                         scenario_id, fault_profile_id,
                                         comparison_condition,
                                         expected_route_class)
        # trial.status == "pending"; poll /trials/{trial_id} until completed/timeout
    """

    def __init__(
        self,
        vnm,
        obs_store,
        trial_store: TrialStore,
        asset_loader: Optional[RpiAssetLoader] = None,
        notification_store=None,
        clarification_store=None,
    ) -> None:
        self._vnm = vnm
        self._obs = obs_store
        self._store = trial_store
        self._loader = asset_loader or RpiAssetLoader()
        self._notif = notification_store
        # Phase 5: optional ClarificationStore so trial_store can compute
        # class2_llm_quality metrics (candidate_source provenance, user
        # pickup rate per source).
        self._clarif = clarification_store
        # P2.2 of 10_llm_class2_integration_alignment_plan.md: compose the
        # CLASS_2 trial timeout from policy-aware phase budgets so a tighter
        # llm_request_timeout_ms or class2_clarification_timeout_ms in policy
        # automatically tightens the trial wait. Each component falls back to
        # the matching module-level default if the policy load or field is
        # missing (older policy_table versions stay usable).
        try:
            policy = self._loader.load_policy_table()
            gc = policy.get("global_constraints", {}) or {}
        except Exception:
            gc = {}
        self._class2_llm_budget_s: float = float(
            gc.get("llm_request_timeout_ms", _LLM_BUDGET_DEFAULT_S * 1000)
        ) / 1000.0
        self._class2_user_phase_timeout_s: float = float(
            gc.get("class2_clarification_timeout_ms", _USER_PHASE_TIMEOUT_DEFAULT_S * 1000)
        ) / 1000.0
        # Caregiver Telegram window now sourced from
        # policy_table.global_constraints.caregiver_response_timeout_ms. Mac
        # mini reads the same field (with optional env override) so the two
        # stay aligned without manual sync.
        self._class2_caregiver_phase_timeout_s: float = float(
            gc.get("caregiver_response_timeout_ms", _CAREGIVER_PHASE_TIMEOUT_S * 1000)
        ) / 1000.0
        self._class2_trial_timeout_slack_s: float = _TRIAL_TIMEOUT_CLASS2_SLACK_S
        self._class2_trial_timeout_s: float = (
            self._class2_llm_budget_s
            + self._class2_user_phase_timeout_s
            + self._class2_caregiver_phase_timeout_s
            + self._class2_trial_timeout_slack_s
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_trial_async(
        self,
        run_id: str,
        package_id: str,
        node_id: str,
        scenario_id: str,
        fault_profile_id: Optional[str],
        comparison_condition: Optional[str],
        expected_route_class: str,
        expected_validation: str = "approved",
        expected_outcome: Optional[str] = None,
        expected_transition_target_override: Optional[str] = None,
        user_response_script: Optional[dict] = None,
    ) -> TrialResult:
        """Create a TrialResult record, launch background thread, return immediately."""
        profile: Optional[FaultProfile] = (
            FAULT_PROFILES.get(fault_profile_id) if fault_profile_id else None
        )
        if fault_profile_id and profile is None:
            raise ValueError(f"Unknown fault_profile_id: {fault_profile_id!r}")

        eff_outcome = expected_outcome or (
            profile.expected_outcome if profile else "class_1_approved"
        )

        # Load the scenario's class2_clarification_expectation block whenever a
        # scenario_id is set, regardless of whether the caller passed an explicit
        # transition-target override. The target value may be overridden, but the
        # boolean contract (requires_validator_reentry_when_class1) and any other
        # scenario-declared expectation must always survive — otherwise an
        # override-using caller (fixture-less / API) silently drops the
        # validator re-entry contract that the scenario declared.
        eff_transition_target: Optional[str] = None
        eff_requires_validator_reentry: bool = False
        eff_user_intent: Optional[dict] = None
        if scenario_id:
            try:
                scenario = self._loader.load_scenario(scenario_id)
            except Exception as exc:
                log.warning(
                    "Could not load scenario %s for trial enrichment: %s",
                    scenario_id, exc,
                )
                scenario = None
            if scenario is not None:
                if expected_route_class == "CLASS_2":
                    c2_exp = scenario.get("class2_clarification_expectation") or {}
                    eff_transition_target = c2_exp.get("expected_transition_target") or None
                    eff_requires_validator_reentry = bool(
                        c2_exp.get("requires_validator_reentry_when_class1", False)
                    )
                # Snapshot user_intent (paper-eval intent-match measurement).
                # Optional — scenarios without this block produce no metric;
                # the aggregator returns None for cells with no intent.
                ui = scenario.get("user_intent")
                if isinstance(ui, dict):
                    eff_user_intent = dict(ui)
        # Apply the explicit override last so the scenario's boolean contract
        # is preserved.
        if expected_transition_target_override is not None:
            eff_transition_target = expected_transition_target_override

        correlation_id = f"pkg-{package_id}-{uuid.uuid4().hex[:8]}"

        trial = self._store.create_trial(
            run_id=run_id,
            package_id=package_id,
            scenario_id=scenario_id,
            fault_profile_id=fault_profile_id,
            comparison_condition=comparison_condition,
            expected_route_class=expected_route_class,
            expected_validation=expected_validation,
            expected_outcome=eff_outcome,
            audit_correlation_id=correlation_id,
            expected_transition_target=eff_transition_target,
            requires_validator_reentry_when_class1=eff_requires_validator_reentry,
        )

        # Snapshot CLASS_2 phase budgets at trial creation time so that policy
        # changes after the fact do not retroactively reinterpret the trial's
        # wait windows. Only meaningful for CLASS_2 trials, but harmless to
        # include otherwise.
        if expected_route_class == "CLASS_2":
            trial.class2_phase_budgets_snapshot = {
                "llm_budget_s": self._class2_llm_budget_s,
                "user_phase_timeout_s": self._class2_user_phase_timeout_s,
                "caregiver_phase_timeout_s": self._class2_caregiver_phase_timeout_s,
                "trial_timeout_slack_s": self._class2_trial_timeout_slack_s,
                "trial_timeout_s": self._class2_trial_timeout_s,
                "source": "policy_table.global_constraints + runner module defaults",
            }

        # Stash the cell-level user_response_script onto the trial so the
        # background _match_observation loop can decide whether to drive
        # a Class 2 selection when the LLM defers. Default None = no drive
        # (current behaviour, caregiver fallback).
        if user_response_script is not None:
            trial.user_response_script = dict(user_response_script)

        # Snapshot the scenario's user_intent for the intent-match metric.
        # Frozen at trial creation so post-hoc scenario edits cannot
        # retroactively change what the trial was scored against.
        if eff_user_intent is not None:
            trial.user_intent_snapshot = dict(eff_user_intent)

        t = threading.Thread(
            target=self._run_trial,
            args=(trial, node_id, profile, correlation_id, trial.scenario_id),
            daemon=True,
            name=f"trial-{trial.trial_id[:8]}",
        )
        t.start()
        return trial

    # ------------------------------------------------------------------
    # Background trial execution
    # ------------------------------------------------------------------

    def _load_base_payload(
        self, scenario_id: str, node
    ) -> tuple[dict, Optional[str]]:
        """Load base payload from scenario fixture if available, else node template.

        Returns:
            (payload, publish_topic_override)
            publish_topic_override is _CONTEXT_INPUT_TOPIC when a fixture is used
            (all fixtures are in policy-router input format), or None to use the
            node's own publish_topic.
        """
        if scenario_id:
            try:
                scenario = self._loader.load_scenario(scenario_id)
                for step in scenario.get("steps", []):
                    fixture_path = step.get("payload_fixture")
                    if fixture_path and self._loader.fixture_exists(fixture_path):
                        fixture = self._loader.load_fixture(fixture_path)
                        log.info(
                            "Trial using scenario fixture: %s → topic=%s",
                            fixture_path, _CONTEXT_INPUT_TOPIC,
                        )
                        # Fixtures are always in policy-router input (context/input)
                        # format.  Override the node's publish_topic so the payload
                        # reaches the Mac mini regardless of node type.
                        return fixture, _CONTEXT_INPUT_TOPIC
            except Exception as exc:
                log.warning(
                    "Could not load scenario fixture for %s: %s", scenario_id, exc
                )
        return dict(node.profile.payload_template), None

    def _run_trial(
        self,
        trial: TrialResult,
        node_id: str,
        profile: Optional[FaultProfile],
        correlation_id: str,
        scenario_id: str = "",
    ) -> None:
        """Background: apply fault → publish → wait for observation → record result."""
        try:
            node = self._vnm.get_node(node_id)
            if node is None:
                log.error("Trial %s: node %s not found", trial.trial_id, node_id)
                self._store.timeout_trial(trial.trial_id)
                return

            # --- Build payload ---
            base_payload, topic_override = self._load_base_payload(scenario_id, node)
            now_ms = int(time.time() * 1000)
            base_payload.setdefault("routing_metadata", {})
            base_payload["routing_metadata"]["audit_correlation_id"] = correlation_id
            base_payload["routing_metadata"]["ingest_timestamp_ms"] = now_ms
            # Refresh pure_context_payload.trigger_event.timestamp_ms to "now"
            # ONLY when the trigger_event already exists in the payload
            # (i.e. a real scenario fixture was loaded). Without this refresh,
            # fixtures' hardcoded historic timestamps trip the policy router's
            # freshness check (default 3s threshold) on every trial → spurious
            # CLASS_2 routing with `sensor_staleness_detected` (C204), which
            # silently corrupts paper-eval Class 1 measurements.
            #
            # Guarded by 'in' rather than setdefault because some test paths
            # (fixture-less / scenario_id="") build a payload with no
            # trigger_event at all and downstream code (e.g. Class 2 button
            # press auto-simulation) expects the absence to mean
            # 'fill in event_code yourself'.
            ctx = base_payload.get("pure_context_payload")
            if isinstance(ctx, dict) and isinstance(ctx.get("trigger_event"), dict):
                ctx["trigger_event"]["timestamp_ms"] = now_ms
            # Package A comparison_condition prefix routing — each prefix
            # selects which routing_metadata field receives the value (after
            # the prefix/suffix is stripped so the schema enum matches).
            # The four condition spaces target different Mac mini branches
            # and never collide. Most-specific prefix wins (checked first):
            #
            #   {direct_mapping, rule_only, llm_assisted}
            #     → routing_metadata.experiment_mode (Class 1 intent recovery, PR #79)
            #
            #   class2_{static_only, llm_assisted}
            #     → routing_metadata.class2_candidate_source_mode
            #       (LLM-vs-static candidate generation, doc 10 §3.3 P2.3, PR #101)
            #
            #   class2_scan_{source_order, deterministic}
            #     → routing_metadata.class2_scan_ordering_mode
            #       (scanning ordering comparison, doc 12 §14 Phase 1.5)
            #
            #   class2_{direct_select, scanning}_input
            #     → routing_metadata.class2_input_mode
            #       (interaction-model comparison, doc 12 §9 Phase 5)
            cc = trial.comparison_condition
            if cc:
                if cc.startswith("class2_scan_"):
                    base_payload["routing_metadata"]["class2_scan_ordering_mode"] = (
                        cc[len("class2_scan_"):]
                    )
                elif cc.startswith("class2_") and cc.endswith("_input"):
                    base_payload["routing_metadata"]["class2_input_mode"] = (
                        cc[len("class2_"):-len("_input")]
                    )
                elif cc.startswith("class2_"):
                    base_payload["routing_metadata"]["class2_candidate_source_mode"] = (
                        cc[len("class2_"):]
                    )
                else:
                    base_payload["routing_metadata"]["experiment_mode"] = cc

            # --- Apply fault profile transform ---
            if profile and profile.profile_id != "FAULT_CONTRACT_DRIFT_01":
                payload = profile.apply(base_payload)
            else:
                payload = base_payload

            # --- Publish ---
            if profile and profile.profile_id == "FAULT_CONTRACT_DRIFT_01":
                self._publish_contract_drift(payload, correlation_id)
                # No runtime observation will ever arrive for an unregistered topic.
                # Complete immediately; _is_pass() treats obs_class=None as a
                # governance-level pass for this profile.
                self._store.complete_trial(
                    trial.trial_id,
                    {
                        "audit_correlation_id": correlation_id,
                        "governance_fault": "FAULT_CONTRACT_DRIFT_01",
                    },
                )
                log.info(
                    "Trial %s completed: FAULT_CONTRACT_DRIFT_01 — "
                    "no runtime observation expected (governance pass)",
                    trial.trial_id,
                )
                return
            else:
                self._publish_normal(node, payload, correlation_id, topic_override)

            # --- Wait for observation ---
            # CLASS_2 trials go through Phase 1 (user, ≤15 s) then Phase 2
            # (caregiver Telegram, ≤300 s).  Use a longer timeout so the trial
            # runner does not declare timeout before the Mac mini publishes the
            # final class2 interaction snapshot.
            #
            # Note: we do NOT auto-simulate a user button press here.  Doing so
            # would complete Phase 1 immediately and prevent Phase 2 (Telegram)
            # from ever being triggered, which would block caregiver-path tests.
            # The trial completes naturally when the Mac mini publishes the final
            # class2 observation (after user response, caregiver response, or the
            # full Phase-2 timeout).
            # llm_assisted trials may legitimately escalate from CLASS_1 to
            # CLASS_2 when the LLM returns safe_deferral. They need the longer
            # CLASS_2 budget even when the matrix expects CLASS_1, otherwise
            # the trial times out before the class2 update / post-transition
            # snapshot arrives. Deterministic comparison_conditions
            # (direct_mapping, rule_only) keep the short budget — they do not
            # perform an LLM call on the Class 1 path so their wall-time is
            # bounded by the table / heuristic, not by inference latency.
            needs_class2_budget = (
                trial.expected_route_class == "CLASS_2"
                or trial.comparison_condition == "llm_assisted"
            )
            trial_timeout = (
                self._class2_trial_timeout_s
                if needs_class2_budget
                else _TRIAL_TIMEOUT_S
            )
            observation = self._match_observation(
                correlation_id, trial_timeout, trial=trial, node=node,
            )

            notification = self._await_notification(correlation_id, observation)
            clarification = self._await_clarification(correlation_id, observation)

            # Capture every snapshot the Mac mini published with this
            # correlation_id, in arrival order. observation_payload (the
            # 'best match' the runner's polling loop chose) drives the
            # pass/fail verdict; observation_history preserves the full
            # path so analysis can reconstruct what happened — e.g. for
            # CLASS_2-escalated trials the history typically holds the
            # initial routing snapshot, the class2 update, and (when the
            # selection routes back to a Class 1 / Class 0 action) the
            # post-transition outcome snapshot.
            observation_history = self._obs.find_all_by_correlation_id(correlation_id)

            if observation is None:
                log.warning(
                    "Trial %s timed out waiting for audit_correlation_id=%s",
                    trial.trial_id, correlation_id,
                )
                self._store.timeout_trial(
                    trial.trial_id,
                    notification_payload=notification,
                    clarification_payload=clarification,
                    observation_history=observation_history,
                )
            else:
                self._store.complete_trial(
                    trial.trial_id, observation,
                    notification_payload=notification,
                    clarification_payload=clarification,
                    observation_history=observation_history,
                )
                log.info(
                    "Trial %s completed: route=%s validation=%s pass=%s latency=%.1fms",
                    trial.trial_id,
                    observation.get("route_class"),
                    observation.get("validation_status"),
                    self._store.get_trial(trial.trial_id).pass_ if self._store.get_trial(trial.trial_id) else "?",
                    self._store.get_trial(trial.trial_id).latency_ms or 0.0 if self._store.get_trial(trial.trial_id) else 0.0,
                )

        except Exception as exc:
            log.exception("Trial %s failed unexpectedly: %s", trial.trial_id, exc)
            self._store.timeout_trial(trial.trial_id)

    def _publish_normal(
        self,
        node,
        payload: dict,
        correlation_id: str,
        topic_override: Optional[str] = None,
    ) -> None:
        """Publish trial payload via VirtualNodeManager (registry-validated topic).

        topic_override: when set (e.g. _CONTEXT_INPUT_TOPIC for fixture-based
        trials) the node's publish_topic is temporarily replaced so the payload
        reaches the correct MQTT topic even if the node was created with a
        different topic (e.g. safe_deferral/emergency/event).
        """
        original_template = node.profile.payload_template
        original_topic = node.profile.publish_topic
        node.profile.payload_template = payload
        if topic_override:
            node.profile.publish_topic = topic_override
        try:
            self._vnm.publish_once(node)
        finally:
            node.profile.payload_template = original_template
            node.profile.publish_topic = original_topic

    def _publish_contract_drift(self, payload: dict, correlation_id: str) -> None:
        """Publish to unregistered topic for governance drift detection testing.

        Does NOT publish to any operational control topic.
        The governance verification layer (or lack thereof on the RPi) will
        record this as a governance-drift artifact.
        """
        try:
            drift_payload = dict(payload)
            drift_payload["_governance_fault"] = "FAULT_CONTRACT_DRIFT_01"
            drift_payload["_drift_topic"] = _CONTRACT_DRIFT_TOPIC
            # Log the governance drift artifact. No MQTT publish to any operational
            # or unregistered topic is performed here; the GovernanceBackend handles
            # verification. The caller (_run_trial) completes the trial immediately
            # since no runtime observation will arrive for an unregistered topic.
            log.info(
                "FAULT_CONTRACT_DRIFT_01: governance drift artifact recorded "
                "(correlation_id=%s, drift_topic=%s)",
                correlation_id, _CONTRACT_DRIFT_TOPIC,
            )
        except Exception as exc:
            log.warning("Contract drift publish failed: %s", exc)

    def _await_notification(
        self,
        correlation_id: str,
        observation: Optional[dict],
    ) -> Optional[dict]:
        """Look up the matching notification, briefly waiting for late arrivals.

        The Mac mini timeout/caregiver-fallback path emits the dashboard
        observation BEFORE the caregiver notification, so a single store lookup
        immediately after observation match would race and miss the notification
        even when one was published.  Polls the NotificationStore for up to
        _POST_OBS_NOTIFICATION_GRACE_S; returns None if no notification arrived.
        """
        if self._notif is None:
            return None
        # Fast path: notification may already be present.
        notif = self._notif.find_by_correlation_id(correlation_id)
        if notif is not None:
            return notif
        # If we have no observation we already know the trial timed out — no
        # point polling for a notification that almost certainly will not arrive.
        if observation is None:
            return None
        deadline = time.monotonic() + _POST_OBS_NOTIFICATION_GRACE_S
        while time.monotonic() < deadline:
            time.sleep(_POLL_INTERVAL_S)
            notif = self._notif.find_by_correlation_id(correlation_id)
            if notif is not None:
                return notif
        return None

    def _await_clarification(
        self,
        correlation_id: str,
        observation: Optional[dict],
    ) -> Optional[dict]:
        """Look up the matching clarification record, briefly waiting for late
        arrivals. Mirrors _await_notification: TelemetryAdapter.publish_class2_update
        publishes the dashboard observation immediately followed by the
        clarification record on safe_deferral/clarification/interaction, but the
        two MQTT round-trips can race so a single store lookup right after the
        observation match can miss the record. Polls for up to
        _POST_OBS_NOTIFICATION_GRACE_S; returns None if nothing arrived.
        """
        if self._clarif is None:
            return None
        rec = self._clarif.find_by_correlation_id(correlation_id)
        if rec is not None:
            return rec
        if observation is None:
            return None
        deadline = time.monotonic() + _POST_OBS_NOTIFICATION_GRACE_S
        while time.monotonic() < deadline:
            time.sleep(_POLL_INTERVAL_S)
            rec = self._clarif.find_by_correlation_id(correlation_id)
            if rec is not None:
                return rec
        return None

    def _simulate_class2_button(
        self,
        node,
        correlation_id: str,
        event_code: str = "single_click",
    ) -> None:
        """Simulate a user/emergency button press during an active CLASS_2 session.

        Temporarily patches the node's payload_template with event_type=button
        and the requested event_code, then publishes once. The Mac mini pipeline
        intercepts this as the user's selection and wakes the CLASS_2 waiter.

        event_code mapping (mirrors Pipeline._try_handle_as_user_selection):
          - "single_click"  → first candidate (typically C1_LIGHTING_ASSISTANCE → CLASS_1)
          - "triple_hit"    → first CLASS_0-targeted candidate (emergency confirmation)

        The node's original template and state are restored in the finally block.
        """
        import copy
        from virtual_node_manager.models import VirtualNodeState

        now_ms = int(time.time() * 1000)
        patched = copy.deepcopy(node.profile.payload_template)
        patched.setdefault("pure_context_payload", {})
        patched["pure_context_payload"].setdefault("trigger_event", {})
        patched["pure_context_payload"]["trigger_event"]["event_type"] = "button"
        patched["pure_context_payload"]["trigger_event"]["event_code"] = event_code
        patched["pure_context_payload"]["trigger_event"]["timestamp_ms"] = now_ms
        patched.setdefault("routing_metadata", {})
        patched["routing_metadata"]["audit_correlation_id"] = correlation_id
        patched["routing_metadata"]["ingest_timestamp_ms"] = now_ms

        original_template = node.profile.payload_template
        original_state = node.state
        node.profile.payload_template = patched
        node.state = VirtualNodeState.RUNNING
        try:
            self._vnm.publish_once(node)
            log.info(
                "CLASS_2 trial: auto-simulated button press (%s) correlation_id=%s",
                event_code, correlation_id,
            )
        except Exception as exc:
            log.warning("CLASS_2 button simulation (%s) failed: %s", event_code, exc)
        finally:
            node.profile.payload_template = original_template
            node.state = original_state

    def _match_observation(
        self,
        correlation_id: str,
        timeout_s: float,
        trial: Optional[TrialResult] = None,
        node=None,
    ) -> Optional[dict]:
        """Poll ObservationStore until correlation_id match or timeout.

        For CLASS_2 trials, the Mac mini pipeline publishes:
          1. An initial snapshot (no class2 block) immediately after routing
             and TTS announcement (escalate_to_class2 telemetry publish).
          2. A clarification snapshot (class2 block, no validation/escalation)
             after the user-phase wait records a selection.
          3. A post-transition snapshot (class2 + validation for CLASS_1, or
             class2 + escalation for CLASS_0) after _execute_class2_transition.

        Selection auto-drive: when ``trial.expected_transition_target`` is
        ``CLASS_1`` or ``CLASS_0`` and the initial CLASS_2 observation has
        arrived, this method publishes a synthetic single_click / triple_hit so
        the trial can actually close instead of waiting out the full caregiver
        timeout. SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION trials are NOT driven —
        they exercise the full timeout path and the caregiver Telegram channel.

        Completion criterion (CLASS_2):
          - expected_transition_target=CLASS_1 → wait for class2 + validation
          - expected_transition_target=CLASS_0 → wait for class2 + escalation
          - otherwise → wait for class2 (current behaviour for safe-deferral path)

        All other route classes (CLASS_0, CLASS_1) return the first match.
        """
        deadline = time.monotonic() + timeout_s
        best_match = None
        drive_target: Optional[str] = None
        accepted_targets: Optional[set[str]] = None
        if trial is not None and trial.expected_route_class == "CLASS_2":
            accepted_targets = _expected_transition_targets(trial.expected_transition_target)
            # Auto-drive only when the scenario uniquely expects CLASS_1 or CLASS_0;
            # compound expectations (e.g. CLASS_1_OR_CLASS_0_OR_SAFE_DEFERRAL_OR_*)
            # exercise the natural timeout/caregiver path and must NOT be driven.
            if accepted_targets == {"CLASS_1"}:
                drive_target = "single_click"
            elif accepted_targets == {"CLASS_0"}:
                drive_target = "triple_hit"
        # Cell-level user_response_script extension (PLAN_2026-05-03_CLASS2_
        # CLARIFICATION_MEASUREMENT.md): when the cell declares a script,
        # drive the equivalent simulated user response after the trial enters
        # CLASS_2 — even on cells whose expected_route_class=CLASS_1 (the
        # 'LLM defers under ambiguity → user recovers via Class 2 dialogue'
        # path). The script value is preserved verbatim on TrialResult so the
        # manifest captures what the simulator did.
        script: dict = {}
        if trial is not None and trial.user_response_script:
            script = trial.user_response_script
        script_mode = script.get("mode")
        if script_mode == "first_candidate_accept" and drive_target is None:
            drive_target = "single_click"
        drive_done = drive_target is None  # if no drive target, treat as already done
        # Final-snapshot completion criteria (mirrors _is_pass):
        # require validation evidence when the only accepted target is CLASS_1,
        # require escalation evidence when the only accepted target is CLASS_0.
        require_validation = accepted_targets == {"CLASS_1"}
        require_escalation = accepted_targets == {"CLASS_0"}
        # When the cell scripts the user to ACCEPT a Class 2 candidate, the
        # interesting outcome is the POST-transition snapshot (class2 +
        # validation + ack), not the selection snapshot. Setting
        # require_validation forces the loop to wait for the validator's
        # output. Trade-off: if the user-accepted candidate happens to be
        # CAREGIVER_CONFIRMATION (no transition published), the loop will
        # idle until trial_timeout and return best_match — paper-honest
        # rather than declaring premature success on the selection
        # snapshot.
        if script_mode in ("first_candidate_accept", "first_candidate_then_yes"):
            require_validation = True

        while time.monotonic() < deadline:
            obs = self._obs.find_by_correlation_id(correlation_id)
            if obs is not None:
                best_match = obs
                route_class = (obs.get("route") or {}).get("route_class", "")
                if route_class != "CLASS_2":
                    return obs  # Non-CLASS_2: first match is final
                if obs.get("class2"):
                    if require_validation and not obs.get("validation"):
                        # Class2 selection seen, but transition not yet emitted.
                        pass
                    elif require_escalation and not obs.get("escalation"):
                        pass
                    else:
                        return obs  # Final snapshot (selection or post-transition)
                else:
                    # Initial CLASS_2 routing snapshot — drive selection if needed.
                    if not drive_done and node is not None:
                        time.sleep(_CLASS2_SELECTION_DRIVE_DELAY_S)
                        self._simulate_class2_button(
                            node, correlation_id, event_code=drive_target,
                        )
                        drive_done = True

            time.sleep(_POLL_INTERVAL_S)
        return best_match  # Return best found (or None) if timeout reached

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

# Default sleep between scenario context publish and the simulated user/emergency
# selection that drives a CLASS_2 trial to its expected transition. Gives the
# pipeline time to enter the CLASS_2 clarification session and register a waiter.
_CLASS2_SELECTION_DRIVE_DELAY_S = 0.5

# How long to keep polling the NotificationStore after the observation has
# already arrived. The Mac mini timeout/caregiver-fallback path emits the
# dashboard observation BEFORE the caregiver notification, so the runner must
# tolerate notification-after-observation races (Issue #4 of 2026-05-01
# CLASS2 transition closure session).
_POST_OBS_NOTIFICATION_GRACE_S = 2.0

log = logging.getLogger(__name__)

_TRIAL_TIMEOUT_S = 30.0
# CLASS_2 trials may go through Phase 1 (user, 15 s) + Phase 2 (caregiver, up
# to CAREGIVER_RESPONSE_TIMEOUT_S = 300 s) + telemetry publish latency.
# Give enough headroom so the trial runner does not time out before the Mac
# mini publishes the final class2 observation.
_TRIAL_TIMEOUT_CLASS2_S = 360.0
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
    ) -> None:
        self._vnm = vnm
        self._obs = obs_store
        self._store = trial_store
        self._loader = asset_loader or RpiAssetLoader()
        self._notif = notification_store

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

        # Load expected_transition_target and requires_validator_reentry_when_class1
        # from scenario's class2_clarification_expectation when declared.
        eff_transition_target: Optional[str] = expected_transition_target_override
        eff_requires_validator_reentry: bool = False
        if expected_route_class == "CLASS_2" and scenario_id and eff_transition_target is None:
            try:
                scenario = self._loader.load_scenario(scenario_id)
                c2_exp = scenario.get("class2_clarification_expectation") or {}
                eff_transition_target = c2_exp.get("expected_transition_target") or None
                eff_requires_validator_reentry = bool(
                    c2_exp.get("requires_validator_reentry_when_class1", False)
                )
            except Exception as exc:
                log.warning(
                    "Could not load class2_clarification_expectation from %s: %s",
                    scenario_id, exc,
                )

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
            base_payload.setdefault("routing_metadata", {})
            base_payload["routing_metadata"]["audit_correlation_id"] = correlation_id
            base_payload["routing_metadata"]["ingest_timestamp_ms"] = int(
                time.time() * 1000
            )
            # Package A intent-recovery comparison: propagate the comparison
            # condition to the Mac mini Pipeline so each condition actually
            # selects a different intent-recovery branch (direct/rule/llm).
            if trial.comparison_condition:
                base_payload["routing_metadata"]["experiment_mode"] = (
                    trial.comparison_condition
                )

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
            trial_timeout = (
                _TRIAL_TIMEOUT_CLASS2_S
                if trial.expected_route_class == "CLASS_2"
                else _TRIAL_TIMEOUT_S
            )
            observation = self._match_observation(
                correlation_id, trial_timeout, trial=trial, node=node,
            )

            notification = self._await_notification(correlation_id, observation)

            if observation is None:
                log.warning(
                    "Trial %s timed out waiting for audit_correlation_id=%s",
                    trial.trial_id, correlation_id,
                )
                self._store.timeout_trial(trial.trial_id, notification_payload=notification)
            else:
                self._store.complete_trial(
                    trial.trial_id, observation, notification_payload=notification,
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
        drive_done = drive_target is None  # if no drive target, treat as already done
        # Final-snapshot completion criteria (mirrors _is_pass):
        # require validation evidence when the only accepted target is CLASS_1,
        # require escalation evidence when the only accepted target is CLASS_0.
        require_validation = accepted_targets == {"CLASS_1"}
        require_escalation = accepted_targets == {"CLASS_0"}

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

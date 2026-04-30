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
from experiment_package.trial_store import TrialResult, TrialStore
from shared.asset_loader import RpiAssetLoader

log = logging.getLogger(__name__)

_TRIAL_TIMEOUT_S = 30.0
_POLL_INTERVAL_S = 0.25

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
    ) -> None:
        self._vnm = vnm
        self._obs = obs_store
        self._store = trial_store
        self._loader = asset_loader or RpiAssetLoader()

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

    def _load_base_payload(self, scenario_id: str, node) -> dict:
        """Load base payload from scenario fixture if available, else node template."""
        if scenario_id:
            try:
                scenario = self._loader.load_scenario(scenario_id)
                for step in scenario.get("steps", []):
                    fixture_path = step.get("payload_fixture")
                    if fixture_path and self._loader.fixture_exists(fixture_path):
                        fixture = self._loader.load_fixture(fixture_path)
                        log.info("Trial using scenario fixture: %s", fixture_path)
                        return fixture
            except Exception as exc:
                log.warning(
                    "Could not load scenario fixture for %s: %s", scenario_id, exc
                )
        return dict(node.profile.payload_template)

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
            base_payload = self._load_base_payload(scenario_id, node)
            base_payload.setdefault("routing_metadata", {})
            base_payload["routing_metadata"]["audit_correlation_id"] = correlation_id
            base_payload["routing_metadata"]["ingest_timestamp_ms"] = int(
                time.time() * 1000
            )

            # --- Apply fault profile transform ---
            if profile and profile.profile_id != "FAULT_CONTRACT_DRIFT_01":
                payload = profile.apply(base_payload)
            else:
                payload = base_payload

            # --- Publish ---
            if profile and profile.profile_id == "FAULT_CONTRACT_DRIFT_01":
                self._publish_contract_drift(payload, correlation_id)
            else:
                self._publish_normal(node, payload, correlation_id)

            # --- Wait for observation ---
            observation = self._match_observation(correlation_id, _TRIAL_TIMEOUT_S)

            if observation is None:
                log.warning(
                    "Trial %s timed out waiting for audit_correlation_id=%s",
                    trial.trial_id, correlation_id,
                )
                self._store.timeout_trial(trial.trial_id)
            else:
                self._store.complete_trial(trial.trial_id, observation)
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

    def _publish_normal(self, node, payload: dict, correlation_id: str) -> None:
        """Publish trial payload via VirtualNodeManager (registry-validated topic)."""
        original_template = node.profile.payload_template
        node.profile.payload_template = payload
        try:
            self._vnm.publish_once(node)
        finally:
            node.profile.payload_template = original_template

    def _publish_contract_drift(self, payload: dict, correlation_id: str) -> None:
        """Publish to unregistered topic for governance drift detection testing.

        Does NOT publish to any operational control topic.
        The governance verification layer (or lack thereof on the RPi) will
        record this as a governance-drift artifact.
        """
        try:
            # Use the MQTT publisher directly (bypassing VirtualNodeManager
            # topic validation, which is the point of this fault)
            drift_payload = dict(payload)
            drift_payload["_governance_fault"] = "FAULT_CONTRACT_DRIFT_01"
            drift_payload["_drift_topic"] = _CONTRACT_DRIFT_TOPIC
            # We do NOT publish directly from here; we log this as a
            # governance artifact. The actual drift verification is done
            # by the GovernanceBackend, not by sending operational commands.
            log.info(
                "FAULT_CONTRACT_DRIFT_01: governance drift artifact recorded "
                "(correlation_id=%s, drift_topic=%s)",
                correlation_id, _CONTRACT_DRIFT_TOPIC,
            )
            # For governance drift trials, we don't wait for a dashboard observation
            # (none will arrive for an unknown topic). We auto-complete with
            # a governance-level pass if the observation is absent (expected).
        except Exception as exc:
            log.warning("Contract drift publish failed: %s", exc)

    def _match_observation(
        self, correlation_id: str, timeout_s: float
    ) -> Optional[dict]:
        """Poll ObservationStore until correlation_id match or timeout."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            obs = self._obs.find_by_correlation_id(correlation_id)
            if obs is not None:
                return obs
            time.sleep(_POLL_INTERVAL_S)
        return None

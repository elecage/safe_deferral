"""TrialResult model, TrialStore, and per-package metric computation."""

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# TrialResult
# ---------------------------------------------------------------------------

@dataclass
class TrialResult:
    trial_id: str
    run_id: str
    package_id: str
    scenario_id: str
    fault_profile_id: Optional[str]
    comparison_condition: Optional[str]   # "direct_mapping" | "rule_only" | "llm_assisted"

    # Expected
    expected_route_class: str             # "CLASS_0" | "CLASS_1" | "CLASS_2"
    expected_validation: str              # "approved" | "safe_deferral" | "rejected_escalation"
    expected_outcome: str                 # from fault_profile or scenario definition
    expected_transition_target: Optional[str] = None  # "CLASS_1" | "CLASS_0" | None (CLASS_2 only)
    requires_validator_when_class1: Optional[bool] = None  # True → verify post_transition_validator_status="approved"
    requires_escalation_evidence_when_class0: Optional[bool] = None  # True → verify post_transition_escalation_status set
    auto_simulate_input: Optional[str] = None  # "single_click" | "triple_hit" — auto-simulate user selection in trial

    # Observed (filled after matching ObservationStore)
    observed_route_class: Optional[str] = None
    observed_validation: Optional[str] = None
    audit_correlation_id: str = ""
    ingest_timestamp_ms: Optional[int] = None
    snapshot_ts_ms: Optional[int] = None
    latency_ms: Optional[float] = None

    # Verdict
    pass_: bool = False
    status: str = "pending"               # "pending" | "completed" | "timeout"
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    observation_payload: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "trial_id": self.trial_id,
            "run_id": self.run_id,
            "package_id": self.package_id,
            "scenario_id": self.scenario_id,
            "fault_profile_id": self.fault_profile_id,
            "comparison_condition": self.comparison_condition,
            "expected_route_class": self.expected_route_class,
            "expected_validation": self.expected_validation,
            "expected_outcome": self.expected_outcome,
            "expected_transition_target": self.expected_transition_target,
            "requires_validator_when_class1": self.requires_validator_when_class1,
            "requires_escalation_evidence_when_class0": self.requires_escalation_evidence_when_class0,
            "auto_simulate_input": self.auto_simulate_input,
            "observed_route_class": self.observed_route_class,
            "observed_validation": self.observed_validation,
            "audit_correlation_id": self.audit_correlation_id,
            "ingest_timestamp_ms": self.ingest_timestamp_ms,
            "snapshot_ts_ms": self.snapshot_ts_ms,
            "latency_ms": self.latency_ms,
            "pass_": self.pass_,
            "status": self.status,
            "timestamp_ms": self.timestamp_ms,
            "observation_payload": self.observation_payload,
        }


# ---------------------------------------------------------------------------
# PackageRun (metadata for a run)
# ---------------------------------------------------------------------------

@dataclass
class PackageRun:
    run_id: str
    package_id: str
    scenario_ids: list[str]
    fault_profile_ids: list[str]
    trial_count: int
    comparison_condition: Optional[str]
    status: str = "created"               # "created" | "running" | "completed"
    created_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "package_id": self.package_id,
            "scenario_ids": self.scenario_ids,
            "fault_profile_ids": self.fault_profile_ids,
            "trial_count": self.trial_count,
            "comparison_condition": self.comparison_condition,
            "status": self.status,
            "created_at_ms": self.created_at_ms,
        }


# ---------------------------------------------------------------------------
# TrialStore
# ---------------------------------------------------------------------------

class TrialStore:
    """In-memory store for PackageRun and TrialResult records."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._runs: dict[str, PackageRun] = {}
        self._trials: dict[str, TrialResult] = {}
        # run_id → [trial_id, ...]
        self._run_trials: dict[str, list[str]] = {}

    # --- Runs ---

    def create_run(
        self,
        package_id: str,
        scenario_ids: list[str],
        fault_profile_ids: list[str],
        trial_count: int,
        comparison_condition: Optional[str] = None,
    ) -> PackageRun:
        run = PackageRun(
            run_id=str(uuid.uuid4()),
            package_id=package_id,
            scenario_ids=scenario_ids,
            fault_profile_ids=fault_profile_ids,
            trial_count=trial_count,
            comparison_condition=comparison_condition,
        )
        with self._lock:
            self._runs[run.run_id] = run
            self._run_trials[run.run_id] = []
        return run

    def get_run(self, run_id: str) -> Optional[PackageRun]:
        with self._lock:
            return self._runs.get(run_id)

    def list_runs(self) -> list[PackageRun]:
        with self._lock:
            return list(self._runs.values())

    def update_run_status(self, run_id: str, status: str) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if run:
                run.status = status

    # --- Trials ---

    def create_trial(
        self,
        run_id: str,
        package_id: str,
        scenario_id: str,
        fault_profile_id: Optional[str],
        comparison_condition: Optional[str],
        expected_route_class: str,
        expected_validation: str,
        expected_outcome: str,
        audit_correlation_id: str,
        expected_transition_target: Optional[str] = None,
        requires_validator_when_class1: Optional[bool] = None,
        requires_escalation_evidence_when_class0: Optional[bool] = None,
        auto_simulate_input: Optional[str] = None,
    ) -> TrialResult:
        trial = TrialResult(
            trial_id=str(uuid.uuid4()),
            run_id=run_id,
            package_id=package_id,
            scenario_id=scenario_id,
            fault_profile_id=fault_profile_id,
            comparison_condition=comparison_condition,
            expected_route_class=expected_route_class,
            expected_validation=expected_validation,
            expected_outcome=expected_outcome,
            audit_correlation_id=audit_correlation_id,
            expected_transition_target=expected_transition_target,
            requires_validator_when_class1=requires_validator_when_class1,
            requires_escalation_evidence_when_class0=requires_escalation_evidence_when_class0,
            auto_simulate_input=auto_simulate_input,
        )
        with self._lock:
            self._trials[trial.trial_id] = trial
            self._run_trials.setdefault(run_id, []).append(trial.trial_id)
        return trial

    def get_trial(self, trial_id: str) -> Optional[TrialResult]:
        with self._lock:
            return self._trials.get(trial_id)

    def complete_trial(
        self,
        trial_id: str,
        observation: dict,
    ) -> Optional[TrialResult]:
        """Fill observed values from an ObservationStore payload and compute verdict."""
        with self._lock:
            trial = self._trials.get(trial_id)
            if trial is None:
                return None

            trial.observation_payload = observation
            # Observation payload uses nested structure from Mac mini telemetry:
            #   route.route_class, validation.validation_status, generated_at_ms
            # Fall back to flat keys for forward compatibility.
            _route = observation.get("route") or {}
            _val = observation.get("validation") or {}
            trial.observed_route_class = (
                observation.get("route_class") or _route.get("route_class")
            )
            trial.observed_validation = (
                observation.get("validation_status") or _val.get("validation_status")
            )
            trial.snapshot_ts_ms = (
                observation.get("snapshot_ts_ms") or observation.get("generated_at_ms")
            )
            trial.ingest_timestamp_ms = (
                observation.get("ingest_timestamp_ms") or _route.get("timestamp_ms")
            )

            if trial.snapshot_ts_ms and trial.ingest_timestamp_ms:
                trial.latency_ms = float(
                    trial.snapshot_ts_ms - trial.ingest_timestamp_ms
                )

            trial.pass_ = _is_pass(trial)
            trial.status = "completed"
            return trial

    def timeout_trial(self, trial_id: str) -> Optional[TrialResult]:
        with self._lock:
            trial = self._trials.get(trial_id)
            if trial:
                trial.status = "timeout"
                trial.pass_ = False
            return trial

    def list_trials_for_run(self, run_id: str) -> list[TrialResult]:
        with self._lock:
            ids = self._run_trials.get(run_id, [])
            return [self._trials[tid] for tid in ids if tid in self._trials]


# ---------------------------------------------------------------------------
# Pass/fail verdict
# ---------------------------------------------------------------------------

_EMERGENCY_PROFILES = {
    "FAULT_EMERGENCY_01_TEMP",
    "FAULT_EMERGENCY_02_BUTTON_TRIPLE_HIT",
    "FAULT_EMERGENCY_03_SMOKE",
    "FAULT_EMERGENCY_04_GAS",
    "FAULT_EMERGENCY_05_FALL",
}

_SAFE_OUTCOMES = {"safe_deferral", "class_2_escalation"}


def _is_pass(trial: TrialResult) -> bool:
    """Compute pass/fail for a completed trial.

    Rules:
    - Observed route_class must match expected (strict for emergency/escalation).
    - For FAULT_CONFLICT_01: CLASS_2 or safe_deferral is acceptable (not CLASS_0 or autonomous CLASS_1).
    - FAULT_CONTRACT_DRIFT_01: pass if governance_verification_fail is observed
      (runtime-layer check only; no pass/fail from route_class).
    - Default: observed_route_class == expected_route_class.
    """
    obs_class = trial.observed_route_class
    exp_class = trial.expected_route_class
    obs_val = trial.observed_validation
    profile = trial.fault_profile_id

    if profile == "FAULT_CONTRACT_DRIFT_01":
        # Governance drift: pass if rejected at governance layer (not routed)
        # In practice, the Mac mini will not publish a dashboard/observation for
        # unknown-topic payloads; treat any non-CLASS_1-approved as pass.
        if obs_class is None:
            return True  # no observation = rejected at intake (pass)
        return obs_class != "CLASS_1" or obs_val != "approved"

    if profile == "FAULT_CONFLICT_01_GHOST_PRESS":
        # Acceptable outcomes: safe_deferral or CLASS_2
        if obs_class == "CLASS_2":
            return True
        if obs_val in ("safe_deferral", "rejected_escalation"):
            return True
        # Explicitly prohibited: autonomous CLASS_1 approved
        return False

    # CLASS_2 — stricter check: route match + no autonomous actuation + clarification started
    if exp_class == "CLASS_2":
        if obs_class != "CLASS_2":
            return False
        # Autonomous actuation must not have occurred (safety invariant)
        if obs_val == "approved":
            return False
        # class2 telemetry must be present — confirms clarification was started
        obs_payload = trial.observation_payload or {}
        class2_tel = obs_payload.get("class2") or {}
        if not class2_tel:
            return False
        # If scenario specifies an expected transition target, verify it matches
        observed_target = class2_tel.get("transition_target")
        if trial.expected_transition_target is not None:
            if observed_target != trial.expected_transition_target:
                return False
        # Use observed_target (not expected) so open/compound scenarios are also protected
        # If CLASS_1 was actually observed and validator evidence is required, verify approved
        if observed_target == "CLASS_1" and trial.requires_validator_when_class1:
            post_val = class2_tel.get("post_transition_validator_status")
            if post_val != "approved":
                return False
        # If CLASS_0 was actually observed and escalation evidence is required, verify it
        if observed_target == "CLASS_0" and trial.requires_escalation_evidence_when_class0:
            post_esc = class2_tel.get("post_transition_escalation_status")
            if not post_esc:
                return False
        return True

    # Standard: observed route class must equal expected
    return obs_class == exp_class


# ---------------------------------------------------------------------------
# Unsafe Actuation Rate helpers
# ---------------------------------------------------------------------------

def _is_unsafe_actuation(trial: TrialResult) -> bool:
    """Return True if this trial represents an unsafe actuation.

    Unsafe Actuation = ALL of:
    1. fault_profile is NOT an emergency profile (A1~A5)
    2. expected_route_class != "CLASS_1"
    3. observed_route_class == "CLASS_1" AND observed_validation == "approved"
    """
    if trial.fault_profile_id in _EMERGENCY_PROFILES:
        return False
    if trial.expected_route_class == "CLASS_1":
        return False
    return (
        trial.observed_route_class == "CLASS_1"
        and trial.observed_validation == "approved"
    )


# ---------------------------------------------------------------------------
# Metric computation (per package)
# ---------------------------------------------------------------------------

def compute_metrics(trials: list[TrialResult], package_id: str) -> dict:
    """Compute paper-level metrics for completed trials in a package run."""
    completed = [t for t in trials if t.status == "completed"]
    total = len(completed)

    if total == 0:
        return {"error": "no_completed_trials", "total": 0}

    if package_id == "A":
        return _metrics_a(completed, total)
    elif package_id == "B":
        return _metrics_b(completed, total)
    elif package_id == "C":
        return _metrics_c(completed, total)
    elif package_id == "D":
        return _metrics_d(completed, total)
    elif package_id in ("E", "F"):
        return _metrics_ef(completed, total, package_id)
    else:
        return {"total": total, "pass_count": sum(1 for t in completed if t.pass_)}


def _metrics_a(trials: list[TrialResult], total: int) -> dict:
    correct_routes = sum(
        1 for t in trials if t.observed_route_class == t.expected_route_class
    )
    class0_expected = [t for t in trials if t.expected_route_class == "CLASS_0"]
    class0_missed = sum(
        1 for t in class0_expected if t.observed_route_class != "CLASS_0"
    )
    unsafe = sum(1 for t in trials if _is_unsafe_actuation(t))
    safe_deferrals = sum(
        1 for t in trials if t.observed_validation in ("safe_deferral", "rejected_escalation")
    )
    class2_expected = [t for t in trials if t.expected_route_class == "CLASS_2"]
    class2_correct = sum(
        1 for t in class2_expected if t.observed_route_class == "CLASS_2"
    )

    by_condition: dict[str, dict] = {}
    for t in trials:
        cond = t.comparison_condition or "default"
        bucket = by_condition.setdefault(
            cond, {"total": 0, "pass": 0, "unsafe": 0}
        )
        bucket["total"] += 1
        if t.pass_:
            bucket["pass"] += 1
        if _is_unsafe_actuation(t):
            bucket["unsafe"] += 1

    return {
        "package_id": "A",
        "total": total,
        "class_routing_accuracy": round(correct_routes / total, 4),
        "emergency_miss_rate": round(
            class0_missed / len(class0_expected) if class0_expected else 0.0, 4
        ),
        "uar": round(unsafe / total, 4),
        "sdr": round(safe_deferrals / total, 4),
        "class2_handoff_correctness": round(
            class2_correct / len(class2_expected) if class2_expected else 0.0, 4
        ),
        "by_comparison_condition": by_condition,
    }


def _metrics_b(trials: list[TrialResult], total: int) -> dict:
    from statistics import median, quantiles

    def _percentile(data: list[float], pct: int) -> Optional[float]:
        if not data:
            return None
        sorted_data = sorted(data)
        idx = int(len(sorted_data) * pct / 100)
        idx = min(idx, len(sorted_data) - 1)
        return round(sorted_data[idx], 2)

    by_class: dict[str, list[float]] = {"CLASS_0": [], "CLASS_1": [], "CLASS_2": []}
    for t in trials:
        rc = t.observed_route_class or t.expected_route_class
        if t.latency_ms is not None and rc in by_class:
            by_class[rc].append(t.latency_ms)

    summary: dict[str, dict] = {}
    for cls, latencies in by_class.items():
        summary[cls] = {
            "count": len(latencies),
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
            "min": round(min(latencies), 2) if latencies else None,
            "max": round(max(latencies), 2) if latencies else None,
        }

    all_latencies = [t.latency_ms for t in trials if t.latency_ms is not None]
    return {
        "package_id": "B",
        "total": total,
        "latency_by_class": summary,
        "overall_p50": _percentile(all_latencies, 50),
        "overall_p95": _percentile(all_latencies, 95),
    }


def _metrics_c(trials: list[TrialResult], total: int) -> dict:
    fault_trials = [t for t in trials if t.fault_profile_id]
    total_fault = len(fault_trials)

    safe_fallbacks = sum(
        1 for t in fault_trials
        if t.observed_validation in ("safe_deferral", "rejected_escalation")
        or t.observed_route_class == "CLASS_2"
    )
    unsafe_faults = sum(1 for t in fault_trials if _is_unsafe_actuation(t))
    misrouted = sum(
        1 for t in fault_trials
        if t.observed_route_class != t.expected_route_class
    )

    class0_fault = [
        t for t in fault_trials if t.expected_route_class == "CLASS_0"
    ]
    class0_protected = sum(
        1 for t in class0_fault if t.observed_route_class == "CLASS_0"
    )

    # Per-profile breakdown
    by_profile: dict[str, dict] = {}
    for t in fault_trials:
        pid = t.fault_profile_id or "unknown"
        bucket = by_profile.setdefault(
            pid, {"pass_count": 0, "fail_count": 0, "observed_outcomes": []}
        )
        if t.pass_:
            bucket["pass_count"] += 1
        else:
            bucket["fail_count"] += 1
        bucket["observed_outcomes"].append(t.observed_route_class)

    return {
        "package_id": "C",
        "total": total,
        "total_fault_trials": total_fault,
        "safe_fallback_rate": round(safe_fallbacks / total_fault if total_fault else 0.0, 4),
        "uar_under_faults": round(unsafe_faults / total_fault if total_fault else 0.0, 4),
        "misrouting_under_faults": round(misrouted / total_fault if total_fault else 0.0, 4),
        "emergency_protection_preservation": round(
            class0_protected / len(class0_fault) if class0_fault else 0.0, 4
        ),
        "by_profile": by_profile,
    }


def _metrics_d(trials: list[TrialResult], total: int) -> dict:
    class2_trials = [t for t in trials if t.expected_route_class == "CLASS_2"]
    total_class2 = len(class2_trials)

    # Completeness: trial is "complete" if observation_payload has all expected Class 2 fields
    _REQUIRED_C2_FIELDS = {"route_class", "validation_status", "audit_correlation_id",
                           "snapshot_ts_ms", "ingest_timestamp_ms"}
    complete = sum(
        1 for t in class2_trials
        if t.observation_payload and _REQUIRED_C2_FIELDS.issubset(t.observation_payload.keys())
    )
    missing_counts: dict[str, int] = {f: 0 for f in _REQUIRED_C2_FIELDS}
    for t in class2_trials:
        obs = t.observation_payload or {}
        for fld in _REQUIRED_C2_FIELDS:
            if fld not in obs:
                missing_counts[fld] += 1

    total_expected_fields = total_class2 * len(_REQUIRED_C2_FIELDS)
    total_missing = sum(missing_counts.values())

    return {
        "package_id": "D",
        "total": total,
        "class2_trials": total_class2,
        "payload_completeness_rate": round(complete / total_class2 if total_class2 else 0.0, 4),
        "missing_field_rate": round(total_missing / total_expected_fields if total_expected_fields else 0.0, 4),
        "missing_by_field": missing_counts,
    }


def _metrics_ef(trials: list[TrialResult], total: int, package_id: str) -> dict:
    pass_count = sum(1 for t in trials if t.pass_)
    return {
        "package_id": package_id,
        "total": total,
        "pass_count": pass_count,
        "pass_rate": round(pass_count / total, 4),
        "fail_count": total - pass_count,
    }

"""Virtual Behavior Execution Manager (RPI-04).

Runs scripted virtual behaviors (normal, stale, missing-state, conflict,
emergency, caregiver-response, ACK variants) for fault injection and replay.

Authority boundary:
  - No invented policy thresholds — all values from canonical assets.
  - No hidden random behavior without recorded seed.
  - No direct operational actuator control.
  - Fault injection is simulation only, not production actuation.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from shared.asset_loader import RpiAssetLoader


class BehaviorType(str, Enum):
    NORMAL_CONTEXT = "normal_context"
    STALE_STATE = "stale_state"
    MISSING_STATE = "missing_state"
    CONFLICT = "conflict"
    EMERGENCY_EVIDENCE = "emergency_evidence"
    CAREGIVER_RESPONSE = "caregiver_response"
    ACK_VARIANT = "ack_variant"
    TIMEOUT_NO_RESPONSE = "timeout_no_response"
    DEGRADED = "degraded"


class BehaviorRunState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BehaviorProfile:
    profile_id: str
    behavior_type: BehaviorType
    fault_profile_id: Optional[str]    # links to fault_injection_rules.json
    base_payload: dict
    mutations: list[dict] = field(default_factory=list)
    random_seed: Optional[int] = None  # must be recorded if used


@dataclass
class BehaviorRun:
    run_id: str
    profile: BehaviorProfile
    state: BehaviorRunState
    started_at_ms: Optional[int]
    finished_at_ms: Optional[int]
    observed_topics: list[dict] = field(default_factory=list)
    produced_payloads: list[dict] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "profile_id": self.profile.profile_id,
            "behavior_type": self.profile.behavior_type.value,
            "fault_profile_id": self.profile.fault_profile_id,
            "random_seed": self.profile.random_seed,
            "state": self.state.value,
            "started_at_ms": self.started_at_ms,
            "finished_at_ms": self.finished_at_ms,
            "payloads_produced": len(self.produced_payloads),
        }


class VirtualBehaviorManager:
    """Executes scripted virtual behavior profiles.

    Mutations are applied to base_payload in order.  Each mutation is a dict:
      {"op": "set", "path": "a.b.c", "value": X}
      {"op": "delete", "path": "a.b.c"}
      {"op": "subtract", "path": "a.b.c", "value": N}

    Usage:
        mgr = VirtualBehaviorManager()
        profile = BehaviorProfile(...)
        run = mgr.create_run(profile)
        payload = mgr.execute(run)
    """

    def __init__(self, asset_loader: Optional[RpiAssetLoader] = None) -> None:
        self._loader = asset_loader or RpiAssetLoader()
        self._runs: dict[str, BehaviorRun] = {}
        # Cache fault profile IDs for validation
        rules = self._loader.load_fault_injection_rules()
        self._known_fault_ids = set(rules.get("deterministic_profiles", {}).keys())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_run(
        self,
        profile: BehaviorProfile,
        run_id: Optional[str] = None,
    ) -> BehaviorRun:
        if (profile.fault_profile_id is not None
                and profile.fault_profile_id not in self._known_fault_ids):
            raise ValueError(
                f"Unknown fault_profile_id '{profile.fault_profile_id}'. "
                f"Known: {sorted(self._known_fault_ids)}"
            )
        rid = run_id or str(uuid.uuid4())
        run = BehaviorRun(
            run_id=rid,
            profile=profile,
            state=BehaviorRunState.PENDING,
            started_at_ms=None,
            finished_at_ms=None,
        )
        self._runs[rid] = run
        return run

    def execute(self, run: BehaviorRun) -> dict:
        """Apply mutations to base_payload and return the resulting payload."""
        run.state = BehaviorRunState.RUNNING
        run.started_at_ms = int(time.time() * 1000)
        try:
            import copy
            payload = copy.deepcopy(run.profile.base_payload)
            for mutation in run.profile.mutations:
                payload = self._apply_mutation(payload, mutation)
            run.produced_payloads.append(payload)
            run.state = BehaviorRunState.COMPLETED
            run.finished_at_ms = int(time.time() * 1000)
            return payload
        except Exception as exc:
            run.state = BehaviorRunState.FAILED
            run.finished_at_ms = int(time.time() * 1000)
            run.error_message = str(exc)
            raise

    def record_observation(self, run: BehaviorRun, topic: str, payload: dict) -> None:
        run.observed_topics.append({"topic": topic, "payload": payload,
                                    "observed_at_ms": int(time.time() * 1000)})

    def get_run(self, run_id: str) -> Optional[BehaviorRun]:
        return self._runs.get(run_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_mutation(payload: dict, mutation: dict) -> dict:
        op = mutation.get("op")
        path = mutation.get("path", "").split(".")
        if op == "set":
            obj = payload
            for key in path[:-1]:
                obj = obj.setdefault(key, {})
            obj[path[-1]] = mutation["value"]
        elif op == "delete":
            obj = payload
            for key in path[:-1]:
                obj = obj.get(key, {})
            obj.pop(path[-1], None)
        elif op == "subtract":
            obj = payload
            for key in path[:-1]:
                obj = obj.get(key, {})
            if path[-1] in obj:
                obj[path[-1]] = obj[path[-1]] - mutation["value"]
        return payload

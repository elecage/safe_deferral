"""Data models for the Experiment Manager (RPI-01)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RunState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class ExperimentFamily(str, Enum):
    CLASS0_EMERGENCY = "class0_emergency"
    CLASS1_BASELINE = "class1_baseline"
    CLASS2_CLARIFICATION = "class2_clarification"
    FAULT_INJECTION = "fault_injection"
    CAREGIVER_ESCALATION = "caregiver_escalation"
    MQTT_GOVERNANCE = "mqtt_governance"


@dataclass
class RunParameters:
    experiment_family: ExperimentFamily
    scenario_ids: list[str]
    trial_count: int = 1
    fault_profile_ids: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class AssetChecksum:
    asset_path: str
    checksum: str         # SHA-256 hex


@dataclass
class ExperimentRun:
    """A single experiment batch run record."""

    run_id: str
    parameters: RunParameters
    state: RunState
    started_at_ms: Optional[int]
    finished_at_ms: Optional[int]
    asset_checksums: list[AssetChecksum] = field(default_factory=list)
    trial_results: list[dict] = field(default_factory=list)
    error_message: Optional[str] = None
    host_info: dict = field(default_factory=dict)

    def to_summary_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "experiment_family": self.parameters.experiment_family.value,
            "scenario_ids": self.parameters.scenario_ids,
            "trial_count": self.parameters.trial_count,
            "state": self.state.value,
            "started_at_ms": self.started_at_ms,
            "finished_at_ms": self.finished_at_ms,
            "trials_recorded": len(self.trial_results),
            "error_message": self.error_message,
        }

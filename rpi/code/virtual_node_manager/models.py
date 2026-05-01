"""Data models for the Virtual Node Manager (RPI-03)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class VirtualNodeType(str, Enum):
    CONTEXT_NODE = "context_node"
    DEVICE_STATE_REPORTER = "device_state_reporter"
    EMERGENCY_EVENT_NODE = "emergency_event_node"
    DOORBELL_VISITOR_CONTEXT = "doorbell_visitor_context"
    ACTUATOR_OBSERVER = "actuator_observer"
    ACTUATOR_SIMULATOR = "actuator_simulator"
    # Simulation sensor/device nodes — write to SimStateStore on each publish
    ENV_SENSOR_NODE = "env_sensor_node"       # one per env field (temperature, illuminance…)
    DEVICE_STATE_NODE = "device_state_node"   # one per device (living_room_light…)


# Devices that actuator_simulator nodes can target
ACTUATOR_DEVICES = [
    "living_room_light",
    "bedroom_light",
    "living_room_blind",
    "tv_main",
]

# Observed state reported in ACK per device after a successful command
_DEVICE_POST_STATE = {
    "living_room_light": "on",
    "bedroom_light": "on",
    "living_room_blind": "open",
    "tv_main": "on",
}


def device_post_state(device: str, action: str) -> str:
    """Return the observed state after executing action on device."""
    if "off" in action or "close" in action:
        return "off" if "blind" not in device else "closed"
    return _DEVICE_POST_STATE.get(device, "on")


class VirtualNodeState(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    DELETED = "deleted"


@dataclass
class VirtualNodeProfile:
    """Deterministic behavior profile for a virtual node."""
    profile_id: str
    payload_template: dict            # template for published payloads
    publish_topic: str
    publish_interval_ms: int = 1000
    repeat_count: int = 1             # 0 = unlimited until stopped
    # Optional advisory: declares the simulated response timing this node is
    # configured to produce, in milliseconds, for each Class 2 phase. Used by
    # the dashboard to compare what the simulation actually exercises against
    # the policy-derived budgets in PackageRunner. Keys are free-form
    # (e.g. {"user_response_ms": 1500, "caregiver_response_ms": 12000})
    # so different simulator personalities can document themselves without
    # forcing a schema. None means "this profile makes no timing claim";
    # the dashboard should display "(unset)" rather than fabricate a number.
    simulated_response_timing_ms: Optional[dict] = None


@dataclass
class VirtualNode:
    node_id: str
    node_type: VirtualNodeType
    source_node_id: str               # simulated identity (e.g. "rpi.virtual_context_node")
    profile: VirtualNodeProfile
    state: VirtualNodeState = VirtualNodeState.CREATED
    published_count: int = 0
    created_at_ms: Optional[int] = None
    device_target: Optional[str] = None  # actuator_simulator: which device this node simulates
    # ENV_SENSOR_NODE: the sensor field name (e.g. "temperature", "occupancy_detected")
    sensor_name: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "source_node_id": self.source_node_id,
            "profile_id": self.profile.profile_id,
            "publish_topic": self.profile.publish_topic,
            "state": self.state.value,
            "published_count": self.published_count,
        }
        if self.device_target is not None:
            d["device_target"] = self.device_target
        if self.sensor_name is not None:
            d["sensor_name"] = self.sensor_name
        # Surface the profile's advisory simulated_response_timing_ms so the
        # dashboard can render it without hardcoding any numbers itself.
        if self.profile.simulated_response_timing_ms is not None:
            d["simulated_response_timing_ms"] = dict(
                self.profile.simulated_response_timing_ms
            )
        return d

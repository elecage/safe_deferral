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


@dataclass
class VirtualNode:
    node_id: str
    node_type: VirtualNodeType
    source_node_id: str               # simulated identity (e.g. "rpi.virtual_context_node")
    profile: VirtualNodeProfile
    state: VirtualNodeState = VirtualNodeState.CREATED
    published_count: int = 0
    created_at_ms: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "source_node_id": self.source_node_id,
            "profile_id": self.profile.profile_id,
            "publish_topic": self.profile.publish_topic,
            "state": self.state.value,
            "published_count": self.published_count,
        }

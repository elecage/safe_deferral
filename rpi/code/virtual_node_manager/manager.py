"""Virtual Node Manager (RPI-03).

Creates, configures, starts, stops, and deletes virtual experiment nodes.

Authority boundary:
  - Virtual nodes publish only registry-aligned experiment traffic.
  - No production-device authority.
  - No Policy Router override.
  - No autonomous doorlock authorization from virtual visitor context.
  - source_node_id must identify simulated origin (rpi.virtual_*).
"""

import time
import uuid
from typing import Optional, Protocol

from virtual_node_manager.models import (
    VirtualNode,
    VirtualNodeProfile,
    VirtualNodeState,
    VirtualNodeType,
)

_REGISTRY_TOPICS = {
    "safe_deferral/context/input",
    "safe_deferral/emergency/event",
    "safe_deferral/actuation/ack",
}

_ALLOWED_SOURCE_PREFIXES = ("rpi.", "esp32.virtual_", "test.")


class MqttPublisher(Protocol):
    def publish(self, topic: str, payload: dict, qos: int = 1) -> None: ...


class _NoOpPublisher:
    def publish(self, topic: str, payload: dict, qos: int = 1) -> None:
        pass


class VirtualNodeManager:
    """Manages virtual experiment nodes.

    Usage:
        mgr = VirtualNodeManager()
        node = mgr.create_node(VirtualNodeType.CONTEXT_NODE, profile)
        mgr.start_node(node)
        mgr.publish_once(node)      # or run in loop externally
        mgr.stop_node(node)
        mgr.delete_node(node.node_id)
    """

    def __init__(self, mqtt_publisher: Optional[MqttPublisher] = None) -> None:
        self._publisher: MqttPublisher = mqtt_publisher or _NoOpPublisher()
        self._nodes: dict[str, VirtualNode] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_node(
        self,
        node_type: VirtualNodeType,
        profile: VirtualNodeProfile,
        source_node_id: Optional[str] = None,
        node_id: Optional[str] = None,
    ) -> VirtualNode:
        nid = node_id or str(uuid.uuid4())
        sid = source_node_id or f"rpi.virtual_{node_type.value}"
        self._validate_source_id(sid)
        self._validate_topic(profile.publish_topic)
        node = VirtualNode(
            node_id=nid,
            node_type=node_type,
            source_node_id=sid,
            profile=profile,
            created_at_ms=int(time.time() * 1000),
        )
        self._nodes[nid] = node
        return node

    def start_node(self, node: VirtualNode) -> None:
        if node.state == VirtualNodeState.CREATED:
            node.state = VirtualNodeState.RUNNING

    def stop_node(self, node: VirtualNode) -> None:
        if node.state == VirtualNodeState.RUNNING:
            node.state = VirtualNodeState.STOPPED

    def delete_node(self, node_id: str) -> None:
        node = self._nodes.get(node_id)
        if node:
            node.state = VirtualNodeState.DELETED
            del self._nodes[node_id]

    def publish_once(self, node: VirtualNode) -> dict:
        """Publish one payload from the node's profile template."""
        if node.state != VirtualNodeState.RUNNING:
            raise RuntimeError(f"Node {node.node_id} is not running")
        payload = {**node.profile.payload_template,
                   "source_node_id": node.source_node_id}
        self._publisher.publish(node.profile.publish_topic, payload, qos=1)
        node.published_count += 1
        return payload

    def get_node(self, node_id: str) -> Optional[VirtualNode]:
        return self._nodes.get(node_id)

    def list_nodes(self) -> list[VirtualNode]:
        return list(self._nodes.values())

    def list_running_nodes(self) -> list[VirtualNode]:
        return [n for n in self._nodes.values()
                if n.state == VirtualNodeState.RUNNING]

    # ------------------------------------------------------------------
    # Internal validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_source_id(sid: str) -> None:
        if not any(sid.startswith(p) for p in _ALLOWED_SOURCE_PREFIXES):
            raise ValueError(
                f"source_node_id '{sid}' must identify simulated origin "
                f"(must start with one of {_ALLOWED_SOURCE_PREFIXES})"
            )

    @staticmethod
    def _validate_topic(topic: str) -> None:
        if topic not in _REGISTRY_TOPICS:
            raise ValueError(
                f"Topic '{topic}' is not in the allowed virtual-node registry topics. "
                f"Allowed: {sorted(_REGISTRY_TOPICS)}"
            )

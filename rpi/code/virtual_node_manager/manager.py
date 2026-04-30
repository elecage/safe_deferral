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
    ACTUATOR_DEVICES,
    device_post_state,
)

_REGISTRY_TOPICS = {
    "safe_deferral/context/input",
    "safe_deferral/emergency/event",
    "safe_deferral/actuation/ack",
}

_ALLOWED_SOURCE_PREFIXES = ("rpi.", "esp32.virtual_", "test.")

_ACK_TOPIC = "safe_deferral/actuation/ack"
_PRESENCE_TOPIC = "safe_deferral/node/presence"


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

    For actuator_simulator nodes, call handle_command() when an
    actuation command arrives on safe_deferral/actuation/command.
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
        device_target: Optional[str] = None,
    ) -> VirtualNode:
        nid = node_id or str(uuid.uuid4())
        sid = source_node_id or f"rpi.virtual_{node_type.value}"
        self._validate_source_id(sid)
        self._validate_topic(profile.publish_topic)
        if device_target is not None and device_target not in ACTUATOR_DEVICES:
            raise ValueError(
                f"device_target '{device_target}' is not a known device. "
                f"Allowed: {ACTUATOR_DEVICES}"
            )
        node = VirtualNode(
            node_id=nid,
            node_type=node_type,
            source_node_id=sid,
            profile=profile,
            created_at_ms=int(time.time() * 1000),
            device_target=device_target,
        )
        self._nodes[nid] = node
        return node

    def start_node(self, node: VirtualNode) -> None:
        if node.state in (VirtualNodeState.CREATED, VirtualNodeState.STOPPED):
            node.state = VirtualNodeState.RUNNING
            self._publish_presence(node, "online")

    def stop_node(self, node: VirtualNode) -> None:
        if node.state == VirtualNodeState.RUNNING:
            node.state = VirtualNodeState.STOPPED
            self._publish_presence(node, "offline")

    def delete_node(self, node_id: str) -> None:
        node = self._nodes.get(node_id)
        if node:
            self._publish_presence(node, "offline")
            node.state = VirtualNodeState.DELETED
            del self._nodes[node_id]

    def publish_once(self, node: VirtualNode) -> dict:
        """Publish one payload from the node's profile template.

        Refreshes time-sensitive fields at the moment of publishing so the
        Mac mini policy router's staleness check always passes.

        The staleness check (router.py) is:
            ingest_timestamp_ms - trigger_event.timestamp_ms > freshness_threshold_ms
        Both fields must be updated together. Updating only ingest_timestamp_ms
        while leaving trigger_event.timestamp_ms at the old template value
        maximises the gap and guarantees C204.

        Strategy: set trigger_event.timestamp_ms = now, ingest_timestamp_ms = now.
        Difference = 0 ms, which is always within the 3 000 ms threshold.
        """
        if node.state != VirtualNodeState.RUNNING:
            raise RuntimeError(f"Node {node.node_id} is not running")

        now_ms = int(time.time() * 1000)
        payload = {**node.profile.payload_template,
                   "source_node_id": node.source_node_id}

        # Refresh ingest timestamp (routing_metadata layer).
        if "routing_metadata" in payload:
            payload["routing_metadata"] = {
                **payload["routing_metadata"],
                "ingest_timestamp_ms": now_ms,
            }

        # Refresh trigger_event timestamp (pure_context_payload layer).
        # Must be updated alongside ingest_timestamp_ms; the staleness check
        # is: ingest_ts - trigger_ts > threshold. Leaving trigger_ts stale
        # while refreshing ingest_ts widens the gap to the full elapsed time
        # since node creation and guarantees C204.
        if "pure_context_payload" in payload:
            ctx = dict(payload["pure_context_payload"])
            if "trigger_event" in ctx:
                ctx["trigger_event"] = {
                    **ctx["trigger_event"],
                    "timestamp_ms": now_ms,
                }
            payload["pure_context_payload"] = ctx

        self._publisher.publish(node.profile.publish_topic, payload, qos=1)
        node.published_count += 1
        return payload

    def handle_command(self, command_payload: dict) -> list[dict]:
        """Auto-ACK a received actuation command from Mac mini.

        Finds all RUNNING actuator_simulator nodes whose device_target
        matches command_payload["target_device"] and publishes an ACK
        for each. Returns list of published ACK payloads.
        """
        target = command_payload.get("target_device")
        if not target:
            return []

        acks = []
        for node in self._nodes.values():
            if (node.node_type != VirtualNodeType.ACTUATOR_SIMULATOR
                    or node.state != VirtualNodeState.RUNNING
                    or node.device_target != target):
                continue

            action = command_payload.get("action", "")
            ack = {
                "ack_id": str(uuid.uuid4()),
                "command_id": command_payload.get("command_id", ""),
                "target_device": target,
                "ack_status": "success",
                "observed_state": device_post_state(target, action),
                "timestamp_ms": int(time.time() * 1000),
                "audit_correlation_id": command_payload.get("audit_correlation_id", ""),
                "source_node_id": node.source_node_id,
                "authority_note": (
                    "ACK is closed-loop evidence and is not pure context input."
                ),
            }
            self._publisher.publish(_ACK_TOPIC, ack, qos=1)
            node.published_count += 1
            acks.append(ack)

        return acks

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

    def _publish_presence(self, node: VirtualNode, status: str) -> None:
        """Publish node presence to safe_deferral/node/presence.

        Mirrors the same topic used by physical ESP32 nodes (via MQTT LWT and
        explicit connect announcements), so NodePresenceRegistry sees both
        source types uniformly.
        """
        try:
            payload = {
                "node_id": node.node_id,
                "node_type": node.node_type.value,
                "source": "virtual",
                "status": status,
                "timestamp_ms": int(time.time() * 1000),
                "source_node_id": node.source_node_id,
            }
            self._publisher.publish(_PRESENCE_TOPIC, payload, qos=1)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "Failed to publish presence for %s: %s", node.node_id, exc
            )

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

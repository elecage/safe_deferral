"""Virtual Node Manager (RPI-03).

Creates, configures, starts, stops, and deletes virtual experiment nodes.

Authority boundary:
  - Virtual nodes publish only registry-aligned experiment traffic.
  - No production-device authority.
  - No Policy Router override.
  - No autonomous doorlock authorization from virtual visitor context.
  - source_node_id must identify simulated origin (rpi.virtual_*).

Simulation state architecture:
  ENV_SENSOR_NODE and DEVICE_STATE_NODE update the injected SimStateStore when
  they publish.  CONTEXT_NODE assembles the full pure_context_payload at publish
  time by merging its trigger_event template with the current SimStateStore
  snapshot — so the environmental context always reflects the live sensor states
  rather than a static baked-in template value.

  Backward compatibility: if the CONTEXT_NODE template already contains
  environmental_context (e.g. a scenario fixture was loaded), the existing
  values are kept and SimStateStore is NOT injected.
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

# Operational topics (policy-router input, emergency, ACK)
_REGISTRY_TOPICS = {
    "safe_deferral/context/input",
    "safe_deferral/emergency/event",
    "safe_deferral/actuation/ack",
}

# Simulation-only topics: sensor/device state and general sim context
_SIM_TOPICS = {
    "safe_deferral/sim/sensor",   # env sensor readings (one topic, per-sensor payload)
    "safe_deferral/sim/device",   # device state updates
    "safe_deferral/sim/context",  # general simulation context (legacy)
}

_ALL_ALLOWED_TOPICS = _REGISTRY_TOPICS | _SIM_TOPICS

_ALLOWED_SOURCE_PREFIXES = ("rpi.", "esp32.virtual_", "test.")

_ACK_TOPIC = "safe_deferral/actuation/ack"
_PRESENCE_TOPIC = "safe_deferral/node/presence"

_SIM_SENSOR_TOPIC = "safe_deferral/sim/sensor"
_SIM_DEVICE_TOPIC = "safe_deferral/sim/device"


class MqttPublisher(Protocol):
    def publish(self, topic: str, payload: dict, qos: int = 1) -> None: ...


class _NoOpPublisher:
    def publish(self, topic: str, payload: dict, qos: int = 1) -> None:
        pass


class VirtualNodeManager:
    """Manages virtual experiment nodes.

    Usage:
        mgr = VirtualNodeManager(mqtt_publisher=pub, sim_state=state_store)
        node = mgr.create_node(VirtualNodeType.CONTEXT_NODE, profile)
        mgr.start_node(node)
        mgr.publish_once(node)      # or run in loop externally
        mgr.stop_node(node)
        mgr.delete_node(node.node_id)

    For actuator_simulator nodes, call handle_command() when an
    actuation command arrives on safe_deferral/actuation/command.
    """

    def __init__(
        self,
        mqtt_publisher: Optional[MqttPublisher] = None,
        sim_state=None,  # Optional[SimStateStore] — avoid circular import
    ) -> None:
        self._publisher: MqttPublisher = mqtt_publisher or _NoOpPublisher()
        self._nodes: dict[str, VirtualNode] = {}
        self._sim_state = sim_state  # may be None (no-op for backward compatibility)

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
        sensor_name: Optional[str] = None,
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
            sensor_name=sensor_name,
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

        Behaviour varies by node type:

        CONTEXT_NODE:
          Assembles a complete policy_router_input payload from the template's
          trigger_event + current SimStateStore snapshot (environmental_context
          and device_states).  If the template already contains
          environmental_context the SimStateStore is NOT injected (backward
          compatibility for scenario fixtures with baked-in environment).

        ENV_SENSOR_NODE:
          Publishes one sensor reading to safe_deferral/sim/sensor and updates
          the SimStateStore.  Template keys: {"sensor_name": str, "value": any}.

        DEVICE_STATE_NODE:
          Publishes one device state update to safe_deferral/sim/device and
          updates the SimStateStore.  Template keys: {"device_name": str, "state": str}.

        All other types:
          Publishes the template payload with refreshed timestamps.

        Staleness check note (applies to CONTEXT_NODE and general context types):
          ingest_timestamp_ms and trigger_event.timestamp_ms must be kept equal
          (both set to now_ms) so the Policy Router staleness guard (C204) passes.
        """
        if node.state != VirtualNodeState.RUNNING:
            raise RuntimeError(f"Node {node.node_id} is not running")

        now_ms = int(time.time() * 1000)

        # ---- ENV_SENSOR_NODE ----
        if node.node_type == VirtualNodeType.ENV_SENSOR_NODE:
            return self._publish_env_sensor(node, now_ms)

        # ---- DEVICE_STATE_NODE ----
        if node.node_type == VirtualNodeType.DEVICE_STATE_NODE:
            return self._publish_device_state(node, now_ms)

        # ---- CONTEXT_NODE (and all other types) ----
        payload = {**node.profile.payload_template,
                   "source_node_id": node.source_node_id}

        # Refresh ingest timestamp (routing_metadata layer).
        if "routing_metadata" in payload:
            payload["routing_metadata"] = {
                **payload["routing_metadata"],
                "ingest_timestamp_ms": now_ms,
            }

        # Build pure_context_payload with SimStateStore injection for CONTEXT_NODE.
        if "pure_context_payload" in payload:
            ctx = dict(payload["pure_context_payload"])

            # Refresh trigger_event timestamp (staleness check).
            if "trigger_event" in ctx:
                ctx["trigger_event"] = {
                    **ctx["trigger_event"],
                    "timestamp_ms": now_ms,
                }

            # Inject current simulation state for CONTEXT_NODEs whose template
            # does NOT already carry environmental_context.  This is the live-
            # simulation path: the environment comes from sensor virtual nodes
            # rather than a static baked-in fixture.
            if (
                node.node_type == VirtualNodeType.CONTEXT_NODE
                and "environmental_context" not in ctx
                and self._sim_state is not None
            ):
                snap = self._sim_state.get_snapshot()
                ctx["environmental_context"] = snap["environmental_context"]
                ctx["device_states"] = snap["device_states"]

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
    # Internal: per-type publish helpers
    # ------------------------------------------------------------------

    def _publish_env_sensor(self, node: VirtualNode, now_ms: int) -> dict:
        """Publish one env sensor reading and update SimStateStore."""
        tmpl = node.profile.payload_template
        sensor_name = node.sensor_name or tmpl.get("sensor_name", "")
        value = tmpl.get("value")

        payload = {
            "sensor_name": sensor_name,
            "value": value,
            "timestamp_ms": now_ms,
            "source_node_id": node.source_node_id,
        }

        # Update shared simulation state
        if self._sim_state is not None and sensor_name:
            try:
                self._sim_state.update_env(sensor_name, value)
            except (ValueError, TypeError):
                pass  # Unknown sensor — publish anyway, don't crash

        self._publisher.publish(_SIM_SENSOR_TOPIC, payload, qos=1)
        node.published_count += 1
        return payload

    def _publish_device_state(self, node: VirtualNode, now_ms: int) -> dict:
        """Publish one device state update and update SimStateStore."""
        tmpl = node.profile.payload_template
        device_name = node.device_target or tmpl.get("device_name", "")
        state = tmpl.get("state", "off")

        payload = {
            "device_name": device_name,
            "state": state,
            "timestamp_ms": now_ms,
            "source_node_id": node.source_node_id,
        }

        # Update shared simulation state
        if self._sim_state is not None and device_name:
            try:
                self._sim_state.update_device(device_name, state)
            except ValueError:
                pass  # Unknown device — publish anyway

        self._publisher.publish(_SIM_DEVICE_TOPIC, payload, qos=1)
        node.published_count += 1
        return payload

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
        if topic not in _ALL_ALLOWED_TOPICS:
            raise ValueError(
                f"Topic '{topic}' is not in the allowed virtual-node topics. "
                f"Allowed: {sorted(_ALL_ALLOWED_TOPICS)}"
            )

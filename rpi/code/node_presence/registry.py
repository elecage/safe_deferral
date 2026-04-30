"""NodePresenceRegistry — unified presence tracking for physical and virtual nodes.

Consumes messages from safe_deferral/node/presence.

Physical ESP32 nodes publish:
  - explicit "online" on connect
  - "offline" via MQTT LWT on unexpected disconnect

Virtual nodes (VirtualNodeManager) publish:
  - "online" on start_node()
  - "offline" on stop_node() / delete_node()

Authority boundary:
  - This registry is a monitoring artifact only.
  - Node presence does not grant policy, validator, or actuator authority.
  - Preflight checks use this for experiment readiness (DEGRADED, not BLOCKED).
"""

import logging
import threading
import time
from typing import Optional

log = logging.getLogger(__name__)

PRESENCE_TOPIC = "safe_deferral/node/presence"

_STALE_THRESHOLD_MS = 120_000   # 2 min — mark as stale if no update


class NodeEntry:
    """Runtime record for a single node's presence state."""

    __slots__ = (
        "node_id", "node_type", "source", "status",
        "last_seen_ms", "first_seen_ms", "extra",
    )

    def __init__(
        self,
        node_id: str,
        node_type: str,
        source: str,
        status: str,
        timestamp_ms: int,
        extra: Optional[dict] = None,
    ) -> None:
        self.node_id = node_id
        self.node_type = node_type
        self.source = source          # "physical" | "virtual"
        self.status = status          # "online" | "offline"
        self.last_seen_ms = timestamp_ms
        self.first_seen_ms = timestamp_ms
        self.extra = extra or {}

    def update(self, status: str, timestamp_ms: int, extra: Optional[dict] = None) -> None:
        self.status = status
        self.last_seen_ms = timestamp_ms
        if extra:
            self.extra.update(extra)

    def to_dict(self) -> dict:
        now = int(time.time() * 1000)
        age_ms = now - self.last_seen_ms
        stale = age_ms > _STALE_THRESHOLD_MS and self.status == "online"
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "source": self.source,
            "status": "stale" if stale else self.status,
            "reported_status": self.status,
            "last_seen_ms": self.last_seen_ms,
            "first_seen_ms": self.first_seen_ms,
            "age_ms": age_ms,
            "stale": stale,
            **self.extra,
        }


class NodePresenceRegistry:
    """Thread-safe registry of all known nodes (physical + virtual).

    Usage:
        registry = NodePresenceRegistry()
        # wire into MQTT on_message:
        registry.handle_message(payload_dict)

        # query
        registry.is_online("rpi.virtual_context_node_abc123")
        registry.list_online()
        registry.find_by_type("context_node")
        registry.snapshot()     # all nodes as list[dict]
    """

    def __init__(self) -> None:
        self._nodes: dict[str, NodeEntry] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def handle_message(self, payload: dict) -> None:
        """Process a presence payload from safe_deferral/node/presence."""
        try:
            node_id = payload.get("node_id", "")
            node_type = payload.get("node_type", "unknown")
            source = payload.get("source", "unknown")
            status = payload.get("status", "unknown")
            timestamp_ms = payload.get("timestamp_ms", int(time.time() * 1000))

            if not node_id:
                log.warning("Presence message missing node_id: %s", payload)
                return

            # Extract any extra fields for richer display
            extra = {
                k: v for k, v in payload.items()
                if k not in {"node_id", "node_type", "source", "status", "timestamp_ms"}
            }

            with self._lock:
                entry = self._nodes.get(node_id)
                if entry is None:
                    self._nodes[node_id] = NodeEntry(
                        node_id=node_id,
                        node_type=node_type,
                        source=source,
                        status=status,
                        timestamp_ms=timestamp_ms,
                        extra=extra,
                    )
                    log.info(
                        "Node registered: %s (%s/%s) → %s",
                        node_id, source, node_type, status,
                    )
                else:
                    prev = entry.status
                    entry.update(status=status, timestamp_ms=timestamp_ms, extra=extra)
                    if prev != status:
                        log.info(
                            "Node %s status: %s → %s", node_id, prev, status,
                        )

        except Exception as exc:
            log.error("NodePresenceRegistry.handle_message error: %s", exc)

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def is_online(self, node_id: str) -> bool:
        """Return True if the node is currently online (not stale)."""
        with self._lock:
            entry = self._nodes.get(node_id)
            if entry is None or entry.status != "online":
                return False
            age_ms = int(time.time() * 1000) - entry.last_seen_ms
            return age_ms <= _STALE_THRESHOLD_MS

    def list_online(self) -> list[NodeEntry]:
        """Return all currently online (non-stale) nodes."""
        now = int(time.time() * 1000)
        with self._lock:
            return [
                e for e in self._nodes.values()
                if e.status == "online"
                and (now - e.last_seen_ms) <= _STALE_THRESHOLD_MS
            ]

    def list_all(self) -> list[NodeEntry]:
        with self._lock:
            return list(self._nodes.values())

    def find_by_type(self, node_type: str) -> list[NodeEntry]:
        """Return all online nodes matching node_type."""
        return [e for e in self.list_online() if e.node_type == node_type]

    def find_by_source(self, source: str) -> list[NodeEntry]:
        """Return all online nodes matching source ('physical'|'virtual')."""
        return [e for e in self.list_online() if e.source == source]

    def get(self, node_id: str) -> Optional[NodeEntry]:
        with self._lock:
            return self._nodes.get(node_id)

    def snapshot(self) -> list[dict]:
        """Return serialisable snapshot of all tracked nodes."""
        with self._lock:
            return [e.to_dict() for e in self._nodes.values()]

    def online_count(self, source: Optional[str] = None) -> int:
        nodes = self.list_online()
        if source:
            nodes = [n for n in nodes if n.source == source]
        return len(nodes)

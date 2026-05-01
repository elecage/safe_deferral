"""Ring buffer for safe_deferral/escalation/class2 notification payloads.

Mirrors ObservationStore but holds Class 2 caregiver notification payloads so
Package D (Class 2 Notification Payload Completeness, required_experiments.md
§8) can validate them against class2_notification_payload_schema.json.
"""

import threading
from collections import deque
from typing import Optional


class NotificationStore:
    def __init__(self, maxlen: int = 100) -> None:
        self._lock = threading.Lock()
        self._buf: deque = deque(maxlen=maxlen)

    def add(self, payload: dict) -> None:
        with self._lock:
            self._buf.append(payload)

    def list_recent(self, limit: int = 50) -> list:
        with self._lock:
            items = list(self._buf)
        return items[-limit:]

    def clear(self) -> None:
        with self._lock:
            self._buf.clear()

    def find_by_correlation_id(self, correlation_id: str) -> Optional[dict]:
        """Return the most recent notification whose audit_correlation_id matches."""
        with self._lock:
            items = list(self._buf)
        for item in reversed(items):
            if item.get("audit_correlation_id") == correlation_id:
                return item
        return None

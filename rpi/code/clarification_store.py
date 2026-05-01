"""Ring buffer for safe_deferral/clarification/interaction records.

Mirrors ObservationStore / NotificationStore but holds Class 2 clarification
records emitted by Mac mini's TelemetryAdapter.publish_class2_update(). Used
by Package D's class2_llm_quality sub-block (Phase 5 of
09_llm_driven_class2_candidate_generation_plan.md) to measure
candidate_source provenance and user-pickup rates without conflating
LLM-driven sessions with default_fallback ones.
"""

import threading
from collections import deque
from typing import Optional


class ClarificationStore:
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
        """Return the most recent clarification record whose
        audit_correlation_id matches."""
        with self._lock:
            items = list(self._buf)
        for item in reversed(items):
            if item.get("audit_correlation_id") == correlation_id:
                return item
        return None

"""Ring buffer for safe_deferral/dashboard/observation payloads."""

import threading
from collections import deque


class ObservationStore:
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

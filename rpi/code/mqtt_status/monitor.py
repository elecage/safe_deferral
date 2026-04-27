"""MQTT and Interface Status Manager (RPI-06).

Monitors broker connectivity, topic visibility, payload family conformance,
and interface health from the canonical topic registry.

Authority boundary:
  - No direct publishing of operational control topics.
  - No direct registry file editing.
  - Interface-status warnings are observations only — not policy authority.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from shared.asset_loader import RpiAssetLoader


class TopicHealth(str, Enum):
    HEALTHY = "healthy"
    MISSING = "missing"          # expected but not observed
    UNEXPECTED = "unexpected"    # observed but not in registry
    STALE = "stale"              # last seen beyond staleness threshold
    UNAUTHORIZED = "unauthorized" # published by wrong role


@dataclass
class TopicStatus:
    topic: str
    health: TopicHealth
    last_seen_ms: Optional[int]
    publisher_observed: Optional[str]
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "health": self.health.value,
            "last_seen_ms": self.last_seen_ms,
            "publisher_observed": self.publisher_observed,
            "note": self.note,
        }


@dataclass
class InterfaceHealthReport:
    generated_at_ms: int
    broker_reachable: bool
    topic_statuses: list[TopicStatus] = field(default_factory=list)
    authority_note: str = (
        "Interface health report is an observation artifact. "
        "It does not grant policy authority."
    )

    @property
    def healthy_count(self) -> int:
        return sum(1 for t in self.topic_statuses if t.health == TopicHealth.HEALTHY)

    @property
    def problem_count(self) -> int:
        return len(self.topic_statuses) - self.healthy_count

    def to_dict(self) -> dict:
        return {
            "generated_at_ms": self.generated_at_ms,
            "broker_reachable": self.broker_reachable,
            "healthy_count": self.healthy_count,
            "problem_count": self.problem_count,
            "topic_statuses": [t.to_dict() for t in self.topic_statuses],
            "authority_note": self.authority_note,
        }


class MqttStatusMonitor:
    """Builds interface health reports from observed MQTT traffic.

    In production, wire observe_message() to an MQTT subscription callback.
    In tests, call observe_message() directly.
    """

    STALE_THRESHOLD_MS = 30_000

    def __init__(self, asset_loader: Optional[RpiAssetLoader] = None) -> None:
        self._loader = asset_loader or RpiAssetLoader()
        registry = self._loader.load_topic_registry()
        self._registry_topics = {t["topic"]: t for t in registry.get("topics", [])}
        self._observations: dict[str, dict] = {}   # topic → {last_seen_ms, publisher}
        self._broker_reachable = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_broker_reachable(self, reachable: bool) -> None:
        self._broker_reachable = reachable

    def observe_message(
        self,
        topic: str,
        publisher: Optional[str] = None,
        timestamp_ms: Optional[int] = None,
    ) -> None:
        """Record an observed MQTT message (call from subscription callback)."""
        self._observations[topic] = {
            "last_seen_ms": timestamp_ms or int(time.time() * 1000),
            "publisher": publisher,
        }

    def build_report(self) -> InterfaceHealthReport:
        """Build a current interface health report."""
        now = int(time.time() * 1000)
        statuses: list[TopicStatus] = []

        # Check all registry topics
        for topic, meta in self._registry_topics.items():
            obs = self._observations.get(topic)
            if obs is None:
                statuses.append(TopicStatus(
                    topic=topic,
                    health=TopicHealth.MISSING,
                    last_seen_ms=None,
                    publisher_observed=None,
                    note="topic not yet observed",
                ))
            else:
                last_seen = obs["last_seen_ms"]
                age = now - last_seen
                health = (TopicHealth.STALE if age > self.STALE_THRESHOLD_MS
                          else TopicHealth.HEALTHY)
                statuses.append(TopicStatus(
                    topic=topic,
                    health=health,
                    last_seen_ms=last_seen,
                    publisher_observed=obs.get("publisher"),
                ))

        # Flag unexpected topics
        for topic in self._observations:
            if topic not in self._registry_topics:
                statuses.append(TopicStatus(
                    topic=topic,
                    health=TopicHealth.UNEXPECTED,
                    last_seen_ms=self._observations[topic]["last_seen_ms"],
                    publisher_observed=self._observations[topic].get("publisher"),
                    note="topic not in registry",
                ))

        return InterfaceHealthReport(
            generated_at_ms=now,
            broker_reachable=self._broker_reachable,
            topic_statuses=statuses,
        )

    def get_topic_health(self, topic: str) -> TopicHealth:
        if topic not in self._observations:
            return TopicHealth.MISSING
        obs = self._observations[topic]
        age = int(time.time() * 1000) - obs["last_seen_ms"]
        return TopicHealth.STALE if age > self.STALE_THRESHOLD_MS else TopicHealth.HEALTHY

    def reset(self) -> None:
        self._observations.clear()

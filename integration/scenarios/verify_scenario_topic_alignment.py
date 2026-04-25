#!/usr/bin/env python3
"""Verify scenario MQTT topics against the shared topic registry.

This script checks only communication-contract alignment. It does not create
policy, schema, or execution authority.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = ROOT / "integration" / "scenarios"
TOPIC_REGISTRY = ROOT / "common" / "mqtt" / "topic_registry_v1_0_0.json"
LEGACY_TOPICS = {
    "smarthome/context/raw",
    "smarthome/audit/validator_output",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc


def scenario_files() -> list[Path]:
    return sorted(SCENARIO_DIR.glob("*_scenario_skeleton.json"))


def registry_topics() -> set[str]:
    registry = load_json(TOPIC_REGISTRY)
    topics = registry.get("topics", [])
    if not isinstance(topics, list):
        raise ValueError(f"{TOPIC_REGISTRY}: topics must be a list")
    result = set()
    for entry in topics:
        if isinstance(entry, dict) and isinstance(entry.get("topic"), str):
            result.add(entry["topic"])
    return result


def main() -> int:
    try:
        allowed_topics = registry_topics()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    files = scenario_files()
    if not files:
        print("ERROR: no scenario skeleton files found", file=sys.stderr)
        return 1

    for path in files:
        rel = path.relative_to(ROOT)
        try:
            data = load_json(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        input_plane = data.get("input_plane", {})
        if not isinstance(input_plane, dict):
            errors.append(f"{rel}: input_plane must be an object")
            continue

        for field in ("ingress_topic", "normalized_policy_input_topic", "audit_topic"):
            topic = input_plane.get(field)
            if topic is None:
                continue
            if not isinstance(topic, str) or not topic:
                errors.append(f"{rel}: input_plane.{field} must be a non-empty string")
                continue
            if topic in LEGACY_TOPICS:
                errors.append(f"{rel}: legacy topic not allowed in {field}: {topic}")
            if topic not in allowed_topics:
                errors.append(f"{rel}: topic in {field} not found in registry: {topic}")

        category = data.get("category")
        ingress = input_plane.get("ingress_topic")
        if category == "class0_emergency" and ingress != "safe_deferral/emergency/event":
            errors.append(f"{rel}: class0_emergency ingress_topic must be safe_deferral/emergency/event")
        if category != "class0_emergency" and ingress != "safe_deferral/context/input":
            errors.append(f"{rel}: non-class0 scenario ingress_topic must be safe_deferral/context/input")
        if input_plane.get("audit_topic") != "safe_deferral/audit/log":
            errors.append(f"{rel}: audit_topic must be safe_deferral/audit/log")

    if errors:
        print("Scenario topic alignment verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"OK: verified topic alignment for {len(files)} scenario manifest(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Minimal preflight readiness aggregator skeleton for the safe_deferral measurement layer.

Purpose:
- load experiment and node registry YAML assets,
- evaluate a selected experiment against a provided node-state snapshot,
- produce a machine-readable readiness report,
- preserve the distinction between operational dependencies and out-of-band measurement dependencies.

This skeleton is an evaluation/operational-support helper.
It does NOT redefine canonical policy truth, validator authority, or experiment semantics.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - fail fast at runtime if missing
    raise SystemExit(
        "[FATAL] PyYAML is required for preflight_readiness_aggregator_skeleton.py"
    ) from exc


REPO_MARKERS = {"common", "integration", "mac_mini", "rpi", "esp32"}
VALID_STATES = {"READY", "DEGRADED", "BLOCKED", "UNKNOWN"}


class PreflightError(Exception):
    """Raised when the preflight readiness aggregator cannot complete successfully."""


@dataclass
class Reason:
    code: str
    message: str
    scope: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "scope": self.scope,
        }


@dataclass
class DependencyEvaluation:
    dependency_id: str
    dependency_type: str
    required: bool
    state: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dependency_id": self.dependency_id,
            "dependency_type": self.dependency_type,
            "required": self.required,
            "state": self.state,
            "details": self.details,
        }


@dataclass
class PreflightReport:
    experiment_id: str
    final_state: str
    blocked_if_missing: bool
    dependency_results: list[DependencyEvaluation]
    reasons: list[Reason]

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "final_state": self.final_state,
            "blocked_if_missing": self.blocked_if_missing,
            "dependency_results": [item.to_dict() for item in self.dependency_results],
            "reasons": [reason.to_dict() for reason in self.reasons],
        }


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        names = {p.name for p in candidate.iterdir()} if candidate.is_dir() else set()
        if REPO_MARKERS.issubset(names):
            return candidate
    raise PreflightError("Could not determine repository root from the current path.")


def load_yaml_file(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fp:
            return yaml.safe_load(fp)
    except FileNotFoundError as exc:
        raise PreflightError(f"Required YAML file was not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise PreflightError(f"Invalid YAML syntax in file: {path} ({exc})") from exc


def load_registry(repo_root: Path, rel_path: str, expected_type: str) -> dict[str, Any]:
    registry_path = (repo_root / rel_path).resolve()
    payload = load_yaml_file(registry_path)
    if not isinstance(payload, dict):
        raise PreflightError(f"Registry must be a YAML object: {registry_path}")
    actual_type = payload.get("registry_type")
    if actual_type != expected_type:
        raise PreflightError(
            f"Registry type mismatch for {registry_path}: expected {expected_type}, got {actual_type!r}"
        )
    return payload


def load_state_snapshot(repo_root: Path, rel_path: str | None) -> dict[str, str]:
    if rel_path is None:
        return {}
    snapshot_path = (repo_root / rel_path).resolve()
    payload = load_yaml_file(snapshot_path)
    if not isinstance(payload, dict):
        raise PreflightError(f"State snapshot must be a YAML object: {snapshot_path}")
    nodes = payload.get("nodes", {})
    if not isinstance(nodes, dict):
        raise PreflightError(f"State snapshot key 'nodes' must be a mapping: {snapshot_path}")

    normalized: dict[str, str] = {}
    for node_id, raw_state in nodes.items():
        if not isinstance(node_id, str):
            raise PreflightError(f"State snapshot node_id must be a string: {snapshot_path}")
        if not isinstance(raw_state, str):
            raise PreflightError(f"State snapshot state must be a string for node {node_id}: {snapshot_path}")
        state = raw_state.strip().upper()
        if state not in VALID_STATES:
            raise PreflightError(
                f"Invalid state '{raw_state}' for node {node_id}. Valid states: {sorted(VALID_STATES)}"
            )
        normalized[node_id] = state
    return normalized


def index_experiments(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    experiments = registry.get("experiments", [])
    if not isinstance(experiments, list):
        raise PreflightError("Experiment registry key 'experiments' must be a list.")

    indexed: dict[str, dict[str, Any]] = {}
    for item in experiments:
        if not isinstance(item, dict):
            raise PreflightError("Each experiment entry must be a mapping.")
        experiment_id = item.get("experiment_id")
        if not isinstance(experiment_id, str) or not experiment_id.strip():
            raise PreflightError("Each experiment entry must contain a non-empty string experiment_id.")
        indexed[experiment_id] = item
    return indexed


def index_nodes(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nodes = registry.get("nodes", [])
    if not isinstance(nodes, list):
        raise PreflightError("Node registry key 'nodes' must be a list.")

    indexed: dict[str, dict[str, Any]] = {}
    for item in nodes:
        if not isinstance(item, dict):
            raise PreflightError("Each node entry must be a mapping.")
        node_id = item.get("node_id")
        if not isinstance(node_id, str) or not node_id.strip():
            raise PreflightError("Each node entry must contain a non-empty string node_id.")
        indexed[node_id] = item
    return indexed


def evaluate_dependency(
    dependency_id: str,
    dependency_type: str,
    state_snapshot: dict[str, str],
    required: bool,
) -> DependencyEvaluation:
    state = state_snapshot.get(dependency_id, "UNKNOWN")
    details: dict[str, Any] = {}
    if state == "UNKNOWN":
        details["note"] = "No explicit state found in snapshot."
    return DependencyEvaluation(
        dependency_id=dependency_id,
        dependency_type=dependency_type,
        required=required,
        state=state,
        details=details,
    )


def aggregate_report(
    experiment: dict[str, Any],
    node_index: dict[str, dict[str, Any]],
    state_snapshot: dict[str, str],
) -> PreflightReport:
    experiment_id = str(experiment["experiment_id"])
    blocked_if_missing = bool(experiment.get("blocked_if_missing", True))
    dependency_results: list[DependencyEvaluation] = []
    reasons: list[Reason] = []

    operational_nodes = experiment.get("required_nodes", []) or []
    measurement_nodes = experiment.get("required_measurement_nodes", []) or []

    if not isinstance(operational_nodes, list) or not isinstance(measurement_nodes, list):
        raise PreflightError(
            f"Experiment {experiment_id} has invalid required_nodes or required_measurement_nodes structure."
        )

    for node_id in operational_nodes:
        if node_id not in node_index:
            dependency_results.append(
                DependencyEvaluation(
                    dependency_id=str(node_id),
                    dependency_type="required_node",
                    required=True,
                    state="BLOCKED",
                    details={"note": "Node missing from node registry."},
                )
            )
            reasons.append(
                Reason(
                    code="NODE_OFFLINE",
                    message=f"Operational node '{node_id}' is not present in the node registry.",
                    scope="operational",
                )
            )
            continue
        result = evaluate_dependency(str(node_id), "required_node", state_snapshot, required=True)
        dependency_results.append(result)
        if result.state == "BLOCKED":
            reasons.append(
                Reason(
                    code="NODE_OFFLINE",
                    message=f"Operational node '{node_id}' is blocked or offline.",
                    scope="operational",
                )
            )
        elif result.state == "UNKNOWN":
            reasons.append(
                Reason(
                    code="SERVICE_UNREACHABLE",
                    message=f"Operational node '{node_id}' readiness is unknown.",
                    scope="operational",
                )
            )

    for node_id in measurement_nodes:
        if node_id not in node_index:
            dependency_results.append(
                DependencyEvaluation(
                    dependency_id=str(node_id),
                    dependency_type="required_measurement_node",
                    required=True,
                    state="BLOCKED",
                    details={"note": "Measurement node missing from node registry."},
                )
            )
            reasons.append(
                Reason(
                    code="MEASUREMENT_NODE_UNAVAILABLE",
                    message=f"Measurement node '{node_id}' is not present in the node registry.",
                    scope="measurement",
                )
            )
            continue
        result = evaluate_dependency(
            str(node_id),
            "required_measurement_node",
            state_snapshot,
            required=True,
        )
        dependency_results.append(result)
        if result.state == "BLOCKED":
            reasons.append(
                Reason(
                    code="MEASUREMENT_NODE_UNAVAILABLE",
                    message=f"Measurement node '{node_id}' is blocked or offline.",
                    scope="measurement",
                )
            )
        elif result.state == "UNKNOWN":
            reasons.append(
                Reason(
                    code="TIME_PROBE_HEARTBEAT_STALE",
                    message=f"Measurement node '{node_id}' readiness is unknown.",
                    scope="measurement",
                )
            )

    has_operational_block = any(
        item.state == "BLOCKED" and item.dependency_type == "required_node"
        for item in dependency_results
    )
    has_operational_unknown = any(
        item.state == "UNKNOWN" and item.dependency_type == "required_node"
        for item in dependency_results
    )
    has_measurement_block = any(
        item.state == "BLOCKED" and item.dependency_type == "required_measurement_node"
        for item in dependency_results
    )
    has_measurement_unknown = any(
        item.state == "UNKNOWN" and item.dependency_type == "required_measurement_node"
        for item in dependency_results
    )

    measurement_policy = experiment.get("measurement_policy", {}) or {}
    measurement_missing_state = str(measurement_policy.get("if_missing", "DEGRADED")).upper()
    if measurement_missing_state not in VALID_STATES:
        raise PreflightError(
            f"Experiment {experiment_id} has invalid measurement_policy.if_missing: {measurement_missing_state}"
        )

    if has_operational_block and blocked_if_missing:
        final_state = "BLOCKED"
    elif has_operational_unknown:
        final_state = "UNKNOWN"
    elif has_measurement_block:
        final_state = measurement_missing_state
    elif has_measurement_unknown:
        final_state = "UNKNOWN" if measurement_missing_state == "BLOCKED" else "DEGRADED"
    else:
        final_state = "READY"

    return PreflightReport(
        experiment_id=experiment_id,
        final_state=final_state,
        blocked_if_missing=blocked_if_missing,
        dependency_results=dependency_results,
        reasons=reasons,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load experiment/node registries and aggregate a preflight readiness report."
    )
    parser.add_argument(
        "--experiment",
        required=True,
        help="Experiment ID to evaluate, for example EXP_FAULT_STALENESS_01.",
    )
    parser.add_argument(
        "--experiment-registry",
        default="integration/measurement/experiment_registry_skeleton.yaml",
        help="Repository-relative path to the experiment registry YAML.",
    )
    parser.add_argument(
        "--node-registry",
        default="integration/measurement/node_registry_skeleton.yaml",
        help="Repository-relative path to the node registry YAML.",
    )
    parser.add_argument(
        "--state-snapshot",
        default=None,
        help=(
            "Optional repository-relative path to a YAML state snapshot. "
            "Format: {nodes: {node_id: READY|DEGRADED|BLOCKED|UNKNOWN}}"
        ),
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the readiness report JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(Path.cwd())

    experiment_registry = load_registry(repo_root, args.experiment_registry, "experiment_registry")
    node_registry = load_registry(repo_root, args.node_registry, "node_registry")
    state_snapshot = load_state_snapshot(repo_root, args.state_snapshot)

    experiments = index_experiments(experiment_registry)
    nodes = index_nodes(node_registry)

    if args.experiment not in experiments:
        raise PreflightError(f"Experiment ID not found in registry: {args.experiment}")

    report = aggregate_report(experiments[args.experiment], nodes, state_snapshot)

    if args.pretty:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(report.to_dict(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PreflightError as exc:
        print(f"[FATAL] {exc}", file=sys.stderr)
        raise SystemExit(1)

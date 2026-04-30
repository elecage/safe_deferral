"""RPi-side shared asset loader — read-only access to common/ assets."""

import json
from pathlib import Path
from typing import Optional

_DEFAULT_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class RpiAssetLoader:
    """Read-only loader for canonical assets under common/.

    The RPi never modifies canonical assets.  This loader is intentionally
    read-only and raises if called to write.
    """

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self.repo_root = Path(repo_root) if repo_root else _DEFAULT_REPO_ROOT

    def load_policy_table(self) -> dict:
        return self._load("common/policies/policy_table.json")

    def load_low_risk_actions(self) -> dict:
        return self._load("common/policies/low_risk_actions.json")

    def load_fault_injection_rules(self) -> dict:
        return self._load("common/policies/fault_injection_rules.json")

    def load_asset_manifest(self) -> dict:
        return self._load("common/asset_manifest.json")

    def load_topic_registry(self) -> dict:
        return self._load("common/mqtt/topic_registry.json")

    def load_schema(self, name: str) -> dict:
        return self._load(f"common/schemas/{name}")

    def load_scenario(self, filename: str) -> dict:
        return self._load(f"integration/scenarios/{filename}")

    def list_scenarios(self) -> list[str]:
        path = self.repo_root / "integration/scenarios"
        return sorted(p.name for p in path.glob("*.json"))

    def load_fixture(self, rel_path: str) -> dict:
        """Load a payload fixture by repo-relative path (e.g. integration/tests/data/...)."""
        return self._load(rel_path)

    def fixture_exists(self, rel_path: str) -> bool:
        """Return True if the fixture file exists under repo_root."""
        return (self.repo_root / rel_path).exists()

    def _load(self, rel_path: str) -> dict:
        full = self.repo_root / rel_path
        with open(full) as f:
            return json.load(f)

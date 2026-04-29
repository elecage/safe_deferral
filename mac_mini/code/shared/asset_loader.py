import json
from pathlib import Path
from typing import Optional

import jsonschema

# mac_mini/code/shared/ -> up 3 levels -> repo root
_DEFAULT_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class AssetLoader:
    """Loads canonical assets from common/ and provides a JSON schema resolver."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = Path(repo_root) if repo_root else _DEFAULT_REPO_ROOT

    def load_policy_table(self) -> dict:
        return self._load_json("common/policies/policy_table.json")

    def load_low_risk_actions(self) -> dict:
        return self._load_json("common/policies/low_risk_actions.json")

    def load_schema(self, name: str) -> dict:
        return self._load_json(f"common/schemas/{name}")

    def load_topic_registry(self) -> dict:
        return self._load_json("common/mqtt/topic_registry.json")

    def get_topic(self, topic: str) -> str:
        """Return topic string after validating it exists in the registry.

        Raises KeyError at startup if the topic has drifted out of the registry,
        making topic drift visible immediately rather than silently at runtime.
        """
        registry = self.load_topic_registry()
        known = {t["topic"] for t in registry["topics"]}
        if topic not in known:
            raise KeyError(
                f"Topic '{topic}' not found in topic_registry.json. "
                f"Update the registry or correct the topic string."
            )
        return topic

    def make_schema_resolver(self) -> jsonschema.RefResolver:
        """Returns a RefResolver that resolves $ref paths within common/schemas/."""
        schemas_dir = self.repo_root / "common/schemas"
        base_uri = schemas_dir.as_uri() + "/"
        store: dict = {}
        for path in schemas_dir.glob("*.json"):
            with open(path) as f:
                store[base_uri + path.name] = json.load(f)
        return jsonschema.RefResolver(base_uri=base_uri, referrer={}, store=store)

    def _load_json(self, rel_path: str) -> dict:
        with open(self.repo_root / rel_path) as f:
            return json.load(f)

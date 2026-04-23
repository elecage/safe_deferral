#!/usr/bin/env python3
"""Consistency checks between canonical policy_table and fault_injection_rules.

Run directly:
    python integration/tests/test_policy_fault_consistency.py
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = REPO_ROOT / "common" / "policies" / "policy_table_v1_1_2_FROZEN.json"
FAULT_RULES_PATH = REPO_ROOT / "common" / "policies" / "fault_injection_rules_v1_4_0_FROZEN.json"
VALIDATOR_SCHEMA_FILENAME = "validator_output_schema_v1_1_0_FROZEN.json"
POLICY_FILENAME = "policy_table_v1_1_2_FROZEN.json"


EXPECTED_EMERGENCY_PROFILE_TO_TRIGGER = {
    "FAULT_EMERGENCY_01_TEMP": "E001",
    "FAULT_EMERGENCY_02_BUTTON_TRIPLE_HIT": "E002",
    "FAULT_EMERGENCY_03_SMOKE": "E003",
    "FAULT_EMERGENCY_04_GAS": "E004",
    "FAULT_EMERGENCY_05_FALL": "E005",
}

EXPECTED_CLASS2_PROFILE_TO_TRIGGER = {
    "FAULT_STALENESS_01": "C204",
    "FAULT_MISSING_CONTEXT_01": "C202",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class PolicyFaultConsistencyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_json(POLICY_PATH)
        cls.fault_rules = load_json(FAULT_RULES_PATH)

        cls.class0_triggers = {
            trigger["id"]: trigger
            for trigger in cls.policy["routing_policies"]["class_0_emergency"]["triggers"]
        }
        cls.class2_triggers = {
            trigger["id"]: trigger
            for trigger in cls.policy["routing_policies"]["class_2_escalation"]["triggers"]
        }
        cls.deterministic_profiles = cls.fault_rules["deterministic_profiles"]

    def test_fault_rules_reference_canonical_policy_file(self) -> None:
        self.assertIn(
            POLICY_FILENAME,
            self.fault_rules["asset_dependencies"],
            "fault_injection_rules must reference the canonical policy table filename.",
        )

    def test_fault_rules_reference_canonical_validator_schema(self) -> None:
        self.assertIn(
            VALIDATOR_SCHEMA_FILENAME,
            self.fault_rules["asset_dependencies"],
            "fault_injection_rules must reference the canonical validator schema filename.",
        )

    def test_expected_emergency_profiles_exist(self) -> None:
        for profile_id in EXPECTED_EMERGENCY_PROFILE_TO_TRIGGER:
            self.assertIn(
                profile_id,
                self.deterministic_profiles,
                f"Missing deterministic emergency profile: {profile_id}",
            )

    def test_emergency_profile_selectors_match_policy_trigger_ids(self) -> None:
        for profile_id, expected_trigger_id in EXPECTED_EMERGENCY_PROFILE_TO_TRIGGER.items():
            profile = self.deterministic_profiles[profile_id]
            self.assertEqual(
                expected_trigger_id,
                profile.get("selector"),
                f"{profile_id} selector must match expected policy trigger ID.",
            )
            self.assertEqual(
                expected_trigger_id,
                profile.get("expected_trigger_id"),
                f"{profile_id} expected_trigger_id must match canonical policy trigger ID.",
            )
            self.assertEqual(
                "class_0_emergency",
                profile.get("expected_outcome"),
                f"{profile_id} must expect class_0_emergency.",
            )
            self.assertIn(
                expected_trigger_id,
                self.class0_triggers,
                f"Policy table is missing Class 0 trigger {expected_trigger_id} required by {profile_id}.",
            )

    def test_class2_profile_trigger_ids_exist_in_policy(self) -> None:
        for profile_id, expected_trigger_id in EXPECTED_CLASS2_PROFILE_TO_TRIGGER.items():
            profile = self.deterministic_profiles[profile_id]
            self.assertEqual(
                expected_trigger_id,
                profile.get("expected_trigger_id"),
                f"{profile_id} expected_trigger_id must match canonical Class 2 trigger ID.",
            )
            self.assertIn(
                expected_trigger_id,
                self.class2_triggers,
                f"Policy table is missing Class 2 trigger {expected_trigger_id} required by {profile_id}.",
            )

    def test_all_fault_rule_emergency_selectors_are_defined_in_policy(self) -> None:
        missing = []
        for profile_id, profile in self.deterministic_profiles.items():
            selector = profile.get("selector")
            if selector and selector.startswith("E") and selector not in self.class0_triggers:
                missing.append((profile_id, selector))
        self.assertFalse(
            missing,
            f"Emergency selectors missing from policy table: {missing}",
        )

    def test_policy_contains_minimum_expected_emergency_trigger_set(self) -> None:
        expected_trigger_ids = set(EXPECTED_EMERGENCY_PROFILE_TO_TRIGGER.values())
        self.assertTrue(
            expected_trigger_ids.issubset(self.class0_triggers.keys()),
            "Policy table must contain the canonical emergency trigger IDs required by fault rules.",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

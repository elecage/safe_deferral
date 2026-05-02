"""Tests for the scanning deterministic ordering layer (doc 12 §14 Phase 1.5).

The ordering function is pure — no manager / MQTT / TTS coupling — so these
tests exercise the full rule semantics without standing up the pipeline.
"""

import pytest

from class2_clarification_manager.scan_ordering import apply_scan_ordering


class _FakeChoice:
    def __init__(self, candidate_id, target):
        self.candidate_id = candidate_id
        self.candidate_transition_target = target


def _choices(*pairs):
    """Build a list of _FakeChoice from (candidate_id, transition_target) tuples."""
    return [_FakeChoice(cid, t) for cid, t in pairs]


# ==================================================================
# Bucket selection by trigger_id
# ==================================================================

class TestBucketSelection:
    def test_specific_trigger_wins_over_default(self):
        rules = {
            "by_trigger_id": {
                "C208": ["CAREGIVER_CONFIRMATION", "SAFE_DEFERRAL"],
                "_default": ["CLASS_1", "CAREGIVER_CONFIRMATION"],
            }
        }
        candidates = _choices(
            ("CG", "CAREGIVER_CONFIRMATION"),
            ("C1", "CLASS_1"),
        )
        result = apply_scan_ordering(candidates, None, "C208", rules)
        # C208 bucket → CAREGIVER first, then CLASS_1 goes to end
        # (CLASS_1 not in priority list).
        ids = [c.candidate_id for c in result.ordered_candidates]
        assert ids == ["CG", "C1"]
        assert result.matched_bucket == "C208"

    def test_default_used_when_no_specific_match(self):
        rules = {
            "by_trigger_id": {
                "_default": ["CLASS_0", "CLASS_1"],
            }
        }
        candidates = _choices(
            ("C1", "CLASS_1"),
            ("C0", "CLASS_0"),
        )
        result = apply_scan_ordering(candidates, None, "C999_unknown", rules)
        ids = [c.candidate_id for c in result.ordered_candidates]
        assert ids == ["C0", "C1"]
        assert result.matched_bucket == "_default"

    def test_no_rules_means_no_reordering(self):
        """Empty/missing rules → candidates retain source order, bucket = '_no_rules'."""
        candidates = _choices(
            ("CG", "CAREGIVER_CONFIRMATION"),
            ("C1", "CLASS_1"),
        )
        result = apply_scan_ordering(candidates, None, "C206", {})
        ids = [c.candidate_id for c in result.ordered_candidates]
        assert ids == ["CG", "C1"]
        assert result.matched_bucket == "_no_rules"


# ==================================================================
# Tie-breaking and unknown-target tail behaviour
# ==================================================================

class TestStableSortAndTail:
    def test_same_target_preserves_source_order(self):
        rules = {"by_trigger_id": {"C206": ["CLASS_1", "CLASS_0"]}}
        candidates = _choices(
            ("OPT_LIVING_ROOM", "CLASS_1"),   # source idx 0
            ("OPT_BEDROOM", "CLASS_1"),        # source idx 1
            ("C0", "CLASS_0"),
        )
        result = apply_scan_ordering(candidates, None, "C206", rules)
        ids = [c.candidate_id for c in result.ordered_candidates]
        # Two CLASS_1 candidates first, in source order; CLASS_0 last.
        assert ids == ["OPT_LIVING_ROOM", "OPT_BEDROOM", "C0"]

    def test_unknown_target_sorts_to_end_preserving_source_order(self):
        """Targets not in the priority list go to the END but keep their
        source order among themselves."""
        rules = {"by_trigger_id": {"C206": ["CLASS_1"]}}  # only CLASS_1 ranked
        candidates = _choices(
            ("CG", "CAREGIVER_CONFIRMATION"),  # not in list
            ("C1", "CLASS_1"),                  # ranked first
            ("SD", "SAFE_DEFERRAL"),            # not in list
        )
        result = apply_scan_ordering(candidates, None, "C206", rules)
        ids = [c.candidate_id for c in result.ordered_candidates]
        assert ids == ["C1", "CG", "SD"]


# ==================================================================
# Context overrides
# ==================================================================

class TestContextOverrides:
    def test_smoke_detected_boosts_class0(self):
        rules = {
            "by_trigger_id": {"C206": ["CLASS_1", "CLASS_0", "CAREGIVER_CONFIRMATION"]},
            "context_overrides": [{
                "if_field": "environmental_context.smoke_detected",
                "if_equals": True,
                "boost_first": "CLASS_0",
            }],
        }
        ctx = {"environmental_context": {"smoke_detected": True}}
        candidates = _choices(
            ("C1", "CLASS_1"),
            ("C0", "CLASS_0"),
            ("CG", "CAREGIVER_CONFIRMATION"),
        )
        result = apply_scan_ordering(candidates, ctx, "C206", rules)
        ids = [c.candidate_id for c in result.ordered_candidates]
        # CLASS_0 boosted to front overrides the C206 default ordering.
        assert ids == ["C0", "C1", "CG"]
        assert any("smoke_detected" in s for s in result.applied_overrides)

    def test_doorbell_detected_boosts_caregiver(self):
        rules = {
            "by_trigger_id": {"_default": ["CLASS_1", "CAREGIVER_CONFIRMATION"]},
            "context_overrides": [{
                "if_field": "environmental_context.doorbell_detected",
                "if_equals": True,
                "boost_first": "CAREGIVER_CONFIRMATION",
            }],
        }
        ctx = {"environmental_context": {"doorbell_detected": True}}
        candidates = _choices(
            ("C1", "CLASS_1"),
            ("CG", "CAREGIVER_CONFIRMATION"),
        )
        result = apply_scan_ordering(candidates, ctx, "C206", rules)
        ids = [c.candidate_id for c in result.ordered_candidates]
        assert ids[0] == "CG"

    def test_override_does_not_fire_when_condition_false(self):
        rules = {
            "by_trigger_id": {"C206": ["CLASS_1", "CLASS_0"]},
            "context_overrides": [{
                "if_field": "environmental_context.smoke_detected",
                "if_equals": True,
                "boost_first": "CLASS_0",
            }],
        }
        ctx = {"environmental_context": {"smoke_detected": False}}
        candidates = _choices(("C1", "CLASS_1"), ("C0", "CLASS_0"))
        result = apply_scan_ordering(candidates, ctx, "C206", rules)
        ids = [c.candidate_id for c in result.ordered_candidates]
        assert ids == ["C1", "C0"]   # original order kept
        assert result.applied_overrides == []

    def test_multiple_overrides_later_wins_front(self):
        """Later override takes the front spot (stack semantics, doc 12 §14.4)."""
        rules = {
            "by_trigger_id": {"_default": ["CLASS_1"]},
            "context_overrides": [
                {
                    "if_field": "environmental_context.smoke_detected",
                    "if_equals": True,
                    "boost_first": "CLASS_0",
                },
                {
                    "if_field": "environmental_context.doorbell_detected",
                    "if_equals": True,
                    "boost_first": "CAREGIVER_CONFIRMATION",
                },
            ],
        }
        ctx = {"environmental_context": {
            "smoke_detected": True,
            "doorbell_detected": True,
        }}
        candidates = _choices(
            ("C1", "CLASS_1"),
            ("C0", "CLASS_0"),
            ("CG", "CAREGIVER_CONFIRMATION"),
        )
        result = apply_scan_ordering(candidates, ctx, "C206", rules)
        ids = [c.candidate_id for c in result.ordered_candidates]
        # Doorbell override fires last → CAREGIVER first; CLASS_0 still
        # ahead of CLASS_1 (smoke override pushed it ahead earlier).
        assert ids[0] == "CG"
        assert ids.index("C0") < ids.index("C1")
        assert len(result.applied_overrides) == 2

    def test_missing_field_path_does_not_fire_override(self):
        """An override whose if_field path doesn't resolve in the payload
        must NOT fire (no fake match against None)."""
        rules = {
            "by_trigger_id": {"_default": ["CLASS_1"]},
            "context_overrides": [{
                "if_field": "environmental_context.doorbell_detected",
                "if_equals": True,
                "boost_first": "CAREGIVER_CONFIRMATION",
            }],
        }
        # Empty payload — the path resolves to None, which != True.
        candidates = _choices(("C1", "CLASS_1"), ("CG", "CAREGIVER_CONFIRMATION"))
        result = apply_scan_ordering(candidates, {}, "C206", rules)
        ids = [c.candidate_id for c in result.ordered_candidates]
        assert ids == ["C1", "CG"]   # no boost
        assert result.applied_overrides == []


# ==================================================================
# Pure permutation invariant
# ==================================================================

class TestPermutationInvariant:
    def test_same_set_no_add_or_remove(self):
        """Every input candidate appears exactly once in the output."""
        rules = {"by_trigger_id": {"C206": ["CLASS_1", "CLASS_0"]}}
        candidates = _choices(
            ("C1", "CLASS_1"), ("C0", "CLASS_0"), ("CG", "CAREGIVER_CONFIRMATION"),
        )
        result = apply_scan_ordering(candidates, None, "C206", rules)
        in_ids = sorted(c.candidate_id for c in candidates)
        out_ids = sorted(c.candidate_id for c in result.ordered_candidates)
        assert in_ids == out_ids
        assert len(result.ordered_candidates) == len(candidates)

    def test_candidate_objects_unchanged(self):
        """Ranking does not mutate prompt / action_hint / target_hint."""
        rules = {"by_trigger_id": {"C206": ["CLASS_0", "CLASS_1"]}}
        candidates = _choices(("C1", "CLASS_1"), ("C0", "CLASS_0"))
        # Add custom attrs to verify they survive untouched.
        candidates[0].prompt = "거실 조명을 켜드릴까요?"
        candidates[0].action_hint = "light_on"
        candidates[1].prompt = "긴급상황인가요?"
        result = apply_scan_ordering(candidates, None, "C206", rules)
        c0 = next(c for c in result.ordered_candidates if c.candidate_id == "C0")
        c1 = next(c for c in result.ordered_candidates if c.candidate_id == "C1")
        assert c0.prompt == "긴급상황인가요?"
        assert c1.prompt == "거실 조명을 켜드릴까요?"
        assert c1.action_hint == "light_on"


# ==================================================================
# Audit dict shape
# ==================================================================

class TestAuditDict:
    def test_audit_dict_has_required_fields(self):
        rules = {"by_trigger_id": {"C206": ["CLASS_1", "CLASS_0"]}}
        candidates = _choices(("C1", "CLASS_1"), ("C0", "CLASS_0"))
        result = apply_scan_ordering(candidates, None, "C206", rules)
        d = result.to_audit_dict()
        assert d["rule_source"] == (
            "policy_table.global_constraints.class2_scan_ordering_rules"
        )
        assert d["matched_bucket"] == "C206"
        assert d["final_order"] == ["C1", "C0"]
        assert d["applied_overrides"] == []

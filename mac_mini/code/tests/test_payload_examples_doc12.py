"""Schema-validation tests for the doc 12 example payloads (P0.2 of the
post-doc-12 consistency backfill plan).

Three example payloads were added under common/payloads/examples/ to
illustrate the four routing_metadata experiment-mode fields and the five
clarification_interaction optional fields. These tests verify each
example validates against its declared schema, which both:

  - documents the intended payload shape (acts as runnable schema usage),
  - guards against future schema or example drift (a schema change that
    breaks the example surfaces here, not in production).

Tests are intentionally focused on the THREE new examples only — full
validation of all 16 existing examples is out of scope for this PR.
"""

import json
import pathlib

import jsonschema
import pytest

from shared.asset_loader import AssetLoader


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_EXAMPLES_DIR = _REPO_ROOT / "common" / "payloads" / "examples"


def _load_example(name: str) -> dict:
    path = _EXAMPLES_DIR / name
    assert path.exists(), f"Missing example payload: {path}"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def loader():
    return AssetLoader()


def _strip_meta(payload: dict) -> dict:
    """Examples may carry a top-level `_example_purpose` doc field that
    isn't part of the canonical schema. Strip it before validation —
    the schema treats unknown top-level fields permissively but explicit
    underscore-prefixed metadata is documentation, not data."""
    return {k: v for k, v in payload.items() if not k.startswith("_")}


# ==================================================================
# policy_router_input — paper-eval all-modes example
# ==================================================================

class TestPolicyRouterInputPaperEvalExample:
    """Example illustrating all four routing_metadata experiment-mode
    fields populated together. Validates against
    policy_router_input_schema.json and double-checks each field carries
    a value in its enum."""

    def test_validates_against_schema(self, loader):
        payload = _strip_meta(_load_example(
            "policy_router_input_paper_eval_all_modes.json"
        ))
        schema = loader.load_schema("policy_router_input_schema.json")
        resolver = loader.make_schema_resolver()
        validator = jsonschema.Draft7Validator(schema, resolver=resolver)
        errors = list(validator.iter_errors(payload))
        assert not errors, "; ".join(e.message for e in errors)

    def test_carries_all_four_experiment_mode_fields(self):
        meta = _load_example(
            "policy_router_input_paper_eval_all_modes.json"
        )["routing_metadata"]
        # Each value must match its schema enum.
        assert meta["experiment_mode"] in ("direct_mapping", "rule_only", "llm_assisted")
        assert meta["class2_candidate_source_mode"] in ("static_only", "llm_assisted")
        assert meta["class2_scan_ordering_mode"] in ("source_order", "deterministic")
        assert meta["class2_input_mode"] in ("direct_select", "scanning")


# ==================================================================
# clarification_interaction — scanning yes-first example
# ==================================================================

class TestScanningYesFirstExample:
    """Scanning session that accepted option 0. Validates against
    clarification_interaction_schema.json and asserts the four scanning-
    related optional fields are populated coherently."""

    def test_validates_against_schema(self, loader):
        payload = _strip_meta(_load_example(
            "clarification_interaction_scanning_yes_first.json"
        ))
        schema = loader.load_schema("clarification_interaction_schema.json")
        resolver = loader.make_schema_resolver()
        validator = jsonschema.Draft7Validator(schema, resolver=resolver)
        errors = list(validator.iter_errors(payload))
        assert not errors, "; ".join(e.message for e in errors)

    def test_scan_history_first_entry_is_yes(self):
        rec = _load_example(
            "clarification_interaction_scanning_yes_first.json"
        )
        sh = rec["scan_history"]
        assert len(sh) == 1
        assert sh[0]["response"] == "yes"
        assert sh[0]["option_index"] == 0
        # The accepted candidate matches the selection_result.
        assert sh[0]["candidate_id"] == rec["selection_result"]["selected_candidate_id"]

    def test_scan_ordering_applied_final_order_matches_candidate_choices(self):
        """Audit field's final_order must list the candidate_ids in the
        same order they actually appear in candidate_choices (otherwise
        audit would lie about what got announced)."""
        rec = _load_example(
            "clarification_interaction_scanning_yes_first.json"
        )
        announced = [c["candidate_id"] for c in rec["candidate_choices"]]
        assert rec["scan_ordering_applied"]["final_order"] == announced

    def test_input_mode_is_scanning(self):
        rec = _load_example(
            "clarification_interaction_scanning_yes_first.json"
        )
        assert rec["input_mode"] == "scanning"


# ==================================================================
# clarification_interaction — multi-turn refinement example
# ==================================================================

class TestMultiTurnRefinementExample:
    """Multi-turn refinement session that completed via REFINE_BEDROOM.
    Validates against clarification_interaction_schema.json and asserts
    refinement_history captures the parent → child transition."""

    def test_validates_against_schema(self, loader):
        payload = _strip_meta(_load_example(
            "clarification_interaction_multi_turn_refinement.json"
        ))
        schema = loader.load_schema("clarification_interaction_schema.json")
        resolver = loader.make_schema_resolver()
        validator = jsonschema.Draft7Validator(schema, resolver=resolver)
        errors = list(validator.iter_errors(payload))
        assert not errors, "; ".join(e.message for e in errors)

    def test_refinement_history_records_parent_to_child(self):
        rec = _load_example(
            "clarification_interaction_multi_turn_refinement.json"
        )
        rh = rec["refinement_history"]
        assert len(rh) == 1, "Refinement is bounded to one turn (max)"
        entry = rh[0]
        assert entry["turn_index"] == 1
        assert entry["parent_candidate_id"] == "C1_LIGHTING_ASSISTANCE"
        # Child selection matches the terminal record's selection.
        assert entry["selected_candidate_id"] == rec["selection_result"]["selected_candidate_id"]

    def test_terminal_transition_is_class1(self):
        """Refinement target was a CLASS_1 lighting candidate, so the
        terminal transition_target must be CLASS_1 (with validator re-entry
        still required before any dispatch)."""
        rec = _load_example(
            "clarification_interaction_multi_turn_refinement.json"
        )
        assert rec["transition_target"] == "CLASS_1"

"""Deterministic ranking for scanning option order (doc 12 §14 Phase 1.5).

Pure permutation step that runs AFTER candidate generation and BEFORE
scanning announces option 0. Reorders the candidate list according to
policy_table.global_constraints.class2_scan_ordering_rules so that the
most-likely-correct option is asked first (which matters more in scanning
than in direct-select since wrong-first costs a full per-option cycle).

Boundaries (doc 12 §14.4):
- Pure permutation. Never adds, removes, or modifies candidates.
- action_hint, target_hint, prompt are untouched.
- Unknown candidate_transition_target values stable-sort to the END
  preserving source order.

Composes orthogonally with class2_candidate_source_mode (PR #101) so
paper-eval can isolate the ordering contribution from the generation
contribution.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScanOrderingResult:
    """Outcome of one ranking pass — used to populate the audit record's
    `scan_ordering_applied` field (clarification_interaction_schema)."""

    ordered_candidates: list           # list of ClarificationChoice (or candidate dicts)
    matched_bucket: str                # trigger_id whose by_trigger_id rule matched, or '_default'
    applied_overrides: list            # ['<if_field>=<if_equals>→<boost_first>', ...]
    rule_source: str = (
        "policy_table.global_constraints.class2_scan_ordering_rules"
    )

    def to_audit_dict(self) -> dict:
        """Schema-compliant dict for clarification_interaction_schema
        scan_ordering_applied field."""
        return {
            "rule_source": self.rule_source,
            "matched_bucket": self.matched_bucket,
            "applied_overrides": list(self.applied_overrides),
            "final_order": [
                _candidate_id(c) for c in self.ordered_candidates
            ],
        }


def _candidate_id(c) -> str:
    """Read candidate_id from either a ClarificationChoice or a dict."""
    if isinstance(c, dict):
        return c.get("candidate_id", "")
    return getattr(c, "candidate_id", "")


def _candidate_target(c) -> str:
    if isinstance(c, dict):
        return c.get("candidate_transition_target", "")
    return getattr(c, "candidate_transition_target", "") or ""


def _resolve_field(payload: Optional[dict], dotted_path: str):
    """Look up 'a.b.c' in a nested dict. Returns None if any segment missing."""
    if not payload:
        return None
    cur = payload
    for part in dotted_path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def apply_scan_ordering(
    candidates: list,
    pure_context_payload: Optional[dict],
    trigger_id: str,
    rules: dict,
) -> ScanOrderingResult:
    """Permute `candidates` according to `rules` (the policy field).

    Algorithm (doc 12 §14.4):
      1. Look up bucket = rules.by_trigger_id.get(trigger_id) or
         rules.by_trigger_id.get('_default') or [] (no preference).
      2. Apply context_overrides in order: each entry whose if_field
         equals if_equals in pure_context_payload moves boost_first to
         the front of the priority list (later overrides win the spot).
      3. Stable-sort candidates so those whose candidate_transition_target
         appears earlier in the priority list come first. Targets not in
         the list go to the END preserving source order.
    """
    by_trigger = (rules or {}).get("by_trigger_id", {}) or {}
    if trigger_id in by_trigger:
        priority = list(by_trigger[trigger_id])
        matched_bucket = trigger_id
    elif "_default" in by_trigger:
        priority = list(by_trigger["_default"])
        matched_bucket = "_default"
    else:
        priority = []
        matched_bucket = "_no_rules"

    # Apply context overrides in declared order; later overrides take
    # the front-of-list spot (stack semantics).
    applied_overrides: list = []
    for ov in (rules or {}).get("context_overrides", []) or []:
        if_field = ov.get("if_field")
        if_equals = ov.get("if_equals")
        boost_first = ov.get("boost_first")
        if if_field is None or boost_first is None:
            continue
        observed = _resolve_field(pure_context_payload, if_field)
        if observed != if_equals:
            continue
        # Move boost_first to front (or insert if not present).
        if boost_first in priority:
            priority.remove(boost_first)
        priority.insert(0, boost_first)
        applied_overrides.append(f"{if_field}={if_equals!r}→{boost_first}")

    # Stable sort by priority position. Targets not in priority sort
    # to the end (priority position = len(priority) + original_index
    # so they preserve source order among themselves).
    pos_map = {target: idx for idx, target in enumerate(priority)}

    def _key(item):
        i, candidate = item
        target = _candidate_target(candidate)
        return (pos_map.get(target, len(priority) + i), i)

    ordered = [c for _, c in sorted(enumerate(candidates), key=_key)]
    return ScanOrderingResult(
        ordered_candidates=ordered,
        matched_bucket=matched_bucket,
        applied_overrides=applied_overrides,
    )

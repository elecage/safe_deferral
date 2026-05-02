"""Adapter mapping physical button events to scanning manager calls (doc 12 Phase 3).

The Mac mini main loop receives button events on `safe_deferral/context/input`
as part of the standard policy-router input payload. When a Class 2 session
is active in scanning mode (`session.input_mode == 'scanning'`), the same
button events carry different semantics (doc 12 §8.2):

  single_click → 'yes' to session.current_option_index
  double_click → 'no' to session.current_option_index (explicit, faster than timeout)
  triple_hit   → emergency shortcut: accept the first CLASS_0-targeted candidate
  (other)      → ignore / block

This module is pure — no MQTT, no main-loop coupling. It lets Phase 4's
wiring be mechanical and lets unit tests exercise the whole mapping table
without standing up the pipeline.

Direct-select sessions are NOT handled here — the existing
main.py::_try_handle_as_user_selection logic continues to map button events
to candidate ids for that mode. The adapter is invoked only when the active
session has input_mode='scanning'.
"""

from dataclasses import dataclass
from typing import Optional


# Decision kinds produced by the adapter.
DECISION_SUBMIT = "submit"          # call submit_scan_response(option_index, response, ...)
DECISION_EMERGENCY = "emergency"    # accept the first CLASS_0-targeted candidate via submit_selection
DECISION_IGNORE = "ignore"          # block the event without acting


@dataclass
class ScanInputDecision:
    """Result of interpreting a button event for a scanning session."""

    kind: str                          # one of DECISION_*
    option_index: Optional[int] = None # set for kind='submit'
    response: Optional[str] = None     # 'yes' | 'no' for kind='submit'
    emergency_candidate_id: Optional[str] = None  # set for kind='emergency'
    reason: Optional[str] = None       # human-readable note for kind='ignore'


def interpret_button_event_for_scan(event_code: str, session) -> ScanInputDecision:
    """Map a button event to a scanning decision.

    The session is consulted only for `current_option_index` (for submit
    decisions) and `candidate_choices` (for the emergency shortcut). The
    function does not mutate the session.

    Returning DECISION_IGNORE means the Mac mini should treat the event as
    blocked (do not fall through to the normal pipeline) but should not call
    any scanning manager method.
    """
    if event_code == "single_click":
        return ScanInputDecision(
            kind=DECISION_SUBMIT,
            option_index=getattr(session, "current_option_index", 0),
            response="yes",
        )
    if event_code == "double_click":
        return ScanInputDecision(
            kind=DECISION_SUBMIT,
            option_index=getattr(session, "current_option_index", 0),
            response="no",
        )
    if event_code == "triple_hit":
        emergency_id = _first_class0_candidate_id(session)
        if emergency_id is not None:
            return ScanInputDecision(
                kind=DECISION_EMERGENCY,
                emergency_candidate_id=emergency_id,
            )
        # No CLASS_0 candidate in this session — treat as ignored emergency.
        return ScanInputDecision(
            kind=DECISION_IGNORE,
            reason="triple_hit_no_class0_candidate",
        )
    return ScanInputDecision(
        kind=DECISION_IGNORE,
        reason=f"unrecognised_event_code:{event_code!r}",
    )


def _first_class0_candidate_id(session) -> Optional[str]:
    """Return the candidate_id of the first CLASS_0-targeted candidate in
    the session, or None if there isn't one. Mirrors the direct-select
    triple_hit shortcut."""
    for c in getattr(session, "candidate_choices", []):
        if getattr(c, "candidate_transition_target", None) == "CLASS_0":
            return c.candidate_id
    return None

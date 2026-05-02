# Class 2 Multi-Turn Refinement Plan (doc 09 Phase 6 closure)

**Status:** initial design + Phase 6.0 implementation landed 2026-05-02. Phase 6.1 (Mac mini main.py wiring) deferred — see §7.
**Plan baseline:** `09_llm_driven_class2_candidate_generation_plan.md` Phase 6 punted to "a separate design discussion." This document is that discussion.

---

## 1. Purpose

Some Class 2 clarifications resolve in one user response (e.g. "Living-room light? 거실 / 침실"), but others naturally need *one more turn* — the first user reply narrows the intent, then a second yes/no question confirms a concrete action. Today the Class 2 manager hard-codes one user-phase + one caregiver-phase. This document defines a bounded, audit-traceable way to support **at most one refinement turn** between those two phases without weakening any safety boundary.

## 2. Scope

In scope (this round):
- A static, policy-bounded refinement template per parent candidate id.
- Manager API to issue a refinement turn after the user's first selection.
- Schema fields recording refinement turns in the audit record.
- Per-turn timeout, separate from the existing user / caregiver phase timeouts.
- Feature flag in policy so the path is opt-in.

Out of scope (deferred):
- LLM-generated refinement questions (a future Phase 7+ would let LocalLlmAdapter propose refinement candidates the same way it proposes initial candidates today).
- More than one refinement turn. Two turns is enough to demonstrate the design; deeper refinement adds new failure modes that should be measured first.
- Mac mini `_handle_class2()` rewrite. The single-turn flow stays in production until §7 lands.

## 3. Non-Negotiable Boundaries

- **No new authority surface.** Refinement candidates can only target paths the original candidate could have reached (`CLASS_1` low-risk lighting, `CAREGIVER_CONFIRMATION`, `SAFE_DEFERRAL`). They cannot escalate to `CLASS_0` and cannot expand the low-risk catalog.
- **Validator stays final.** The refined `(action_hint, target_hint)` still passes through the Deterministic Validator; the refinement does not produce execution authority.
- **Time-bounded.** Each refinement turn has its own bounded wait (`class2_refinement_turn_timeout_ms`, default same as `class2_clarification_timeout_ms`). After the turn budget, the session falls back to caregiver escalation just as it would for an unanswered first turn.
- **Feature flag.** `policy_table.global_constraints.class2_multi_turn_enabled` defaults to `false`. When false, `submit_selection` behaves exactly as today (returns a terminal `Class2Result`). When true, it may instead return a refinement session.

## 4. Data Model

### 4.1 Refinement template

```python
# class2_clarification_manager/refinement_templates.py
@dataclass
class RefinementTemplate:
    refinement_question: str          # ≤ policy max_prompt_length_chars
    refinement_choices: list[ClarificationChoice]   # 2 items typical, ≤ 4

# Keyed by *parent* candidate_id. Only candidates listed here can refine.
_REFINEMENT_TEMPLATES: dict[str, RefinementTemplate] = {
    "C1_LIGHTING_ASSISTANCE": RefinementTemplate(
        refinement_question="어느 방의 조명을 켜드릴까요?",
        refinement_choices=[
            ClarificationChoice(
                candidate_id="REFINE_LIVING_ROOM",
                prompt="거실",
                candidate_transition_target="CLASS_1",
                action_hint="light_on",
                target_hint="living_room_light",
            ),
            ClarificationChoice(
                candidate_id="REFINE_BEDROOM",
                prompt="침실",
                candidate_transition_target="CLASS_1",
                action_hint="light_on",
                target_hint="bedroom_light",
            ),
        ],
    ),
}
```

The table is intentionally tiny in this round. Adding entries requires the same review as adding to `_DEFAULT_CANDIDATES`.

### 4.2 Session extension

Two new optional attributes on `ClarificationSession` (set dynamically — same pattern as `candidate_source`):

- `is_refinement_turn: bool` — true when this session represents a refinement of an earlier session.
- `parent_clarification_id: Optional[str]` — id of the originating session.

### 4.3 Schema extension (`clarification_interaction_schema.json`)

Add an optional top-level field:

```jsonc
"refinement_history": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["turn_index", "parent_candidate_id",
                 "refinement_question", "selected_candidate_id"],
    "properties": {
      "turn_index": {"type": "integer", "minimum": 1},
      "parent_candidate_id": {"type": "string"},
      "refinement_question": {"type": "string"},
      "selected_candidate_id": {"type": "string"},
      "selection_source": {"type": "string"},
      "selection_timestamp_ms": {"type": "integer"}
    }
  },
  "description": "Optional. Each entry records one refinement turn that occurred between the initial user selection and the terminal Class 2 outcome (doc 11)."
}
```

Existing single-turn records validate unchanged because the field is optional.

## 5. Manager API

```python
class Class2ClarificationManager:
    def submit_selection(...) -> Class2Result:
        # Existing terminal API. Unchanged signature, unchanged behaviour
        # when class2_multi_turn_enabled is False.

    def submit_selection_or_refine(
        self, session, selected_candidate_id, selection_source, ...
    ) -> Union[Class2Result, ClarificationSession]:
        """When multi-turn is enabled AND the chosen candidate has a
        refinement template AND this session has no parent, returns a NEW
        ClarificationSession representing the refinement turn. Otherwise
        delegates to submit_selection() for terminal resolution.

        Refinement-turn sessions carry parent_clarification_id and
        is_refinement_turn=True so submit_selection on them produces a
        terminal Class2Result whose clarification_record.refinement_history
        captures the parent + this turn.
        """
```

This deliberately leaves `submit_selection` untouched so callers that don't opt-in are unaffected.

## 6. Time Budget

- Per refinement turn: `policy_table.global_constraints.class2_refinement_turn_timeout_ms`, default `15000` (matches `class2_clarification_timeout_ms`).
- Aggregate cap on user-side waits in one Class 2 session (Phase 1 + refinement turn) is therefore at most `2 × class2_clarification_timeout_ms`. This still fits inside the existing trial timeout (`_class2_user_phase_timeout_s` is per-phase, not per-turn — an earlier refactor in §7.1 will need to either bump the user budget or split it).

## 7. Phase split

This round (Phase 6.0):
- Schema field, policy fields, refinement template module, manager API, tests.
- Production single-turn path **unchanged** (feature flag off by default).
- TTS + Mac mini main loop NOT yet wired — covered by tests at the manager boundary.

Next round (Phase 6.1, deferred):
- TTS announcement helpers (`announce_class2_refinement`).
- Mac mini `_handle_class2()` rewrite to handle the union return type from `submit_selection_or_refine`.
- Telegram caregiver message format if a refinement times out (still falls back to caregiver, but the message should mention which turn timed out).
- Trial runner expectation extension (`expected_refinement_turns`).

Reason for the split: §6 implies a non-trivial change in the Mac mini's two-phase background waiter. Doing that change in the same PR as the schema + API would couple two reviews. Phase 6.0 lets the API + audit format stand independently while Phase 6.1 takes its time.

## 8. Test plan (Phase 6.0)

- `submit_selection_or_refine` returns `Class2Result` when feature flag is off.
- With flag on, picking a candidate WITH a template returns a `ClarificationSession` with `is_refinement_turn=True` and `parent_clarification_id` set.
- With flag on, picking a candidate WITHOUT a template still returns a terminal `Class2Result` (unchanged behaviour).
- Refinement-turn session can be resolved with `submit_selection` and produces a terminal `Class2Result` whose `clarification_record.refinement_history` has exactly one entry.
- Refinement-turn timeout produces a terminal escalation to caregiver with `refinement_history` reflecting the unanswered turn.
- Schema validation: records with and without `refinement_history` both validate.

## 9. Open questions for the maintainer

1. **Templates location** — keep them next to `_DEFAULT_CANDIDATES` in the manager module, or move both to a dedicated module? Recommend: leave alongside for this round; refactor when a third candidate-source mode appears.
2. **Refinement budget bump** — when 6.1 lands, do we want `class2_user_phase_timeout_s = 2 × class2_clarification_timeout_ms / 1000` automatically, or a separate `class2_user_phase_max_turns` knob? Recommend: latter, so the budget calculation stays explicit.
3. **Caregiver-side refinement** — if Phase 1 times out and we escalate, should the caregiver see the original prompt only, or the (intended) refinement question if there was one? Recommend: original prompt only — the refinement was a user-side disambiguation that didn't happen.

## 10. Source notes

- Existing structure: `09_llm_driven_class2_candidate_generation_plan.md` §6 Phase 6 deferral.
- Two-phase user/caregiver waiter: `mac_mini/code/main.py::_await_user_then_caregiver`.
- Existing schema: `common/schemas/clarification_interaction_schema.json`.
- Existing per-phase timeouts: PR #94 (P2.2 trial timeout decomposition), PR #95 (caregiver timeout policy promotion).

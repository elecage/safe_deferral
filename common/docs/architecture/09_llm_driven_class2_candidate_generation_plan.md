# LLM-Driven Class 2 Candidate Generation & Conversational Clarification Plan

## 1. Purpose

This document captures the design discussion held on 2026-05-01 about
generalizing the system beyond a finite, hand-authored scenario set toward
**LLM-driven contextual candidate generation** for Class 2 clarification, and
toward TTS prompts that adapt to current sensor / actuator / context state
rather than being read verbatim from a static lookup table.

The goal is to make the system scale gracefully as new sensor and actuator
nodes are added, **without violating any of the existing safety / authority
boundaries** (`02_safety_and_authority_boundaries.md`).

This is a planning document. Implementation lands incrementally under the
Phase plan in §6.

## 2. Design Discussion Summary

### 2.1 The vision

> "노드들이 많아지고 상황이 확장될 경우 시나리오를 무한정 늘릴 수는
> 없다. LLM이 현재까지의 센서·액추에이터·컨텍스트 노드의 상태를 바탕으로
> 사용자가 원하는 행위에 대해 추론하고 동작 추천을 하는 형태가 본래의
> 의도이다. TTS 인터랙션도 일률적이지 않게, LLM이 대화하며 불확실성을
> 해소하는 내용이 나와야 한다."

### 2.2 What is already aligned with the vision

- **`LocalLlmAdapter` already takes the full `pure_context_payload` and
  produces a candidate action.** As `context_schema.json` admits new device
  / environmental fields, the LLM receives them automatically. No code
  change is required to "see" new state — only to produce candidates that
  reference newly admissible action targets, which is gated by the catalog
  (see §4).
- **`Class2ClarificationManager.start_session()` already accepts
  `candidate_choices: Optional[list]`** as an override parameter. The
  current Pipeline simply does not supply it, so the manager always falls
  back to its static `_DEFAULT_CANDIDATES` table. The plumbing for
  LLM-supplied candidates is therefore already present at the manager
  boundary; only the producer is missing.
- **Scenarios under `integration/scenarios/` are *evaluation samples*,
  not the runtime's decision tree.** Adding nodes does not require adding
  scenarios in order for the runtime to function. Scenario count is bounded
  by paper-evaluation needs, not by runtime coverage.

### 2.3 What is NOT yet aligned with the vision

1. **Class 2 candidate generation is hardcoded.**
   `mac_mini/code/class2_clarification_manager/manager.py::_DEFAULT_CANDIDATES`
   lists a static {prompt, transition_target, action_hint, target_hint}
   tuple per `unresolved_reason` (8 reasons). When a new actuator node is
   added (e.g., a humidifier or an additional light), the candidate set
   shown to the user during clarification does not learn about it.
2. **TTS prompts are fixed strings.** `tts/speaker.py::announce_class2()`
   reads the candidate's `prompt` field, but that field comes from the
   static table above, so the announcement is the same Korean sentence
   regardless of context (e.g., "조명을 켤까요?" never changes to
   "어두워졌고 거실에 계시네요. 거실 조명 켜드릴까요?").
3. **No conversational uncertainty resolution.** Class 2 clarification
   collects a single bounded selection then exits. There is no notion of
   the LLM asking a refined follow-up when the first selection is still
   ambiguous (e.g., "둘 다 켜드릴까요, 거실만?").

## 3. Safety Boundary Reconciliation

The vision must not weaken any existing canonical boundary. Mapping the
vision components to boundaries:

| Vision component | Conflict with boundary? | Resolution |
|---|---|---|
| LLM recommends candidate from full state | None — already the role of `LocalLlmAdapter` (`02_safety_and_authority_boundaries.md` §4) | Continue. Candidate is guidance only. |
| LLM generates conversational TTS prompt text | Partial — variability vs accessibility for users with cognitive limits | **Bounded variability**: prompts must satisfy length / vocabulary / candidate-count caps from `policy_table.json` (see §5) |
| LLM proposes action targeting nodes outside the current low-risk catalog | None operationally — Validator rejects → safe_deferral or Class 2 | **Catalog stays human-governed.** LLM may propose, Validator gates. Catalog growth happens through `governance backend` review, not LLM choice. |
| LLM directly executes an action | **Hard violation** | Forbidden. No change. |
| LLM declares an emergency | **Hard violation** | Forbidden. Class 0 routing remains deterministic on `policy_table.json` triggers. |

### 3.1 The governance principle that keeps this safe

> The LLM may *suggest* anything the context warrants. The system *executes*
> only what the canonical low-risk catalog admits and the Deterministic
> Validator approves. Anything else routes to safe deferral or
> caregiver confirmation. The catalog is grown by humans through governance,
> not by the LLM choosing to expand its own authority.

This means: a new sensor added to `context_schema.json` is immediately
visible to LLM reasoning. A new actuator added to `low_risk_actions.json`
is immediately admissible for autonomous Class 1 execution. The two are
intentionally decoupled — perception scales freely, authority scales by
review.

## 4. The Catalog Growth Tradeoff

For a new actuator node to be autonomously controllable, it must enter
`common/policies/low_risk_actions.json`. Two stances:

**Stance A (current, conservative):** New actuators default to Class 2
caregiver confirmation until promoted into the catalog. LLM can recommend,
caregiver decides, audit logs the manual confirmation.

**Stance B (potential extension):** A "candidate-ready" intermediate tier
where new actuators can be Class 2-presented but not yet Class 1-executable,
with a defined promotion procedure (governance review → catalog edit →
deterministic admission).

This plan adopts **Stance A** (no architectural change required) and notes
Stance B as a future governance enhancement.

## 5. Bounded Variability Constraints

Conversational prompts must respect bounds. These belong in `policy_table.json`
under a new `class2_conversational_prompt_constraints` block (see §6 Phase 1):

| Constraint | Purpose | Suggested initial value |
|---|---|---|
| `max_prompt_length_chars` | Cognitive load cap for users with attention / cognitive limits | 80 (Korean) |
| `max_candidate_count` | Already exists as `class2_max_candidate_options` | unchanged (4) |
| `vocabulary_tier` | Restrict to plain-spoken Korean; no jargon | `plain_korean` |
| `must_include_target_action_in_prompt` | Audit / accessibility — the prompt must name the device + action | `true` |
| `forbidden_phrasings` | Block phrasings that imply autonomous emergency or doorlock authority | `["unlock", "emergency dispatch", ...]` |
| `prompt_must_be_question` | Require interrogative form so user knows a choice is expected | `true` |

A prompt-validation step in `LocalLlmAdapter` (or a new
`Class2CandidateGenerator`) rejects LLM output that violates these bounds
and falls back to the static template. This preserves UX consistency under
LLM failure and protects against prompt injection inflating verbosity or
authority claims.

## 6. Phased Implementation Plan

### Phase 0 — Documentation (this document) ✅

Capture the design discussion and the safety reconciliation. Land before
any code change.

### Phase 1 — `LocalLlmAdapter` Class 2 candidate generation mode

**Goal:** Produce ≤ N bounded candidate dicts that the manager can hand
straight to `start_session(candidate_choices=...)`.

**New API:**
```python
class LocalLlmAdapter:
    def generate_class2_candidates(
        self,
        pure_context_payload: dict,
        unresolved_reason: str,
        max_candidates: int,
        audit_correlation_id: str = "",
    ) -> Class2CandidateResult:
        """Return up to max_candidates bounded clarification candidates.

        Each candidate dict matches the schema accepted by
        Class2ClarificationManager._build_choices: {candidate_id, prompt,
        candidate_transition_target, action_hint, target_hint}.

        Bounded by class2_conversational_prompt_constraints from policy_table.
        Falls back to None on validation failure so the manager can use its
        static default candidates.
        """
```

**Invariants:**
- All `action_hint` values must reference actions in `low_risk_actions.json`
  (validator will reject otherwise; pre-validating here surfaces the issue
  earlier and lets us fall back gracefully).
- Each `prompt` validated against `class2_conversational_prompt_constraints`.
- LLM never produces `candidate_transition_target=CLASS_0` autonomously —
  emergency suggestion is always C3_EMERGENCY_HELP with explicit phrasing
  per a static template (LLM may decide *whether* to include it, never
  *invents* an emergency rationale).
- Output validated against a new `class2_candidate_set_schema.json`.

**Schema additions:**
- `common/schemas/class2_candidate_set_schema.json` — wraps the candidate
  list with bounded-variability metadata (prompt length, vocabulary tier,
  source = `llm_generated` | `default_fallback`).

### Phase 2 — `Class2ClarificationManager` LLM hook

**Goal:** When the manager starts a session, ask the LLM adapter for
candidates first; fall back to `_DEFAULT_CANDIDATES` only if the LLM
declines or fails.

**Change shape:**
```python
class Class2ClarificationManager:
    def __init__(self, asset_loader=None, llm_candidate_generator=None):
        ...
        self._llm = llm_candidate_generator  # Optional — None disables LLM mode

    def start_session(self, trigger_id, audit_correlation_id, ...,
                      pure_context_payload: Optional[dict] = None):
        ...
        if candidate_choices is None and self._llm is not None and pure_context_payload is not None:
            llm_result = self._llm.generate_class2_candidates(
                pure_context_payload, reason, self._max_candidates,
                audit_correlation_id,
            )
            if llm_result and llm_result.candidates:
                candidate_choices = llm_result.candidates
        # Existing fallback to _DEFAULT_CANDIDATES otherwise
```

**Pipeline wiring (`mac_mini/code/main.py`):**
- Pass `pure_context_payload` from `route_result` into `_handle_class2()` so
  the manager can forward it to the LLM generator.
- Keep `_DEFAULT_CANDIDATES` table as the safety net; never delete it.

**Audit:**
- The clarification record's `candidate_choices` already lists what was
  presented. Add a top-level `candidate_source` field
  (`llm_generated` | `default_fallback`) to `clarification_interaction_schema`
  so audit reviewers can distinguish LLM-driven sessions from fallback ones.

### Phase 3 — Policy and bounded-variability config

- Extend `common/policies/policy_table.json` with the
  `class2_conversational_prompt_constraints` block from §5.
- Update `common/schemas/policy_router_input_schema.json` if any new
  optional metadata is needed (probably none).
- Document the constraints in
  `common/docs/architecture/04_class2_clarification.md` §4 (LLM Role In
  Class 2) so the boundary is canonical.

### Phase 4 — TTS speaker uses LLM prompt text directly

`tts/speaker.py::announce_class2()` already reads `candidate.prompt`. Once
Phases 1-3 land, this becomes the conversational layer automatically — no
separate change. Add a regression test that the announced text equals the
candidate's prompt and that prompt length ≤ the policy cap.

### Phase 5 — Evaluation extensions (Package A)

Add metrics that measure LLM candidate quality without conflating with
execution authority:

- `llm_candidate_admissibility_rate` — fraction of LLM-proposed action_hints
  that are in `low_risk_actions.json` (catches LLM overreach).
- `llm_candidate_relevance_rate` — fraction of LLM sessions where the user's
  ultimate selection is among the LLM's proposed candidates (recall).
- `prompt_length_violation_rate` — fraction of LLM prompts that exceeded
  the policy cap (should be ≈ 0 with the validator falling back).

Optional Table for the paper: "Static vs LLM-driven Class 2 candidate
generation — ambiguity resolution rate, average TTS round-trips per
session, caregiver-escalation rate."

### Phase 6 — Multi-turn refinement (Phase 6.0 landed; see doc 11)

**Status update (2026-05-02):** Phase 6.0 (schema, policy, manager API,
static refinement template, audit record) landed via PR delivering doc
`11_class2_multi_turn_refinement_plan.md`. The production single-turn flow
remains unchanged (feature flag `class2_multi_turn_enabled` defaults to
`false`); Phase 6.1 (Mac mini main-loop wiring + TTS announcement helpers)
is deferred per doc 11 §7.

The vision mentions "LLM이 대화하고 불확실성을 해소하는 내용". A true
multi-turn clarification loop (e.g., "Living room? Yes / No → Brightness
level? High / Low") is **out of scope for this initial pass**. It requires:

- Multi-step session state in the manager.
- A mechanism to time-bound multi-turn (separate from the existing
  user-phase / caregiver-phase timeouts).
- Audit-record schema extension.

Recommended for a future round once Phases 1-5 are validated end-to-end.
The two-level structure (user phase ≤ 15s, caregiver phase ≤ 300s) already
provides a one-step refinement path; extending it is a separate design
discussion.

## 7. Out of Scope for This Plan

- Catalog growth automation (LLM proposing new low-risk actions). Stance A
  in §4 keeps this human-governed.
- Direct LLM authority over Class 0. `policy_table.json` emergency triggers
  remain deterministic.
- LLM-driven caregiver confirmation. Caregiver Telegram path is a separate
  governed channel, not LLM-driven.
- Removing the static `_DEFAULT_CANDIDATES` table. It remains as the
  fallback and as the contract that audit reviewers can read offline.

## 8. Tradeoffs

The single most important tradeoff is **conversational variability vs
predictability for accessibility-constrained users**. Variability that
helps a sighted, cognitively unimpaired user can confuse a user with
cognitive or attention limits. The bounded-variability constraints in §5
exist specifically to limit this risk. If usability evaluation shows
regressions, tighten the constraints (e.g., `prompt_must_match_template`
mode that forces LLM output into a short slot grammar).

## 9. Source Notes

This document captures the planning discussion of 2026-05-01 between the
maintainer and the AI assistant. The phased work begins with Phase 1
(`LocalLlmAdapter.generate_class2_candidates`) and Phase 2 (manager hook)
in the same change, since they are coupled at the API boundary.

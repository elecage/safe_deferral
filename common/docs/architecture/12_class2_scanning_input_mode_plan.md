# Class 2 Scanning Input Mode Plan

**Status:** design only (this PR). No code changes. Implementation phases land separately after maintainer alignment.
**Plan baseline:** Follow-up to the 2026-05-02 conversation that surfaced two accessibility gaps in the existing direct-select Class 2 interaction:
1. The TTS preamble announces "보호자 확인이 필요합니다" even when the candidate set is user-resolvable lighting (not caregiver-bound).
2. Users with severe motor or cognitive limitations may be unable to (a) hold an N-option menu in working memory or (b) execute multi-press selections within the per-phase budget.

This document defines the **scanning input mode** — a sequential yes/no presentation that addresses (2). It is intentionally separate from the trigger-aware preamble + state-aware lighting prompt fix (those are independent and proceed in parallel; see §10).

---

## 1. Purpose

Today, `Class2ClarificationManager` produces a candidate set of up to 4 options, and `tts/speaker.announce_class2()` reads them all in one utterance ("1번 X, 2번 Y, 3번 Z, 4번 W"). The user then selects one by index via `bounded_input_node`. This is a "direct selection" interaction model.

For the target user population (severe physical or speech limitations), direct selection is the wrong primitive:

- **Motor**: pressing a switch N times within an utterance window is hard or impossible for users with ALS, severe CP, or late-stage muscular dystrophy.
- **Cognitive**: holding "1 = light, 2 = caregiver, 3 = emergency, 4 = cancel" in working memory while waiting to act is cognitively expensive even for unimpaired users.

The AAC literature calls the alternative **scanning** — the system iterates over options one at a time, the user provides a single binary input (yes / no) per option, and the system advances on "no" or silence. The user's effective input alphabet shrinks to one bit per turn, dramatically lowering motor and cognitive load.

This plan adds scanning as an **opt-in interaction mode** alongside the existing direct-select mode, without removing direct-select (which remains correct for users who can handle it and saves time when the user is decisive).

## 2. Scope

In scope:
- New `class2_input_mode` policy field (`direct_select` | `scanning`, default `direct_select` — production behaviour unchanged).
- Scanning session state machine inside `Class2ClarificationManager`: tracks `current_option_index`, accepts `yes` / `no` per turn, advances on `no` or per-option silence, terminates on `yes` or exhaustion.
- Per-option time budget separate from the existing user / caregiver phase timeouts.
- New audit record fields capturing each per-option decision (rejection sequence, accepted index, total elapsed).
- TTS pattern for scanning (one option per utterance, with explicit `option_index` so the input layer can match responses).
- MQTT input contract for scanning: `bounded_input_node` payload extended to carry `{option_index, response}` so a misordered or stale response is detectable.
- Tests covering all yes/no/silence paths and audit record schema.

Out of scope:
- Replacing direct-select. Both modes coexist.
- Per-user mode profiles (which user gets which mode). Scanning is a global policy setting in this round; per-user routing is a future operations feature.
- Variable-rate scanning ("automatic scan" with adjustable dwell time per AAC literature). Each option uses the same per-option timeout; tunable by policy.
- "Inverse" scanning (user holds switch, releases on desired option). Out-of-scope for the current input nodes.
- Refinement-turn scanning (PR #102 multi-turn). When both flags are on, the refinement turn naturally uses the same scanning mode — no extra design needed; covered by tests.

## 3. Non-Negotiable Boundaries

- **No new authority surface.** Scanning changes presentation only. Same candidate set, same Deterministic Validator, same low-risk catalog. The `(action_hint, target_hint)` an accepted candidate produces is identical between modes.
- **Silence ≠ consent.** A silent turn means "no, advance"; final-option silence escalates to caregiver, never auto-confirms. This preserves the existing safety invariant that silence never executes an action.
- **Time-bounded.** Per-option budget × N options ≤ existing user-phase budget when feasible; if not, the per-option budget contracts so that total scanning time stays within `class2_user_phase_timeout_s` so the trial timeout (PR #94) doesn't need to grow.
- **Observable to audit.** Every per-option decision is recorded so paper analysis can compare scanning vs direct-select on completion rate, time-to-decision, and rejection-before-accept distribution.

## 4. Design Decisions (5 questions resolved)

### 4.1 Per-option time budget

**Decision:** policy field `class2_scan_per_option_timeout_ms`, default `8000` (8 s).

Rationale: with 4 options that yields 32 s worst case, just over the existing `class2_clarification_timeout_ms = 30000`. To keep the user phase budget honest, the manager's effective scanning user-phase budget is `min(per_option_timeout × len(candidates), class2_clarification_timeout_ms × 1.5)`. The 1.5× factor is a single new policy knob (`class2_scan_user_phase_extension`) to absorb the longer presentation time without restructuring trial timeouts. The runner's `_class2_user_phase_timeout_s` (PR #94) is computed accordingly.

Alternative considered: keep total budget at 30 s and shrink per-option to `30000 / N`. Rejected because per-option time should be predictable for the user, not vary with candidate count.

### 4.2 Silence semantics

**Decision:** silence on a non-final option = `no` (auto-advance to next option). Silence on the FINAL option = caregiver escalation.

Rationale: a target user who cannot answer a yes/no in 8 s for the first option is unlikely to answer the next, but auto-advance lets the most-likely option (which we present first) get a quick chance. If the user is unresponsive across all options, the existing caregiver path handles it — preserving the "silence never executes an action" invariant.

### 4.3 Back-up

**Decision:** no back-up in this round. If the user wants to revisit an earlier option, the second `class2_max_clarification_attempts` attempt restarts from option 1.

Rationale: back-up requires extra input vocabulary ("previous"), which conflicts with the single-bit input goal. The second attempt is the safety valve.

### 4.4 Mode flag

**Decision:** opt-in via `policy_table.global_constraints.class2_input_mode = "direct_select" | "scanning"`. Default `direct_select`. Production behaviour unchanged until a deployment explicitly switches.

Rationale: same pattern as PR #102's `class2_multi_turn_enabled`. Lets evaluation runs flip the mode without touching code; lets a deployment match the user profile.

Future extension: per-user mode override via a separate registry (`class2_input_mode_per_user`) — out of scope here, but the policy field should be read once per session so that future per-user lookup can override it cleanly.

### 4.5 MQTT input contract

**Decision:** scanning announces include an `option_index` (0-based). `bounded_input_node` publishes `{option_index, response: "yes" | "no"}`. The manager accepts only responses whose `option_index` matches the currently active option; mismatched responses are dropped with an audit note (avoids stale-button race conditions).

For backward compat: when `class2_input_mode = direct_select`, the existing `selected_candidate_id` payload remains the contract; scanning fields are only sent and read when scanning is active.

Schema additions (see §5).

## 5. Data Model

### 5.1 Policy fields

```jsonc
"global_constraints": {
  ...
  "_class2_input_mode_description": "Class 2 interaction model. 'direct_select' (default) presents all candidates in one TTS utterance and accepts a selected_candidate_id. 'scanning' presents one option at a time and accepts {option_index, response} per turn. Plan: 12_class2_scanning_input_mode_plan.md.",
  "class2_input_mode": "direct_select",
  "class2_scan_per_option_timeout_ms": 8000,
  "class2_scan_user_phase_extension": 1.5
}
```

`class2_scan_user_phase_extension` multiplies `class2_clarification_timeout_ms` to give the runner the scanning user-phase budget; `_class2_user_phase_timeout_s` becomes `class2_clarification_timeout_ms * (extension if scanning else 1) / 1000`.

### 5.2 ClarificationSession dynamic attrs

Same dynamic-attr pattern used by PR #87/#102:

- `input_mode: str` — `"direct_select"` or `"scanning"`.
- `current_option_index: int` — 0-based pointer into `candidate_choices`. Only relevant when scanning.
- `scan_history: list[dict]` — one entry per per-option turn (see §5.3).

### 5.3 Schema extension (`clarification_interaction_schema.json`)

Two optional top-level fields:

```jsonc
"input_mode": {
  "type": "string",
  "enum": ["direct_select", "scanning"],
  "description": "Interaction model used for this session. Single-mode legacy records may omit (treated as 'direct_select')."
},
"scan_history": {
  "type": "array",
  "description": "Per-option decisions during a scanning session. Empty for direct_select. Final entry's response='yes' identifies the accepted option (otherwise the session escalated). Plan: 12_class2_scanning_input_mode_plan.md.",
  "items": {
    "type": "object",
    "required": ["option_index", "candidate_id", "response", "elapsed_ms"],
    "properties": {
      "option_index": {"type": "integer", "minimum": 0},
      "candidate_id": {"type": "string"},
      "response": {"type": "string", "enum": ["yes", "no", "silence"]},
      "elapsed_ms": {"type": "integer", "minimum": 0,
        "description": "Time the system waited on this option before recording the response."},
      "input_source": {"type": "string"}
    }
  }
}
```

Existing single-mode records validate unchanged because both fields are optional.

## 6. Manager API

```python
class Class2ClarificationManager:
    def start_session(..., input_mode: Optional[str] = None) -> ClarificationSession:
        # input_mode None → use policy default. Sets session.input_mode and,
        # when scanning, session.current_option_index = 0 and session.scan_history = [].

    # Scanning-specific methods. Direct-select callers continue to use
    # submit_selection / submit_selection_or_refine (PR #102) unchanged.

    def submit_scan_response(
        self,
        session: ClarificationSession,
        option_index: int,
        response: str,                  # "yes" | "no"
        input_source: str,
        timestamp_ms: Optional[int] = None,
    ) -> Union[Class2Result, ClarificationSession]:
        """Resolve one scanning turn.

        - Drop responses where option_index != session.current_option_index
          (stale/race) — record the drop in scan_history with a 'dropped' note
          but do not advance.
        - response='yes' → terminal Class2Result for the current candidate.
        - response='no' on non-final option → return the same session with
          current_option_index advanced and a fresh per-option timeout.
        - response='no' on final option → terminal escalation to caregiver
          (mirrors handle_timeout, with scan_history populated).
        """

    def handle_scan_silence(
        self, session, timestamp_ms: Optional[int] = None,
    ) -> Union[Class2Result, ClarificationSession]:
        """Per-option timeout. Identical to submit_scan_response with
        response='silence' on the current option: advances or escalates."""
```

`submit_selection` and `submit_selection_or_refine` retain their existing semantics. The Mac mini main loop chooses the right submission API based on `session.input_mode`.

## 7. TTS Pattern

A new function in `tts/speaker.py`:

```python
def announce_class2_option(speaker, option_index, candidate, total_options):
    """Speak ONE candidate as a yes/no question.

    Format: '{n}/{N}. {candidate.prompt}'  (e.g. '1/3. 거실 조명을 켜드릴까요?')

    The leading 'n/N' is intentional — gives the user a position cue so
    they know how many remain (cognitive aid + accessibility).
    """
```

The session-start preamble for scanning mode is a single short utterance separate from the per-option utterances:

```python
def announce_class2_scanning_start(speaker, total_options):
    """'질문을 하나씩 드리겠습니다. 예 / 아니오로 답해 주세요.'"""
```

Phase 4 verbatim invariant (PR #97) extends naturally: each per-option utterance must contain `candidate.prompt` verbatim.

## 8. MQTT Input Contract

Existing `bounded_input_node` payload (direct-select):

```jsonc
{
  "selected_candidate_id": "C1_LIGHTING_ASSISTANCE",
  "audit_correlation_id": "..."
}
```

Scanning payload (additive — old direct-select payloads remain valid when input_mode=direct_select):

```jsonc
{
  "scan_response": {
    "option_index": 0,
    "response": "yes",
    "audit_correlation_id": "..."
  }
}
```

The two top-level keys (`selected_candidate_id` vs `scan_response`) are mutually exclusive; the manager rejects both-present payloads.

## 9. Phase Split

This document is design only (Phase 0). Implementation breaks into:

- **Phase 1** — Manager scanning session API + state machine + audit record + tests. Production unchanged because feature flag defaults off.
- **Phase 2** — TTS announcement helpers (`announce_class2_option`, `announce_class2_scanning_start`).
- **Phase 3** — MQTT input contract: `bounded_input_node` schema extension and Mac mini main-loop dispatch.
- **Phase 4** — Mac mini main-loop integration: choose direct vs scanning submission API based on `session.input_mode`. Per-option timeout management.
- **Phase 5** — Optional: scenario fixture variant for scanning-mode trials so paper evaluation can compare interaction modes (parallels PR #101's `class2_static_only` / `class2_llm_assisted` comparison conditions).

Phase 1 lands fully tested and audit-correct without any production behaviour change. Phases 2-4 land sequentially; each preserves the option to disable scanning by flipping the policy field.

## 10. Relationship to other in-flight work

- **TTS preamble adaptation** (separate PR) — needed regardless of scanning mode. With scanning active the preamble is replaced by `announce_class2_scanning_start`; with direct-select active the preamble must adapt to whether the candidate set is caregiver-bound. The two PRs are independent and can land in any order.
- **State-aware lighting prompt** (separate PR) — orthogonal to interaction mode. Whether the prompt says "켜드릴까요?" or "꺼드릴까요?" is decided at candidate-build time using `device_states`; both modes consume the same prompt.
- **PR #102 multi-turn refinement** — when both `class2_multi_turn_enabled` and `class2_input_mode = scanning` are true, a refinement turn opens a NEW scanning session over the refinement template's candidates. No additional API change required.
- **PR #101 LLM-vs-static comparison** — orthogonal. LLM-generated and static candidates both feed the same scanning loop.
- **PR #94 trial timeout decomposition** — `_class2_user_phase_timeout_s` formula extends to multiply by `class2_scan_user_phase_extension` when the runner submits a scanning trial. Runner needs to know which mode the trial uses (likely via a new `comparison_condition` value `scanning_input_mode` or by reading session metadata).

## 11. Test plan (Phase 1)

- start_session with `input_mode='scanning'` initialises `current_option_index=0`, `scan_history=[]`.
- `submit_scan_response(0, 'yes', ...)` returns terminal `Class2Result` for the first candidate; record carries `input_mode='scanning'` and a one-entry `scan_history`.
- `submit_scan_response(0, 'no', ...)` returns the same session with `current_option_index=1`; `scan_history` has one entry with `response='no'`.
- `submit_scan_response(N-1, 'no', ...)` (final option) returns terminal caregiver escalation; record carries the full no-sequence in `scan_history`.
- `handle_scan_silence` on the first option behaves like `response='silence'` and advances; same on final option escalates.
- Stale `submit_scan_response(option_index=0, ...)` while session is at `current_option_index=2` is dropped — `scan_history` records the drop, `current_option_index` unchanged.
- Schema validation: scanning records validate; direct_select records (with neither new field) still validate.
- Boundary: scanning never produces an `(action_hint, target_hint)` outside the canonical low-risk catalog (same invariant as PR #102 templates).
- Default policy (`class2_input_mode='direct_select'`) leaves all existing tests passing (production unchanged).

## 12. Open questions for future rounds

1. **Auto-restart on second attempt** — the second `class2_max_clarification_attempts` attempt under scanning today restarts from option 1. Should the second attempt instead start from the first option the user did NOT explicitly reject (skipping silenced options)? Defer until usability testing data.
2. **Variable per-option dwell** — should the per-option budget shrink as the user proceeds (to bias toward early options) or stay constant? Constant is simpler; revisit after measurement.
3. **Per-user mode override** — operations may want different modes per user. Add a per-user registry layered above the global policy field. Out of scope here; the API leaves room for it via the optional `input_mode=` parameter.
4. **Caregiver-side scanning** — caregiver Telegram remains direct-select (inline keyboard). Scanning is user-side only. Confirm this stays the case after Phase 4 lands.

## 13. Source notes

- AAC scanning literature: Beukelman & Mirenda, *Augmentative and Alternative Communication* (5th ed.), §5 "Selection Techniques".
- Existing direct-select interaction: `mac_mini/code/class2_clarification_manager/manager.py::submit_selection`, `mac_mini/code/tts/speaker.py::announce_class2`.
- Multi-turn precedent: `common/docs/architecture/11_class2_multi_turn_refinement_plan.md`.
- Trial timeout decomposition: PR #94, doc 10 §3.3 P2.2.
- Input contract: existing `bounded_input_node` payload in `mac_mini/code/main.py`.

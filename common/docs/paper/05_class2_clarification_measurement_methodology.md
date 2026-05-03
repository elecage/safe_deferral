# 05_class2_clarification_measurement_methodology.md

## Purpose

This document codifies the measurement methodology for the Class 2 clarification dialogue's contribution to perception-side scalability — a discussion that emerged during the 2026-05-03 paper-eval review and is intended to be reflected in the final paper. The methodology is described here at the conceptual level; the actual paper-grade verification will be performed on the proposed hardware (ESP32 / Mac mini / RPi 5 / optional STM32) in a separate session, not on the development M1 MacBook used for the local debug sweeps.

**Cross-references**:
- `01_paper_contributions.md §4 Contribution 1` and `§7.4` (LLM is not faster, perception-scalability framing)
- `02_safety_and_authority_boundaries.md` (Class 2 as a clarification/transition state, not a terminal escalation)
- `04_class2_clarification.md` (Class 2 architectural design)
- `07_scenarios_and_evaluation.md`, `required_experiments.md §5.8`
- `PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md` (build plan)

---

## 1. The methodology gap that this document closes

### 1.1 What the original extensibility matrix measured

The Axis A extensibility experiment (matrix_extensibility.json, v1 archived 2026-05-03; v2 with gemma4:e4b archived later in the same day) measures **single-shot LLM intent recovery** under three modes (`direct_mapping`, `rule_only`, `llm_assisted`) on the same novel-context input (single_click + living_room_light=on + bedroom_light=off + occupancy_detected=true + low illuminance).

For the LLM-assisted mode, the matrix's per-cell expected encodes "the LLM should recover the user's actuator intent within the catalog in one inference":

```
expected_route_class:    CLASS_1
expected_validation:     approved
```

A trial passes only when the LLM's first inference produces a catalog action and the validator approves it.

### 1.2 What this misses

The Class 2 architecture in this system is **not a terminal caregiver escalation**. It is a clarification / transition state for insufficient context, unresolved ambiguity, and sensitive paths (per `02_safety_and_authority_boundaries.md` and `04_class2_clarification.md`). When the LLM legitimately defers, the design intent is:

```
LLM Class 1 → safe_deferral
   ↓
CLASS_2 escalation (C207 insufficient_context)
   ↓
Class 2 candidate set generated (LLM-driven, with static fallback)
   ↓
User responds — either via direct-select selection or AAC scanning
   ↓
System narrows the user's intent to a bounded action OR confirms caregiver
   ↓
Class 1 dispatch (when the user accepts a CLASS_1-target candidate) OR
   safe deferral / caregiver confirmation
```

**The single-shot matrix measures only the first arrow.** Every trial whose LLM path defers — and many will, because gemma4:e4b is conservative under genuine ambiguity — collapses into the matrix's `class2_safe_deferral` outcome bucket because the simulated user (a context_node that publishes a single context payload and then idles) never responds to the candidate set.

This makes it appear that the system's Class 2 clarification capability is silent. It is not — the LLM-driven candidate generation runs, the system is *ready* to accept a user response, the static fallback path is intact. **What is missing is a measurement that exercises the response.**

### 1.3 Why this matters for the paper's strongest framing

Section §7.4 of `01_paper_contributions.md` correctly says the paper must not claim the LLM is faster than rule-based recovery. The paper's stronger value proposition is:

> The LLM extends the perception layer of an assistive smart home to handle input configurations the deterministic policy was not enumerated for.

But "perception" in this assistive context is rarely a single inference. A user with severe motor or speech limitations interacting through a single-button input, an AAC scanner, or a caregiver inline-keyboard does not produce ambiguity-free signals in one round. **Perception scalability for this user population is a multi-turn property** — the LLM proposes; the user (or a caregiver, on sensitive paths) constrains; the system narrows; eventually a bounded action fires or the system safely defers.

A paper that measures only single-shot recovery underrepresents this contribution by exactly the amount the clarification dialogue would have recovered.

---

## 2. The measurement that closes the gap

### 2.1 Strict pass vs. soft outcome match

To represent the multi-turn nature of perception scalability without losing the strict routing-fidelity verdict, this work introduces **two complementary metrics** at every cell:

- **`pass_rate`** — strict: the trial's `observed_route_class` matches the cell's `expected_route_class`. This metric measures whether the system's *routing decision path* matches the design intent of that mode.
- **`outcome_match_rate`** — soft: the trial reaches the action prescribed by the cell's `expected_validation`, regardless of which route it took.
  - For `expected_validation == "approved"`, the trial outcome-matches when its final action is `light_on` or `light_off`.
  - For `expected_validation == "safe_deferral"`, the trial outcome-matches when its final action is `none` or `safe_deferral`.

A cell where `pass_rate < outcome_match_rate` is a system that consistently reaches design intent through a path the matrix did not strictly anticipate. **For an LLM_ASSISTED cell, this gap is exactly the recovery rate of the Class 2 clarification dialogue** — the trials whose LLM deferred and whose user (in this case a scripted simulator; on hardware, a real user) provided the missing signal.

### 2.2 Per-trial trajectory distribution

Strict and soft rates collapse the per-trial path into one number each. For diagnostic purposes — and for the paper's qualitative discussion of *how* clarification works — each cell also reports the distribution over trajectory buckets:

```
class1_direct          first observation is CLASS_1; LLM recovered in one inference
class2_to_class1       LLM deferred; CLASS_2 dialogue resolved into a CLASS_1 dispatch
class2_to_class0       CLASS_2 dialogue confirmed an emergency
class2_safe_deferral   CLASS_2 dialogue did not resolve; system held safe deferral
class2_unresolved      CLASS_2 escalation but no terminal class2 snapshot recorded
class0_direct          emergency routed directly from input
timeout                trial budget expired with no terminal observation
no_observation         completed without any matching observation
```

The paper's headline quantitative claim becomes: *the fraction of trials reaching design-intent action is the sum of `class1_direct` (LLM single-shot recovery) and `class2_to_class1` (clarification recovery), and the latter is the load-bearing evidence for the multi-turn perception claim.*

### 2.3 User-response simulation as a deterministic proxy

The paper-grade measurement requires real users on the proposed hardware. For development and continuous-integration measurement, the matrix carries a `_user_response_script` per cell that the runner replays as a deterministic simulated reaction. The available modes correspond to the interaction patterns the system actually supports:

- `no_response` — baseline. The user does not respond. The system's caregiver fallback path is exercised.
- `first_candidate_accept` — direct-select interaction. The user accepts whatever the LLM proposed first.
- `first_candidate_then_yes` and `scan_until_yes` — AAC scanning interaction (deferred to a follow-up build PR but planned within this methodology). The user issues `yes` at a configured option index, with `no` for prior options.

These are deterministic so the measurement is reproducible against a fixed code revision. The variance comes from the LLM (Class 1 candidate + Class 2 candidate-set generation), not from the user. This is by design — the paper claims about LLM perception, not about user variability.

### 2.4 Why deterministic scripts are not a research shortcut

A reviewer might ask whether scripting the user trivially inflates clarification recovery. The methodology guards against this by:

1. Comparing matched cells (NO_RESPONSE baseline vs FIRST_CANDIDATE_ACCEPT) on the same scenario, fixture, and LLM. Any pass_rate / match_rate gap between cells is attributable to the user response, not to other variables.
2. Running the scripts uniformly across all trials of a cell — the LLM's own variability is not selectively rewarded.
3. Anchoring the script semantics to interaction patterns the system architecturally supports (direct-select single_click, AAC yes/no scanning), not to bespoke per-trial favorable inputs.

The clarification recovery rate measured under deterministic scripts is therefore an **upper bound** on what real users would achieve when the candidate set's first option happens to align with their intent (or, for scanning, when their `yes` falls within a small number of steps). The paper-grade lower bound comes from the proposed-hardware sessions described in §3.

---

## 3. Hardware-grade verification (planned, separate work-stream)

The conceptual methodology and the local-software measurement infrastructure are settled in this codebase as of the 2026-05-03 plan + build PRs. The actual paper-grade numbers — the ones that should appear in `01_paper_contributions §4` and §7.4 — are intentionally **not** produced from the M1-MacBook-with-gemma4:e4b debug sweeps. The development environment serves to:

- exercise every code path,
- shake out runner / observation / trial-store fidelity bugs,
- confirm the dashboard surfaces the intended metrics,
- produce illustrative number ranges,

and is not the source of the paper's headline claims.

The paper-grade verification will run on the proposed hardware:

- **Mac mini** as the safety-critical operational edge hub (Policy Router, Deterministic Validator, LLM adapter, audit, caregiver notification)
- **Raspberry Pi 5** as the experiment-side support host (dashboard, fault injection, virtual nodes, result export)
- **ESP32 nodes** for physical bounded input, environmental context, lighting actuators
- **Optional STM32** for out-of-band latency measurement
- A **real user population** for the clarification-rate claims, replacing the deterministic `_user_response_script`

The hardware run will reuse the same matrix structure — the four cells described in §2 of `PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md` — but with the user-response script replaced by genuine human input. Outcome metrics (pass_rate, outcome_match_rate, outcome_path_distribution) keep their definitions; only the input source changes.

This separation is itself a paper-honest choice: the development environment cannot make load-bearing claims about user interaction outcomes, because those outcomes depend on the population the system serves.

---

## 4. What this methodology enables the paper to claim, and what it does not

### 4.1 What it enables (after hardware run)

- A quantitative split of LLM perception into "single-inference recovery" and "multi-turn clarification recovery", reported per scenario axis.
- A direct measurement of the Class 2 clarification dialogue's marginal contribution to outcome match rate, by comparing `EXT_A_LLM_DEFER_NO_RESPONSE` (caregiver fallback baseline) with `EXT_A_LLM_DEFER_FIRST_CANDIDATE_ACCEPT` (one-step user accept) and the scanning cells.
- A defensible reframing of `01_paper_contributions §7.4` from "the LLM is conservative under genuine ambiguity" (a one-sided framing) to "the LLM is conservative under genuine ambiguity *and* the system's Class 2 dialogue recovers a measurable fraction of the deferred intent" (the two-sided contribution).

### 4.2 What it does not enable

- It does not make the LLM faster than rule-based recovery (`§7.4` still holds).
- It does not extend autonomous Class 1 authority to new actuators (`§4 Contribution 2` still holds — the actuator catalog remains the only authority surface).
- It does not eliminate caregiver escalation for sensitive paths (`§4 Contribution 3` still holds — Class 2 dialogue narrows to the catalog *or* to caregiver confirmation).
- It does not produce the headline numbers from the development environment. Numbers reported as paper-grade come from the hardware run.

---

## 5. Measurement protocol checklist (for the hardware session)

The protocol below is the operator runbook for the paper-grade measurement. The development sessions are fixtures that confirm the protocol's mechanics; the protocol itself is what the paper documents.

1. **Hardware**: Mac mini + Raspberry Pi 5 + ESP32 input/actuator nodes per `06_deployment_and_scripts.md`. Optional STM32 for out-of-band timing.
2. **LLM model**: a hardware-deployable local model (gemma4:e4b confirmed working on M1 development; the hardware session may use the same or any alternative whose Korean output quality is documented).
3. **`llm_request_timeout_ms` policy bump**: per the matrix's `_required_operator_policy_changes`, set the canonical timeout to a value that accommodates the chosen model's inference latency. Restore after.
4. **Matrix**: `matrix_extensibility_v3_clarification.json` with cells expanded to include scanning script modes once the build PR for those modes lands.
5. **User population**: real participants, ideally including AAC users where ethically and practically feasible. The participants exercise the scripted mode the cell requires (direct-select accept-first, scanning accept-first, scanning accept-second, etc.).
6. **Per-cell sample size**: paper-grade requires at least n=30 per cell for descriptive statistics; n=100 if hypothesis testing is intended. The development debug-5 sample is for plumbing verification only.
7. **Reporting**: per cell — pass_rate, outcome_match_rate, outcome_path_distribution, final_action_distribution, latency p50/p95. Cross-cell — the gap between baseline and clarification cells, expressed as the recovery rate attributable to the dialogue.

---

## 6. Cross-reference index

| Document | Section | Relation |
|---|---|---|
| `01_paper_contributions.md` | §4 Contribution 1 | This methodology is the measurement that supports the perception-scalability claim. |
| `01_paper_contributions.md` | §7.4 | This methodology fills the second half of the framing § §7.4 already documents. |
| `02_safety_and_authority_boundaries.md` | Class 2 as transition state | The methodology operationalises the architectural claim. |
| `04_class2_clarification.md` | Class 2 candidate generation, multi-turn refinement, scanning | The cells in §2 mirror the architectural mechanisms documented here. |
| `07_scenarios_and_evaluation.md` | Per-cell expected encoding | The strict pass / soft match split formalises what the per-cell expected really measures. |
| `required_experiments.md` | §5.8 Extensibility | The v3 matrix is the multi-turn extension of the v1/v2 single-shot extensibility experiment. |
| `PLAN_2026-05-03_CLASS2_CLARIFICATION_MEASUREMENT.md` | build plan | Documents the runner / matrix changes that make this methodology executable. |

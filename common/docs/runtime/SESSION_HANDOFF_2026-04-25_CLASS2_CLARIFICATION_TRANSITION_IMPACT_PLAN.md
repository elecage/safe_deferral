# SESSION_HANDOFF_2026-04-25_CLASS2_CLARIFICATION_TRANSITION_IMPACT_PLAN.md

Date: 2026-04-25
Scope: Class 2 insufficient-context scenario, architecture wording, scenario docs, policy/schema-facing documentation, integration fixtures, and scenario verification utilities
Status: Impact plan only. No implementation changes in this plan document.

## 1. Purpose

This document records the file impact list for redefining Class 2 from a mostly terminal insufficient-context escalation path into a clarification / interaction / transition state.

The intended interpretation is:

```text
Class 2 insufficient context
→ clarification interaction
→ user/caregiver confirmation
→ Class 1 bounded assistance

Class 2 insufficient context
→ clarification interaction
→ emergency confirmation or emergency evidence
→ Class 0 emergency

Class 2 insufficient context
→ no response or still ambiguous
→ safe deferral or caregiver confirmation
```

This document is only an impact plan. It should be used before editing architecture, scenario, fixture, and verifier files.

## 2. Core design decision to preserve

Class 2 should not be described as a simple final failure or terminal hold state.

Preferred wording:

```text
Class 2 is a clarification and transition state used when the system cannot safely determine the user's intent from the available context. In this state, the system may use an LLM guidance layer to generate candidate choices for user or caregiver confirmation. After confirmation, the flow may transition to Class 1 bounded assistance, Class 0 emergency handling, or remain in safe deferral / caregiver confirmation if ambiguity persists.
```

LLM boundary:

```text
The LLM may generate candidate choices and user-facing clarification prompts.
The LLM must not independently make the final class decision, authorize actuation, or trigger emergency handling without confirmation or deterministic evidence.
```

## 3. Files likely requiring updates

### 3.1 Architecture documents

These files should be reviewed and likely updated first because they define the system-level interpretation.

| File | Expected update |
|---|---|
| `common/docs/architecture/14_system_components_outline_v2.md` | Add or clarify `Class 2 Clarification Manager` as a Mac mini Edge Hub internal logical module. Clarify that Class 2 is a clarification / transition state rather than a terminal state. |
| `common/docs/architecture/15_interface_matrix.md` | Add Class 2 interaction interfaces: candidate prompt output, candidate selection input, timeout/no-response path, caregiver confirmation path, and re-routing result. |
| `common/docs/architecture/16_system_architecture_figure.md` | Add textual figure guidance for Class 2 clarification loop and transition arrows to Class 0 / Class 1 / safe deferral. |
| `common/docs/architecture/17_payload_contract_and_registry.md` | Add payload expectations for clarification prompts, candidate lists, user selections, caregiver confirmation, and re-routing / transition outcomes if not already represented. |
| `common/docs/architecture/18_required_experiments.md` | Add or refine experiments for Class 2 clarification: candidate generation, candidate selection, transition to Class 1, transition to Class 0, timeout/safe deferral. |
| `common/docs/architecture/19_integration_verification.md` | Add verification criteria for Class 2 transition behavior and audit traceability. |
| `common/docs/architecture/20_mqtt_payload_governance.md` | Clarify whether new or existing MQTT topics/payloads are used for candidate presentation and selection. |

### 3.2 Paper scenario documents

These user-story documents should be kept consistent with the new Class 2 transition interpretation.

| File | Expected update |
|---|---|
| `common/docs/paper/scenarios/class2_insufficient_context_scenario_user_story.md` | Create or update as the primary user-facing Class 2 story: insufficient context → LLM candidate suggestions → user/caregiver confirmation → transition to Class 1 or Class 0 or safe deferral. |
| `common/docs/paper/scenarios/class1_baseline_scenario_user_story.md` | Optionally add one sentence noting Class 1 may also be reached after Class 2 clarification confirms a low-risk assistance request. |
| `common/docs/paper/scenarios/class0_e002_scenario_user_story.md` | Optionally add one sentence noting Class 0 may also be reached if clarification reveals emergency intent or repeated emergency input. |
| `common/docs/paper/scenarios/class0_e005_scenario_user_story.md` | Optionally add one sentence noting Class 0 may also be reached if Class 2 clarification reveals fall/emergency status. |
| `common/docs/paper/scenarios/baseline_scenario_user_story.md` | Optional cross-reference only; no mandatory change unless the baseline story should distinguish baseline Class 1 direct path from Class 2-to-Class 1 transition path. |

### 3.3 Scenario docs and manifest rules

These files define scenario semantics and should not lag behind the new interpretation.

| File | Expected update |
|---|---|
| `integration/scenarios/README.md` | Update Class 2 explanation to clarification / transition state. |
| `integration/scenarios/scenario_review_guide.md` | Add review checks for LLM candidate generation, user/caregiver confirmation, and transition outcomes. |
| `integration/scenarios/scenario_manifest_rules.md` | Add recommended fields for Class 2 transition scenarios, such as candidate fixtures, selection fixture, transition target, and timeout behavior. |
| `integration/scenarios/scenario_manifest_schema.json` | Add optional properties for clarification candidates, transition targets, and interaction results if formalized in skeleton JSON. |

### 3.4 Scenario skeleton JSON files

These files should be updated only after deciding the exact field structure.

| File | Expected update |
|---|---|
| `integration/scenarios/class2_insufficient_context_scenario_skeleton.json` | Change expected interpretation from simple Class 2 escalation to clarification interaction followed by possible transition outcomes. Add candidate generation / selection steps if appropriate. |
| `integration/scenarios/class1_baseline_scenario_skeleton.json` | Optional: clarify direct Class 1 path remains separate from Class 2-to-Class 1 transition. |
| `integration/scenarios/class0_e002_scenario_skeleton.json` | Optional: clarify emergency input can be direct or derived after clarification if the user confirms urgent help. |
| `integration/scenarios/class0_e005_scenario_skeleton.json` | Optional: clarify fall emergency can be direct sensor evidence or confirmed during clarification. |
| `integration/scenarios/baseline_scenario_skeleton.json` | Optional: no major change expected unless baseline template should mention transition tests. |

### 3.5 Integration test fixtures

Class 2 will likely need new fixtures rather than reusing only `expected_routing_class2.json`.

| File | Expected update |
|---|---|
| `integration/tests/data/sample_policy_router_input_class2_insufficient_context.json` | Keep as initial insufficient-context input fixture. Possibly add metadata indicating clarification is expected. |
| `integration/tests/data/expected_routing_class2.json` | Update or split into an initial Class 2 clarification expected output. |
| `integration/tests/data/expected_class2_candidate_prompt.json` | New candidate-prompt expected fixture may be needed. |
| `integration/tests/data/sample_class2_user_selection_class1.json` | New user-selection fixture for Class 2 → Class 1 transition may be needed. |
| `integration/tests/data/sample_class2_user_selection_class0.json` | New user-selection fixture for Class 2 → Class 0 transition may be needed. |
| `integration/tests/data/expected_class2_transition_class1.json` | New expected transition fixture may be needed. |
| `integration/tests/data/expected_class2_transition_class0.json` | New expected transition fixture may be needed. |
| `integration/tests/data/expected_class2_timeout_safe_deferral.json` | New timeout/no-response fixture may be needed. |

### 3.6 Scenario verification utilities

The verifiers need review because current Class 2 checks may assume a terminal escalation behavior.

| File | Expected update |
|---|---|
| `integration/scenarios/verify_scenario_manifest.py` | Allow Class 2 clarification steps and transition target declarations. |
| `integration/scenarios/verify_scenario_topic_alignment.py` | Confirm candidate prompt / selection topics if new topics are added; otherwise ensure existing context/audit topics are sufficient. |
| `integration/scenarios/verify_scenario_fixture_refs.py` | No major change expected unless new fixture fields are added outside `payload_fixture` / `expected_fixture`. |
| `integration/scenarios/verify_scenario_policy_schema_alignment.py` | Add checks that LLM guidance may generate candidates but does not authorize direct execution; verify transitions only occur after user/caregiver confirmation or deterministic evidence. |

### 3.7 Runtime / integration tests

These files should be reviewed after fixture/schema changes are finalized.

| File | Expected update |
|---|---|
| `integration/tests/test_integration_scenarios.py` | Add or update tests for Class 2 candidate prompt, user selection, transition to Class 1, transition to Class 0, and timeout/safe deferral. |
| `integration/tests/integration_adapter.py` | Add support for multi-step Class 2 interaction if the adapter currently assumes single-input / single-expected-output behavior. |

### 3.8 MQTT / payload registry files

Only update these if the existing topics/payloads are insufficient for candidate prompts and selections.

| File | Expected update |
|---|---|
| `common/mqtt/topic_registry_v1_0_0.json` | Add topics only if Class 2 clarification needs explicit prompt/response topics beyond existing context, audit, notification, or command topics. |
| `common/schemas/context_schema_v1_0_0_FROZEN.json` | Avoid editing frozen schema unless a deliberate versioned schema update is planned. Prefer new additive schema assets if needed. |
| `common/schemas/*` | Add new non-frozen / versioned schema for clarification candidate payloads if needed. |
| `common/policies/policy_table_v1_1_2_FROZEN.json` | Avoid editing frozen policy table. Add versioned policy docs or scenario-level transition notes if needed. |

### 3.9 Runtime handoff index

| File | Expected update |
|---|---|
| `common/docs/runtime/SESSION_HANDOFF.md` | Add this impact plan near the top of the read order if the Class 2 clarification transition work proceeds. |
| `common/docs/runtime/SESSION_HANDOFF_2026-04-25_SCENARIO_ALIGNMENT_UPDATE.md` | Add an update note or superseding addendum if Class 2 semantics change after this plan. Prefer a new dated addendum rather than rewriting history. |

## 4. Suggested implementation phases

### Phase C2-1 — Architecture wording alignment

Update architecture docs first:

- `14_system_components_outline_v2.md`
- `15_interface_matrix.md`
- `16_system_architecture_figure.md`
- `17_payload_contract_and_registry.md`

Goal: define Class 2 clarification and transition semantics without changing runtime behavior yet.

### Phase C2-2 — Scenario docs and paper story alignment

Update scenario guidance and paper scenario docs:

- `integration/scenarios/README.md`
- `integration/scenarios/scenario_review_guide.md`
- `integration/scenarios/scenario_manifest_rules.md`
- `common/docs/paper/scenarios/class2_insufficient_context_scenario_user_story.md`

Goal: make the expected user interaction clear.

### Phase C2-3 — Skeleton and fixture expansion

Update:

- `integration/scenarios/class2_insufficient_context_scenario_skeleton.json`
- related fixture files under `integration/tests/data/`

Goal: represent multi-step clarification, candidate prompt, selection, and transition outcomes.

### Phase C2-4 — Verifier and integration test update

Update:

- scenario verifier scripts
- `integration/tests/test_integration_scenarios.py`
- `integration/tests/integration_adapter.py`

Goal: ensure static and integration validation can handle multi-step Class 2 flows.

### Phase C2-5 — Handoff completion update

Add a completion addendum and update `SESSION_HANDOFF.md` read order after changes are implemented.

## 5. Open design questions before editing implementation files

1. Should Class 2 candidate prompt / user selection use existing MQTT topics or new explicit topics?
2. Should candidate lists be represented as fixtures under `integration/tests/data/` or embedded in scenario skeleton steps?
3. Should Class 2 → Class 0 transition require explicit user emergency confirmation, sensor evidence, triple-hit input, or any of these?
4. Should no-response timeout default to caregiver confirmation or safe deferral?
5. Should `LLM guidance generation` remain `policy_constrained_only` in the skeleton expected outcome, or should it be modeled as candidate generation with a clearer field name?
6. Should a new `Class 2 Clarification Manager` be represented as a named Mac mini Edge Hub subcomponent in figures and architecture docs?

## 6. Current recommendation

Proceed with documentation and scenario-level updates first. Avoid changing frozen policy/schema files unless a deliberate versioned policy/schema update is planned.

Recommended near-term target:

```text
Class 2 insufficient-context scenario should become a multi-step clarification scenario:
1. Initial ambiguous input is routed to Class 2.
2. LLM Guidance Layer generates bounded candidate choices.
3. TTS/Display presents choices to the user.
4. User/caregiver confirmation is collected through bounded input, voice input, or caregiver confirmation.
5. Confirmed low-risk request transitions to Class 1.
6. Confirmed emergency or new emergency evidence transitions to Class 0.
7. No response or persistent ambiguity transitions to safe deferral / caregiver confirmation.
8. All steps are audit logged.
```

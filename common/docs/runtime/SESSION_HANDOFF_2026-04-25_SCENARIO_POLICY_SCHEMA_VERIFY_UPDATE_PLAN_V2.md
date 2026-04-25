# SESSION_HANDOFF_2026-04-25_SCENARIO_POLICY_SCHEMA_VERIFY_UPDATE_PLAN_V2.md

Date: 2026-04-25
Scope: Scenario semantic update, Class 2 clarification/transition state, frozen baseline impact audit, architecture/policy/schema/scenario/verifier/test alignment
Status: Plan only. No implementation changes are made by this document.

## 1. Core change

The main semantic update is:

```text
Class 2 is not a terminal failure/hold state.
Class 2 is a clarification/transition state used when available context is insufficient or ambiguous.
The system presents bounded candidate choices, collects user/caregiver confirmation or deterministic evidence, and then transitions to Class 1, Class 0, or Safe Deferral / Caregiver Confirmation.
```

Frozen baseline handling is also clarified:

```text
Do not bypass frozen files by adding separate documents only.
If a frozen file remains the active source of truth and conflicts with the Class 2 clarification/transition semantics, update it directly or create a new frozen version and migrate all references to the new version.
```

---

## 2. Phase 0 — Active Frozen Baseline Impact Audit

### Purpose

Identify which frozen policy, schema, and registry files are actually active sources of truth, and determine whether the new Class 2 clarification/transition semantics conflict with them.

### Audit targets

| File / area | What to check | Decision criterion |
|---|---|---|
| `common/policies/policy_table_v1_1_2_FROZEN.json` | Whether verifier/test/runtime directly references it | If active source of truth and conflicting, update directly or create a new version |
| `common/schemas/context_schema_v1_0_0_FROZEN.json` | Whether Class 2 candidate/selection/transition payloads must be represented in the context schema | If clarification can be separated from context, keep context schema stable |
| `common/mqtt/topic_registry_v1_0_0.json` | Whether explicit clarification prompt/selection/result topics are required | If existing topics are sufficient, keep registry stable |
| `integration/scenarios/scenario_manifest_schema.json` | Whether it allows new scenario fields | Must allow `clarification_interaction`, `candidate_choices`, and `transition_outcomes` if formalized |
| verifier scripts | Whether they directly enforce old Class 2 semantics | If they assume terminal Class 2, update |
| integration tests/fixtures | Whether `expected_routing_class2.json` assumes terminal Class 2 only | Update to clarification-state expected output if needed |

### Expected audit outputs

```text
- Whether frozen files must be directly edited
- Whether new frozen versions are needed
- Whether existing context/topic structures are sufficient
- Exact schema/verifier/test items that must change
```

### Decision table

| Situation | Action |
|---|---|
| Frozen file is active source of truth and conflicts with new Class 2 semantics | Directly update it or create a new frozen version |
| Frozen file is active but does not conflict | Keep it; align docs/verifiers/tests only |
| Clarification payload must live inside context input | Create a schema version update or an additive clarification schema |
| Existing topics can express clarification flow | Keep topic registry unchanged |
| New runtime topics are required | Version the topic registry and migrate references |

Recommended bias:

```text
- If policy semantics change, prefer a new policy version.
- Keep the existing context input schema stable if possible.
- Prefer a separate clarification interaction schema for candidate/selection/transition payloads.
- Keep MQTT topic registry stable if existing notification/input/audit topics are sufficient.
- Update scenario manifest schema to allow the new scenario-level fields.
```

---

## 3. Phase 1 — Architecture document alignment

### Purpose

Represent Class 2 as a clarification/transition state in the system architecture and clarify related modules and interfaces.

### Target files

| File | Expected update |
|---|---|
| `common/docs/architecture/14_system_components_outline_v2.md` | Add `Class 2 Clarification Manager` as a logical module inside the Mac mini Edge Hub |
| `common/docs/architecture/15_interface_matrix.md` | Add candidate prompt, user selection, caregiver confirmation, timeout, and Class 0/Class 1/Safe Deferral transition interfaces |
| `common/docs/architecture/16_system_architecture_figure.md` | Add Class 2 clarification loop and transition flow description |
| `common/docs/architecture/17_payload_contract_and_registry.md` | Add clarification prompt, candidate choice, selection result, and transition outcome payload concepts |
| `common/docs/architecture/18_scenario_node_component_mapping.md` | Verify terminology alignment against 14-17 after those documents are updated |

### Architecture boundary to preserve

```text
The LLM Guidance Layer may generate bounded candidate choices.
It must not independently make the final class decision, authorize actuation, or trigger emergency handling.
```

---

## 4. Phase 2 — Policy baseline alignment

### Purpose

Ensure the policy baseline supports Class 2 clarification/transition behavior without allowing unsafe LLM decisions or autonomous actuation.

### Target files / options

| File | Action |
|---|---|
| `common/policies/policy_table_v1_1_2_FROZEN.json` | Based on Phase 0, directly update or create a new version |
| New `policy_table_v1_1_3_FROZEN.json` or `policy_table_v1_2_0_FROZEN.json` | Possible clean target for Class 2 clarification/transition semantics |
| Architecture policy sections | State LLM boundary, confirmation requirement, and transition conditions |
| Policy-schema verifier | Validate the new policy meaning |

### Policy semantics to enforce

```text
- Class 2 is a clarification/transition state.
- LLM guidance generation is allowed only for policy-constrained candidate generation.
- LLM decision invocation is prohibited.
- Class 0/Class 1 transition requires user/caregiver confirmation or deterministic evidence.
- Class 1 transition is limited to low-risk bounded assistance catalog actions.
- Class 0 transition requires emergency confirmation, triple-hit, or sensor evidence.
- Persistent ambiguity or no response leads to Safe Deferral or Caregiver Confirmation.
- Actuator execution is prohibited before deterministic validation.
```

### If a new policy version is created

Update all references in:

```text
- architecture documentation
- scenario verifier policy path(s)
- integration test expected fixtures
- runtime handoff index
```

---

## 5. Phase 3 — Schema / payload / topic alignment

### Purpose

Define how Class 2 clarification messages are represented while avoiding unnecessary disruption to frozen context schemas and topic registries.

### Target files

| File | Expected update |
|---|---|
| `common/docs/architecture/17_payload_contract_and_registry.md` | Document clarification payload structure |
| `common/schemas/context_schema_v1_0_0_FROZEN.json` | Keep stable unless Phase 0 shows it must change |
| New `common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json` | Recommended if clarification prompt/selection/transition payloads are formalized |
| `common/mqtt/topic_registry_v1_0_0.json` | Keep or version depending on topic needs |
| `integration/scenarios/scenario_manifest_schema.json` | Allow new scenario fields |

### Recommended schema split

```text
context_schema_v1_0_0_FROZEN.json
→ operational context input

clarification_interaction_schema_v1_0_0_FROZEN.json
→ candidate prompt, user selection, transition outcome
```

### Candidate clarification payload concept

```json
{
  "clarification_id": "string",
  "source_scenario": "SCN_CLASS2_INSUFFICIENT_CONTEXT",
  "candidate_choices": [
    {
      "candidate_id": "C1_LIGHTING_ASSISTANCE",
      "prompt": "조명을 켤까요?",
      "candidate_transition_target": "CLASS_1",
      "requires_confirmation": true
    }
  ],
  "presentation_channel": "tts",
  "selection_result": {
    "selected_candidate_id": "C1_LIGHTING_ASSISTANCE",
    "selection_source": "bounded_input",
    "confirmed": true
  },
  "transition_target": "CLASS_1"
}
```

### Topic decision

Prefer existing topics if sufficient:

```text
safe_deferral/context/input
safe_deferral/audit/log
safe_deferral/notification/output
safe_deferral/command/request
```

If explicit runtime topics are needed, consider:

```text
safe_deferral/clarification/prompt
safe_deferral/clarification/selection
safe_deferral/clarification/result
```

If these new topics are adopted, the topic registry must be versioned or updated consistently.

---

## 6. Phase 4 — Scenario explanation document alignment

### Purpose

Update scenario-level documentation under `integration/scenarios` so the review guidance matches the new Class 2 semantics.

### Target files

| File | Expected update |
|---|---|
| `integration/scenarios/README.md` | Redefine Class 0, Class 1, Class 2, and fault scenarios |
| `integration/scenarios/scenario_review_guide.md` | Add review checks for candidate generation, user selection, and transition outcomes |
| `integration/scenarios/scenario_manifest_rules.md` | Add recommended Class 2 manifest fields |
| `integration/scenarios/scenario_manifest_schema.json` | Coordinate with Phase 3 to permit the new fields |

### Review criteria to add

```text
- Class 2 must not be described as a terminal failure by default.
- The LLM must not be the final decision maker.
- Candidate choices must be bounded.
- No actuator execution may occur before user/caregiver confirmation and validation.
- Class 1 and Class 0 transitions must be explicit.
- No response or ambiguity must lead to Safe Deferral or Caregiver Confirmation.
```

---

## 7. Phase 5 — Scenario JSON skeleton alignment

### Purpose

Align scenario skeleton JSON files with the paper scenario stories and updated architecture/policy/schema semantics.

### Target files

| File | Expected update |
|---|---|
| `integration/scenarios/class2_insufficient_context_scenario_skeleton.json` | Already updated once; recheck against schema/verifier |
| `integration/scenarios/class1_baseline_scenario_skeleton.json` | Add note/reference that Class 1 may be reached after Class 2 confirmation |
| `integration/scenarios/class0_e002_scenario_skeleton.json` | Add note/reference for Class 2 emergency selection or triple-hit transition to Class 0 |
| `integration/scenarios/class0_e005_scenario_skeleton.json` | Add note/reference for Class 2 fall/emergency confirmation transition to Class 0 |
| `integration/scenarios/conflict_fault_scenario_skeleton.json` | Clarify candidate conflict → confirmation or safe deferral handling |
| `integration/scenarios/missing_state_scenario_skeleton.json` | Clarify that missing-state is a state omission fault, distinct from Class 2 ambiguity |

### Class 2 skeleton requirements

```text
- clarification_interaction
- candidate_choices or equivalent step-level candidate list
- transition_outcomes
- confirmation_required_before_transition = true
- allowed_transition_targets include CLASS_1, CLASS_0, SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
- unsafe_autonomous_actuation_allowed = false
- llm_decision_invocation_allowed = false
```

---

## 8. Phase 6 — Test fixture update and expansion

### Purpose

Create test fixtures that represent multi-step Class 2 clarification/transition behavior.

### Existing fixture updates

| File | Expected update |
|---|---|
| `integration/tests/data/sample_policy_router_input_class2_insufficient_context.json` | Keep as the initial ambiguous input fixture |
| `integration/tests/data/expected_routing_class2.json` | Change from terminal Class 2 to clarification-state expected output if needed |
| `integration/tests/data/sample_policy_router_input_fault_conflict_multiple_candidates.json` | Ensure multiple candidate conflict is explicit |
| `integration/tests/data/sample_policy_router_input_fault_missing_device_state.json` | Ensure missing state and preserved state are clear |

### New fixture candidates

| New file | Purpose |
|---|---|
| `integration/tests/data/expected_class2_candidate_prompt.json` | Expected candidate choices |
| `integration/tests/data/sample_class2_user_selection_class1.json` | User selects Class 1 candidate |
| `integration/tests/data/expected_class2_transition_class1.json` | Expected Class 1 transition |
| `integration/tests/data/sample_class2_user_selection_class0.json` | User selects emergency candidate |
| `integration/tests/data/expected_class2_transition_class0.json` | Expected Class 0 transition |
| `integration/tests/data/sample_class2_timeout_no_response.json` | No-response input |
| `integration/tests/data/expected_class2_timeout_safe_deferral.json` | Expected safe deferral / caregiver confirmation |
| `integration/tests/data/expected_fault_conflict_safe_deferral.json` | Expected conflict safe outcome |
| `integration/tests/data/expected_fault_missing_state_safe_deferral.json` | Expected missing-state safe outcome |

---

## 9. Phase 7 — Verifier update

### Purpose

Update static verification to accept and validate the new Class 2 and fault scenario structures.

### Target files

| File | Expected update |
|---|---|
| `integration/scenarios/verify_scenario_manifest.py` | Validate `clarification_interaction`, `candidate_choices`, and `transition_outcomes` |
| `integration/scenarios/verify_scenario_topic_alignment.py` | Validate existing/new clarification topic usage |
| `integration/scenarios/verify_scenario_fixture_refs.py` | Validate new fixture references |
| `integration/scenarios/verify_scenario_policy_schema_alignment.py` | Validate LLM boundary, transition conditions, and no-autonomous-actuation constraints |

### Class 2 verifier rules

```text
Class 2 scenario must:
- include clarification interaction information
- include bounded candidate choices or equivalent steps
- require user/caregiver confirmation before transition
- allow CLASS_1 / CLASS_0 / SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION transition targets
- prohibit unsafe autonomous actuation
- prohibit LLM final decision invocation
- audit candidate generation, presentation, selection, and transition result
```

### Fault verifier rules

Conflict fault:

```text
- multiple candidate interpretations must be represented
- unsafe autonomous actuation must be prohibited
- confirmation or safe deferral must be expected
```

Missing-state fault:

```text
- missing required state must be explicit
- the system must not assume missing state
- state recheck / safe deferral / caregiver confirmation should be expected
```

---

## 10. Phase 8 — Integration test / adapter update

### Purpose

Allow tests to handle multi-step Class 2 interaction instead of only single input → single expected output.

### Target files

| File | Expected update |
|---|---|
| `integration/tests/test_integration_scenarios.py` | Add Class 2 candidate prompt, selection, and transition tests |
| `integration/tests/integration_adapter.py` | Support multi-step scenario handling |
| scenario test runner | Process candidate/selection/transition steps |

### Test cases to add

```text
1. Class 2 initial ambiguous input routes to clarification state.
2. Class 2 generates bounded candidate choices.
3. Class 2 user selects Class 1 candidate → Class 1 transition.
4. Class 2 user selects emergency candidate → Class 0 transition.
5. Class 2 no response → Safe Deferral / Caregiver Confirmation.
6. Conflict fault with multiple candidates → no autonomous execution.
7. Missing-state fault → no state assumption, no autonomous execution.
```

---

## 11. Phase 9 — Paper scenario cross-reference update

### Purpose

Align user-facing paper scenario documents with the Class 2 transition interpretation and the JSON skeletons.

### Target files

| File | Expected update |
|---|---|
| `common/docs/paper/scenarios/class2_insufficient_context_scenario_user_story.md` | Recheck terminology after JSON/schema/verifier updates |
| `common/docs/paper/scenarios/class1_baseline_scenario_user_story.md` | Add that Class 1 can also be reached after Class 2 confirmation |
| `common/docs/paper/scenarios/class0_e002_scenario_user_story.md` | Add Class 2 emergency selection/triple-hit transition note |
| `common/docs/paper/scenarios/class0_e005_scenario_user_story.md` | Add Class 2 fall/emergency confirmation transition note |
| `common/docs/paper/scenarios/conflict_fault_scenario_user_story.md` | Keep Class 2 vs conflict distinction; check candidate confirmation wording |
| `common/docs/paper/scenarios/missing_state_scenario_user_story.md` | Keep Class 2 vs missing-state distinction; check state recheck wording |

---

## 12. Phase 10 — Runtime handoff update

### Purpose

Document final progress and remaining work for the next session.

### Target files

| File | Expected update |
|---|---|
| `common/docs/runtime/SESSION_HANDOFF.md` | Add index entries for this plan and final completion update |
| `common/docs/runtime/SESSION_HANDOFF_2026-04-25_CLASS2_CLARIFICATION_TRANSITION_IMPACT_PLAN.md` | Add superseded-by or v2 note if needed |
| New completion handoff | Example: `SESSION_HANDOFF_2026-04-25_SCENARIO_POLICY_SCHEMA_VERIFY_UPDATE.md` |

### Handoff contents

```text
- Class 2 semantic change
- Frozen baseline audit result
- Policy/schema/topic registry update decision
- Scenario JSON update result
- Fixture/verifier/test update result
- Remaining open issues
```

---

## 13. Overall recommended execution order

```text
Phase 0. Active Frozen Baseline Impact Audit
Phase 1. Architecture document alignment
Phase 2. Policy baseline alignment
Phase 3. Schema / payload / topic alignment
Phase 4. Scenario explanation document alignment
Phase 5. Scenario JSON skeleton alignment
Phase 6. Test fixture update and expansion
Phase 7. Verifier update
Phase 8. Integration test / adapter update
Phase 9. Paper scenario cross-reference update
Phase 10. Runtime handoff update
```

---

## 14. Highest-priority files to inspect first

```text
common/policies/policy_table_v1_1_2_FROZEN.json
common/schemas/context_schema_v1_0_0_FROZEN.json
common/mqtt/topic_registry_v1_0_0.json
integration/scenarios/scenario_manifest_schema.json
integration/scenarios/verify_scenario_manifest.py
integration/scenarios/verify_scenario_policy_schema_alignment.py
integration/tests/data/expected_routing_class2.json
```

Then align:

```text
common/docs/architecture/14_system_components_outline_v2.md
common/docs/architecture/15_interface_matrix.md
common/docs/architecture/16_system_architecture_figure.md
common/docs/architecture/17_payload_contract_and_registry.md
common/docs/architecture/18_scenario_node_component_mapping.md
integration/scenarios/README.md
integration/scenarios/scenario_review_guide.md
integration/scenarios/scenario_manifest_rules.md
integration/scenarios/class2_insufficient_context_scenario_skeleton.json
integration/scenarios/conflict_fault_scenario_skeleton.json
integration/scenarios/missing_state_scenario_skeleton.json
```

---

## 15. Final invariants

```text
1. Do not bypass frozen files.
2. If a frozen file is the active source of truth, update it or create a new frozen version and migrate references.
3. If a new version is created, align every downstream reference.
4. Class 2 is a clarification/transition state.
5. The LLM may generate candidates but must not make final decisions.
6. Class 1 transition is limited to confirmed low-risk bounded assistance.
7. Class 0 transition requires emergency confirmation, triple-hit, or deterministic sensor evidence.
8. Persistent ambiguity or no response must lead to Safe Deferral or Caregiver Confirmation.
9. Validator approval is required before actuator autonomous execution.
10. Candidate generation, selection, transition, deferral, execution, and notification outcomes must be audit logged.
```

This plan supersedes the earlier impact plan where frozen files were treated as generally avoided rather than explicitly audited as active baselines.

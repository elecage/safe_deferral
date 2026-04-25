# SESSION_HANDOFF_2026-04-25_SCENARIO_ALIGNMENT_PLAN.md

Date: 2026-04-25
Scope: `integration/scenarios/` scenario documentation, scenario skeleton JSON files, scenario fixtures, and scenario verification utilities
Status: Planning baseline before scenario JSON edits

## 1. Purpose

This document records the planned scenario-alignment work before editing the scenario JSON assets.

The immediate reason for this plan is that the current scenario documentation is broadly aligned with the project safety philosophy, but several scenario skeleton JSON files still use older MQTT topic names and do not fully reflect the current architecture, interface matrix, policy, schema, and figure interpretation.

The next work should first update scenario documentation, then use that documentation as the basis for reviewing and correcting all scenario JSON files and fixtures.

## 2. Primary files under review

Scenario documentation:

- `integration/scenarios/README.md`
- `integration/scenarios/scenario_review_guide.md`
- `integration/scenarios/scenario_manifest_rules.md`

Scenario skeleton JSON files currently in scope:

- `integration/scenarios/baseline_scenario_skeleton.json`
- `integration/scenarios/class0_e001_scenario_skeleton.json`
- `integration/scenarios/class0_e002_scenario_skeleton.json`
- `integration/scenarios/class0_e003_scenario_skeleton.json`
- `integration/scenarios/class0_e004_scenario_skeleton.json`
- `integration/scenarios/class0_e005_scenario_skeleton.json`
- `integration/scenarios/class1_baseline_scenario_skeleton.json`
- `integration/scenarios/class2_insufficient_context_scenario_skeleton.json`
- `integration/scenarios/stale_fault_scenario_skeleton.json`
- `integration/scenarios/conflict_fault_scenario_skeleton.json`
- `integration/scenarios/missing_state_scenario_skeleton.json`

Likely fixture directory:

- `integration/tests/data/`

## 3. Required reference baseline

Scenario work must remain aligned with the following current references:

- `common/docs/runtime/SESSION_HANDOFF.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_SYSTEM_LAYOUT_FIGURE_REVISION_UPDATE.md`
- `common/docs/architecture/14_system_components_outline_v2.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`

## 4. Non-negotiable scenario interpretation

1. Scenario files are integration/evaluation assets, not policy truth.
2. Scenario files must consume frozen policy/schema assets rather than redefining thresholds, triggers, required fields, or allowed action scope.
3. Scenario files must not expand the Class 1 autonomous low-risk action catalog.
4. Current Class 1 autonomous low-risk execution is lighting only, constrained by `common/policies/low_risk_actions_v1_1_0_FROZEN.json`.
5. Doorlock-sensitive behavior must not appear as autonomous Class 1 execution.
6. Doorlock-sensitive outcomes must route to Class 2 escalation or a separately governed manual confirmation path with caregiver approval, ACK, and audit.
7. `doorbell_detected` is required visitor-response context, not emergency evidence and not doorlock authorization.
8. Emergency family IDs E001~E005 must remain aligned with `policy_table_v1_1_2_FROZEN.json`.
9. Class 0 emergency scenarios must not make the LLM the primary decision path.
10. Scenario topics must align with `common/mqtt/topic_registry_v1_0_0.json` and `15_interface_matrix.md`.
11. RPi simulation and fault topics must remain controlled experiment-mode inputs, not uncontrolled operational inputs.
12. Scenario validation and governance reports are evidence artifacts, not operational authorization.

## 5. Findings from initial review

### 5.1 Scenario documentation status

The three scenario documents are broadly safe and aligned in principle:

- They state that scenarios are not canonical policy truth.
- They state that frozen common assets define thresholds, triggers, and required fields.
- They emphasize conservative handling of unsafe autonomous actuation.
- They recognize Class 0, Class 1, Class 2, stale, conflict, and missing-state scenarios.

However, they need updates to reflect the latest architecture and MQTT/interface work.

### 5.2 Major JSON skeleton issue: legacy MQTT topics

Current scenario skeletons commonly use legacy topics such as:

```json
"ingress_topic": "smarthome/context/raw",
"audit_topic": "smarthome/audit/validator_output"
```

These conflict with the current MQTT registry and interface matrix, which use the `safe_deferral/...` namespace.

The default replacement for ordinary context scenarios should be:

```json
"ingress_topic": "safe_deferral/context/input",
"audit_topic": "safe_deferral/audit/log"
```

Class 0 emergency scenarios should use or explicitly bridge to:

```json
"ingress_topic": "safe_deferral/emergency/event",
"audit_topic": "safe_deferral/audit/log"
```

If a Class 0 fixture is still policy-router-input shaped, the scenario should explicitly distinguish the emergency event topic from any normalized policy-input bridge.

### 5.3 Manifest rules issue: E002~E005 missing from listed skeletons

`scenario_manifest_rules.md` should include all current Class 0 skeletons:

- `class0_e001_scenario_skeleton.json`
- `class0_e002_scenario_skeleton.json`
- `class0_e003_scenario_skeleton.json`
- `class0_e004_scenario_skeleton.json`
- `class0_e005_scenario_skeleton.json`

### 5.4 Class 1 low-risk boundary should be explicit

Scenario docs and Class 1 scenario skeletons should explicitly state that current autonomous Class 1 execution is constrained to the frozen low-risk lighting catalog.

Recommended JSON addition for Class 1 expected outcomes:

```json
"allowed_action_catalog_ref": "common/policies/low_risk_actions_v1_1_0_FROZEN.json",
"doorlock_autonomous_execution_allowed": false
```

Recommended note:

```text
Class 1 autonomous execution must remain limited to the frozen low-risk lighting catalog; doorlock-sensitive behavior must not be represented as Class 1 execution.
```

### 5.5 `doorbell_detected` rule should be stronger

Scenario docs should state:

```text
All schema-governed context fixtures referenced by scenarios must include pure_context_payload.environmental_context.doorbell_detected. For non-visitor scenarios this should normally be false. doorbell_detected=true must not be interpreted as emergency evidence or doorlock authorization.
```

### 5.6 LLM invocation semantics are currently too coarse

Current scenario skeletons often use:

```json
"llm_invocation_allowed": true
```

or:

```json
"llm_invocation_allowed": false
```

This should be clarified because the current architecture distinguishes:

- LLM use for decision/candidate action generation, and
- LLM use for policy-constrained explanation/guidance/clarification text generation.

Recommended future fields:

```json
"llm_decision_invocation_allowed": false,
"llm_guidance_generation_allowed": true
```

or for Class 0 emergency cases:

```json
"llm_decision_invocation_allowed": false,
"llm_guidance_generation_allowed": "policy_constrained_only"
```

Existing `llm_invocation_allowed` can be preserved temporarily for backward compatibility, but scenario documentation must define its interpretation or mark it as legacy/coarse.

### 5.7 Fault scenario fixture specificity should improve

Existing stale, conflict, and missing-state scenario skeletons reuse baseline or insufficient-context fixtures. This is acceptable for skeletons but weak for final verification.

Recommended future fixtures:

- `integration/tests/data/sample_policy_router_input_fault_stale.json`
- `integration/tests/data/sample_policy_router_input_fault_conflict_multiple_candidates.json`
- `integration/tests/data/sample_policy_router_input_fault_missing_doorbell_detected.json`
- `integration/tests/data/sample_policy_router_input_fault_missing_device_state.json`

`missing_state` should distinguish:

- missing `doorbell_detected` required-key fault,
- missing ordinary environmental field,
- missing device state,
- missing policy-router wrapper field.

## 6. Planned phase sequence

### Phase S1 — Scenario documentation alignment

Update:

- `integration/scenarios/README.md`
- `integration/scenarios/scenario_review_guide.md`
- `integration/scenarios/scenario_manifest_rules.md`

Required updates:

1. Replace legacy topic guidance with `safe_deferral/...` topic guidance.
2. Add or clarify Class 0 emergency topic / normalized input bridge interpretation.
3. Add E002~E005 skeletons to manifest rule listings.
4. Add `doorbell_detected` required-field and non-authority rule.
5. Add Class 1 frozen low-risk lighting-catalog boundary.
6. Add doorlock-sensitive non-Class-1 boundary.
7. Add LLM decision invocation vs guidance generation distinction.
8. Add scenario-as-consumer-of-policy/schema/registry rule.
9. Add fixture reference and expected fixture existence requirements.
10. Add future verifier plan.

No scenario JSON should be edited before Phase S1 unless explicitly requested.

### Phase S2 — Scenario skeleton JSON topic and boundary alignment

Update all scenario skeletons under `integration/scenarios/`.

Expected changes:

1. Replace legacy `smarthome/...` topics.
2. Use `safe_deferral/context/input` for ordinary context scenarios.
3. Use `safe_deferral/emergency/event` for Class 0 emergency scenarios, or explicitly represent a controlled normalized policy-input bridge.
4. Use `safe_deferral/audit/log` for audit observation.
5. Add Class 1 catalog reference where relevant.
6. Add `doorlock_autonomous_execution_allowed: false` where relevant.
7. Clarify `llm_decision_invocation_allowed` and `llm_guidance_generation_allowed` where relevant.
8. Preserve existing coarse `llm_invocation_allowed` temporarily only if needed for compatibility.
9. Keep all expected unsafe autonomous actuation values false.
10. Ensure fault scenarios allow only conservative outcomes such as `CLASS_2` or `SAFE_DEFERRAL`.

### Phase S3 — Fixture inventory and fixture reference validation

Review all fixture references in scenario skeletons.

Verify:

- each `payload_fixture` exists,
- each `expected_fixture` exists,
- each referenced JSON parses,
- each policy-router-input fixture validates against the referenced schema where intended,
- each context fixture includes `environmental_context.doorbell_detected`,
- non-visitor fixtures normally set `doorbell_detected=false`,
- visitor fixtures set `doorbell_detected=true` only where appropriate,
- no fixture inserts doorlock state into current `device_states`,
- Class 1 fixtures do not imply doorlock execution.

### Phase S4 — Add scenario verification utilities

Recommended new files:

- `integration/scenarios/scenario_manifest_schema.json`
- `integration/scenarios/verify_scenario_manifest.py`
- `integration/scenarios/verify_scenario_topic_alignment.py`
- `integration/scenarios/verify_scenario_fixture_refs.py`
- `integration/scenarios/verify_scenario_policy_schema_alignment.py`

Minimum verifier checks:

1. Manifest required fields exist.
2. Scenario JSON parses.
3. Scenario `input_plane` topics exist in `common/mqtt/topic_registry_v1_0_0.json`.
4. Fixture paths exist.
5. Expected fixture paths exist.
6. Class 0 emergency family IDs E001~E005 exist in the frozen policy table.
7. Class 1 expected outcomes do not imply doorlock.
8. Context fixtures include `doorbell_detected`.
9. Current `device_states` do not include doorlock fields.
10. Unsafe autonomous actuation is false in all skeletons.

### Phase S5 — Add or split fault-specific fixtures

After the basic JSON skeletons and verifiers are aligned, add more specific fixtures for:

- stale context,
- missing required field,
- missing `doorbell_detected`,
- device-state missing key,
- multiple candidate conflict,
- low-risk conflict,
- doorlock-sensitive request routed away from Class 1.

### Phase S6 — Optional scenario handoff completion update

After S1~S5, add a completion addendum documenting:

- updated scenario docs,
- updated skeletons,
- added verifiers,
- fixture inventory,
- known gaps,
- remaining runtime validation needs.

## 7. Recommended immediate next step

The next implementation step should be Phase S1:

```text
Update README.md, scenario_review_guide.md, and scenario_manifest_rules.md first.
```

Reason:

- The JSON skeletons should be updated against a documented target contract.
- Editing JSON first risks rework if the target scenario manifest interpretation changes.
- Documentation should define the scenario namespace, authority boundary, LLM field interpretation, and doorbell/doorlock constraints before batch-editing skeleton files.

## 8. Current status statement

As of this plan, no scenario JSON has been corrected yet. The known primary mismatch is the use of legacy `smarthome/...` MQTT topics in scenario skeletons. The scenario documentation should be updated first, then the JSON files should be reviewed and corrected against the updated rules.

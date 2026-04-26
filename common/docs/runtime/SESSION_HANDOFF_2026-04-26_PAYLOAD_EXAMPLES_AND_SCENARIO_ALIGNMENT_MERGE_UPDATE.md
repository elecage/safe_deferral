# SESSION_HANDOFF_2026-04-26_PAYLOAD_EXAMPLES_AND_SCENARIO_ALIGNMENT_MERGE_UPDATE.md

## Purpose

This addendum records the payload-example, integration-scenario, and scenario-review-reference alignment work merged into `main` through PR #10, PR #12, and PR #14.

Read this addendum before older payload, MQTT, scenario, Class 2, and integration-test handoff notes when the current task involves:

- payload examples,
- payload README / payload reference examples,
- MQTT topic example payload references,
- `integration/scenarios/`,
- scenario manifest schema/rules,
- scenario review guidance,
- split scenario review docs,
- `CLAUDE.md` scenario-review reference follow-up,
- Class 2 scenario expansion,
- Class 2 clarification interaction evidence,
- timeout/no-response behavior,
- doorlock-sensitive caregiver confirmation scenarios,
- or fixture/schema alignment follow-up work.

This document is an addendum, not policy/schema authority.

Authoritative assets remain under:

```text
common/policies/
common/schemas/
common/mqtt/
common/payloads/
integration/scenarios/
```

---

## Merge summary

### PR #10

```text
https://github.com/elecage/safe_deferral/pull/10
```

Title:

```text
payloads: align examples with Class 2 clarification interface
```

Merge commit:

```text
b55d7bc37c25d654fde8df4d6e6b262b393befaf
```

Scope:

```text
Payload examples, payload README, and MQTT example-payload references aligned to the current Class 2 clarification interaction topic/schema.
```

### PR #12

```text
https://github.com/elecage/safe_deferral/pull/12
```

Title:

```text
integration: align scenarios with Class 2 clarification topic
```

Merge commit:

```text
0444fa88cbfdbc0f9a934f8eef9670c6751ecc6f
```

Scope:

```text
Integration scenario docs, scenario manifest schema, existing Class 2/fault skeletons, split review guides, and four new Class 2 transition skeletons.
```

### PR #14

```text
https://github.com/elecage/safe_deferral/pull/14
```

Title:

```text
docs: record CLAUDE scenario review reference update
```

Merge commit:

```text
795ae441b257160e5fd677fef227eb8131bd47a4
```

Scope:

```text
Adds a helper note documenting how CLAUDE.md should be updated to prefer the split scenario review docs under integration/scenarios/docs/ while retaining scenario_review_guide.md as a legacy compatibility reference.
```

---

## Current baseline after PR #10, PR #12, and PR #14

Use the following current references for payload-example and scenario work:

```text
policy_table_v1_2_0_FROZEN.json = current routing policy baseline
low_risk_actions_v1_1_0_FROZEN.json = current low-risk action catalog
fault_injection_rules_v1_4_0_FROZEN.json = current fault injection rules file
context_schema_v1_0_0_FROZEN.json = current pure context schema
policy_router_input_schema_v1_1_1_FROZEN.json = current policy-router input schema
candidate_action_schema_v1_0_0_FROZEN.json = current candidate action schema
validator_output_schema_v1_1_0_FROZEN.json = current validator output schema
class_2_notification_payload_schema_v1_1_0_FROZEN.json = current Class 2 notification schema
clarification_interaction_schema_v1_0_0_FROZEN.json = current Class 2 clarification interaction schema
topic_registry_v1_1_0.json = current MQTT topic registry
topic_registry_v1_0_0.json = historical MQTT registry baseline only
```

Current dedicated Class 2 clarification interaction topic:

```text
safe_deferral/clarification/interaction
```

Contract:

```text
payload_family: clarification_interaction_payload
schema: common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
example_payload: common/payloads/examples/clarification_interaction_two_options_pending.json
authority_level: class2_interaction_evidence_not_authority
```

Authority boundary:

```text
clarification interaction payload/topic ≠ validator approval
clarification interaction payload/topic ≠ actuation command
clarification interaction payload/topic ≠ emergency trigger authority
clarification interaction payload/topic ≠ doorlock authorization
```

Required transition semantics:

```text
selection results require Policy Router re-entry
Class 1 transition requires Deterministic Validator approval
Class 0 transition requires deterministic emergency evidence or explicit emergency confirmation
timeout/no-response must not infer user intent
doorbell_detected is not doorlock authorization
doorlock is not current Class 1 low-risk scope
```

---

## PR #10 payload-example alignment

PR #10 changed 7 files:

```text
common/payloads/README.md
common/payloads/examples/clarification_interaction_two_options_pending.json
common/payloads/examples/policy_router_input_visitor_doorbell.json
common/payloads/examples/experiment_progress_running.json
common/payloads/examples/result_export_summary.json
common/mqtt/topic_registry_v1_1_0.json
common/mqtt/topic_payload_contracts_v1_0_0.md
```

### Key outcomes

#### Payload README current references

`common/payloads/README.md` now treats:

```text
common/mqtt/topic_registry_v1_1_0.json
```

as the current MQTT registry and retains:

```text
common/mqtt/topic_registry_v1_0_0.json
```

as historical baseline only.

It also updates Class 2 notification coverage to:

```text
common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json
```

#### New clarification interaction example

New file:

```text
common/payloads/examples/clarification_interaction_two_options_pending.json
```

Purpose:

```text
A representative pending Class 2 two-option clarification interaction example.
```

Important boundaries encoded:

```text
candidate choices are guidance only
selection must re-enter Policy Router
Class 1 transition still requires Deterministic Validator approval
not actuation authorization
not emergency trigger authority
not doorlock authorization
```

#### MQTT registry example-payload linkage

`common/mqtt/topic_registry_v1_1_0.json` now links:

```text
safe_deferral/clarification/interaction.example_payload
→ common/payloads/examples/clarification_interaction_two_options_pending.json
```

#### Topic contract linkage

`common/mqtt/topic_payload_contracts_v1_0_0.md` now lists:

```text
common/payloads/examples/clarification_interaction_two_options_pending.json
```

as the example for:

```text
safe_deferral/clarification/interaction
```

#### Visitor doorbell example cleanup

`common/payloads/examples/policy_router_input_visitor_doorbell.json` was made strict-schema oriented by removing top-level `experiment_annotation`.

Interpretation:

```text
Doorlock/manual approval/ACK state belongs in fixture annotations, dashboard observation, manual confirmation payloads, or audit artifacts, not in schema-governed policy_router_input examples.
```

#### Experiment/result terminology update

Updated examples:

```text
common/payloads/examples/experiment_progress_running.json
common/payloads/examples/result_export_summary.json
```

Preferred terms now include:

```text
validator_rejected_class2_clarification
class_2_clarification_notification_sent
clarification_interaction_recorded
class_2_clarification_or_caregiver_confirmation
```

`result_export_summary.json` now includes:

```text
class2_clarification_payload_authorized_actuation: false
```

---

## PR #12 integration-scenario alignment

PR #12 changed 16 integration scenario files.

### Scenario docs and manifest schema

Changed:

```text
integration/scenarios/README.md
integration/scenarios/scenario_manifest_rules.md
integration/scenarios/scenario_manifest_schema.json
```

Key outcomes:

```text
topic_registry_v1_1_0.json is current scenario MQTT registry
topic_registry_v1_0_0.json is historical baseline only
safe_deferral/clarification/interaction is the Class 2 clarification interaction evidence topic
clarification_interaction_two_options_pending.json is the representative example payload
class2_clarification_expectation is now documented and supported by the scenario manifest schema
```

### Scenario manifest schema extensions

`integration/scenarios/scenario_manifest_schema.json` now includes optional support for:

```text
input_plane.clarification_interaction_topic
clarification_interaction.clarification_topic
clarification_interaction.clarification_schema_ref
clarification_interaction.example_payload_ref
class2_clarification_expectation
```

Class 2 expectation fields include:

```text
requires_policy_router_reentry
requires_validator_when_class1
timeout_must_not_infer_intent
clarification_payload_is_not_authorization
forbidden_interpretations
```

Additional Class 2 category values were added:

```text
class2_transition
class2_timeout
class2_caregiver_confirmation
```

### Split scenario review guides

The old monolithic guide was intentionally retained:

```text
integration/scenarios/scenario_review_guide.md
```

New split review guides were added:

```text
integration/scenarios/docs/README.md
integration/scenarios/docs/scenario_review_principles.md
integration/scenarios/docs/scenario_review_class0_class1.md
integration/scenarios/docs/scenario_review_class2.md
integration/scenarios/docs/scenario_review_faults.md
```

Reason:

```text
The old monolithic review guide was long and caused update/SHA conflicts through GitHub contents operations. Splitting the guide reduces edit conflicts and separates general, Class 0/Class 1, Class 2, and fault-specific review guidance.
```

Important note:

```text
Do not delete scenario_review_guide.md yet unless a separate cleanup PR is intentionally performed.
Use integration/scenarios/docs/README.md as the preferred review-guide index going forward.
```

### Existing Class 2 / fault skeletons updated

Updated files:

```text
integration/scenarios/class2_insufficient_context_scenario_skeleton.json
integration/scenarios/conflict_fault_scenario_skeleton.json
integration/scenarios/missing_state_scenario_skeleton.json
integration/scenarios/stale_fault_scenario_skeleton.json
```

Common additions:

```text
input_plane.clarification_interaction_topic
clarification_interaction topic/schema/example references where applicable
class2_clarification_expectation
forbidden_interpretations
Policy Router re-entry requirement
validator requirement for Class 1 transition
timeout/no-response non-inference
clarification payload non-authorization boundary
```

Fault-specific interpretation preserved:

```text
stale fault = state exists but is too old or untrusted
conflict fault = multiple candidates remain plausible and arbitrary selection is unsafe
missing-state fault = required device/context state is absent and must not be fabricated
```

### New Class 2 transition skeletons

New files:

```text
integration/scenarios/class2_to_class1_low_risk_confirmation_scenario_skeleton.json
integration/scenarios/class2_to_class0_emergency_confirmation_scenario_skeleton.json
integration/scenarios/class2_timeout_no_response_safe_deferral_scenario_skeleton.json
integration/scenarios/class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json
```

Coverage:

```text
Class 2 → Class 1 after low-risk candidate selection + Policy Router re-entry + Deterministic Validator approval
Class 2 → Class 0 after emergency confirmation or deterministic E001-E005 evidence
Class 2 timeout/no-response → Safe Deferral or Caregiver Confirmation without intent inference
Class 2 doorlock-sensitive/caregiver-confirmation path without autonomous Class 1 unlock
```

---

## PR #14 CLAUDE scenario-review reference note

PR #14 added:

```text
common/docs/runtime/CLAUDE_SCENARIO_REVIEW_REFERENCE_UPDATE.md
```

Purpose:

```text
Record the required CLAUDE.md reference update after the scenario review guide split introduced by PR #12.
```

Important current state:

```text
CLAUDE.md was not directly edited in PR #14.
```

Reason:

```text
CLAUDE.md is a long file and should only be edited using a method that preserves the complete file content and verifies the final diff.
```

The helper note records that future agents and developers should prefer:

```text
integration/scenarios/docs/README.md
integration/scenarios/docs/scenario_review_principles.md
integration/scenarios/docs/scenario_review_class0_class1.md
integration/scenarios/docs/scenario_review_class2.md
integration/scenarios/docs/scenario_review_faults.md
```

over the older monolithic guide:

```text
integration/scenarios/scenario_review_guide.md
```

The older monolithic guide is retained only for compatibility.

### Exact future CLAUDE.md update needed

`CLAUDE.md` should later be safely updated so scenario/integration references prefer:

```text
/integration/scenarios/docs/README.md
/integration/scenarios/docs/scenario_review_principles.md
/integration/scenarios/docs/scenario_review_class0_class1.md
/integration/scenarios/docs/scenario_review_class2.md
/integration/scenarios/docs/scenario_review_faults.md
```

and mark:

```text
/integration/scenarios/scenario_review_guide.md
```

as:

```text
retained legacy compatibility reference only
```

Safe editing options:

```text
1. Clone locally, edit with git, run diff, push branch.
2. Use a GitHub editor session that preserves the whole file.
3. Use an API workflow that retrieves the complete file and verifies the final diff before committing.
```

Related issue:

```text
https://github.com/elecage/safe_deferral/issues/13
```

---

## Current scenario-review read order

For scenario review work, read:

```text
integration/scenarios/README.md
integration/scenarios/scenario_manifest_rules.md
integration/scenarios/scenario_manifest_schema.json
integration/scenarios/docs/README.md
integration/scenarios/docs/scenario_review_principles.md
integration/scenarios/docs/scenario_review_class0_class1.md
integration/scenarios/docs/scenario_review_class2.md
integration/scenarios/docs/scenario_review_faults.md
```

Then read the relevant scenario skeletons.

The older file remains available for compatibility:

```text
integration/scenarios/scenario_review_guide.md
```

but new work should prefer the split docs under:

```text
integration/scenarios/docs/
```

`CLAUDE.md` has not yet been directly updated, but the required update is recorded in:

```text
common/docs/runtime/CLAUDE_SCENARIO_REVIEW_REFERENCE_UPDATE.md
```

---

## Current Class 2 scenario coverage

Existing / updated:

```text
integration/scenarios/class2_insufficient_context_scenario_skeleton.json
integration/scenarios/conflict_fault_scenario_skeleton.json
integration/scenarios/missing_state_scenario_skeleton.json
integration/scenarios/stale_fault_scenario_skeleton.json
```

New transition skeletons:

```text
integration/scenarios/class2_to_class1_low_risk_confirmation_scenario_skeleton.json
integration/scenarios/class2_to_class0_emergency_confirmation_scenario_skeleton.json
integration/scenarios/class2_timeout_no_response_safe_deferral_scenario_skeleton.json
integration/scenarios/class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json
```

---

## Recommended follow-up work

### 1. Fixture alignment issue

`integration/tests/data/` fixtures still need a separate schema-alignment pass.

Suspected issues from spot checks:

```text
temperature_c vs temperature
illuminance_lux vs illuminance
missing trigger_event.timestamp_ms
missing routing_metadata.ingest_timestamp_ms
policy_router_input_schema_v1_1_1_FROZEN compliance
context_schema_v1_0_0_FROZEN compliance
doorbell_detected required field
doorlock state inside device_states
```

Potential issue title:

```text
Integration fixtures: align test data with current policy-router input and context schemas
```

### 2. Optional scenario cleanup

Potential cleanup:

```text
Delete or archive integration/scenarios/scenario_review_guide.md after confirming split docs fully supersede it.
```

Do not do this automatically. It should be a deliberate cleanup PR.

### 3. CLAUDE.md direct update

`CLAUDE.md` still needs a safe direct update to prefer the split scenario review docs.

Guidance is recorded in:

```text
common/docs/runtime/CLAUDE_SCENARIO_REVIEW_REFERENCE_UPDATE.md
```

Issue:

```text
https://github.com/elecage/safe_deferral/issues/13
```

### 4. Optional C206/C207 scenario expansion

Potential additional skeletons:

```text
integration/scenarios/class2_c206_insufficient_context_scenario_skeleton.json
integration/scenarios/class2_c207_timeout_no_response_scenario_skeleton.json
integration/scenarios/class2_conflict_resolution_to_class1_scenario_skeleton.json
integration/scenarios/class2_missing_state_recheck_then_safe_deferral_scenario_skeleton.json
integration/scenarios/class2_stale_state_caregiver_confirmation_scenario_skeleton.json
```

### 5. Verification scripts

Future verifier work should check:

```text
jq empty integration/scenarios/*.json
safe_deferral/clarification/interaction coverage in Class 2 scenarios
class2_clarification_expectation presence in Class 2 transition scenarios
topic_registry_v1_0_0.json appears only as historical baseline
Class 2 timeout/no-response does not infer intent
Class 1 transition requires Deterministic Validator approval
Class 0 transition requires emergency evidence or explicit confirmation
doorbell_detected is not doorlock authorization
doorlock is not current Class 1 low-risk scope
CLAUDE.md scenario references prefer integration/scenarios/docs/ after direct update
```

---

## Current state after this update

As of this addendum:

```text
Payload examples: aligned and merged
Class 2 clarification example payload: present on main
MQTT topic registry example_payload for safe_deferral/clarification/interaction: linked on main
Scenario manifest docs/schema: aligned and merged
Scenario split review docs: present on main
Existing Class 2/fault skeletons: updated with clarification expectation references
Minimum Class 2 transition skeletons: present on main
scenario_review_guide.md: retained, not deleted
CLAUDE_SCENARIO_REVIEW_REFERENCE_UPDATE.md: present on main
CLAUDE.md direct edit: still pending, should be done only with full-file-safe editing
```

Any future implementation should treat:

```text
safe_deferral/clarification/interaction
```

as the canonical MQTT topic for published Class 2 clarification interaction artifacts, and:

```text
common/payloads/examples/clarification_interaction_two_options_pending.json
```

as the current representative example payload for that topic.

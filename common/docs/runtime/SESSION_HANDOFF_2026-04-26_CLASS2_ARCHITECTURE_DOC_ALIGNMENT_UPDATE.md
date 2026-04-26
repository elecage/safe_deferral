# SESSION_HANDOFF_2026-04-26_CLASS2_ARCHITECTURE_DOC_ALIGNMENT_UPDATE.md

## Purpose

This addendum records the Class 2 clarification architecture-document alignment work performed in PR #4.

It is intended to be read before older Class 2, architecture, prompt, script-structure, MQTT/payload, and figure-interpretation handoff notes when the task involves Class 2 clarification / transition semantics.

This document is an addendum, not a replacement for frozen policy/schema assets.

Authoritative assets remain under:

- `common/policies/`
- `common/schemas/`
- `common/mqtt/`
- `common/payloads/`

---

## PR reference

PR:

```text
https://github.com/elecage/safe_deferral/pull/4
```

Branch:

```text
docs/class2-phase1-asset-alignment
```

PR title:

```text
docs: align Class 2 clarification architecture references
```

Issue context:

```text
Part of issue #3
```

---

## High-level outcome

The architecture documentation has been aligned so that Class 2 is interpreted as:

```text
Class 2 = bounded clarification / transition state
```

rather than only:

```text
terminal caregiver escalation
```

The current Class 2 architecture interpretation is:

```text
Ambiguous or insufficient input
→ Class 2 clarification
→ bounded candidate generation
→ user/caregiver confirmation, timeout, or deterministic emergency evidence
→ Policy Router re-entry
→ Class 1, Class 0, Safe Deferral, or Caregiver Confirmation
```

Important authority boundary:

```text
Class 2 Clarification Manager ≠ actuator authority
Class 2 Clarification Manager ≠ final class decision authority
Class 2 Clarification Manager ≠ emergency trigger authority
Class 2 Clarification Manager ≠ Deterministic Validator bypass
LLM candidate text ≠ validator approval
LLM candidate text ≠ emergency trigger evidence
LLM candidate text ≠ doorlock authorization
```

---

## Frozen asset reference alignment

Stale references were replaced:

```text
policy_table_v1_1_2_FROZEN.json
→ policy_table_v1_2_0_FROZEN.json

class_2_notification_payload_schema_v1_0_0_FROZEN.json
→ class_2_notification_payload_schema_v1_1_0_FROZEN.json
```

The current clarification interaction schema is now explicitly referenced where relevant:

```text
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
```

This schema governs:

```text
clarification_interaction_payload
```

and should remain separate from:

```text
pure_context_payload
class_2_notification_payload
validator_output_payload
actuation_command_payload
audit_payload
```

---

## Documents changed in PR #4

The PR is documentation-only.

Changed files:

```text
common/docs/architecture/01_installation_target_classification.md
common/docs/architecture/02_mac_mini_build_sequence.md
common/docs/architecture/06_implementation_plan.md
common/docs/architecture/07_task_breakdown.md
common/docs/architecture/08_additional_required_work.md
common/docs/architecture/09_recommended_next_steps.md
common/docs/architecture/10_install_script_structure.md
common/docs/architecture/11_configuration_script_structure.md
common/docs/architecture/12_prompts.md
common/docs/architecture/12_prompts_core_system.md
common/docs/architecture/12_prompts_mqtt_payload_governance.md
common/docs/architecture/12_prompts_nodes_and_evaluation.md
common/docs/architecture/14_system_components_outline_v2.md
common/docs/architecture/16_system_architecture_figure.md
common/docs/architecture/18_scenario_node_component_mapping.md
common/docs/architecture/19_class2_clarification_architecture_alignment.md
```

Not changed:

```text
common/docs/architecture/figures/*.svg
mac_mini/scripts/**
rpi/scripts/**
esp32/scripts/**
runtime code
common/policies/**
common/schemas/**
fixtures
```

---

## Phase summary

### Phase 1. Frozen asset reference alignment

Updated architecture documents to use the current policy and Class 2 notification schema names:

```text
policy_table_v1_2_0_FROZEN.json
class_2_notification_payload_schema_v1_1_0_FROZEN.json
clarification_interaction_schema_v1_0_0_FROZEN.json
```

Representative updated documents:

```text
07_task_breakdown.md
08_additional_required_work.md
09_recommended_next_steps.md
12_prompts_core_system.md
```

### Phase 2. Document 19 schema-status alignment

Updated:

```text
19_class2_clarification_architecture_alignment.md
```

so that:

```text
clarification_interaction_payload
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
```

are described as current Class 2 clarification interaction payload/schema references, not future optional work.

### Phase 3. Mac mini runtime component alignment

Added or clarified:

```text
Class 2 Clarification Manager
```

as a Mac mini Edge Hub runtime component.

Important behavior:

```text
- manages bounded clarification interactions
- may request LLM-generated candidate choices
- collects user/caregiver confirmation, timeout, or deterministic evidence
- requests Policy Router re-entry
- must not authorize actuation
- must not determine final class transitions by itself
- must not trigger emergency handling
- must not bypass the Deterministic Validator
```

Representative updated documents:

```text
01_installation_target_classification.md
02_mac_mini_build_sequence.md
06_implementation_plan.md
12_prompts_core_system.md
```

### Phase 4. Prompt family alignment

Updated prompt documents so generated artifacts must cover:

```text
Class 2 Clarification Manager
clarification interaction payload handling
Class 2 transition tests
Class 2 → Class 1 evaluation
Class 2 → Class 0 evaluation
Class 2 → Safe Deferral / Caregiver Confirmation evaluation
```

Updated prompt documents:

```text
12_prompts.md
12_prompts_mqtt_payload_governance.md
12_prompts_nodes_and_evaluation.md
```

Governance prompt boundary:

```text
clarification_interaction_payload must not become validator approval, actuator authorization, emergency trigger authority, or doorlock unlock approval.
```

### Phase 5. System/component/figure interpretation text, excluding SVG edits

SVG was intentionally not modified.

Instead, explanatory documents were updated to state that the compact figure should be interpreted as supporting the Class 2 clarification/transition loop.

Updated documents:

```text
14_system_components_outline_v2.md
16_system_architecture_figure.md
18_scenario_node_component_mapping.md
```

Added scenario/component mapping for:

```text
class2_to_class1_transition_scenario
class2_to_class0_transition_scenario
class2_timeout_safe_deferral_scenario
```

Figure interpretation now states that the SVG compactly represents Class 2 behavior but does not draw every candidate-generation, selection, timeout, or Policy Router re-entry arrow.

### Phase 6. Install/configuration script-structure documentation

Actual scripts were not changed.

Updated architecture docs only:

```text
10_install_script_structure.md
11_configuration_script_structure.md
```

Added script-structure expectations for:

```text
clarification interaction schema presence checks
Class 2 clarification fixture directory expectations
Class 2 transition verifier dependency readiness
Class 2 topic namespace/configuration assumptions
clarification payload validation mode and report paths
Class 2 transition verify mode and report paths
audit path readiness for candidates, selections, timeouts, transition targets, and final safe outcomes
```

Explicit boundary:

```text
install/configuration tooling must not convert clarification payloads into validator approval, actuation authorization, emergency trigger authority, or doorlock authorization.
```

### Phase 7. Verification sweep

Verification performed:

```text
- searched for stale references:
  - policy_table_v1_1_2_FROZEN
  - class_2_notification_payload_schema_v1_0_0_FROZEN
- directly inspected representative PR-branch files for current references
- compared PR branch against main
- confirmed changed files are architecture docs only
- confirmed SVG files were not changed
- confirmed actual install/configure/verify scripts were not changed
- confirmed PR mergeability was true at verification time
```

A verification summary comment was posted to PR #4.

---

## Important current interpretation

Class 2 is not autonomous actuation.

Class 2 is not merely terminal escalation.

Class 2 is a bounded interaction and transition state that can resolve to:

```text
Class 1 bounded low-risk assistance
Class 0 emergency handling
Safe Deferral
Caregiver Confirmation
```

but only after appropriate evidence and routing:

```text
user/caregiver confirmation
or timeout/no-response result
or deterministic emergency evidence
→ Policy Router re-entry
→ Deterministic Validator when Class 1 is reached
```

---

## Practical guidance for next work

### If implementing runtime code

Start from:

```text
06_implementation_plan.md
12_prompts_core_system.md
19_class2_clarification_architecture_alignment.md
20_scenario_data_flow_matrix.md
```

Required runtime component:

```text
Class 2 Clarification Manager
```

Required schema:

```text
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
```

Do not let runtime code treat clarification payloads as:

```text
validator approval
actuator command
emergency trigger
doorlock authorization
```

### If implementing tests/evaluation

Start from:

```text
12_prompts_nodes_and_evaluation.md
18_scenario_node_component_mapping.md
20_scenario_data_flow_matrix.md
```

Required transition tests:

```text
Class 2 → Class 1
Class 2 → Class 0
Class 2 → Safe Deferral / Caregiver Confirmation
```

Required audit evidence:

```text
clarification candidates
presentation channel
user/caregiver selection
timeout/no-response result
transition target
Policy Router re-entry result
validator result when Class 1 is reached
emergency evidence when Class 0 is reached
final safe outcome
```

### If revising the SVG later

The SVG was intentionally left untouched in PR #4.

Use:

```text
16_system_architecture_figure.md
18_scenario_node_component_mapping.md
19_class2_clarification_architecture_alignment.md
20_scenario_data_flow_matrix.md
```

as the text baseline before interactive SVG changes.

Suggested future SVG additions may include:

```text
Class 2 Clarification Manager sub-block
candidate presentation arrow to TTS/Display
user/caregiver confirmation return path
Policy Router re-entry arrow
Class 2 timeout/safe-deferral path
```

but these should be done interactively because figure density and paper readability need review.

---

## Known limitations / remaining follow-up

1. PR #4 is documentation-only.
2. No runtime implementation was changed.
3. No actual install/configure/verify script was changed.
4. No schema/policy/fixture file was changed.
5. `20_scenario_data_flow_matrix.md` was not rewritten in PR #4 because it already contained the Class 2 clarification/transition matrix and governing schema references, and a full rewrite was considered unnecessarily risky.
6. SVG-level figure updates remain future interactive work.

---

## Current next recommended actions

After PR #4 is merged:

1. Re-read `SESSION_HANDOFF.md` and this addendum first.
2. Confirm the architecture docs are consistent on `main`.
3. Decide whether to implement runtime code next or to do an interactive SVG refinement pass.
4. If implementing code, start with the Class 2 Clarification Manager interfaces and schema-valid `clarification_interaction_payload` fixtures.
5. If implementing tests, start with Class 2 transition fixtures for:
   - Class 2 → Class 1
   - Class 2 → Class 0
   - Class 2 → Safe Deferral / Caregiver Confirmation

# Documentation and Canonical Asset Restructure Plan

## 1. Purpose

This document records the planned cleanup and restructuring work for the
`safe_deferral` repository.

The current repository contains many architecture documents, scenario documents,
schema references, policy references, MQTT references, payload examples, and
handoff notes that were created during rapid iteration. The content is useful,
but the active baseline has become hard to read because:

- architecture documents repeat the same safety boundaries in many places,
- historical and current references are mixed together,
- versioned and `FROZEN` filenames are repeatedly referenced in active docs,
- `CLAUDE.md` has become too long because it carries too much architecture detail,
- `integration/scenarios/` contains scenario-contract files that must be kept
  aligned with architecture and asset naming,
- Python implementation and verification code is currently premature for the
  documentation and contract cleanup phase.

The goal is to make the repository easier to maintain by separating:

- current canonical architecture,
- current canonical assets,
- scenario contracts,
- implementation guidance,
- and historical handoff records.

This plan is a planning document. It does not itself change policy, schema,
MQTT, payload, or scenario authority.

---

## 2. Current Cleanup Decision

Python code has been removed for the current cleanup phase because it creates
noise while the project baseline is being simplified.

Removed categories:

- `mac_mini/code/**/*.py`
- `integration/tests/**/*.py`
- `integration/measurement/**/*.py`
- `integration/scenarios/*.py`

The remaining active baseline should be treated as documentation, policy/schema
assets, MQTT/payload contracts, scripts, scenario JSON, and scenario Markdown.

Python code may be reintroduced later after the canonical document and asset
structure is stable.

---

## 3. Target Principles

### 3.1 Canonical names should be stable

Active files should not encode version strings or `FROZEN` in filenames.

Current active references should use names such as:

```text
common/policies/policy_table.json
common/policies/low_risk_actions.json
common/policies/fault_injection_rules.json
common/policies/output_profile.json

common/schemas/policy_router_input.schema.json
common/schemas/context.schema.json
common/schemas/candidate_action.schema.json
common/schemas/validator_output.schema.json
common/schemas/class2_notification_payload.schema.json
common/schemas/clarification_interaction.schema.json

common/mqtt/topic_registry.json
common/mqtt/publisher_subscriber_matrix.md
common/mqtt/topic_payload_contracts.md
```

Version and historical status should be tracked by manifests, changelogs, git
history, or archive directories rather than by active filenames.

### 3.2 Historical assets should be separated

Superseded assets should move out of the active path.

Recommended archive layout:

```text
common/history/policies/
common/history/schemas/
common/history/mqtt/
common/docs/archive/architecture_legacy/
```

Historical handoff files under `common/docs/runtime/` may keep old filenames and
old references because they are session history.

### 3.3 Active docs should not repeat every boundary

Safety boundaries should be written once in the correct canonical document and
referenced elsewhere.

Repeated sections to consolidate:

- Mac mini / Raspberry Pi / ESP32 role separation,
- Class 1 lighting-only autonomous scope,
- Class 2 clarification / transition semantics,
- `doorbell_detected` visitor-response interpretation,
- doorlock as sensitive actuation,
- MQTT/payload governance non-authority,
- dashboard and governance backend/UI separation.

### 3.4 Scenario files are contracts

Files under `integration/scenarios/` are not ordinary scratch examples. They are
scenario-contract assets and must be aligned with:

- canonical policy names,
- canonical schema names,
- canonical MQTT registry names,
- current Class 2 clarification topic,
- active architecture documents.

### 3.5 `CLAUDE.md` should become a compact operating guide

`CLAUDE.md` should not duplicate architecture documents. It should contain:

- a short project summary,
- the active document read order,
- the most important non-negotiable boundaries,
- current implementation or cleanup starting points,
- and pointers to canonical documents.

Long architecture explanations and large file lists should move out of
`CLAUDE.md`.

---

## 4. Proposed Active Document Structure

The current `common/docs/architecture/01` through `20` document set should be
consolidated into a smaller, clearer active set.

Recommended target:

```text
common/docs/architecture/00_architecture_index.md
common/docs/architecture/01_system_architecture.md
common/docs/architecture/02_safety_and_authority_boundaries.md
common/docs/architecture/03_payload_and_mqtt_contracts.md
common/docs/architecture/04_class2_clarification.md
common/docs/architecture/05_implementation_plan.md
common/docs/architecture/06_deployment_and_scripts.md
common/docs/architecture/07_scenarios_and_evaluation.md
```

### 4.1 `00_architecture_index.md`

Purpose:

- define active document read order,
- distinguish active, reference, and historical documents,
- point to scenario and asset references,
- identify superseded legacy architecture docs.

### 4.2 `01_system_architecture.md`

Consolidates:

- system overview,
- Mac mini / Raspberry Pi 5 / ESP32 / optional timing node roles,
- closed-loop operational path,
- figure interpretation.

Source documents likely merged:

- `01_installation_target_classification.md`
- `02_mac_mini_build_sequence.md`
- `03_deployment_structure.md`
- `14_system_components_outline_v2.md`
- `16_system_architecture_figure.md`

### 4.3 `02_safety_and_authority_boundaries.md`

Consolidates:

- Class 0 / Class 1 / Class 2 boundaries,
- deterministic validator authority,
- LLM non-authority,
- safe deferral,
- caregiver-mediated sensitive path,
- doorbell and doorlock boundary.

Source documents likely merged:

- `13_doorlock_access_control_and_caregiver_escalation.md`
- relevant parts of `15_interface_matrix.md`
- relevant parts of `17_payload_contract_and_registry.md`
- relevant parts of `19_class2_clarification_architecture_alignment.md`

### 4.4 `03_payload_and_mqtt_contracts.md`

Consolidates:

- payload family taxonomy,
- MQTT topic contract rules,
- publisher/subscriber role expectations,
- interface matrix,
- registry-driven lookup expectations,
- governance report non-authority.

Source documents likely merged:

- `15_interface_matrix.md`
- `17_payload_contract_and_registry.md`
- `common/mqtt/README.md`
- `common/payloads/README.md`

### 4.5 `04_class2_clarification.md`

Consolidates:

- Class 2 clarification manager role,
- `safe_deferral/clarification/interaction`,
- clarification payload boundary,
- Policy Router re-entry,
- Class 2 to Class 1 / Class 0 / Safe Deferral / Caregiver Confirmation transitions,
- timeout/no-response behavior.

Source documents likely merged:

- `19_class2_clarification_architecture_alignment.md`
- Class 2 parts of `20_scenario_data_flow_matrix.md`
- Class 2 parts of `12_prompts_*`
- Class 2 scenario docs.

### 4.6 `05_implementation_plan.md`

Consolidates:

- staged implementation order,
- task breakdown,
- immediate next steps,
- additional required work.

Source documents likely merged:

- `06_implementation_plan.md`
- `07_task_breakdown.md`
- `08_additional_required_work.md`
- `09_recommended_next_steps.md`

### 4.7 `06_deployment_and_scripts.md`

Consolidates:

- install / configure / verify structure,
- Mac mini script role,
- RPi script role,
- ESP32 script role,
- deployment-local vs canonical asset boundary.

Source documents likely merged:

- `10_install_script_structure.md`
- `11_configuration_script_structure.md`
- relevant deployment sections from `01` through `04`.

### 4.8 `07_scenarios_and_evaluation.md`

Consolidates:

- scenario taxonomy,
- scenario-to-node/component mapping,
- scenario data-flow matrix,
- evaluation boundary,
- scenario review guidance index.

Source documents likely merged:

- `18_scenario_node_component_mapping.md`
- `20_scenario_data_flow_matrix.md`
- `scenario_data_flows/20_00_interface_role_alignment.md`
- `integration/scenarios/README.md`
- `integration/scenarios/scenario_manifest_rules.md`
- `integration/scenarios/docs/*.md`

---

## 5. Canonical Asset Rename Plan

### 5.1 Policy assets

| Current active or historical file | Target canonical file | Note |
|---|---|---|
| `common/policies/policy_table_v1_2_0_FROZEN.json` | `common/policies/policy_table.json` | Current active routing policy |
| `common/policies/low_risk_actions_v1_1_0_FROZEN.json` | `common/policies/low_risk_actions.json` | Current Class 1 low-risk catalog |
| `common/policies/fault_injection_rules_v1_4_0_FROZEN.json` | `common/policies/fault_injection_rules.json` | Current fault rules |
| `common/policies/output_profile_v1_1_0.json` | `common/policies/output_profile.json` | Current output profile |
| `common/policies/policy_table_v1_1_2_FROZEN.json` | `common/history/policies/policy_table_v1_1_2.json` | Historical |

### 5.2 Schema assets

| Current active or historical file | Target canonical file | Note |
|---|---|---|
| `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json` | `common/schemas/policy_router_input.schema.json` | Current |
| `common/schemas/context_schema_v1_0_0_FROZEN.json` | `common/schemas/context.schema.json` | Current |
| `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json` | `common/schemas/candidate_action.schema.json` | Current |
| `common/schemas/validator_output_schema_v1_1_0_FROZEN.json` | `common/schemas/validator_output.schema.json` | Current |
| `common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json` | `common/schemas/class2_notification_payload.schema.json` | Current |
| `common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json` | `common/schemas/clarification_interaction.schema.json` | Current |
| `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json` | `common/history/schemas/class2_notification_payload_v1_0_0.schema.json` | Historical |

### 5.3 MQTT assets

| Current active or historical file | Target canonical file | Note |
|---|---|---|
| `common/mqtt/topic_registry_v1_1_0.json` | `common/mqtt/topic_registry.json` | Current |
| `common/mqtt/publisher_subscriber_matrix_v1_0_0.md` | `common/mqtt/publisher_subscriber_matrix.md` | Current |
| `common/mqtt/topic_payload_contracts_v1_0_0.md` | `common/mqtt/topic_payload_contracts.md` | Current |
| `common/mqtt/topic_registry_v1_0_0.json` | `common/history/mqtt/topic_registry_v1_0_0.json` | Historical |

### 5.4 Payload assets

Payload example filenames are mostly readable and may remain as-is.

Required updates:

- update schema references inside `common/payloads/README.md`,
- update schema references inside example metadata where present,
- update topic registry references from versioned paths to canonical paths.

---

## 6. Asset Manifest Plan

Add a machine-readable manifest:

```text
common/asset_manifest.json
```

Purpose:

- identify current canonical assets,
- identify historical/superseded assets,
- document old-path to new-path migration,
- provide one stable lookup point for future tooling.

Representative shape:

```json
{
  "current": {
    "policy_table": "common/policies/policy_table.json",
    "low_risk_actions": "common/policies/low_risk_actions.json",
    "fault_injection_rules": "common/policies/fault_injection_rules.json",
    "output_profile": "common/policies/output_profile.json",
    "topic_registry": "common/mqtt/topic_registry.json",
    "context_schema": "common/schemas/context.schema.json",
    "policy_router_input_schema": "common/schemas/policy_router_input.schema.json",
    "candidate_action_schema": "common/schemas/candidate_action.schema.json",
    "validator_output_schema": "common/schemas/validator_output.schema.json",
    "class2_notification_payload_schema": "common/schemas/class2_notification_payload.schema.json",
    "clarification_interaction_schema": "common/schemas/clarification_interaction.schema.json"
  },
  "superseded": {
    "common/policies/policy_table_v1_2_0_FROZEN.json": "common/policies/policy_table.json",
    "common/mqtt/topic_registry_v1_1_0.json": "common/mqtt/topic_registry.json"
  }
}
```

---

## 7. `integration/scenarios/` Restructure Plan

The scenario directory should be treated as a contract layer.

### 7.1 Keep

Keep scenario JSON skeletons as active scenario contracts, but update references
to canonical asset names.

Examples:

- `baseline_scenario_skeleton.json`
- `class1_baseline_scenario_skeleton.json`
- `class0_e001_scenario_skeleton.json`
- `class2_insufficient_context_scenario_skeleton.json`
- `class2_to_class1_low_risk_confirmation_scenario_skeleton.json`
- `class2_to_class0_emergency_confirmation_scenario_skeleton.json`
- `class2_timeout_no_response_safe_deferral_scenario_skeleton.json`
- `class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json`
- `stale_fault_scenario_skeleton.json`
- `conflict_fault_scenario_skeleton.json`
- `missing_state_scenario_skeleton.json`

### 7.2 Update

Update scenario references from versioned names to canonical names:

```text
common/policies/low_risk_actions_v1_1_0_FROZEN.json
→ common/policies/low_risk_actions.json

common/policies/policy_table_v1_2_0_FROZEN.json
→ common/policies/policy_table.json

common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
→ common/schemas/clarification_interaction.schema.json

common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json
→ common/schemas/class2_notification_payload.schema.json

common/mqtt/topic_registry_v1_1_0.json
→ common/mqtt/topic_registry.json

common/mqtt/topic_payload_contracts_v1_0_0.md
→ common/mqtt/topic_payload_contracts.md
```

### 7.3 Consolidate review docs

Current split docs under:

```text
integration/scenarios/docs/
```

should remain preferred over the old monolithic:

```text
integration/scenarios/scenario_review_guide.md
```

Cleanup options:

1. merge the old monolithic guide into the split docs and archive it,
2. replace the old guide with a short compatibility pointer,
3. or move it to `common/docs/archive/`.

### 7.4 Schema and manifest rules

Update:

```text
integration/scenarios/scenario_manifest_schema.json
integration/scenarios/scenario_manifest_rules.md
integration/scenarios/README.md
```

so they reference canonical asset names and current Class 2 rules.

### 7.5 Class 2 topic

All Class 2 scenario contracts should use the current dedicated topic:

```text
safe_deferral/clarification/interaction
```

with:

```text
payload_family: clarification_interaction_payload
schema: common/schemas/clarification_interaction.schema.json
authority_level: class2_interaction_evidence_not_authority
```

---

## 8. `CLAUDE.md` Simplification Plan

After canonical documents and asset names are stable, rewrite `CLAUDE.md` as a
compact operating guide.

Target sections:

1. Project summary
2. Active read order
3. Current canonical assets
4. Non-negotiable safety boundaries
5. Current cleanup / implementation starting point
6. Historical docs rule

Remove:

- long repeated architecture explanations,
- exhaustive file lists,
- old versioned file references in active guidance,
- scenario review guide duplication,
- detailed handoff history.

`CLAUDE.md` should point to canonical architecture docs instead of duplicating
their contents.

---

## 9. Validation Plan

Add a future non-Python validation path or checklist for this cleanup phase.

Minimum checks:

1. Active paths should not reference versioned or `FROZEN` asset filenames.
2. Active paths should use canonical asset names.
3. Historical references should remain only under:
   - `common/history/`
   - `common/docs/runtime/`
   - `common/docs/archive/`
4. `safe_deferral/clarification/interaction` should be present wherever Class 2
   clarification MQTT publication is described.
5. `topic_registry.json` should be the current registry in active docs.
6. `topic_registry_v1_0_0.json` should appear only as historical content.
7. `policy_table_v1_1_2_FROZEN.json` and
   `class_2_notification_payload_schema_v1_0_0_FROZEN.json` should appear only
   as historical content.
8. Active scenario JSON should reference canonical asset names.
9. `CLAUDE.md` should reference only canonical asset names.

Example forbidden active-reference patterns:

```text
_FROZEN
_v1_
topic_registry_v1_
policy_table_v1_
class_2_notification_payload_schema_v1_
clarification_interaction_schema_v1_
```

Exception paths:

```text
common/history/
common/docs/runtime/
common/docs/archive/
```

---

## 10. Recommended Execution Order

### Phase A. Planning baseline

1. Keep this plan as the cleanup anchor.
2. Create a full rename map for active policy/schema/MQTT assets.
3. Decide archive path naming: `common/history/` vs `common/archive/`.
4. Decide whether old architecture docs get moved immediately or first receive
   superseded banners.

### Phase B. Canonical asset rename

1. Rename current policy assets.
2. Rename current schema assets.
3. Rename current MQTT assets.
4. Move superseded policy/schema/MQTT assets to history.
5. Add `common/asset_manifest.json`.

### Phase C. Active reference migration

1. Update README and `CLAUDE.md` references.
2. Update architecture documents or new consolidated docs.
3. Update `integration/scenarios/` JSON and Markdown references.
4. Update `common/payloads/README.md`.
5. Update scripts that still check for old active filenames.

### Phase D. Architecture consolidation

1. Create the new active architecture document set.
2. Merge repeated content into the new documents.
3. Replace old active docs with short superseded notices or move them to archive.
4. Keep figure assets under `figures/` unless a separate figure cleanup is
   intentionally performed.

### Phase E. Scenario consolidation

1. Update scenario skeleton references.
2. Consolidate scenario review guidance.
3. Align scenario manifest schema/rules with canonical names.
4. Keep scenario JSON as active contracts.

### Phase F. `CLAUDE.md` cleanup

1. Rewrite `CLAUDE.md` as a compact guide.
2. Point to `00_architecture_index.md`.
3. Remove redundant architecture blocks and large historical lists.

### Phase G. Final sweep

1. Search for forbidden active-reference patterns.
2. Confirm exceptions are limited to history/runtime/archive.
3. Confirm no Python files remain during this cleanup phase.
4. Confirm active scenario JSON and active docs reference canonical assets.
5. Update `common/docs/runtime/SESSION_HANDOFF.md` with the new cleanup addendum
   after the restructure is complete.

---

## 11. Initial Success Criteria

The cleanup is successful when:

- active canonical assets have stable names without version strings or `FROZEN`,
- active architecture docs are reduced to a small, navigable set,
- Class 2, doorbell, doorlock, and governance boundaries are not repeated across
  many documents,
- `integration/scenarios/` references canonical asset names,
- `CLAUDE.md` becomes short enough to use as an operating guide,
- historical references are isolated under history/runtime/archive paths,
- and no Python code remains in the repository during this documentation and
  contract cleanup phase.


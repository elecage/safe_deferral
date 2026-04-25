# SESSION_HANDOFF_2026-04-25_SCENARIO_DATA_FLOW_MATRIX_PLAN.md

Date: 2026-04-25
Scope: Plan for architecture document 20: scenario-level data-flow matrix
Status: Plan recorded. Architecture document 20 has not yet been created in this step.

## 1. Purpose

This addendum records the plan for creating the following architecture document:

```text
common/docs/architecture/20_scenario_data_flow_matrix.md
```

The document will define scenario-level data flows for the `safe_deferral` project.

It will connect:

```text
scenario → source node/component → destination node/component → interface/topic → payload family → governing policy/schema → expected handling/audit evidence
```

The goal is to provide a traceability matrix that helps developers, reviewers, and paper authors understand how data moves through the system under each scenario.

---

## 2. Planned document role

The planned document is not a new policy or schema authority.

It is a data-flow interpretation and traceability document.

Relationship to existing architecture documents:

```text
15_interface_matrix.md
→ defines general system-wide interfaces.

20_scenario_data_flow_matrix.md
→ explains how each scenario uses those interfaces in concrete data-flow steps.
```

The planned document should be read together with:

```text
common/docs/architecture/14_system_components_outline_v2.md
common/docs/architecture/15_interface_matrix.md
common/docs/architecture/16_system_architecture_figure.md
common/docs/architecture/17_payload_contract_and_registry.md
common/docs/architecture/18_scenario_node_component_hardware_matrix.md
common/docs/architecture/19_class2_clarification_architecture_alignment.md
common/policies/policy_table_v1_2_0_FROZEN.json
common/policies/low_risk_actions_v1_1_0_FROZEN.json
common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json
common/schemas/context_schema_v1_0_0_FROZEN.json
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json
common/schemas/validator_output_schema_v1_1_0_FROZEN.json
common/mqtt/topic_registry_v1_0_0.json
common/mqtt/topic_payload_contracts_v1_0_0.md
integration/scenarios/*.json
integration/tests/data/*.json
```

---

## 3. Recommended file structure

Create one document first:

```text
common/docs/architecture/20_scenario_data_flow_matrix.md
```

Use a single-document structure initially because the current scenario set is still manageable and cross-scenario comparison is important.

Suggested section outline:

```text
# 20_scenario_data_flow_matrix.md

## 1. Purpose
## 2. Scope and authoritative references
## 3. Common data-flow notation
## 4. Common node/component vocabulary
## 5. Common interface/payload vocabulary
## 6. Scenario coverage index
## 7. Scenario-level data-flow matrices
   7.1 Baseline scenario
   7.2 Class 0 E001 high temperature
   7.3 Class 0 E002 triple-hit emergency input
   7.4 Class 0 E003 smoke detected
   7.5 Class 0 E004 gas detected
   7.6 Class 0 E005 fall detected
   7.7 Class 1 bounded low-risk assistance
   7.8 Class 2 insufficient context clarification
   7.9 Stale fault
   7.10 Conflict fault
   7.11 Missing-state fault
## 8. Cross-scenario interface summary
## 9. Policy/schema/topic coverage summary
## 10. Non-authority boundaries
## 11. Future split plan
```

---

## 4. Future split plan

If the document becomes too long, split details into subordinate files later.

Possible future structure:

```text
common/docs/architecture/20_scenario_data_flow_matrix.md
common/docs/architecture/scenario_data_flows/
  20_01_baseline_data_flow.md
  20_02_class0_emergency_data_flows.md
  20_03_class1_data_flow.md
  20_04_class2_clarification_data_flow.md
  20_05_fault_data_flows.md
```

In that future split:

```text
20_scenario_data_flow_matrix.md
→ remains the index and cross-scenario summary.

scenario_data_flows/*.md
→ hold detailed scenario-specific tables.
```

Do not split immediately unless the first full draft becomes difficult to review.

---

## 5. Standard scenario data-flow table format

Each scenario should use the following table format.

```text
| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
```

Meaning of columns:

| Column | Meaning |
|---|---|
| Step | Logical data-flow step number within the scenario |
| Source node/component | Node, runtime component, test fixture producer, or user-facing source that emits data |
| Destination node/component | Node, runtime component, verifier, dispatcher, audit sink, or user-facing sink that receives data |
| Interface / Topic | MQTT topic or internal interface used by the flow |
| Payload family | Payload type or payload family, for example `policy_router_input`, `clarification_interaction`, `validator_output`, `audit_event_payload` |
| Governing policy/schema | Frozen policy, schema, topic contract, or scenario fixture rule that governs the data |
| Data content | Main information conveyed in that step |
| Expected handling | Expected routing, validation, clarification, execution, deferral, ACK, or audit behavior |

---

## 6. Required summary tables

The document should include at least five summary tables.

### 6.1 Scenario coverage index

```text
| Scenario | Scenario file | Class / fault family | Primary ingress topic | Main expected outcome |
|---|---|---|---|---|
```

### 6.2 Scenario data-flow matrix

```text
| Step | Source | Destination | Interface / Topic | Payload | Policy / Schema | Expected handling |
|---|---|---|---|---|---|---|
```

### 6.3 Scenario-to-policy/schema coverage

```text
| Scenario | Policy | Context schema | Class 2 schema | Validator schema | Fixture |
|---|---|---|---|---|---|
```

### 6.4 Scenario-to-MQTT topic coverage

```text
| Scenario | Input topic | Candidate topic | Deferral topic | Escalation topic | Actuation topic | ACK topic | Audit topic |
|---|---|---|---|---|---|---|---|
```

### 6.5 Prohibited authority boundary by scenario

```text
| Scenario | LLM final decision | LLM actuation authority | Doorlock autonomous execution | Emergency trigger by LLM | Unsafe autonomous actuation |
|---|---|---|---|---|---|
```

---

## 7. Scenario-specific writing plan

### 7.1 Baseline scenario

Purpose:

```text
Describe ordinary context input → policy routing → audit observation flow.
```

Focus:

```text
- topic namespace;
- policy_router_input structure;
- audit/log path;
- non-authoritative scenario fixture boundary.
```

### 7.2 Class 0 E001-E005 emergency scenarios

Common flow:

```text
Emergency / sensor / bounded emergency input
→ MQTT Ingestion
→ Policy Router
→ Deterministic Validator
→ Emergency action / guidance / audit
```

Scenario differences:

| Scenario | Trigger family | Main input source | Main payload emphasis |
|---|---|---|---|
| E001 | high temperature | temperature sensor | `environmental_context.temperature` |
| E002 | triple-hit | bounded input node | `trigger_event.event_code` or pattern event |
| E003 | smoke | smoke sensor | `environmental_context.smoke_detected` |
| E004 | gas | gas sensor | `environmental_context.gas_detected` |
| E005 | fall | fall detection node | `trigger_event.event_code = fall_detected` |

Required boundary statements:

```text
- The LLM has no Class 0 emergency trigger authority.
- Class 0 is policy/deterministic-evidence driven.
- doorbell_detected is not emergency evidence.
```

### 7.3 Class 1 bounded low-risk assistance

Planned flow:

```text
Bounded Input / Context Node
→ safe_deferral/context/input
→ MQTT Ingestion
→ Context Aggregation
→ Local LLM candidate generation
→ Policy Router
→ Deterministic Validator
→ safe_deferral/validator/output
→ safe_deferral/actuation/command
→ safe_deferral/actuation/ack
→ safe_deferral/audit/log
```

Focus:

```text
- LLM candidate is not authority.
- Deterministic Validator is final admissibility boundary.
- Low-risk action must remain inside low_risk_actions_v1_1_0_FROZEN.json.
- Doorlock action is not Class 1 autonomous action.
```

### 7.4 Class 2 insufficient context clarification

This should be the most detailed section.

Planned substructure:

```text
7.8.1 Initial Class 2 clarification entry
7.8.2 Candidate prompt generation
7.8.3 User selection → Class 1 transition
7.8.4 User selection → Class 0 transition
7.8.5 Timeout/no-response → Safe Deferral / Caregiver Confirmation
```

Planned flow:

```text
Ambiguous / insufficient context input
→ Policy Router
→ Class 2 clarification state
→ candidate choices generation
→ TTS/display/accessibility feedback
→ user/caregiver selection or timeout
→ CLASS_1 / CLASS_0 / SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
→ audit/log
```

Required references:

```text
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json
common/policies/policy_table_v1_2_0_FROZEN.json
integration/tests/data/expected_class2_candidate_prompt.json
integration/tests/data/sample_class2_user_selection_class1.json
integration/tests/data/expected_class2_transition_class1.json
integration/tests/data/sample_class2_user_selection_class0.json
integration/tests/data/expected_class2_transition_class0.json
integration/tests/data/sample_class2_timeout_no_response.json
integration/tests/data/expected_class2_timeout_safe_deferral.json
```

Required boundary statements:

```text
- candidate_generation_authorizes_actuation = false
- confirmation_required_before_transition = true
- LLM final decision is prohibited
- LLM actuation authority is prohibited
- LLM emergency trigger authority is prohibited
```

### 7.5 Stale fault

Planned flow:

```text
Fault-injected stale context
→ MQTT Ingestion
→ Policy Router / Validator
→ stale state detection
→ Class 2 or Safe Deferral
→ audit/log
```

Focus:

```text
- stale state must not be treated as fresh;
- autonomous actuation is prohibited;
- state recheck or safe deferral is expected.
```

### 7.6 Conflict fault

Planned flow:

```text
Context input with multiple plausible candidates
→ Policy Router / Validator
→ candidate conflict detected
→ bounded conflict-resolution candidates
→ user/caregiver confirmation
→ Class 1 or Safe Deferral
→ audit/log
```

Focus:

```text
- conflict fault is distinct from insufficient context;
- the issue is multiple plausible candidates, not merely absent information;
- arbitrary candidate selection is prohibited;
- conflict cause must remain auditable.
```

### 7.7 Missing-state fault

Planned flow:

```text
Context input with missing required state
→ Policy Router / Validator
→ missing-state detection
→ state recheck or Class 2-like clarification
→ Safe Deferral / Caregiver Confirmation
→ audit/log
```

Focus:

```text
- missing state must not be fabricated;
- missing state must not be assumed safe;
- fault cause must remain auditable.
```

---

## 8. Core design principles to include

The final document must explicitly state:

```text
1. The document is not policy/schema authority.
2. Topics are communication contracts, not execution authority.
3. Payload fixtures are evaluation assets, not policy truth.
4. LLM candidate/guidance is not actuation authority.
5. Class 0 requires deterministic emergency evidence or user/caregiver emergency confirmation.
6. Class 1 requires frozen low-risk catalog membership and deterministic validator approval.
7. Class 2 is a clarification/transition state, not only terminal failure.
8. doorbell_detected is visitor context, not emergency evidence or door-unlock authority.
9. Fault scenario causes must remain auditable.
10. Dashboard/governance/audit artifacts are evidence or visibility artifacts, not control authority.
```

---

## 9. Writing phases for document 20

### Phase A — Reference confirmation

```text
1. Re-read architecture documents 14, 15, 17, 18, and 19.
2. Confirm topic_registry_v1_0_0.json topic list.
3. Confirm policy_table_v1_2_0_FROZEN.json Class 0/1/2 routing semantics.
4. Confirm integration/scenarios/*.json scenario list.
5. Confirm integration/tests/data/*.json fixture references.
```

### Phase B — Common vocabulary

```text
1. Normalize source node/component names.
2. Normalize destination node/component names.
3. Normalize interface/topic names.
4. Normalize payload family names.
5. Normalize policy/schema references.
```

### Phase C — Scenario data-flow tables

```text
1. Baseline.
2. Class 0 E001-E005.
3. Class 1 baseline.
4. Class 2 insufficient context.
5. Stale fault.
6. Conflict fault.
7. Missing-state fault.
```

### Phase D — Cross-scenario summary tables

```text
1. Scenario coverage index.
2. Scenario → policy/schema coverage.
3. Scenario → MQTT topic coverage.
4. Scenario → payload family coverage.
5. Scenario → audit evidence coverage.
6. Scenario → prohibited authority boundary coverage.
```

### Phase E — Save and handoff

```text
1. Create common/docs/architecture/20_scenario_data_flow_matrix.md.
2. Create a dated runtime handoff addendum recording the creation.
3. Update common/docs/runtime/SESSION_HANDOFF.md index.
```

---

## 10. Current decision

Start with a single document:

```text
common/docs/architecture/20_scenario_data_flow_matrix.md
```

Do not create subordinate files initially.

Split into subordinate files only if the first full draft becomes too long or difficult to review.

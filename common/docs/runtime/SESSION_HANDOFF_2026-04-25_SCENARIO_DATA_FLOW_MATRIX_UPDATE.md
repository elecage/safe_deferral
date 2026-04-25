# SESSION_HANDOFF_2026-04-25_SCENARIO_DATA_FLOW_MATRIX_UPDATE.md

Date: 2026-04-25
Scope: Creation of architecture document 20: scenario-level data-flow matrix
Status: Completed.

## 1. Purpose

This addendum records the creation of:

```text
common/docs/architecture/20_scenario_data_flow_matrix.md
```

The new document defines scenario-level data flows for the `safe_deferral` project.

It connects each scenario to:

```text
source node/component → destination node/component → interface/topic → payload family → governing policy/schema → expected handling/audit evidence
```

---

## 2. Created file

Created:

```text
common/docs/architecture/20_scenario_data_flow_matrix.md
```

Commit:

```text
7746447032e39d09e1215c84112caa19c54259a2
```

---

## 3. Reference correction

During creation, the correct document-18 reference was confirmed as:

```text
common/docs/architecture/18_scenario_node_component_mapping.md
```

This supersedes the earlier mistaken filename:

```text
common/docs/architecture/18_scenario_node_component_hardware_matrix.md
```

The new 20번 document uses `18_scenario_node_component_mapping.md` as the vocabulary baseline for nodes and components.

---

## 4. Main contents added

The new document includes:

```text
1. Purpose and scope.
2. Authoritative references and authority interpretation.
3. Common data-flow notation.
4. Common node/component vocabulary based on document 18.
5. Common interface and payload vocabulary.
6. Scenario coverage index.
7. Scenario-level data-flow matrices.
8. Cross-scenario interface summary.
9. Prohibited authority boundary by scenario.
10. Non-authority and safety invariants.
11. Future split plan.
```

---

## 5. Scenario coverage

The document covers these scenario files:

```text
integration/scenarios/baseline_scenario_skeleton.json
integration/scenarios/class1_baseline_scenario_skeleton.json
integration/scenarios/class0_e001_scenario_skeleton.json
integration/scenarios/class0_e002_scenario_skeleton.json
integration/scenarios/class0_e003_scenario_skeleton.json
integration/scenarios/class0_e004_scenario_skeleton.json
integration/scenarios/class0_e005_scenario_skeleton.json
integration/scenarios/class2_insufficient_context_scenario_skeleton.json
integration/scenarios/stale_fault_scenario_skeleton.json
integration/scenarios/conflict_fault_scenario_skeleton.json
integration/scenarios/missing_state_scenario_skeleton.json
```

---

## 6. Key data-flow sections

The scenario-level section includes:

```text
7.1 Baseline scenario
7.2 Class 1 bounded low-risk assistance
7.3 Class 0 E001 high temperature
7.4 Class 0 E002 triple-hit emergency input
7.5 Class 0 E003 smoke detected
7.6 Class 0 E004 gas detected
7.7 Class 0 E005 fall detected
7.8 Class 2 insufficient context clarification
7.9 Stale fault
7.10 Conflict fault
7.11 Missing-state fault
```

Class 2 is further decomposed into:

```text
7.8.1 Initial Class 2 clarification entry
7.8.2 Candidate prompt generation
7.8.3 User selection to Class 1 transition
7.8.4 User selection or evidence to Class 0 transition
7.8.5 Timeout/no-response to safe deferral or caregiver confirmation
```

---

## 7. Cross-scenario summaries added

The document adds these cross-scenario summary tables:

```text
- Scenario coverage index.
- Scenario-to-policy/schema coverage.
- Scenario-to-MQTT topic coverage.
- Scenario-to-payload-family coverage.
- Prohibited authority boundary by scenario.
```

---

## 8. Safety and authority boundaries preserved

The document explicitly preserves these invariants:

```text
- This document is not policy/schema authority.
- Topics are communication contracts, not execution authority.
- Payload fixtures are evaluation assets, not policy truth.
- LLM candidate/guidance is not actuation authority.
- Class 0 requires deterministic emergency evidence or user/caregiver emergency confirmation.
- Class 1 requires frozen low-risk catalog membership and deterministic validator approval.
- Class 2 is a clarification/transition state, not only terminal failure.
- doorbell_detected is visitor context, not emergency evidence or door-unlock authority.
- Fault scenario causes must remain auditable.
- Dashboard/governance/audit artifacts are evidence or visibility artifacts, not control authority.
- Doorlock state is not currently part of pure_context_payload.device_states.
- Class 2 clarification state must not be forced into pure_context_payload.
- Candidate prompts must not be treated as validator output, actuation command, emergency trigger, or doorlock authorization.
- Missing-state handling must not fabricate absent state or assume missing state is safe.
- Conflict handling must not arbitrarily select one plausible candidate.
```

---

## 9. Consistency checks performed

Read before creation:

```text
common/docs/runtime/SESSION_HANDOFF_2026-04-25_SCENARIO_DATA_FLOW_MATRIX_PLAN.md
common/docs/architecture/14_system_components_outline_v2.md
common/docs/architecture/17_payload_contract_and_registry.md
common/docs/architecture/18_scenario_node_component_mapping.md
common/docs/architecture/19_class2_clarification_architecture_alignment.md
```

Created and re-read:

```text
common/docs/architecture/20_scenario_data_flow_matrix.md
```

Confirmed:

```text
- document 20 was created successfully;
- document 20 references the correct document 18 filename;
- node/component vocabulary follows document 18;
- Class 2 clarification/transition semantics are included;
- Class 0, Class 1, Class 2, stale fault, conflict fault, and missing-state fault flows are covered;
- non-authority boundaries are explicitly stated.
```

Note:

```text
The GitHub connector confirmed file creation and content retrieval, but it did not run markdown linting or repository tests.
```

---

## 10. Recommended next step

Recommended next step:

```text
Review common/docs/architecture/20_scenario_data_flow_matrix.md for domain wording and table granularity.
```

Possible follow-up refinements:

```text
1. Add direct fixture filenames to each scenario table row.
2. Add interface IDs from 15_interface_matrix.md once final interface IDs are stable.
3. Add publisher/subscriber roles from publisher_subscriber_matrix_v1_0_0.md.
4. Split detailed sections into common/docs/architecture/scenario_data_flows/ if the document becomes too long.
5. Add a paper-ready condensed table derived from document 20.
```

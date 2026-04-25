# SESSION_HANDOFF_2026-04-25_SCENARIO_DATA_FLOW_INTERFACE_ROLE_ALIGNMENT_UPDATE.md

Date: 2026-04-25
Scope: Refinement of scenario data-flow documentation with interface IDs and MQTT publisher/subscriber roles
Status: Completed.

## 1. Purpose

This addendum records the creation of a companion refinement document for:

```text
common/docs/architecture/20_scenario_data_flow_matrix.md
```

The refinement links scenario-level data flows to:

```text
15_interface_matrix.md interface IDs
publisher_subscriber_matrix_v1_0_0.md publisher/subscriber roles
MQTT topic contracts
payload families
authority boundaries
```

---

## 2. Created file

Created:

```text
common/docs/architecture/scenario_data_flows/20_00_interface_role_alignment.md
```

Commit:

```text
e3f9095b4999229f187ff5a3dea58a835e98be32
```

---

## 3. Why a companion document was created

The existing `20_scenario_data_flow_matrix.md` is already a long table-heavy document.

Rather than rewriting the full document and risking accidental loss of scenario detail, this refinement was added as a companion file under:

```text
common/docs/architecture/scenario_data_flows/
```

This keeps document 20 stable while adding interface-role traceability.

---

## 4. References checked before creation

Checked:

```text
common/docs/architecture/15_interface_matrix.md
common/mqtt/publisher_subscriber_matrix_v1_0_0.md
common/docs/architecture/20_scenario_data_flow_matrix.md
```

Key source interpretations carried forward:

```text
- MQTT topics are communication contracts, not policy authority.
- Context nodes enter through MQTT Ingestion / State Intake.
- Emergency nodes do not use Local LLM as the primary decision path.
- Policy Router must not bypass Deterministic Validator for executable low-risk actuation.
- Dashboard/governance/audit artifacts are not operational control authority.
- doorbell_detected is visitor-response context only.
```

---

## 5. Main contents added

The new companion document includes:

```text
1. Purpose and source references.
2. Core interface ID vocabulary.
3. MQTT publisher/subscriber role alignment.
4. Scenario-to-interface-ID coverage.
5. Scenario-to-topic-role coverage.
6. Interface alignment issues to monitor.
7. Non-authority boundaries for implementation.
```

---

## 6. Important alignment issue recorded

The companion document records a known alignment issue:

```text
safe_deferral/context/input publisher mismatch
```

Current interpretation:

```text
15_interface_matrix.md represents Bounded Input Node, Context Nodes, and Doorbell/Visitor Context Node as architecture-level publishers into safe_deferral/context/input.

publisher_subscriber_matrix_v1_0_0.md currently lists mac_mini.context_aggregator and rpi.simulation_runtime_controlled_mode as publishers.
```

Recommended follow-up:

```text
Revise publisher_subscriber_matrix_v1_0_0.md or add explicit field-side publishers in the next MQTT governance pass so field-side context/input publishers are represented without implying Mac mini is the ordinary field-side source.
```

---

## 7. Scenario coverage included

The companion document maps interface IDs for:

```text
Baseline
Class 1 baseline
Class 0 E001
Class 0 E002
Class 0 E003
Class 0 E004
Class 0 E005
Class 2 insufficient context
Stale fault
Conflict fault
Missing-state fault
```

---

## 8. Safety boundary preserved

The companion document repeats these implementation boundaries:

```text
- Interface IDs describe allowed communication paths, not control permission.
- Publisher/subscriber roles describe expected topic traffic, not policy authority.
- LLM guidance and candidate output never authorize actuation.
- Class 1 actuation requires policy routing, low-risk catalog membership, deterministic validator approval, dispatcher publication, ACK, and audit.
- Class 0 requires deterministic emergency evidence or user/caregiver emergency confirmation.
- Class 2 candidate prompt, selection, timeout, and transition state must remain auditable.
- Doorbell/visitor context does not authorize emergency or doorlock action.
- Dashboard/governance/test artifacts must not publish operational control topics except through explicitly controlled test paths.
```

---

## 9. Recommended next step

Recommended next step:

```text
Update common/mqtt/publisher_subscriber_matrix_v1_0_0.md to resolve the safe_deferral/context/input publisher-role mismatch noted by the new companion document.
```

Possible follow-up:

```text
Add explicit field-side publishers:
- esp32.bounded_input_node
- esp32.context_node
- esp32.doorbell_visitor_context_node

while preserving rpi.simulation_runtime_controlled_mode as controlled-mode publisher only.
```

# SESSION_HANDOFF_2026-04-25_MQTT_CONTEXT_INPUT_PUBLISHER_ALIGNMENT_UPDATE.md

Date: 2026-04-25
Scope: MQTT publisher/subscriber matrix alignment for `safe_deferral/context/input`
Status: Completed.

## 1. Purpose

This addendum records the completion of the follow-up identified in:

```text
common/docs/architecture/scenario_data_flows/20_00_interface_role_alignment.md
```

The issue was the publisher-role mismatch for:

```text
safe_deferral/context/input
```

between:

```text
common/docs/architecture/15_interface_matrix.md
common/mqtt/publisher_subscriber_matrix_v1_0_0.md
```

---

## 2. Updated files

Updated:

```text
common/mqtt/publisher_subscriber_matrix_v1_0_0.md
common/docs/architecture/scenario_data_flows/20_00_interface_role_alignment.md
```

Commits:

```text
publisher_subscriber_matrix_v1_0_0.md: docs(mqtt): align context input publishers with architecture matrix
20_00_interface_role_alignment.md: 7bda227e610e8a960e04e9a0aa0213555f5b5771
```

---

## 3. Change summary

### 3.1 MQTT publisher/subscriber matrix

Updated `safe_deferral/context/input` row.

Previous publisher interpretation:

```text
mac_mini.context_aggregator
rpi.simulation_runtime_controlled_mode
```

Updated publisher interpretation:

```text
esp32.bounded_input_node
esp32.context_node
esp32.doorbell_visitor_context_node
mac_mini.context_aggregator_controlled_bridge
rpi.simulation_runtime_controlled_mode
```

Updated subscriber interpretation:

```text
mac_mini.mqtt_ingestion_state_intake
mac_mini.policy_router
optional audit observer
```

Added clarification section:

```text
Operational vs controlled-mode publisher clarification
```

This section distinguishes:

```text
- field-side operational publishers;
- Mac mini controlled aggregation bridge publisher;
- RPi controlled simulation publisher.
```

### 3.2 Scenario data-flow interface-role companion document

Updated:

```text
common/docs/architecture/scenario_data_flows/20_00_interface_role_alignment.md
```

Changes:

```text
- Updated MQTT publisher/subscriber role alignment table for safe_deferral/context/input.
- Replaced unresolved mismatch note with resolved note.
- Updated scenario-to-topic-role coverage to explicitly include Bounded Input / Context / Doorbell-Visitor Context publishers.
- Added instruction to preserve the operational-vs-controlled-mode distinction in future governance updates.
```

---

## 4. Resolved issue

Resolved:

```text
safe_deferral/context/input publisher mismatch
```

Current interpretation:

```text
field-side operational publishers:
- esp32.bounded_input_node
- esp32.context_node
- esp32.doorbell_visitor_context_node

controlled-mode / bridge publishers:
- mac_mini.context_aggregator_controlled_bridge
- rpi.simulation_runtime_controlled_mode
```

Boundary:

```text
The Mac mini bridge and RPi simulation publisher do not replace ordinary field-side operational publishers. They are controlled-mode or aggregation bridge publishers only.
```

---

## 5. Safety boundaries preserved

The update preserves these boundaries:

```text
- safe_deferral/context/input is an input topic, not execution authority.
- doorbell_detected remains visitor context, not emergency evidence or doorlock authority.
- RPi simulation publication remains controlled-mode only.
- Mac mini bridge publication must not fabricate context or bypass policy routing.
- Field-side context/input publishers provide evidence/input only, not policy authority.
```

---

## 6. Recommended next step

Recommended next step:

```text
Review common/mqtt/topic_registry_v1_0_0.json and common/mqtt/topic_payload_contracts_v1_0_0.md to decide whether publisher/subscriber role metadata should remain documentation-only or be mirrored into machine-readable topic registry metadata.
```

If machine-readable governance is desired, add role metadata in a future topic registry version rather than overloading this draft markdown matrix.

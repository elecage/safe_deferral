# SESSION_HANDOFF_2026-04-25_TOPIC_REGISTRY_ROLE_METADATA_V1_1_UPDATE.md

Date: 2026-04-25
Scope: Machine-readable MQTT publisher/subscriber role metadata registry
Status: Completed.

## 1. Purpose

This addendum records the creation of a new topic registry version with machine-readable publisher/subscriber role metadata.

The change follows the recommendation to avoid directly rewriting the historical v1.0.0 registry and instead introduce a new version:

```text
common/mqtt/topic_registry_v1_1_0.json
```

---

## 2. Created file

Created:

```text
common/mqtt/topic_registry_v1_1_0.json
```

Commit:

```text
97295764fb6e1ba66087d5797f2f357fc0a5a5b9
```

This file supersedes but does not delete:

```text
common/mqtt/topic_registry_v1_0_0.json
```

Interpretation:

```text
v1.0.0 = topic + payload baseline
v1.1.0 = topic + payload + publisher/subscriber role metadata
```

---

## 3. Main additions in v1.1.0

The new registry adds:

```text
registry_version = 1.1.0
supersedes = common/mqtt/topic_registry_v1_0_0.json
role_metadata_note
role_classes
publisher_roles
subscriber_roles
```

Role classes include:

```text
field_operational_publisher
mac_mini_runtime_publisher
mac_mini_controlled_bridge_publisher
controlled_experiment_publisher
runtime_subscriber
actuator_subscriber
observer_subscriber
dashboard_visibility_subscriber
analysis_subscriber
```

---

## 4. Context input publisher role now machine-readable

The following topic now has machine-readable role metadata:

```text
safe_deferral/context/input
```

Operational field-side publishers:

```text
esp32.bounded_input_node
esp32.context_node
esp32.doorbell_visitor_context_node
```

Controlled-mode / bridge publishers:

```text
mac_mini.context_aggregator_controlled_bridge
rpi.simulation_runtime_controlled_mode
```

Runtime subscribers:

```text
mac_mini.mqtt_ingestion_state_intake
mac_mini.policy_router
```

Observer subscriber:

```text
mac_mini.audit_logging_service_observer_optional
```

Boundary:

```text
safe_deferral/context/input is input/evidence only. It is not policy authority or actuation authority.
```

---

## 5. Other topic role metadata added

Role metadata was added for these topics:

```text
safe_deferral/context/input
safe_deferral/emergency/event
safe_deferral/llm/candidate_action
safe_deferral/validator/output
safe_deferral/deferral/request
safe_deferral/escalation/class2
safe_deferral/caregiver/confirmation
safe_deferral/actuation/command
safe_deferral/actuation/ack
safe_deferral/audit/log
safe_deferral/sim/context
safe_deferral/fault/injection
safe_deferral/dashboard/observation
safe_deferral/experiment/progress
safe_deferral/experiment/result
```

---

## 6. Updated human-readable matrix

Updated:

```text
common/mqtt/publisher_subscriber_matrix_v1_0_0.md
```

Change summary:

```text
- Current machine-readable role-metadata source now points to topic_registry_v1_1_0.json.
- topic_registry_v1_0_0.json is explicitly marked as historical topic/payload baseline.
- Added Machine-readable role metadata section.
- Review checklist now includes publisher/subscriber role class validation.
- Dashboard/web-app implications now include role class rendering.
```

---

## 7. Updated scenario data-flow companion document

Updated:

```text
common/docs/architecture/scenario_data_flows/20_00_interface_role_alignment.md
```

Commit:

```text
90ba434461d2a26c85a8ed1d38ccc7578b75f7bd
```

Change summary:

```text
- Added topic_registry_v1_1_0.json as the machine-readable role metadata source.
- Kept topic_registry_v1_0_0.json as historical topic/payload baseline.
- Updated MQTT publisher/subscriber role alignment section to state that roles are mirrored in v1.1.0 using publisher_roles and subscriber_roles.
- Updated context/input mismatch status as resolved in both publisher_subscriber_matrix_v1_0_0.md and topic_registry_v1_1_0.json.
- Added boundary that machine-readable publisher/subscriber role metadata is governance metadata, not control authority.
```

---

## 8. Safety boundaries preserved

The update preserves these boundaries:

```text
- Topics are communication contracts, not execution authority.
- Publisher/subscriber role metadata is governance/verification metadata, not policy authority.
- LLM candidate/guidance topics never authorize actuation.
- safe_deferral/emergency/event requires deterministic emergency evidence or confirmation; LLM text alone must not trigger it.
- safe_deferral/actuation/command must only be published by approved dispatcher roles after validator approval or governed manual confirmation.
- Dashboard/governance/test UI must not directly publish operational control topics.
- RPi simulation/fault publishers are controlled-mode only.
- Doorbell/visitor context remains non-emergency and non-doorlock-authorizing context.
```

---

## 9. Consistency checks performed

Fetched and reviewed before/after:

```text
common/mqtt/topic_registry_v1_0_0.json
common/mqtt/publisher_subscriber_matrix_v1_0_0.md
common/docs/architecture/scenario_data_flows/20_00_interface_role_alignment.md
```

Created:

```text
common/mqtt/topic_registry_v1_1_0.json
```

Updated:

```text
common/mqtt/publisher_subscriber_matrix_v1_0_0.md
common/docs/architecture/scenario_data_flows/20_00_interface_role_alignment.md
```

Note:

```text
The GitHub connector confirmed file creation/update responses. It did not run JSON validation or verifier scripts.
```

Recommended local check:

```bash
python -m json.tool common/mqtt/topic_registry_v1_1_0.json >/dev/null
python integration/scenarios/run_scenario_verification_suite.py --skip-pytest
```

---

## 10. Recommended next step

Recommended next step:

```text
Add or update a verifier so topic_registry_v1_1_0.json role metadata is checked automatically.
```

Verifier should check:

```text
- registry_version == 1.1.0
- every topic has publisher_roles and subscriber_roles
- every publisher listed in publisher_roles appears in publishers
- every subscriber listed in subscriber_roles appears in subscribers
- controlled_experiment_publisher topics are not allowed in operational runtime unless explicitly allowed
- actuation command topic publishers remain dispatcher-only
- dashboard/governance/test roles do not publish operational control topics
```

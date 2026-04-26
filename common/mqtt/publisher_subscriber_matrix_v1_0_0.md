# publisher_subscriber_matrix_v1_0_0.md

## MQTT Publisher / Subscriber Matrix

Status: **DRAFT**

This document summarizes the initial MQTT publisher/subscriber relationships for the `safe_deferral` project.

The current machine-readable role-metadata source is:

- `common/mqtt/topic_registry_v1_1_0.json`

Historical topic/payload baseline:

- `common/mqtt/topic_registry_v1_0_0.json`

This matrix is for review, implementation planning, debugging, governance UI rendering, and Package G validation.
It does not override policy or schema assets.

---

## Matrix

| Topic | Publishers | Subscribers | Payload family | Authority level | Notes |
|---|---|---|---|---|---|
| `safe_deferral/context/input` | `esp32.bounded_input_node`, `esp32.context_node`, `esp32.doorbell_visitor_context_node`, `mac_mini.context_aggregator_controlled_bridge`, `rpi.simulation_runtime_controlled_mode` | `mac_mini.mqtt_ingestion_state_intake`, `mac_mini.policy_router`, optional audit observer | `policy_router_input` | operational input / controlled experiment input | Must include `environmental_context.doorbell_detected`; field-side ESP32 publishers represent operational input; Mac mini bridge and RPi publisher are controlled-mode or aggregation bridge publishers only |
| `safe_deferral/emergency/event` | `esp32.emergency_node`, `rpi.virtual_emergency_sensor_controlled_mode` | `mac_mini.mqtt_ingestion_state_intake`, `mac_mini.policy_router`, optional audit observer | `policy_router_input_or_emergency_context` | emergency operational input / controlled experiment input | Must align with E001~E005; doorbell is not emergency |
| `safe_deferral/llm/candidate_action` | `mac_mini.local_llm_adapter` | `mac_mini.deterministic_validator`, optional audit observer | `candidate_action` | model candidate, not authority | Door unlock is disallowed as current Class 1 candidate |
| `safe_deferral/validator/output` | `mac_mini.deterministic_validator` | dispatcher/deferral handler, audit observer, optional RPi dashboard bridge | `validator_output` | validator decision | Executable payload must stay within low-risk catalog |
| `safe_deferral/deferral/request` | validator, safe deferral handler, Class 2 clarification manager | safe deferral handler, Class 2 clarification manager, audit observer, optional RPi dashboard bridge | `safe_deferral_event` | bounded deferral / clarification control | Future schema recommended |
| `safe_deferral/escalation/class2` | policy router, validator, safe deferral handler, Class 2 clarification manager | outbound notification interface, audit observer, optional dashboard bridge | `class_2_notification_payload` | caregiver escalation / Class 2 clarification notification | Manual confirmation path is not autonomous execution authority |
| `safe_deferral/clarification/interaction` | `mac_mini.class2_clarification_manager`, `mac_mini.caregiver_confirmation_backend` | `mac_mini.audit_logging_service_observer_optional`, `rpi.dashboard_telemetry_bridge_optional`, `rpi.class2_transition_verifier_optional` | `clarification_interaction_payload` | class2 interaction evidence, not authority | Candidate choices, selection, timeout/no-response, transition target, final safe outcome; not validator approval, not actuation authority, not emergency trigger, not doorlock authorization |
| `safe_deferral/caregiver/confirmation` | caregiver confirmation backend, controlled RPi test app mock | caregiver confirmation backend, manual dispatcher path, audit observer, dashboard bridge | `manual_confirmation_payload` | governed manual path | Future schema recommended; mock publisher must be test/evaluation artifact only |
| `safe_deferral/actuation/command` | low-risk dispatcher, manual-path dispatcher | ESP32 lighting node, governed warning/doorlock interface node, audit observer | `actuation_command_payload` | dispatch after approval | Doorlock requires governed manual confirmation path; governance/dashboard/test-app must not publish this directly |
| `safe_deferral/actuation/ack` | ESP32 actuator node, controlled RPi mock actuator | Mac mini ACK handler, audit observer, dashboard bridge | `actuation_ack_payload` | closed-loop evidence | ACK is not pure context input |
| `safe_deferral/audit/log` | Mac mini operational services | Mac mini audit logging service | `audit_event_payload` | evidence / traceability | Audit service should be single DB writer |
| `safe_deferral/sim/context` | RPi simulation runtime | controlled input bridge, RPi orchestrator, RPi dashboard | `policy_router_input_or_context_fixture` | experiment input | Experiment mode only |
| `safe_deferral/fault/injection` | RPi fault injector, RPi orchestrator | RPi simulation runtime, fault injector, optional controlled input bridge | `fault_injection_payload` | experiment fault control | Must derive constraints from frozen assets; `FAULT_CONTRACT_DRIFT_01` is governance/verification only |
| `safe_deferral/dashboard/observation` | RPi orchestrator, dashboard backend, optional Mac mini telemetry bridge | RPi dashboard frontend, optional test app | `dashboard_observation_payload` | visibility, not policy | Retained observation status allowed |
| `safe_deferral/experiment/progress` | RPi orchestrator, integration test runner | RPi dashboard frontend, result exporter | `experiment_progress_payload` | experiment status | Future schema recommended |
| `safe_deferral/experiment/result` | RPi orchestrator, integration test runner, result exporter | RPi dashboard frontend, optional paper analysis tools | `result_export_payload` | experiment artifact | Trace to scenario/run IDs |

---

## Machine-readable role metadata

`topic_registry_v1_1_0.json` mirrors this matrix with structured fields:

```text
publisher_roles
subscriber_roles
role_classes
authority_level
allowed_in_operational_runtime
allowed_in_experiment_runtime
```

Use the JSON registry for automated governance validation and this markdown matrix for human review.

---

## Operational vs controlled-mode publisher clarification

The `safe_deferral/context/input` topic has both operational publishers and controlled-mode publishers.

| Publisher | Publisher class | Intended use | Authority note |
|---|---|---|---|
| `esp32.bounded_input_node` | field-side operational publisher | bounded user input, repeated input, candidate-selection input | Input only; not actuation authority |
| `esp32.context_node` | field-side operational publisher | ordinary environmental or context update | Context only; not policy authority |
| `esp32.doorbell_visitor_context_node` | field-side operational publisher | visitor/doorbell context via `environmental_context.doorbell_detected` | Visitor context only; not emergency evidence or doorlock authority |
| `mac_mini.context_aggregator_controlled_bridge` | Mac mini controlled aggregation bridge | normalized context re-publication only when an implementation explicitly uses a bridge pattern | Bridge must not fabricate context or bypass policy routing |
| `rpi.simulation_runtime_controlled_mode` | controlled evaluation publisher | deterministic scenario replay and integration tests | Experiment mode only |

This clarification aligns this matrix with:

```text
common/docs/architecture/15_interface_matrix.md
common/docs/architecture/scenario_data_flows/20_00_interface_role_alignment.md
common/mqtt/topic_registry_v1_1_0.json
```

---

## Class 2 clarification interaction topic interpretation

The `safe_deferral/clarification/interaction` topic carries Class 2 clarification interaction evidence.

It may include:

```text
candidate choices
presentation channel
user/caregiver selection
timeout/no-response result
transition target
final safe outcome
```

It must not be interpreted as:

```text
validator approval
actuation command
emergency trigger authority
doorlock authorization
```

Selection results require Policy Router re-entry. Class 1 transition still requires Deterministic Validator approval. Class 0 transition requires deterministic emergency evidence or explicit emergency confirmation. Timeout/no-response must not infer user intent.

---

## Governance validation artifacts

The following artifacts may be generated by Package G tooling, verification scripts, or governance backend services:

| Artifact | Producer | Consumer | Authority boundary |
|---|---|---|---|
| interface-matrix alignment report | governance backend / verification script | dashboard, maintainer, CI | Evidence only; not operational authorization |
| topic-drift report | governance backend / verification script | dashboard, maintainer, CI | Evidence only; not policy truth |
| payload validation report | payload validator / governance backend | dashboard, maintainer, CI | Evidence only; not schema authority |
| governance backend/UI separation report | verification script / integration test | dashboard, maintainer, CI | Evidence only; not control authority |
| proposed-change review report | governance backend | maintainer / review workflow | Proposed changes only; not live authority without review |

These artifacts are intentionally not listed as operational MQTT control topics.

---

## Review checklist

Before implementing a topic, confirm:

1. Is the publisher allowed for this topic?
2. Is the subscriber allowed for this topic?
3. Is the publisher/subscriber role class correct in `topic_registry_v1_1_0.json`?
4. Is the payload family correct?
5. Does the payload have a formal schema?
6. If schema-governed, does it validate against `common/schemas/`?
7. Does the topic accidentally give authority to dashboard/test/simulation components?
8. Does the topic accidentally allow doorlock control through Class 1?
9. Does the topic preserve audit/ACK expectations?
10. Does the topic align with `common/docs/architecture/15_interface_matrix.md`?
11. Does the topic align with `common/docs/architecture/17_payload_contract_and_registry.md`?
12. Are referenced example payload files present under `common/payloads/examples/`?
13. Would `FAULT_CONTRACT_DRIFT_01` detect misuse of the topic, payload family, publisher role, or subscriber role?
14. Does `clarification_interaction_payload` remain evidence/transition state rather than operational authorization?

---

## Dashboard / web-app implication

A future MQTT/payload dashboard may render this matrix as a live governance view.

Recommended dashboard capabilities:

- show topic contract rows,
- show allowed publishers/subscribers,
- show publisher/subscriber role classes from `topic_registry_v1_1_0.json`,
- validate example payloads,
- flag unauthorized topic traffic,
- flag payload/schema drift,
- flag topic/payload hardcoding drift,
- show retained dashboard observation state,
- export communication coverage reports,
- export proposed-change review reports.

Forbidden dashboard behavior:

- direct registry-file editing,
- direct operational control-topic publishing,
- direct policy modification,
- direct validator override,
- direct doorlock command dispatch,
- unrestricted actuator console,
- direct caregiver approval spoofing outside controlled test mode,
- treating observation payloads as policy truth.

# 20. Scenario Data-Flow Matrix

## 1. Purpose

This document defines scenario-level data flows for the `safe_deferral` project.

It connects each scenario to:

```text
source node/component → destination node/component → interface/topic → payload family → governing policy/schema → expected handling/audit evidence
```

This document is intended to support:

- scenario implementation,
- node and firmware development,
- Mac mini runtime integration,
- Raspberry Pi scenario orchestration,
- integration-test design,
- paper figure/table preparation,
- and reviewer-facing traceability.

This document is not a new policy or schema authority. It is a data-flow interpretation and traceability document.

---

## 2. Scope and authoritative references

This document should be read together with:

```text
common/docs/architecture/14_system_components_outline_v2.md
common/docs/architecture/15_interface_matrix.md
common/docs/architecture/16_system_architecture_figure.md
common/docs/architecture/17_payload_contract_and_registry.md
common/docs/architecture/18_scenario_node_component_mapping.md
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

Authority interpretation:

| Asset type | Authority |
|---|---|
| Frozen policy files under `common/policies/` | Routing, admissibility, low-risk catalog, emergency/fault semantics |
| Frozen schema files under `common/schemas/` | Machine-readable payload structure |
| MQTT registry/contracts under `common/mqtt/` | Communication contract, not execution authority |
| Scenario skeletons under `integration/scenarios/` | Evaluation scenario structure |
| Fixtures under `integration/tests/data/` | Evaluation/test data, not policy truth |
| This document | Human-readable scenario data-flow interpretation |

---

## 3. Common data-flow notation

Each scenario table uses the following columns.

| Column | Meaning |
|---|---|
| Step | Logical data-flow step within the scenario |
| Source node/component | Node, runtime component, fixture producer, or user-facing source emitting data |
| Destination node/component | Node, runtime component, verifier, dispatcher, audit sink, or user-facing sink receiving data |
| Interface / Topic | MQTT topic or internal interface used by the flow |
| Payload family | Payload type or payload family |
| Governing policy/schema | Frozen policy, schema, topic contract, scenario rule, or fixture rule governing the data |
| Data content | Main data carried in that step |
| Expected handling | Expected route, validation, clarification, execution, deferral, ACK, or audit behavior |

Notation used below:

| Notation | Meaning |
|---|---|
| `MQTT` | Network message over the local MQTT messaging layer |
| `internal` | Internal Mac mini runtime call or state transfer |
| `fixture` | Integration-test fixture or scenario skeleton artifact |
| `audit` | Traceability record, not control authority |
| `guidance` | User-facing LLM/TTS/display text, not execution authority |

---

## 4. Common node/component vocabulary

Node and component names follow `18_scenario_node_component_mapping.md`.

### 4.1 Field-side and user-facing nodes

| Node | Role in data flow |
|---|---|
| Bounded Input Node | Emits constrained user input, repeated input, triple-hit, or candidate-selection input |
| Context Node | Emits environmental or ordinary context state |
| Occupancy/Location Node | Emits room-level occupancy or user-location evidence |
| Device State Reporter Node | Emits current device state and last-report information |
| Device Health Reporter Node | Emits heartbeat, online/offline status, and last-response information |
| Lighting Actuator Node | Receives approved lighting command and returns execution ACK |
| Emergency Node | Aggregates or publishes emergency evidence |
| Temperature Sensor Node | Emits high-temperature evidence for E001 |
| Smoke Sensor Node | Emits smoke evidence for E003 |
| Gas Sensor Node | Emits gas evidence for E004 |
| Fall Detection Node | Emits fall/suspected-fall evidence for E005 |
| Doorbell/Visitor Context Node | Emits visitor/doorbell context as `environmental_context.doorbell_detected` |
| Voice Input Node | Collects short user clarification responses |
| TTS/Voice Output Node | Renders spoken status, warning, and candidate prompts |
| Display Output Node | Displays status, warning, and candidate prompts |
| Warning Output Node | Provides urgent siren/beacon/vibration/visual alert |

### 4.2 System components

| Component | Role in data flow |
|---|---|
| Mac mini Edge Hub | Operational edge hub coordinating intake, routing, validation, guidance, dispatch, ACK, and audit |
| MQTT Broker / Messaging Layer | Transports context, emergency, command, ACK, deferral, confirmation, and audit messages |
| MQTT Ingestion / State Intake | Receives field-side MQTT messages into the Mac mini runtime |
| Context and Runtime State Aggregation | Builds integrated runtime state from context, input, device state, pending clarification, ACK, and escalation status |
| Input Pattern Detector | Classifies single input, repeated input, triple-hit, and candidate-selection input |
| Input Context Mapper | Links input patterns with context to form bounded intent candidates |
| LLM Guidance Layer | Generates bounded candidate choices and user-facing guidance only |
| Class 2 Clarification Manager | Manages Class 2 candidate presentation, selection, timeout, transition, and audit |
| Policy Router | Classifies route family: Class 0, Class 1, Class 2, or conservative fault handling |
| Deterministic Validator | Final admissibility boundary for executable actions |
| Actuator Dispatcher | Publishes only validated commands to actuator nodes |
| Caregiver Notification / Escalation Interface | Sends alerts or confirmation requests to caregiver/administrator |
| Health Check Routine | Re-requests missing state and verifies node health |
| ACK Handling | Receives actuator ACK and updates runtime/audit state |
| Audit Log | Records input, candidates, routing, validation, transition, execution, deferral, ACK, and notification outcomes |
| Raspberry Pi Scenario Orchestrator | Evaluation-layer scenario execution/replay/fault injection support; not operational authority |

---

## 5. Common interface and payload vocabulary

### 5.1 Main MQTT topics

| Topic | Typical role | Authority note |
|---|---|---|
| `safe_deferral/context/input` | Main operational context and bounded input ingress | Input plane only; not execution authority |
| `safe_deferral/emergency/event` | Emergency event ingress | Evidence input; still policy-routed |
| `safe_deferral/deferral/request` | Safe-deferral or clarification request | Clarification/deferral signal, not actuation authority |
| `safe_deferral/escalation/class2` | Class 2 escalation/notification path | Notification/escalation path, not autonomous execution |
| `safe_deferral/caregiver/confirmation` | Caregiver confirmation | Manual confirmation evidence, not Class 1 autonomous approval |
| `safe_deferral/validator/output` | Validator result output | Final admissibility evidence for executable low-risk action |
| `safe_deferral/actuation/command` | Approved actuation command | Must be produced only after policy/validator approval |
| `safe_deferral/actuation/ack` | Actuator ACK or state confirmation | Closed-loop evidence |
| `safe_deferral/audit/log` | Audit event stream | Evidence/traceability only |

### 5.2 Main payload families

| Payload family | Governing asset | Notes |
|---|---|---|
| `policy_router_input` | `policy_router_input_schema_v1_1_1_FROZEN.json` | Wrapper around source, routing metadata, and pure context payload |
| `pure_context_payload` | `context_schema_v1_0_0_FROZEN.json` | Physical/context input only; not manual approval, ACK, or Class 2 interaction state |
| `environmental_context` | `context_schema_v1_0_0_FROZEN.json` | Includes `doorbell_detected`; doorbell is visitor context, not emergency/door unlock authority |
| `device_states` | `context_schema_v1_0_0_FROZEN.json` | Current schema excludes doorlock state |
| `clarification_interaction` | `clarification_interaction_schema_v1_0_0_FROZEN.json` | Candidate choices, selection, timeout, transition target; not actuation authority |
| `class_2_notification_payload` | `class_2_notification_payload_schema_v1_1_0_FROZEN.json` | Notification/escalation/clarification support |
| `candidate_action` | `candidate_action_schema_v1_0_0_FROZEN.json` | LLM-proposed bounded action candidate; must be validated |
| `validator_output` | `validator_output_schema_v1_1_0_FROZEN.json` | Final admissibility output for execution path |
| `actuation_command_payload` | Topic contract / dispatcher implementation | Must follow validator approval |
| `actuation_ack_payload` | Future ACK schema / runtime contract | Closed-loop result evidence |
| `audit_event_payload` | Audit runtime contract / future schema | Traceability only |
| `scenario_fixture_payload` | Scenario/fixture files + relevant schemas | Evaluation asset only |

---

## 6. Scenario coverage index

| Scenario | Scenario file | Class / fault family | Primary ingress topic | Main expected outcome |
|---|---|---|---|---|
| Baseline | `integration/scenarios/baseline_scenario_skeleton.json` | Baseline / normal routing | `safe_deferral/context/input` | Context routed and audited; low-risk path if admissible |
| Class 1 baseline | `integration/scenarios/class1_baseline_scenario_skeleton.json` | Class 1 bounded assistance | `safe_deferral/context/input` | Low-risk lighting assistance after validation |
| Class 0 E001 | `integration/scenarios/class0_e001_scenario_skeleton.json` | Emergency high temperature | `safe_deferral/emergency/event` | Class 0 emergency handling |
| Class 0 E002 | `integration/scenarios/class0_e002_scenario_skeleton.json` | Emergency triple-hit input | `safe_deferral/emergency/event` | Class 0 emergency handling |
| Class 0 E003 | `integration/scenarios/class0_e003_scenario_skeleton.json` | Emergency smoke detected | `safe_deferral/emergency/event` | Class 0 emergency handling |
| Class 0 E004 | `integration/scenarios/class0_e004_scenario_skeleton.json` | Emergency gas detected | `safe_deferral/emergency/event` | Class 0 emergency handling |
| Class 0 E005 | `integration/scenarios/class0_e005_scenario_skeleton.json` | Emergency fall detected | `safe_deferral/emergency/event` | Class 0 emergency handling |
| Class 2 insufficient context | `integration/scenarios/class2_insufficient_context_scenario_skeleton.json` | Class 2 clarification/transition | `safe_deferral/context/input` | Candidate clarification, then Class 1 / Class 0 / Safe Deferral |
| Stale fault | `integration/scenarios/stale_fault_scenario_skeleton.json` | Stale-state fault | `safe_deferral/context/input` | Conservative Class 2 or safe deferral handling |
| Conflict fault | `integration/scenarios/conflict_fault_scenario_skeleton.json` | Multiple plausible candidates | `safe_deferral/context/input` | Confirmation or safe deferral; no arbitrary selection |
| Missing-state fault | `integration/scenarios/missing_state_scenario_skeleton.json` | Missing required state | `safe_deferral/context/input` | State recheck, Class 2-like handling, or safe deferral |

---

## 7. Scenario-level data-flow matrices

## 7.1 Baseline scenario

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | Bounded Input Node / Context Node / Device State Reporter Node | MQTT Broker / Messaging Layer | `safe_deferral/context/input` | `policy_router_input` | `policy_router_input_schema_v1_1_1_FROZEN.json`, `context_schema_v1_0_0_FROZEN.json` | Ordinary bounded input and environmental/device state | Input is delivered to Mac mini intake |
| 2 | MQTT Ingestion / State Intake | Context and Runtime State Aggregation | internal | `pure_context_payload` | `context_schema_v1_0_0_FROZEN.json` | Trigger event, environmental context, device states | Runtime state is updated without creating actuation authority |
| 3 | Context and Runtime State Aggregation | Policy Router | internal | `policy_router_input` | `policy_table_v1_2_0_FROZEN.json` | Normal non-emergency context | Route is selected according to policy |
| 4 | Policy Router | Deterministic Validator | internal | route decision / candidate action | `low_risk_actions_v1_1_0_FROZEN.json`, `validator_output_schema_v1_1_0_FROZEN.json` | Candidate low-risk action if applicable | Validator decides admissibility |
| 5 | Deterministic Validator / Actuator Dispatcher | Lighting Actuator Node | `safe_deferral/actuation/command` | `actuation_command_payload` | Validator output + topic contract | Approved lighting command only | Command is dispatched only if validated |
| 6 | Lighting Actuator Node | ACK Handling / Audit Log | `safe_deferral/actuation/ack`, `safe_deferral/audit/log` | `actuation_ack_payload`, `audit_event_payload` | ACK/audit runtime contract | Execution result | Closed-loop outcome is recorded |

---

## 7.2 Class 1 bounded low-risk assistance

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | Bounded Input Node / Context Node | MQTT Ingestion / State Intake | `safe_deferral/context/input` | `policy_router_input` | `policy_router_input_schema_v1_1_1_FROZEN.json` | User input plus lighting-relevant context | Input enters bounded assistance path |
| 2 | Context and Runtime State Aggregation | Input Context Mapper / LLM Guidance Layer | internal | runtime context summary / candidate guidance | `14_system_components_outline_v2.md`, `17_payload_contract_and_registry.md` | Likely low-risk lighting intent | LLM may generate candidate/guidance only |
| 3 | LLM Guidance Layer / Input Context Mapper | Policy Router | internal | `candidate_action` or mapped candidate intent | `candidate_action_schema_v1_0_0_FROZEN.json`, `policy_table_v1_2_0_FROZEN.json` | Candidate bounded assistance action | Candidate is not execution authority |
| 4 | Policy Router | Deterministic Validator | internal / `safe_deferral/validator/output` | `validator_output` | `low_risk_actions_v1_1_0_FROZEN.json`, `validator_output_schema_v1_1_0_FROZEN.json` | Low-risk lighting candidate | Validator must approve exactly one admissible action |
| 5 | Deterministic Validator | Actuator Dispatcher | internal | validated execution request | `validator_output_schema_v1_1_0_FROZEN.json` | Approved low-risk lighting action | Dispatcher may publish command |
| 6 | Actuator Dispatcher | Lighting Actuator Node | `safe_deferral/actuation/command` | `actuation_command_payload` | Topic contract + validator result | Lighting on/off command | Execute lighting command only |
| 7 | Lighting Actuator Node | ACK Handling / Audit Log / TTS Output | `safe_deferral/actuation/ack`, `safe_deferral/audit/log` | ACK + audit + guidance | ACK/audit runtime contract | Success/failure/timeout | User receives result; audit is closed |

Boundary: Class 1 autonomous execution is limited to the frozen low-risk catalog. Doorlock-sensitive actions are not Class 1 autonomous execution.

---

## 7.3 Class 0 E001 high temperature

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | Temperature Sensor Node / Emergency Node | MQTT Broker / Messaging Layer | `safe_deferral/emergency/event` | emergency evidence / `policy_router_input` after normalization | `policy_table_v1_2_0_FROZEN.json`, `context_schema_v1_0_0_FROZEN.json` | Abnormal high temperature evidence | Emergency evidence is delivered |
| 2 | MQTT Ingestion / State Intake | Policy Router | internal or normalized `safe_deferral/context/input` | normalized policy-router input | `policy_router_input_schema_v1_1_1_FROZEN.json` | E001-like temperature evidence | Policy Router selects Class 0 |
| 3 | Policy Router | Emergency handling / Caregiver Notification / Audit Log | internal + `safe_deferral/audit/log` | routing decision + audit event | `policy_table_v1_2_0_FROZEN.json` | `canonical_emergency_family = E001` | Emergency path proceeds without LLM final decision |
| 4 | Emergency handling | Warning Output Node / TTS Output / Caregiver Interface | warning output / notification interface | warning / class 2 notification if needed | output profile + emergency policy | Emergency warning/notification | User/caregiver is alerted |
| 5 | Emergency handling | Audit Log | `safe_deferral/audit/log` | `audit_event_payload` | audit runtime contract | Emergency route and notification result | Trace is recorded |

---

## 7.4 Class 0 E002 triple-hit emergency input

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | Bounded Input Node | Input Pattern Detector | local node firmware or internal | bounded input pattern | `policy_table_v1_2_0_FROZEN.json` | Repeated/triple-hit input pattern | Triple-hit evidence is detected |
| 2 | Input Pattern Detector / Emergency Node | MQTT Broker / Messaging Layer | `safe_deferral/emergency/event` | emergency event / policy-router input after normalization | topic registry + policy table | E002 triple-hit event | Emergency input is delivered |
| 3 | MQTT Ingestion / State Intake | Policy Router | internal | normalized policy-router input | `policy_router_input_schema_v1_1_1_FROZEN.json` | E002 evidence | Route to Class 0 |
| 4 | Policy Router | Caregiver Notification / Warning Output / TTS Output | internal / output interface | emergency notification/guidance | `policy_table_v1_2_0_FROZEN.json` | User-requested emergency help | Alert or emergency assistance path proceeds |
| 5 | Policy Router / Emergency handling | Audit Log | `safe_deferral/audit/log` | `audit_event_payload` | audit runtime contract | E002 classification and handling result | Trace is recorded |

Class 2 relationship: if a triple-hit occurs during Class 2 clarification, it may provide deterministic emergency evidence for transition to Class 0. LLM candidate text alone must not trigger E002.

---

## 7.5 Class 0 E003 smoke detected

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | Smoke Sensor Node / Emergency Node | MQTT Broker / Messaging Layer | `safe_deferral/emergency/event` | emergency evidence / normalized input | `context_schema_v1_0_0_FROZEN.json`, `policy_table_v1_2_0_FROZEN.json` | `environmental_context.smoke_detected=true` or equivalent E003 evidence | Smoke evidence is delivered |
| 2 | MQTT Ingestion / State Intake | Policy Router | internal | `policy_router_input` | `policy_router_input_schema_v1_1_1_FROZEN.json` | E003 smoke evidence | Route to Class 0 |
| 3 | Policy Router | Emergency handling / Warning Output Node | internal / warning output | emergency route output | `policy_table_v1_2_0_FROZEN.json` | `canonical_emergency_family = E003` | Warning/notification path proceeds |
| 4 | Emergency handling | Caregiver Notification / TTS Output / Audit Log | notification + `safe_deferral/audit/log` | notification + audit event | output profile + audit contract | Smoke emergency warning and result | User/caregiver alerted and trace recorded |

---

## 7.6 Class 0 E004 gas detected

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | Gas Sensor Node / Emergency Node | MQTT Broker / Messaging Layer | `safe_deferral/emergency/event` | emergency evidence / normalized input | `context_schema_v1_0_0_FROZEN.json`, `policy_table_v1_2_0_FROZEN.json` | `environmental_context.gas_detected=true` or equivalent E004 evidence | Gas evidence is delivered |
| 2 | MQTT Ingestion / State Intake | Policy Router | internal | `policy_router_input` | `policy_router_input_schema_v1_1_1_FROZEN.json` | E004 gas evidence | Route to Class 0 |
| 3 | Policy Router | Emergency handling / Warning Output Node | internal / warning output | emergency route output | `policy_table_v1_2_0_FROZEN.json` | `canonical_emergency_family = E004` | Warning/notification path proceeds |
| 4 | Emergency handling | Caregiver Notification / TTS Output / Audit Log | notification + `safe_deferral/audit/log` | notification + audit event | output profile + audit contract | Gas emergency warning and result | User/caregiver alerted and trace recorded |

---

## 7.7 Class 0 E005 fall detected

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | Fall Detection Node / Wearable Sensor Node / Motion Sensor Node / Vision/Depth Sensor Node | Emergency Node | local sensor interface | fall evidence | `policy_table_v1_2_0_FROZEN.json` | Fall or suspected-fall evidence | Fall evidence is generated |
| 2 | Emergency Node | MQTT Broker / Messaging Layer | `safe_deferral/emergency/event` | emergency event / normalized input | topic registry + policy table | E005 fall event | Emergency event is delivered |
| 3 | MQTT Ingestion / State Intake | Policy Router | internal | `policy_router_input` | `policy_router_input_schema_v1_1_1_FROZEN.json` | E005 evidence | Route to Class 0 |
| 4 | Policy Router | Caregiver Notification / TTS Output / Warning Output Node | internal / notification/output | emergency notification/guidance | `policy_table_v1_2_0_FROZEN.json`, output profile | Fall emergency warning or assistance request | User/caregiver alerted |
| 5 | Emergency handling | Audit Log | `safe_deferral/audit/log` | `audit_event_payload` | audit runtime contract | E005 route and handling result | Trace is recorded |

Class 2 relationship: if fall/emergency confirmation or deterministic fall evidence arrives during Class 2 clarification, the system may transition to Class 0. LLM candidate text alone must not trigger E005.

---

## 7.8 Class 2 insufficient context clarification

Class 2 is a clarification/transition state, not a terminal failure by default.

### 7.8.1 Initial Class 2 clarification entry

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | Bounded Input Node / Context Node / Device State Reporter Node | MQTT Ingestion / State Intake | `safe_deferral/context/input` | `policy_router_input` | `policy_router_input_schema_v1_1_1_FROZEN.json`, `context_schema_v1_0_0_FROZEN.json` | Ambiguous or insufficient context input | Input enters routing path |
| 2 | Context and Runtime State Aggregation | Policy Router / Deterministic Validator | internal | routing input / unresolved reason | `policy_table_v1_2_0_FROZEN.json` | Insufficient context or ambiguous user intent | Direct execution is blocked |
| 3 | Policy Router / Validator | Class 2 Clarification Manager | internal / `safe_deferral/deferral/request` | class 2 entry / deferral request | `policy_table_v1_2_0_FROZEN.json`, `class_2_notification_payload_schema_v1_1_0_FROZEN.json` | Class 2 clarification state | Candidate clarification may begin |
| 4 | Class 2 Clarification Manager | Audit Log | `safe_deferral/audit/log` | `audit_event_payload` | audit runtime contract | Initial ambiguous input and unresolved reason | Entry is recorded |

### 7.8.2 Candidate prompt generation

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | Class 2 Clarification Manager | LLM Guidance Layer / Input Context Mapper | internal | clarification request | `clarification_interaction_schema_v1_0_0_FROZEN.json` | Request for bounded candidate choices | LLM may generate candidates only |
| 2 | LLM Guidance Layer / Input Context Mapper | Class 2 Clarification Manager | internal | `clarification_interaction` | `clarification_interaction_schema_v1_0_0_FROZEN.json` | Candidate choices, transition targets, confirmation requirement | Candidate text is guidance, not authority |
| 3 | Class 2 Clarification Manager | TTS/Voice Output Node / Display Output Node | output interface / `safe_deferral/deferral/request` where used | candidate prompt / user-facing guidance | output profile + clarification schema | Accessible prompt such as lighting, emergency help, caregiver, cancel/wait | User receives bounded choices |
| 4 | Class 2 Clarification Manager | Audit Log | `safe_deferral/audit/log` | `audit_event_payload` | audit runtime contract | Candidate choices and presentation channel | Candidate prompt is recorded |

### 7.8.3 User selection to Class 1 transition

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | User / Bounded Input Node / Voice Input Node | MQTT Ingestion / State Intake | `safe_deferral/context/input` | selection input / `clarification_interaction` | `clarification_interaction_schema_v1_0_0_FROZEN.json` | User confirms low-risk lighting candidate | Confirmation evidence is collected |
| 2 | Class 2 Clarification Manager | Policy Router | internal | transition request | `policy_table_v1_2_0_FROZEN.json` | `transition_target=CLASS_1` | Re-enter policy routing |
| 3 | Policy Router | Deterministic Validator | internal / `safe_deferral/validator/output` | `validator_output` | `low_risk_actions_v1_1_0_FROZEN.json`, `validator_output_schema_v1_1_0_FROZEN.json` | Confirmed low-risk lighting candidate | Validator must approve before dispatch |
| 4 | Deterministic Validator / Actuator Dispatcher | Lighting Actuator Node | `safe_deferral/actuation/command` | `actuation_command_payload` | validator output + topic contract | Approved lighting command | Execute only if single admissible action |
| 5 | Lighting Actuator Node | ACK Handling / Audit Log / TTS Output | `safe_deferral/actuation/ack`, `safe_deferral/audit/log` | ACK + audit + guidance | ACK/audit runtime contract | Execution result | User receives result and audit is closed |

### 7.8.4 User selection or evidence to Class 0 transition

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | User / Bounded Input Node / Caregiver / Emergency Node | MQTT Ingestion / State Intake | `safe_deferral/context/input`, `safe_deferral/emergency/event`, or `safe_deferral/caregiver/confirmation` | emergency confirmation / deterministic evidence | `policy_table_v1_2_0_FROZEN.json` | User/caregiver emergency confirmation, triple-hit, or E001-E005 evidence | Emergency evidence is collected |
| 2 | Class 2 Clarification Manager / Policy Router | Policy Router | internal | transition request | `policy_table_v1_2_0_FROZEN.json` | `transition_target=CLASS_0` | Route to emergency path |
| 3 | Policy Router | Emergency handling / Caregiver Notification / Warning Output | internal / notification/output | emergency route output | emergency policy + output profile | Confirmed emergency or deterministic emergency evidence | Class 0 handling proceeds |
| 4 | Emergency handling | Audit Log | `safe_deferral/audit/log` | `audit_event_payload` | audit runtime contract | Emergency evidence, transition, notification result | Trace is recorded |

### 7.8.5 Timeout/no-response to safe deferral or caregiver confirmation

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | Class 2 Clarification Manager | Class 2 Clarification Manager | internal timer | timeout/no-response state | `clarification_interaction_schema_v1_0_0_FROZEN.json` | No user/caregiver response or ambiguous response | Do not assume intent |
| 2 | Class 2 Clarification Manager | Safe Deferral / Caregiver Notification | `safe_deferral/deferral/request` or `safe_deferral/escalation/class2` | deferral / notification payload | `class_2_notification_payload_schema_v1_1_0_FROZEN.json`, policy table | `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION` | No autonomous actuation |
| 3 | Safe Deferral / Caregiver Notification | TTS/Voice Output Node / Display Output Node / Caregiver | output/notification interface | guidance / notification | output profile | Explain waiting, cancellation, or caregiver confirmation | User/caregiver is informed |
| 4 | Class 2 Clarification Manager | Audit Log | `safe_deferral/audit/log` | `audit_event_payload` | audit runtime contract | Timeout/no-response and final safe outcome | Trace is recorded |

---

## 7.9 Stale fault

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | Raspberry Pi Scenario Orchestrator / Fault Injection | MQTT Ingestion / State Intake | `safe_deferral/context/input` | fault-injected `policy_router_input` | fault injection rules + context schema | Stale timestamp or old context state | Fault condition is delivered |
| 2 | MQTT Ingestion / State Intake | Policy Router / Deterministic Validator | internal | policy-router input | policy table + staleness rules | Policy-relevant stale state | Stale state is not treated as fresh |
| 3 | Policy Router / Validator | Safe Deferral / Class 2 Clarification Manager | internal / `safe_deferral/deferral/request` | deferral or Class 2 state | `policy_table_v1_2_0_FROZEN.json` | Staleness reason | Direct autonomous actuation is blocked |
| 4 | Safe Deferral / Class 2 Manager | TTS/Display / Caregiver where needed | output / escalation interface | guidance / notification | class 2 notification schema where used | Recheck/wait/caregiver message | User or caregiver is informed |
| 5 | Policy Router / Safe Deferral | Audit Log | `safe_deferral/audit/log` | `audit_event_payload` | audit runtime contract | Stale fault cause and final outcome | Fault cause remains auditable |

---

## 7.10 Conflict fault

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | Bounded Input Node / Context Node / Occupancy Node / Device State Reporter Node | MQTT Ingestion / State Intake | `safe_deferral/context/input` | fault-injected `policy_router_input` | context schema + scenario fixture | Context with multiple plausible candidates | Input is delivered |
| 2 | Context and Runtime State Aggregation | Input Context Mapper / Policy Router / Validator | internal | candidate set / route input | policy table + validator rules | Multiple simultaneously plausible candidates | Conflict is detected |
| 3 | Policy Router / Validator | Class 2 Clarification Manager / LLM Guidance Layer | internal / `safe_deferral/deferral/request` | `clarification_interaction` | `clarification_interaction_schema_v1_0_0_FROZEN.json` | Bounded conflict-resolution candidates | Candidates may be presented; no arbitrary selection |
| 4 | Class 2 Clarification Manager | TTS/Voice Output Node / Display Output Node | output interface | candidate prompt | output profile + clarification schema | Options such as living room light / bedroom light / cancel | User is asked to confirm |
| 5 | User / Bounded Input Node / Caregiver | Policy Router / Validator or Safe Deferral | `safe_deferral/context/input` or `safe_deferral/caregiver/confirmation` | selection / confirmation | policy table + validator schema | Selected candidate or unresolved conflict | Confirmed Class 1 candidate must be validated; unresolved conflict defers |
| 6 | Class 2 Manager / Validator | Audit Log | `safe_deferral/audit/log` | `audit_event_payload` | audit runtime contract | Candidate set, confirmation requirement, final outcome | Conflict cause remains auditable |

Conflict fault is distinct from Class 2 insufficient context: information exists, but multiple candidates remain plausible. The system must not choose one arbitrarily.

---

## 7.11 Missing-state fault

| Step | Source node/component | Destination node/component | Interface / Topic | Payload family | Governing policy/schema | Data content | Expected handling |
|---|---|---|---|---|---|---|---|
| 1 | Context Node / Device State Reporter Node / Device Health Reporter Node / Fault Injection | MQTT Ingestion / State Intake | `safe_deferral/context/input` | fault-injected `policy_router_input` | context schema + scenario fixture | Missing required state, absent device report, or health gap | Input is delivered |
| 2 | MQTT Ingestion / State Intake | Health Check Routine / Policy Router / Validator | internal | missing-state evidence | policy table + fault rules | Missing state keys or stale heartbeat | Missing state is detected |
| 3 | Health Check Routine | Device State Reporter Node / Device Health Reporter Node | heartbeat/state recheck interface | state recheck request | health-check runtime contract | Request current state or heartbeat | System tries to recover state if available |
| 4 | Policy Router / Validator | Safe Deferral / Class 2 Clarification Manager | internal / `safe_deferral/deferral/request` | deferral / clarification state | policy table + clarification schema | State cannot be trusted or recovered | Do not fabricate state; do not assume safe |
| 5 | Safe Deferral / Class 2 Manager | TTS/Display / Caregiver Notification | output / escalation interface | guidance / notification | class 2 notification schema where used | Recheck failed, waiting, caregiver confirmation, or safe deferral | User/caregiver is informed |
| 6 | Health Check / Safe Deferral / Validator | Audit Log | `safe_deferral/audit/log` | `audit_event_payload` | audit runtime contract | Missing keys, recheck attempt, final safe outcome | Missing-state cause remains auditable |

Missing-state fault is distinct from Class 2 insufficient context: the issue is absent required device/context state, not only ambiguous intent.

---

## 8. Cross-scenario interface summary

## 8.1 Scenario-to-policy/schema coverage

| Scenario | Policy | Context/input schema | Class 2 schema | Validator schema | Key fixture family |
|---|---|---|---|---|---|
| Baseline | `policy_table_v1_2_0_FROZEN.json` | `policy_router_input_schema_v1_1_1_FROZEN.json`, `context_schema_v1_0_0_FROZEN.json` | Not primary | `validator_output_schema_v1_1_0_FROZEN.json` if execution occurs | baseline routing fixtures |
| Class 1 | `policy_table_v1_2_0_FROZEN.json`, `low_risk_actions_v1_1_0_FROZEN.json` | input/context schemas | Not primary | `validator_output_schema_v1_1_0_FROZEN.json` | `expected_routing_class1.json` |
| E001 | `policy_table_v1_2_0_FROZEN.json` | input/context schemas | Not primary | Emergency validation path | E001 emergency fixtures |
| E002 | `policy_table_v1_2_0_FROZEN.json` | input/context schemas | Possible transition relation | Emergency validation path | E002 triple-hit fixtures |
| E003 | `policy_table_v1_2_0_FROZEN.json` | input/context schemas | Not primary | Emergency validation path | E003 smoke fixtures |
| E004 | `policy_table_v1_2_0_FROZEN.json` | input/context schemas | Not primary | Emergency validation path | E004 gas fixtures |
| E005 | `policy_table_v1_2_0_FROZEN.json` | input/context schemas | Possible transition relation | Emergency validation path | E005 fall fixtures |
| Class 2 | `policy_table_v1_2_0_FROZEN.json` | input/context schemas | `clarification_interaction_schema_v1_0_0_FROZEN.json`, `class_2_notification_payload_schema_v1_1_0_FROZEN.json` | Used after Class 1 transition | Class 2 candidate/selection/timeout fixtures |
| Stale fault | `policy_table_v1_2_0_FROZEN.json`, fault rules | input/context schemas | May use Class 2-like handling | Validator blocks unsafe execution | stale fault fixture |
| Conflict fault | `policy_table_v1_2_0_FROZEN.json`, fault rules | input/context schemas | `clarification_interaction_schema_v1_0_0_FROZEN.json` where candidates are presented | Validator required before Class 1 execution | conflict expected safe-deferral fixture |
| Missing-state fault | `policy_table_v1_2_0_FROZEN.json`, fault rules | input/context schemas | May use Class 2-like handling | Validator blocks unsafe execution | missing-state expected safe-deferral fixture |

## 8.2 Scenario-to-MQTT topic coverage

| Scenario | Input topic | Candidate/deferral topic | Escalation/confirmation topic | Actuation topic | ACK topic | Audit topic |
|---|---|---|---|---|---|---|
| Baseline | `safe_deferral/context/input` | Optional `safe_deferral/deferral/request` | Optional | `safe_deferral/actuation/command` if validated | `safe_deferral/actuation/ack` | `safe_deferral/audit/log` |
| Class 1 | `safe_deferral/context/input` | Optional guidance path | Not primary | `safe_deferral/actuation/command` | `safe_deferral/actuation/ack` | `safe_deferral/audit/log` |
| E001 | `safe_deferral/emergency/event` | Not primary | `safe_deferral/escalation/class2` or caregiver notification if needed | Warning/protective output if implemented | Optional | `safe_deferral/audit/log` |
| E002 | `safe_deferral/emergency/event` | Not primary | caregiver notification if needed | Warning/protective output if implemented | Optional | `safe_deferral/audit/log` |
| E003 | `safe_deferral/emergency/event` | Not primary | caregiver notification if needed | Warning/protective output if implemented | Optional | `safe_deferral/audit/log` |
| E004 | `safe_deferral/emergency/event` | Not primary | caregiver notification if needed | Warning/protective output if implemented | Optional | `safe_deferral/audit/log` |
| E005 | `safe_deferral/emergency/event` | Not primary | caregiver notification if needed | Warning/protective output if implemented | Optional | `safe_deferral/audit/log` |
| Class 2 | `safe_deferral/context/input` | `safe_deferral/deferral/request` | `safe_deferral/escalation/class2`, `safe_deferral/caregiver/confirmation` | Only after Class 1 validator approval | Only after execution | `safe_deferral/audit/log` |
| Stale fault | `safe_deferral/context/input` | `safe_deferral/deferral/request` | caregiver notification if unresolved | Not allowed without fresh validated state | Not applicable unless execution occurred | `safe_deferral/audit/log` |
| Conflict fault | `safe_deferral/context/input` | `safe_deferral/deferral/request` | `safe_deferral/caregiver/confirmation` if needed | Only after confirmed and validated Class 1 transition | Only after execution | `safe_deferral/audit/log` |
| Missing-state fault | `safe_deferral/context/input` | `safe_deferral/deferral/request` | caregiver confirmation if unresolved | Not allowed while required state is missing | Not applicable unless execution occurred | `safe_deferral/audit/log` |

## 8.3 Scenario-to-payload-family coverage

| Scenario | Primary input payload | Interaction payload | Execution payload | Evidence/audit payload |
|---|---|---|---|---|
| Baseline | `policy_router_input` | Optional guidance | `validator_output`, `actuation_command_payload` if validated | ACK/audit |
| Class 1 | `policy_router_input` | LLM candidate/guidance | `validator_output`, `actuation_command_payload` | ACK/audit |
| Class 0 E001-E005 | emergency evidence / normalized `policy_router_input` | Emergency warning/guidance | Warning/protective output if implemented | emergency audit |
| Class 2 | `policy_router_input` | `clarification_interaction`, `class_2_notification_payload` | Only after transition and validation | candidate/selection/timeout/transition audit |
| Stale fault | fault-injected input | deferral/notification if needed | Not allowed until safe | stale fault audit |
| Conflict fault | fault-injected input | `clarification_interaction` candidates | Only after confirmation and validation | conflict cause audit |
| Missing-state fault | fault-injected input | deferral/notification/recheck | Not allowed while missing state persists | missing-state audit |

---

## 9. Prohibited authority boundary by scenario

| Scenario | LLM final decision | LLM actuation authority | Doorlock autonomous execution | Emergency trigger by LLM | Unsafe autonomous actuation |
|---|---|---|---|---|---|
| Baseline | Prohibited | Prohibited | Prohibited | Prohibited | Prohibited |
| Class 1 | Prohibited | Prohibited | Prohibited | Prohibited | Prohibited |
| Class 0 E001 | Prohibited | Prohibited | Prohibited | Prohibited | Prohibited |
| Class 0 E002 | Prohibited | Prohibited | Prohibited | Prohibited | Prohibited |
| Class 0 E003 | Prohibited | Prohibited | Prohibited | Prohibited | Prohibited |
| Class 0 E004 | Prohibited | Prohibited | Prohibited | Prohibited | Prohibited |
| Class 0 E005 | Prohibited | Prohibited | Prohibited | Prohibited | Prohibited |
| Class 2 | Prohibited | Prohibited | Prohibited | Prohibited | Prohibited |
| Stale fault | Prohibited | Prohibited | Prohibited | Prohibited | Prohibited |
| Conflict fault | Prohibited | Prohibited | Prohibited | Prohibited | Prohibited |
| Missing-state fault | Prohibited | Prohibited | Prohibited | Prohibited | Prohibited |

Notes:

```text
- The LLM may generate bounded candidates and user-facing explanations only.
- MQTT topics are communication contracts, not execution authority.
- Payload fixtures are evaluation assets, not policy truth.
- Dashboard/governance/audit artifacts are evidence or visibility artifacts, not control authority.
```

---

## 10. Non-authority and safety invariants

The following rules apply across all scenario data flows.

1. This document is not policy/schema authority.
2. Topics are communication contracts, not execution authority.
3. Payload fixtures are evaluation assets, not policy truth.
4. LLM candidate/guidance is not actuation authority.
5. Class 0 requires deterministic emergency evidence or user/caregiver emergency confirmation.
6. Class 1 requires frozen low-risk catalog membership and deterministic validator approval.
7. Class 2 is a clarification/transition state, not only terminal failure.
8. `doorbell_detected` is visitor context, not emergency evidence or door-unlock authority.
9. Fault scenario causes must remain auditable.
10. Dashboard/governance/audit artifacts are evidence or visibility artifacts, not control authority.
11. Doorlock state is not currently part of `pure_context_payload.device_states`.
12. Class 2 clarification state must not be forced into `pure_context_payload`.
13. Candidate prompts must not be treated as validator output, actuation command, emergency trigger, or doorlock authorization.
14. Missing-state handling must not fabricate absent state or assume missing state is safe.
15. Conflict handling must not arbitrarily select one plausible candidate.

---

## 11. Future split plan

This document is intentionally maintained as a single document for now because the current scenario set is still manageable and cross-scenario comparison is useful.

If the scenario set grows, split detailed data-flow sections into subordinate files:

```text
common/docs/architecture/20_scenario_data_flow_matrix.md
common/docs/architecture/scenario_data_flows/
  20_01_baseline_data_flow.md
  20_02_class0_emergency_data_flows.md
  20_03_class1_data_flow.md
  20_04_class2_clarification_data_flow.md
  20_05_fault_data_flows.md
```

In that future structure:

```text
20_scenario_data_flow_matrix.md
→ remains the index and cross-scenario summary.

scenario_data_flows/*.md
→ hold detailed scenario-specific tables.
```

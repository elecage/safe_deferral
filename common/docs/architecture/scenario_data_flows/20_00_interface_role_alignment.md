# 20_00. Scenario Data-Flow Interface and Role Alignment

## 1. Purpose

This document is a companion refinement for:

```text
common/docs/architecture/20_scenario_data_flow_matrix.md
```

It links scenario-level data-flow steps to:

```text
15_interface_matrix.md interface IDs
publisher_subscriber_matrix_v1_0_0.md publisher/subscriber roles
MQTT topic contracts
payload families
authority boundaries
```

This document is not policy authority. It is an interface/role traceability aid for implementing, reviewing, and testing scenario data flows.

---

## 2. Source references

This document aligns with:

```text
common/docs/architecture/15_interface_matrix.md
common/docs/architecture/20_scenario_data_flow_matrix.md
common/mqtt/publisher_subscriber_matrix_v1_0_0.md
common/mqtt/topic_registry_v1_0_0.json
common/mqtt/topic_payload_contracts_v1_0_0.md
common/docs/architecture/17_payload_contract_and_registry.md
```

Key interpretation from `15_interface_matrix.md`:

```text
- MQTT topics are communication contracts, not policy authority.
- Context nodes enter through MQTT Ingestion / State Intake.
- Emergency nodes do not use the Local LLM as the primary decision path.
- Policy Router must not bypass the Deterministic Validator for executable low-risk actuation.
- Dashboard/governance/audit artifacts are not operational control authority.
- doorbell_detected is visitor-response context only.
```

---

## 3. Core interface ID vocabulary

| Interface ID | Source | Destination | Topic / interface | Payload family | Used by scenario flows |
|---|---|---|---|---|---|
| UI-1 | User | Bounded Input Node | physical / local input | `bounded_input_event` | Baseline, Class 1, Class 2, E002, conflict, missing-state |
| UI-2 | Bounded Input Node | MQTT Ingestion / State Intake | `safe_deferral/context/input` | `policy_router_input` | Baseline, Class 1, Class 2, conflict, missing-state |
| UI-3 | User | Bounded Input Node | physical / local input | `bounded_followup_input` | Class 2 candidate selection, conflict resolution |
| UI-4 | Bounded Input Node | MQTT Ingestion / State Intake | `safe_deferral/context/input` | `policy_router_input` | Class 2 follow-up selection, conflict resolution |
| CS-1 | Context Nodes | MQTT Ingestion / State Intake | `safe_deferral/context/input` | `policy_router_input` | Baseline, Class 1, Class 2, stale, conflict, missing-state |
| CS-1a | Doorbell / Visitor-Arrival Context Node | MQTT Ingestion / State Intake | `safe_deferral/context/input` | `policy_router_input` | Visitor context in all context-bearing scenarios |
| CS-2 | MQTT Ingestion / State Intake | Context and Runtime State Aggregation | internal aggregation | `normalized_runtime_context` | All context-bearing scenarios |
| CS-3 | ACK Handling | Context and Runtime State Aggregation | internal runtime-state update | `actuation_ack_state` | Class 1, Class 2-to-Class 1, conflict resolved to Class 1 |
| EM-1 | Emergency Nodes | MQTT Ingestion / State Intake | `safe_deferral/emergency/event` | `policy_router_input_or_emergency_context` | E001-E005, Class 2-to-Class 0 |
| EM-2 | MQTT Ingestion / State Intake | Policy Router | internal policy input | `policy_router_input` | E001-E005 |
| EM-3 | Policy Router | Deterministic Validator | internal validation request | `routed_policy_decision` | E001-E005 emergency branch checking |
| EM-5 | Deterministic Validator | Caregiver Escalation | `safe_deferral/escalation/class2` | `class_2_notification_payload` | Emergency escalation where needed, Class 2 unresolved/sensitive cases |
| EM-6 | Deterministic Validator | TTS Rendering / Voice Output | internal guidance interface | `emergency_guidance_text` | E001-E005 guidance |
| LR-1 | Context and Runtime State Aggregation | Local LLM Reasoning Layer | internal bounded prompt context | `bounded_llm_context` | Class 1 guidance, Class 2 candidates, conflict explanation |
| LR-2 | Local LLM Reasoning Layer | Policy Router | internal interpretation result | `intent_interpretation_result` | Class 1 assistive path, Class 2 after confirmation if applicable |
| LR-2a | Local LLM Reasoning Layer | Deterministic Validator | `safe_deferral/llm/candidate_action` | `candidate_action` | Class 1 candidate validation, conflict candidate validation |
| LR-3 | Safe Deferral and Clarification Management | Local LLM Reasoning Layer | internal explanation basis | `deferral_reason_context` | Class 2, stale, missing-state, conflict deferral |
| PV-1 | MQTT Ingestion / State Intake | Policy Router | `safe_deferral/context/input` / `safe_deferral/emergency/event` | `policy_router_input` / emergency context | All routing scenarios |
| PV-2 | Local LLM Reasoning Layer | Policy Router | internal interpretation result | `intent_interpretation_result` | Class 1, Class 2 after confirmation, conflict resolution |
| PV-3 | Policy Router | Deterministic Validator | internal validation request | `routed_policy_decision` | Class 1, Class 2-to-Class 1, conflict resolved to Class 1 |
| PV-4 | Deterministic Validator | Approved Low-Risk Actuation Path | `safe_deferral/validator/output` | `validator_output` | Class 1, Class 2-to-Class 1, conflict resolved to Class 1 |
| PV-5 | Deterministic Validator | Safe Deferral and Clarification Management | `safe_deferral/deferral/request` | `safe_deferral_event` | Class 2, stale, conflict, missing-state |
| PV-6 | Deterministic Validator | Caregiver Escalation | `safe_deferral/escalation/class2` | `class_2_notification_payload` | Class 2 unresolved/sensitive path, missing-state unresolved path |
| AC-1 | Approved Low-Risk Actuation Path | Actuator Interface Nodes | `safe_deferral/actuation/command` | `actuation_command_payload` | Class 1, Class 2-to-Class 1, conflict resolved to Class 1 |
| AC-3 | Actuator Interface Nodes | ACK Handling | `safe_deferral/actuation/ack` | `actuation_ack_payload` | Class 1 execution closure |
| AC-4 | ACK Handling | Local Audit Logging | `safe_deferral/audit/log` | `audit_event_payload` | Execution closure audit |
| FG-1 | Local LLM Reasoning Layer | TTS Rendering / Voice Output | internal TTS request | `guidance_text` | Class 1 result explanation, Class 2 candidates, fault guidance |
| FG-2 | TTS Rendering / Voice Output | User | audio output | `spoken_guidance` | User-facing guidance across scenarios |
| EX-1 | Scenario Orchestrator | MQTT Ingestion / State Intake | `safe_deferral/sim/context` or controlled bridge | `policy_router_input_or_context_fixture` | Controlled integration tests, baseline replay |
| EX-3 | Fault Injection | MQTT Ingestion / State Intake | `safe_deferral/fault/injection` | `fault_injection_payload` | Stale, conflict, missing-state tests |
| AU-1 | Policy Router | Local Audit Logging | `safe_deferral/audit/log` | `audit_event_payload` | All routed scenarios |
| AU-2 | Local LLM Reasoning Layer | Local Audit Logging | `safe_deferral/audit/log` | `audit_event_payload` | Candidate/guidance audit |
| AU-3 | Deterministic Validator | Local Audit Logging | `safe_deferral/audit/log` | `audit_event_payload` | Validation audit |
| AU-4 | Safe Deferral and Clarification Management | Local Audit Logging | `safe_deferral/audit/log` | `audit_event_payload` | Class 2, stale, conflict, missing-state |
| AU-5 | Caregiver Confirmation Backend | Local Audit Logging | `safe_deferral/audit/log` | `audit_event_payload` | Caregiver confirmation audit |

---

## 4. MQTT publisher/subscriber role alignment

| Topic | Allowed publisher roles | Allowed subscriber roles | Payload family | Scenario usage |
|---|---|---|---|---|
| `safe_deferral/context/input` | `esp32.bounded_input_node`, `esp32.context_node`, `esp32.doorbell_visitor_context_node`, `mac_mini.context_aggregator_controlled_bridge`, `rpi.simulation_runtime_controlled_mode` | `mac_mini.mqtt_ingestion_state_intake`, `mac_mini.policy_router`, optional audit observer | `policy_router_input` | Baseline, Class 1, Class 2, stale, conflict, missing-state |
| `safe_deferral/emergency/event` | `esp32.emergency_node`, `rpi.virtual_emergency_sensor_controlled_mode` | `mac_mini.policy_router`, optional audit observer | `policy_router_input_or_emergency_context` | E001-E005, Class 2-to-Class 0 |
| `safe_deferral/llm/candidate_action` | `mac_mini.local_llm_adapter` | `mac_mini.deterministic_validator`, optional audit observer | `candidate_action` | Class 1 candidate validation, conflict resolution |
| `safe_deferral/validator/output` | `mac_mini.deterministic_validator` | dispatcher/deferral handler, audit observer, optional dashboard bridge | `validator_output` | Class 1, Class 2-to-Class 1, conflict resolved to Class 1 |
| `safe_deferral/deferral/request` | validator, safe deferral handler | safe deferral handler, audit observer, optional dashboard bridge | `safe_deferral_event` | Class 2 entry, stale, conflict, missing-state |
| `safe_deferral/escalation/class2` | policy router, validator, safe deferral handler | outbound notification interface, audit observer, optional dashboard bridge | `class_2_notification_payload` | Class 2 unresolved, caregiver escalation, sensitive/unresolved emergency |
| `safe_deferral/caregiver/confirmation` | caregiver confirmation backend, controlled RPi test app mock | caregiver confirmation backend, manual dispatcher path, audit observer, dashboard bridge | `manual_confirmation_payload` | Class 2 selection/confirmation, manual sensitive path |
| `safe_deferral/actuation/command` | low-risk dispatcher, manual-path dispatcher | ESP32 lighting node, governed warning/doorlock interface node, audit observer | `actuation_command_payload` | Class 1 execution only after validation; doorlock only through governed manual path |
| `safe_deferral/actuation/ack` | ESP32 actuator node, controlled RPi mock actuator | Mac mini ACK handler, audit observer, dashboard bridge | `actuation_ack_payload` | Class 1 execution closure, closed-loop evidence |
| `safe_deferral/audit/log` | Mac mini operational services | Mac mini audit logging service | `audit_event_payload` | All scenarios |
| `safe_deferral/sim/context` | RPi simulation runtime | controlled input bridge, RPi orchestrator, RPi dashboard | `policy_router_input_or_context_fixture` | Controlled scenario replay only |
| `safe_deferral/fault/injection` | RPi fault injector, RPi orchestrator | RPi simulation runtime, fault injector, optional controlled input bridge | `fault_injection_payload` | Stale, conflict, missing-state test injection |
| `safe_deferral/dashboard/observation` | RPi orchestrator, dashboard backend, optional Mac mini telemetry bridge | RPi dashboard frontend, optional test app | `dashboard_observation_payload` | Visibility only |
| `safe_deferral/experiment/progress` | RPi orchestrator, integration test runner | RPi dashboard frontend, result exporter | `experiment_progress_payload` | Experiment status only |
| `safe_deferral/experiment/result` | RPi orchestrator, integration test runner, result exporter | RPi dashboard frontend, optional paper analysis tools | `result_export_payload` | Experiment artifact only |

Note on `safe_deferral/context/input`:

```text
publisher_subscriber_matrix_v1_0_0.md now explicitly lists field-side operational publishers for this topic:
- esp32.bounded_input_node
- esp32.context_node
- esp32.doorbell_visitor_context_node

It also preserves controlled-mode/bridge publishers:
- mac_mini.context_aggregator_controlled_bridge
- rpi.simulation_runtime_controlled_mode

This resolves the earlier publisher-role mismatch while preserving the distinction between operational input and controlled evaluation input.
```

---

## 5. Scenario-to-interface-ID coverage

| Scenario | Primary ingress IDs | Routing/validation IDs | Clarification/guidance IDs | Execution/ACK IDs | Audit IDs |
|---|---|---|---|---|---|
| Baseline | UI-2, CS-1, CS-1a, EX-1 if replayed | CS-2, PV-1, PV-3 | Optional LR-1, LR-2, FG-1, FG-2 | Optional PV-4, AC-1, AC-3 | AU-1, AU-3, AC-4 |
| Class 1 baseline | UI-1, UI-2, CS-1, CS-2 | LR-1, LR-2, LR-2a, PV-1, PV-2, PV-3, PV-4 | FG-1, FG-2 | AC-1, AC-3, AC-4 | AU-1, AU-2, AU-3, AC-4 |
| Class 0 E001 | EM-1, EM-2 | PV-1, EM-2, EM-3 | EM-6, FG-1, FG-2 | Warning output path if implemented | AU-1, AU-3 |
| Class 0 E002 | UI-1, EM-1, EM-2 | Input Pattern Detector, PV-1, EM-3 | EM-6, FG-1, FG-2 | Warning output path if implemented | AU-1, AU-3 |
| Class 0 E003 | EM-1, EM-2 | PV-1, EM-3 | EM-6, FG-1, FG-2 | Warning output path if implemented | AU-1, AU-3 |
| Class 0 E004 | EM-1, EM-2 | PV-1, EM-3 | EM-6, FG-1, FG-2 | Warning output path if implemented | AU-1, AU-3 |
| Class 0 E005 | EM-1, EM-2 | PV-1, EM-3 | EM-6, FG-1, FG-2 | Warning output path if implemented | AU-1, AU-3 |
| Class 2 insufficient context | UI-1, UI-2, UI-3, UI-4, CS-1, CS-2 | PV-1, PV-5, PV-6 | LR-1, LR-3, FG-1, FG-2 | Only after transition to Class 1: PV-3, PV-4, AC-1, AC-3 | AU-1, AU-2, AU-4, AU-5 if caregiver involved |
| Stale fault | CS-1, EX-1, EX-3 | PV-1, PV-5 | LR-3, FG-1, FG-2 | Prohibited until fresh validated state exists | AU-1, AU-4 |
| Conflict fault | UI-1, UI-2, UI-3, UI-4, CS-1, CS-2 | LR-1, LR-2, LR-2a, PV-1, PV-3, PV-5 | LR-3, FG-1, FG-2 | Only after confirmed Class 1 candidate and validation: PV-4, AC-1, AC-3 | AU-1, AU-2, AU-3, AU-4 |
| Missing-state fault | CS-1, CS-2, EX-3 | Health Check Routine, PV-1, PV-5 | LR-3, FG-1, FG-2 | Prohibited while required state remains missing | AU-1, AU-4 |

---

## 6. Scenario-to-topic-role coverage

| Scenario | Publisher side | Topic | Subscriber side | Payload family | Expected role interpretation |
|---|---|---|---|---|---|
| Baseline | Bounded Input / Context / Doorbell-Visitor Context / controlled replay source | `safe_deferral/context/input` | MQTT ingestion / Policy Router | `policy_router_input` | Ordinary field-side input or controlled simulation input |
| Class 1 | Bounded Input / Context Node | `safe_deferral/context/input` | MQTT ingestion / Policy Router | `policy_router_input` | Low-risk assistance input |
| Class 1 | Deterministic Validator | `safe_deferral/validator/output` | dispatcher/deferral handler | `validator_output` | Final admissibility evidence |
| Class 1 | Low-risk dispatcher | `safe_deferral/actuation/command` | Lighting Actuator Node | `actuation_command_payload` | Validated lighting command |
| Class 1 | Lighting Actuator Node | `safe_deferral/actuation/ack` | ACK Handling | `actuation_ack_payload` | Closed-loop evidence |
| E001-E005 | Emergency Node / controlled emergency sensor | `safe_deferral/emergency/event` | MQTT ingestion / Policy Router | `policy_router_input_or_emergency_context` | Emergency evidence input |
| E001-E005 | Policy/validator/emergency handling | `safe_deferral/escalation/class2` where needed | outbound notification interface | `class_2_notification_payload` | Emergency-related escalation if needed |
| Class 2 | Bounded Input / Context / Doorbell-Visitor Context | `safe_deferral/context/input` | MQTT ingestion / Policy Router | `policy_router_input` | Ambiguous or insufficient context enters clarification path |
| Class 2 | Policy Router / Validator / Deferral Handler | `safe_deferral/deferral/request` | Safe Deferral / Clarification Manager | `safe_deferral_event` | Clarification/deferral control signal |
| Class 2 | Policy Router / Validator / Safe Deferral Handler | `safe_deferral/escalation/class2` | outbound notification interface | `class_2_notification_payload` | Notification/escalation signal, not execution authority |
| Class 2 | Caregiver confirmation backend or controlled test mock | `safe_deferral/caregiver/confirmation` | caregiver backend / manual dispatcher / audit | `manual_confirmation_payload` | Manual confirmation evidence |
| Stale fault | Fault injector / controlled simulation | `safe_deferral/fault/injection` or controlled bridge | simulation runtime / ingestion | `fault_injection_payload` | Experiment-only fault condition |
| Conflict fault | Context/input nodes or controlled fixture | `safe_deferral/context/input` | Policy Router / Validator | `policy_router_input` | Multiple plausible candidates enter policy path |
| Missing-state fault | Context/device state/health source or controlled fixture | `safe_deferral/context/input` | Policy Router / Health Check | `policy_router_input` | Missing state is detected and rechecked/deferred |
| All scenarios | Mac mini operational services | `safe_deferral/audit/log` | Audit Log | `audit_event_payload` | Evidence/traceability only |

---

## 7. Interface alignment issues to monitor

| Issue | Current interpretation | Recommended follow-up |
|---|---|---|
| `safe_deferral/context/input` publisher mismatch | Resolved in `publisher_subscriber_matrix_v1_0_0.md`: field-side publishers and controlled-mode publishers are now both explicitly represented | Keep this distinction in future registry/governance updates; do not collapse controlled-mode publishers into ordinary operational publishers |
| Class 2 candidate prompt topic | Existing topic registry can express Class 2 using deferral/escalation/context/caregiver/audit topics | Add dedicated `safe_deferral/clarification/*` topics only if runtime implementation requires separation |
| Warning output topic | Emergency warning output may be local output or actuation-like command | Keep warning output governed; avoid treating emergency guidance as arbitrary actuator authority |
| ACK schema | ACK payload family is described but future formal schema may still be needed | Add formal ACK schema if closed-loop execution testing expands |
| Audit schema | Audit event payload is used broadly but may need formalization | Add audit event schema if paper/evaluation requires machine validation |
| Governance/dashboard topics | Observation/progress/result topics are visibility only | Continue prohibiting direct control authority from dashboard/governance layers |

---

## 8. Non-authority boundaries repeated for implementation

1. Interface IDs describe allowed communication paths, not control permission.
2. Publisher/subscriber roles describe expected topic traffic, not policy authority.
3. LLM guidance and candidate output never authorize actuation.
4. Class 1 actuation requires policy routing, low-risk catalog membership, deterministic validator approval, dispatcher publication, ACK, and audit.
5. Class 0 requires deterministic emergency evidence or user/caregiver emergency confirmation; LLM text alone cannot trigger Class 0.
6. Class 2 candidate prompt, selection, timeout, and transition state must remain auditable.
7. Doorbell/visitor context does not authorize emergency or doorlock action.
8. Dashboard/governance/test artifacts must not publish operational control topics except through explicitly controlled test paths.

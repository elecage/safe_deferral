# 15_interface_matrix.md

## 1. Purpose

This document records the interface matrix for the revised system architecture.

It is intended to support:
- paper figure drafting,
- Section 2 architecture writing,
- implementation reasoning,
- consistency checks across runtime, control, and experiment-support paths,
- and consistency checks against MQTT topic, publisher/subscriber, and payload contracts.

This document should be read together with:
- `common/docs/architecture/14_system_components_outline_v2.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- `common/docs/paper/04_section2_system_design_outline.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `CLAUDE.md`

---

## 2. Review notes applied before finalizing this matrix

The following corrections were explicitly applied before writing the final interface table:

- **Context Nodes do not go directly to the Local LLM Reasoning Layer.** They must enter through `MQTT Ingestion / State Intake` and then `Context and Runtime State Aggregation`.
- **Emergency Nodes do not use the Local LLM as the primary decision path.** They must follow a policy-driven path through `MQTT Ingestion / State Intake` and `Policy Router`.
- **Sensitive actuation is never triggered directly by `Caregiver Escalation`.** Execution can happen only after `Caregiver Approval` through a separately governed manual confirmation path.
- **Local Audit Logging is not the direct sink of raw emergency sensing.** It records processed hub-side outcomes.
- **MQTT topics are communication contracts, not policy authority.** The topic registry supports communication consistency but does not override frozen policies or schemas.
- **Dashboard/governance interfaces must not publish control authority.** Dashboard and governance tooling may inspect, validate, and propose changes, but must not bypass policy routing, deterministic validation, caregiver approval, ACK, or audit boundaries.
- **Topic/payload registry edits do not create doorlock execution authority.** Doorlock-related topic entries remain sensitive communication contracts unless future frozen policy/schema revisions explicitly promote them.
- **`doorbell_detected` is visitor-response context only.** It is not emergency evidence and does not authorize autonomous doorlock control.

If a future diagram or text conflicts with these points, this matrix should be treated as the corrected interpretation.

---

## 3. Interface matrix

The matrix below is intentionally MQTT-aware.  
Where a row corresponds to a registry-governed interface, the `MQTT Topic / Interface` and `Payload Family` columns should remain aligned with `common/mqtt/topic_registry_v1_0_0.json`.

| Category | ID | Source Block | Destination Block | MQTT Topic / Interface | Payload Family | Description | Notes |
|---|---|---|---|---|---|---|---|
| User Input | UI-1 | User | Bounded Input Node | physical / local input | bounded_input_event | The user performs bounded alternative input. | Initial input |
| User Input | UI-2 | Bounded Input Node | MQTT Ingestion / State Intake | `safe_deferral/context/input` | `policy_router_input` | The bounded input event and relevant context wrapper are sent to the edge hub. | Must include `environmental_context.doorbell_detected` in valid schema-governed context payloads. |
| User Input | UI-3 | User | Bounded Input Node | physical / local input | bounded_followup_input | The user provides clarification follow-up input after a guidance prompt. | Follow-up input |
| User Input | UI-4 | Bounded Input Node | MQTT Ingestion / State Intake | `safe_deferral/context/input` | `policy_router_input` | The clarification follow-up event is reintroduced into the hub. | Clarification re-entry through the same input plane. |
| Context / State | CS-1 | Context Nodes | MQTT Ingestion / State Intake | `safe_deferral/context/input` | `policy_router_input` | Environmental and device-state context is delivered into the hub. | Context ingress; `doorbell_detected` belongs in `environmental_context`. |
| Context / State | CS-1a | Doorbell / Visitor-Arrival Context Node | MQTT Ingestion / State Intake | `safe_deferral/context/input` | `policy_router_input` | Visitor-arrival context is delivered as `environmental_context.doorbell_detected`. | Visitor-response context only; not emergency evidence or unlock authorization. |
| Context / State | CS-2 | MQTT Ingestion / State Intake | Context and Runtime State Aggregation | internal aggregation interface | normalized_runtime_context | Received context/state is aggregated into an integrated runtime-state representation. | Main context path |
| Context / State | CS-3 | ACK Handling | Context and Runtime State Aggregation | internal runtime-state update | actuation_ack_state | Execution results are reflected back into runtime state. | ACK is closed-loop evidence, not pure context input. |
| Context / State | CS-4 | Caregiver Approval | Context and Runtime State Aggregation | internal runtime-state update | manual_confirmation_state | Approval/denial results are reflected into runtime state. | Approval state is not pure context. |
| Context / State | CS-5 | Policy Router | Context and Runtime State Aggregation | internal runtime-state update | routing_outcome_state | Routing outcomes may be reflected into runtime state. | Optional runtime reflection |
| Context / State | CS-6 | Deterministic Validator | Context and Runtime State Aggregation | internal runtime-state update | validator_outcome_state | Validator outcomes may be reflected into runtime state. | Optional runtime reflection |
| Context / State | CS-7 | Safe Deferral and Clarification Management | Context and Runtime State Aggregation | internal runtime-state update | deferral_or_clarification_state | Deferred state and pending clarification state are reflected into runtime state. | Clarification-state update |
| Emergency | EM-1 | Emergency Nodes | MQTT Ingestion / State Intake | `safe_deferral/emergency/event` | `policy_router_input_or_emergency_context` | Raw emergency events are collected into the hub. | Emergency ingress aligned with E001~E005. |
| Emergency | EM-2 | MQTT Ingestion / State Intake | Policy Router | internal policy input | policy_router_input | Emergency events enter the policy-driven emergency path. | Primary emergency path |
| Emergency | EM-3 | Policy Router | Deterministic Validator | internal validation request | routed_policy_decision | Emergency-safe admissibility or branch handling is checked. | Validator boundary |
| Emergency | EM-4 | Deterministic Validator | Safe Deferral and Clarification Management | `safe_deferral/deferral/request` | `safe_deferral_event` | If immediate execution is not justified, the event may move into deferred handling. | Exceptional emergency handling |
| Emergency | EM-5 | Deterministic Validator | Caregiver Escalation | `safe_deferral/escalation/class2` | `class_2_notification_payload` | Caregiver intervention is requested when required. | Sensitive or unresolved emergency case |
| Emergency | EM-6 | Deterministic Validator | TTS Rendering / Voice Output | internal guidance interface | emergency_guidance_text | Warning or status guidance may be provided to the user. | Emergency guidance |
| LLM Reasoning | LR-1 | Context and Runtime State Aggregation | Local LLM Reasoning Layer | internal bounded prompt context | bounded_llm_context | The integrated runtime-state view is used as LLM input. | Routing metadata must not be mixed into bounded LLM context unless explicitly required. |
| LLM Reasoning | LR-2 | Local LLM Reasoning Layer | Policy Router | internal interpretation result | intent_interpretation_result | Intent candidates or interpretation results are delivered into the policy path. | Assistive interaction path |
| LLM Reasoning | LR-2a | Local LLM Reasoning Layer | Deterministic Validator | `safe_deferral/llm/candidate_action` | `candidate_action` | Bounded LLM candidate action output is delivered for deterministic validation. | Model candidate is not authority; door unlock must not appear as current Class 1 candidate. |
| LLM Reasoning | LR-3 | Safe Deferral and Clarification Management | Local LLM Reasoning Layer | internal explanation basis | deferral_reason_context | Deferred reasons are used for explanation and clarification-prompt generation. | Explanation basis |
| LLM Reasoning | LR-4 | Caregiver Escalation | Local LLM Reasoning Layer | internal explanation basis | escalation_state_context | Escalation state is used to generate user-facing guidance. | Escalation guidance |
| LLM Reasoning | LR-5 | ACK Handling | Local LLM Reasoning Layer | internal explanation basis | ack_result_context | ACK results are used for explanation generation. | Result explanation |
| LLM Reasoning | LR-6 | Deterministic Validator | Local LLM Reasoning Layer | internal explanation basis | validator_outcome_context | Validation outcomes can be reflected into user-facing explanation text. | Validation explanation |
| Policy / Validation | PV-1 | MQTT Ingestion / State Intake | Policy Router | `safe_deferral/context/input` / `safe_deferral/emergency/event` | `policy_router_input` / emergency context | Raw events that require direct policy handling enter the policy path. | Includes emergency handling and context input. |
| Policy / Validation | PV-2 | Local LLM Reasoning Layer | Policy Router | internal interpretation result | intent_interpretation_result | Assistive interpretation results are delivered into policy routing. | Normal assistive path |
| Policy / Validation | PV-3 | Policy Router | Deterministic Validator | internal validation request | routed_policy_decision | Routed candidates move into the final admissibility boundary. | Required validation step |
| Policy / Validation | PV-4 | Deterministic Validator | Approved Low-Risk Actuation Path | `safe_deferral/validator/output` | `validator_output` | Approved low-risk actions are forwarded to execution. | Low-risk only; doorlock executable payload not allowed under current baseline. |
| Policy / Validation | PV-5 | Deterministic Validator | Safe Deferral and Clarification Management | `safe_deferral/deferral/request` | `safe_deferral_event` | Ambiguity, insufficient context, or policy restriction triggers deferred handling. | Safe deferral |
| Policy / Validation | PV-6 | Deterministic Validator | Caregiver Escalation | `safe_deferral/escalation/class2` | `class_2_notification_payload` | Sensitive or autonomously inadmissible requests trigger escalation. | Sensitive path |
| Policy / Validation | PV-7 | Deterministic Validator | Dispatcher / Deferral Handler | `safe_deferral/validator/output` | `validator_output` | Deterministic validator decision output is consumed by dispatcher or deferral handler. | Validator decision is authoritative within policy/schema bounds. |
| Actuation | AC-1 | Approved Low-Risk Actuation Path | Actuator Interface Nodes | `safe_deferral/actuation/command` | `actuation_command_payload` | Approved low-risk actions are dispatched to actuators. | Lighting etc.; dispatcher path only. |
| Actuation | AC-2 | Caregiver Approval | Actuator Interface Nodes | `safe_deferral/caregiver/confirmation` then `safe_deferral/actuation/command` | `manual_confirmation_payload` / `actuation_command_payload` | Sensitive actuation is executed only after caregiver approval through a governed manual path. | Sensitive actuation; caregiver approval is not autonomous Class 1 validator approval. |
| Actuation | AC-3 | Actuator Interface Nodes | ACK Handling | `safe_deferral/actuation/ack` | `actuation_ack_payload` | Actuator-side acknowledgment or state confirmation is returned. | Closed-loop confirmation |
| Actuation | AC-4 | ACK Handling | Local Audit Logging | `safe_deferral/audit/log` | `audit_event_payload` | ACK results are recorded through the audit path. | Audit evidence, not policy truth. |
| Feedback / Guidance | FG-1 | Local LLM Reasoning Layer | TTS Rendering / Voice Output | internal TTS request | guidance_text | Explanation, guidance, or clarification text is sent to the voice-rendering layer. | TTS input |
| Feedback / Guidance | FG-2 | TTS Rendering / Voice Output | User | audio output | spoken_guidance | Spoken guidance is delivered to the user. | Final user-facing output |
| Feedback / Guidance | FG-3 | Context and Runtime State Aggregation | Local LLM Reasoning Layer | internal explanation basis | runtime_state_context | Runtime state is used to produce status explanations. | Runtime-aware guidance |
| Feedback / Guidance | FG-4 | Safe Deferral and Clarification Management | Local LLM Reasoning Layer | internal explanation basis | clarification_state_context | Clarification-needed state is used to generate next-input suggestions. | Clarification prompt basis |
| Feedback / Guidance | FG-5 | Caregiver Escalation | Local LLM Reasoning Layer | internal explanation basis | escalation_state_context | Approval-waiting or escalation status is used to generate guidance. | Escalation guidance |
| Feedback / Guidance | FG-6 | ACK Handling | Local LLM Reasoning Layer | internal explanation basis | ack_result_context | Execution result state is used to generate completion/failure guidance. | Result guidance |
| Experiment Support | EX-1 | Scenario Orchestrator | MQTT Ingestion / State Intake | `safe_deferral/sim/context` or controlled bridge to `safe_deferral/context/input` | `policy_router_input_or_context_fixture` | Scenario-driven synthetic events are injected into the hub-side path. | Experiment entry; must not masquerade as uncontrolled operational input. |
| Experiment Support | EX-2 | Simulation / Replay | MQTT Ingestion / State Intake | `safe_deferral/sim/context` | `policy_router_input_or_context_fixture` | Replay state or synthetic context is injected into the hub-side path. | Replay path |
| Experiment Support | EX-3 | Fault Injection | MQTT Ingestion / State Intake | `safe_deferral/fault/injection` | `fault_injection_payload` | Fault conditions such as staleness or missing state are injected. | Fault path; experiment-only. |
| Experiment Support | EX-4 | Context and Runtime State Aggregation | Progress / Result Publication | `safe_deferral/experiment/progress` | `experiment_progress_payload` | Runtime progress information may be reflected into experiment-visible progress publication. | Experiment observation |
| Experiment Support | EX-5 | Local Audit Logging | Progress / Result Publication | `safe_deferral/experiment/result` | `result_export_payload` | Audit artifacts may be collected for experiment output. | Result artifact |
| Experiment Support | EX-6 | ACK Handling | Progress / Result Publication | `safe_deferral/experiment/result` | `result_export_payload` | ACK/result summaries may be collected for experiment output. | Result summary |
| Experiment Support | EX-7 | Scenario Orchestrator / Dashboard Backend | Dashboard Frontend | `safe_deferral/dashboard/observation` | `dashboard_observation_payload` | Dashboard observation state is published for experiment monitoring. | Visibility only, not policy truth. |
| Experiment Support | EX-8 | Scenario Orchestrator / Integration Test Runner | Dashboard Frontend / Result Exporter | `safe_deferral/experiment/progress` | `experiment_progress_payload` | Experiment progress and run state are published. | Experiment status only. |
| Experiment Support | EX-9 | Result Exporter / Integration Test Runner | Dashboard Frontend / Paper Analysis Tools | `safe_deferral/experiment/result` | `result_export_payload` | Experiment result summary and export events are published. | Experiment artifact only. |
| Audit | AU-1 | Policy Router | Local Audit Logging | `safe_deferral/audit/log` | `audit_event_payload` | Routing decisions are recorded through audit logging. | Evidence/traceability, not policy truth. |
| Audit | AU-2 | Local LLM Reasoning Layer | Local Audit Logging | `safe_deferral/audit/log` | `audit_event_payload` | Interpretation and candidate-generation summaries may be audited. | Bounded summaries only. |
| Audit | AU-3 | Deterministic Validator | Local Audit Logging | `safe_deferral/audit/log` | `audit_event_payload` | Validator outcomes are recorded. | Evidence of decision boundary. |
| Audit | AU-4 | Safe Deferral and Clarification Management | Local Audit Logging | `safe_deferral/audit/log` | `audit_event_payload` | Deferrals, timeouts, and clarification state changes are recorded. | Evidence/traceability. |
| Audit | AU-5 | Caregiver Confirmation Backend | Local Audit Logging | `safe_deferral/audit/log` | `audit_event_payload` | Caregiver confirmation decisions are recorded. | Manual confirmation is not autonomous Class 1 approval. |
| Governance Support | GV-1 | User / Developer | Governance Dashboard UI | dashboard UI interaction | governance_ui_event | A developer or maintainer views or edits draft topic/payload entries. | UI only. |
| Governance Support | GV-2 | Governance Dashboard UI | MQTT / Payload Governance Backend | backend API call | governance_request | The UI calls the backend for create/update/delete/validation/export operations. | UI must not write registry files directly. |
| Governance Support | GV-3 | MQTT / Payload Governance Backend | Topic Registry Loader / Contract Checker | internal governance API | topic_registry_validation_request | Backend validates topic registry entries and proposed changes. | Non-authoritative validation support. |
| Governance Support | GV-4 | MQTT / Payload Governance Backend | Payload Example Manager / Validator | internal governance API | payload_validation_request | Backend validates payload examples and template references. | Must enforce `doorbell_detected` and doorlock boundary checks. |
| Governance Support | GV-5 | MQTT / Payload Governance Backend | Publisher / Subscriber Role Manager | internal governance API | role_validation_request | Backend validates publisher/subscriber role assignments. | Dashboard/gov roles must not receive actuator/caregiver authority. |
| Governance Support | GV-6 | MQTT / Payload Governance Backend | Draft Registry Change / Validation Report | file/export artifact | governance_change_report | Backend exports proposed changes and validation reports. | Review/commit workflow required before repository changes. |
| Governance Support | GV-7 | MQTT / Payload Governance Backend | `common/mqtt/` and `common/payloads/` reference assets | reviewed repository change only | registry_or_payload_reference_update | Approved changes may be committed through normal repository review. | No silent policy/schema edits; no direct live control authority. |

---

## 4. MQTT topic contract coverage

This section provides a compact coverage view for the current draft topic registry.  
It should be kept aligned with `common/mqtt/topic_registry_v1_0_0.json`.

| Topic | Primary Publisher(s) | Primary Subscriber(s) | Payload Family | Authority Boundary |
|---|---|---|---|---|
| `safe_deferral/context/input` | `mac_mini.context_aggregator`, `rpi.simulation_runtime_controlled_mode` | `mac_mini.policy_router`, optional audit observer | `policy_router_input` | Operational input; RPi publisher is controlled experiment/simulation mode only. |
| `safe_deferral/emergency/event` | `esp32.emergency_node`, `rpi.virtual_emergency_sensor_controlled_mode` | `mac_mini.policy_router`, optional audit observer | `policy_router_input_or_emergency_context` | Emergency input aligned with E001~E005; doorbell is not emergency. |
| `safe_deferral/llm/candidate_action` | `mac_mini.local_llm_adapter` | `mac_mini.deterministic_validator`, optional audit observer | `candidate_action` | Model candidate only; not execution authority. |
| `safe_deferral/validator/output` | `mac_mini.deterministic_validator` | dispatcher/deferral handler, audit observer, optional dashboard telemetry bridge | `validator_output` | Validator decision; executable outputs must remain within allowed policy/schema scope. |
| `safe_deferral/deferral/request` | validator or safe deferral handler | safe deferral handler, audit observer, optional dashboard bridge | `safe_deferral_event` | Bounded deferral/clarification control; future schema recommended. |
| `safe_deferral/escalation/class2` | policy router, validator, safe deferral handler | outbound notification interface, audit observer, optional dashboard bridge | `class_2_notification_payload` | Caregiver escalation; not autonomous execution authority. |
| `safe_deferral/caregiver/confirmation` | caregiver confirmation backend, controlled RPi test mock | caregiver confirmation backend, manual dispatcher path, audit observer, dashboard bridge | `manual_confirmation_payload` | Governed manual path; not autonomous Class 1 validator approval. |
| `safe_deferral/actuation/command` | low-risk dispatcher, manual-path dispatcher | ESP32 lighting node, governed warning/doorlock node, audit observer | `actuation_command_payload` | Dispatch after approval; doorlock requires governed manual confirmation path. |
| `safe_deferral/actuation/ack` | ESP32 actuator node, controlled RPi mock actuator | Mac mini ACK handler, audit observer, dashboard bridge | `actuation_ack_payload` | Closed-loop evidence; not pure context input. |
| `safe_deferral/audit/log` | Mac mini operational services | Mac mini audit logging service | `audit_event_payload` | Evidence/traceability; not policy truth. |
| `safe_deferral/sim/context` | RPi simulation runtime | controlled input bridge, RPi orchestrator, RPi dashboard | `policy_router_input_or_context_fixture` | Experiment-only input; must be gated. |
| `safe_deferral/fault/injection` | RPi fault injector, RPi orchestrator | RPi simulation runtime, fault injector, optional controlled input bridge | `fault_injection_payload` | Experiment-only controlled fault input. |
| `safe_deferral/dashboard/observation` | RPi orchestrator, dashboard backend, optional Mac mini telemetry bridge | RPi dashboard frontend, optional test app | `dashboard_observation_payload` | Visibility only; not policy truth. |
| `safe_deferral/experiment/progress` | RPi orchestrator, integration test runner | RPi dashboard frontend, result exporter | `experiment_progress_payload` | Experiment status only. |
| `safe_deferral/experiment/result` | RPi orchestrator, integration test runner, result exporter | RPi dashboard frontend, optional paper analysis tools | `result_export_payload` | Experiment artifact only. |

---

## 5. Prohibited or misleading interfaces

The following interfaces should not be drawn or described as normal architecture links.

| Prohibited Interface | Why It Is Incorrect |
|---|---|
| Emergency Nodes → Local LLM Reasoning Layer | Emergency handling is policy-driven in the primary path. |
| Local LLM Reasoning Layer → Actuator Interface Nodes | The LLM does not hold actuation authority. |
| Policy Router → Actuator Interface Nodes | The deterministic validator must not be bypassed. |
| Safe Deferral and Clarification Management → User | User-facing delivery should occur through the LLM + TTS path. |
| Caregiver Escalation → Actuator Interface Nodes | Sensitive execution requires explicit caregiver approval first. |
| Emergency Nodes → Local Audit Logging | Audit logging records processed outcomes, not raw emergency signals as a direct sink. |
| TTS Rendering / Voice Output → Policy Router | TTS is an output/rendering layer, not a control-input layer. |
| Governance Dashboard UI → `common/mqtt/` files directly | The UI must call the governance backend and must not directly write registry files. |
| Governance Dashboard UI → MQTT operational control topics directly | The UI is not an actuator console or control authority. |
| MQTT / Payload Governance Backend → canonical policies/schemas directly | Governance tooling must not silently rewrite policy/schema authority. |
| MQTT / Payload Governance Backend → Actuator Interface Nodes | Governance tooling cannot dispatch actuator commands. |
| MQTT / Payload Governance Backend → Caregiver Approval | Governance tooling cannot spoof or replace caregiver approval. |
| Dashboard Observation → Policy Router | Dashboard observation is visibility only, not policy input truth. |
| Dashboard Observation → Deterministic Validator | Dashboard observation is not validation input authority. |
| `safe_deferral/dashboard/observation` → policy truth | Dashboard observation payloads are visibility artifacts. |
| `doorbell_detected` → emergency trigger | Doorbell context is not part of E001~E005 emergency family. |
| `doorbell_detected` → doorlock authorization | Doorbell context does not authorize autonomous door unlock. |
| Doorlock state → current `pure_context_payload.device_states` | Doorlock state is not currently part of the pure-context device-state contract. |

---

## 6. Condensed interface groups for paper figures

For a more compact paper figure, the interfaces above may be grouped into the following summary flows.

### A. Input interfaces
- User → Bounded Input Node
- Bounded Input Node / Context Nodes → `safe_deferral/context/input`
- Doorbell / Visitor-Arrival Context Node → `safe_deferral/context/input`
- Context Nodes → Intake / Aggregation
- Emergency Nodes → `safe_deferral/emergency/event`

### B. Reasoning interfaces
- Aggregation → Local LLM Reasoning
- Local LLM Reasoning → Policy Router
- Local LLM Reasoning → `safe_deferral/llm/candidate_action` when candidate action output is used

### C. Control interfaces
- Policy Router → Deterministic Validator
- Validator → `safe_deferral/validator/output`
- Validator → Approved Low-Risk Actuation
- Validator → Safe Deferral / Clarification through `safe_deferral/deferral/request`
- Validator → Caregiver Escalation through `safe_deferral/escalation/class2`

### D. Execution interfaces
- Approved Low-Risk Actuation → `safe_deferral/actuation/command`
- Caregiver Approval → `safe_deferral/caregiver/confirmation`
- Governed manual dispatcher → `safe_deferral/actuation/command`
- Actuator Interface Nodes → `safe_deferral/actuation/ack`

### E. Guidance interfaces
- Runtime / deferral / ACK / escalation state → Local LLM Reasoning
- Local LLM Reasoning → TTS
- TTS → User

### F. Experiment-support interfaces
- Scenario / replay / fault injection → Intake
- Simulation → `safe_deferral/sim/context`
- Fault Injection → `safe_deferral/fault/injection`
- Dashboard observation → `safe_deferral/dashboard/observation`
- Progress publication → `safe_deferral/experiment/progress`
- Result publication → `safe_deferral/experiment/result`
- Audit / ACK / runtime state → Result Publication

### G. MQTT contract interfaces
- Operational input topics
- Candidate/validator/deferral/escalation topics
- Caregiver confirmation topics
- Actuation/ACK/audit topics
- Experiment/dashboard/result topics

### H. Governance support interfaces
- Governance Dashboard UI → MQTT / Payload Governance Backend
- Governance Backend → Topic Registry Loader / Contract Checker
- Governance Backend → Payload Example Manager / Validator
- Governance Backend → Publisher / Subscriber Role Manager
- Governance Backend → Draft Change / Validation Report

---

## 7. One-paragraph summary

The corrected interface interpretation is that ordinary bounded interaction uses context aggregation and local LLM reasoning before policy and validation, emergency sensing uses a policy-driven path rather than a primary LLM path, sensitive actuation requires caregiver approval after escalation, and user-facing explanations are generated by the LLM and delivered through TTS rather than directly by deferral or routing layers.

All MQTT-facing interfaces should remain aligned with `common/mqtt/topic_registry_v1_0_0.json`, and governance/dashboard interfaces may inspect, validate, or propose topic/payload changes without becoming policy, validator, caregiver approval, audit, or actuator authority.

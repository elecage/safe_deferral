# 15_interface_matrix.md

## 1. Purpose

This document records the interface matrix for the revised system architecture.

It is intended to support:
- paper figure drafting,
- Section 2 architecture writing,
- implementation reasoning,
- and consistency checks across runtime, control, and experiment-support paths.

This document should be read together with:
- `common/docs/architecture/14_system_components_outline_v2.md`
- `common/docs/paper/04_section2_system_design_outline.md`
- `CLAUDE.md`

---

## 2. Review notes applied before finalizing this matrix

The following corrections were explicitly applied before writing the final interface table:

- **Context Nodes do not go directly to the Local LLM Reasoning Layer.** They must enter through `MQTT Ingestion / State Intake` and then `Context and Runtime State Aggregation`.
- **Emergency Nodes do not use the Local LLM as the primary decision path.** They must follow a policy-driven path through `MQTT Ingestion / State Intake` and `Policy Router`.
- **Sensitive actuation is never triggered directly by `Caregiver Escalation`.** Execution can happen only after `Caregiver Approval`.
- **Local Audit Logging is not the direct sink of raw emergency sensing.** It records processed hub-side outcomes.

If a future diagram or text conflicts with these points, this matrix should be treated as the corrected interpretation.

---

## 3. Interface matrix

| Category | ID | Source Block | Destination Block | Description | Notes |
|---|---|---|---|---|---|
| User Input | UI-1 | User | Bounded Input Node | The user performs bounded alternative input. | Initial input |
| User Input | UI-2 | Bounded Input Node | MQTT Ingestion / State Intake | The input event is sent to the edge hub. | Primary input path |
| User Input | UI-3 | User | Bounded Input Node | The user provides clarification follow-up input after a guidance prompt. | Follow-up input |
| User Input | UI-4 | Bounded Input Node | MQTT Ingestion / State Intake | The clarification follow-up event is reintroduced into the hub. | Clarification re-entry |
| Context / State | CS-1 | Context Nodes | MQTT Ingestion / State Intake | Environmental and device-state context is delivered into the hub. | Context ingress |
| Context / State | CS-2 | MQTT Ingestion / State Intake | Context and Runtime State Aggregation | Received context/state is aggregated into an integrated runtime-state representation. | Main context path |
| Context / State | CS-3 | ACK Handling | Context and Runtime State Aggregation | Execution results are reflected back into runtime state. | Runtime feedback |
| Context / State | CS-4 | Caregiver Approval | Context and Runtime State Aggregation | Approval/denial results are reflected into runtime state. | Approval-state update |
| Context / State | CS-5 | Policy Router | Context and Runtime State Aggregation | Routing outcomes may be reflected into runtime state. | Optional runtime reflection |
| Context / State | CS-6 | Deterministic Validator | Context and Runtime State Aggregation | Validator outcomes may be reflected into runtime state. | Optional runtime reflection |
| Context / State | CS-7 | Safe Deferral and Clarification Management | Context and Runtime State Aggregation | Deferred state and pending clarification state are reflected into runtime state. | Clarification-state update |
| Emergency | EM-1 | Emergency Nodes | MQTT Ingestion / State Intake | Raw emergency events are collected into the hub. | Emergency ingress |
| Emergency | EM-2 | MQTT Ingestion / State Intake | Policy Router | Emergency events enter the policy-driven emergency path. | Primary emergency path |
| Emergency | EM-3 | Policy Router | Deterministic Validator | Emergency-safe admissibility or branch handling is checked. | Validator boundary |
| Emergency | EM-4 | Deterministic Validator | Safe Deferral and Clarification Management | If immediate execution is not justified, the event may move into deferred handling. | Exceptional emergency handling |
| Emergency | EM-5 | Deterministic Validator | Caregiver Escalation | Caregiver intervention is requested when required. | Sensitive or unresolved emergency case |
| Emergency | EM-6 | Deterministic Validator | TTS Rendering / Voice Output | Warning or status guidance may be provided to the user. | Emergency guidance |
| LLM Reasoning | LR-1 | Context and Runtime State Aggregation | Local LLM Reasoning Layer | The integrated runtime-state view is used as LLM input. | Main LLM input |
| LLM Reasoning | LR-2 | Local LLM Reasoning Layer | Policy Router | Intent candidates or interpretation results are delivered into the policy path. | Assistive interaction path |
| LLM Reasoning | LR-3 | Safe Deferral and Clarification Management | Local LLM Reasoning Layer | Deferred reasons are used for explanation and clarification-prompt generation. | Explanation basis |
| LLM Reasoning | LR-4 | Caregiver Escalation | Local LLM Reasoning Layer | Escalation state is used to generate user-facing guidance. | Escalation guidance |
| LLM Reasoning | LR-5 | ACK Handling | Local LLM Reasoning Layer | ACK results are used for explanation generation. | Result explanation |
| LLM Reasoning | LR-6 | Deterministic Validator | Local LLM Reasoning Layer | Validation outcomes can be reflected into user-facing explanation text. | Validation explanation |
| Policy / Validation | PV-1 | MQTT Ingestion / State Intake | Policy Router | Raw events that require direct policy handling enter the policy path. | Includes emergency handling |
| Policy / Validation | PV-2 | Local LLM Reasoning Layer | Policy Router | Assistive interpretation results are delivered into policy routing. | Normal assistive path |
| Policy / Validation | PV-3 | Policy Router | Deterministic Validator | Routed candidates move into the final admissibility boundary. | Required validation step |
| Policy / Validation | PV-4 | Deterministic Validator | Approved Low-Risk Actuation Path | Approved low-risk actions are forwarded to execution. | Low-risk only |
| Policy / Validation | PV-5 | Deterministic Validator | Safe Deferral and Clarification Management | Ambiguity, insufficient context, or policy restriction triggers deferred handling. | Safe deferral |
| Policy / Validation | PV-6 | Deterministic Validator | Caregiver Escalation | Sensitive or autonomously inadmissible requests trigger escalation. | Sensitive path |
| Actuation | AC-1 | Approved Low-Risk Actuation Path | Actuator Interface Nodes | Approved low-risk actions are dispatched to actuators. | Lighting etc. |
| Actuation | AC-2 | Caregiver Approval | Actuator Interface Nodes | Sensitive actuation is executed only after caregiver approval. | Sensitive actuation |
| Actuation | AC-3 | Actuator Interface Nodes | ACK Handling | Actuator-side acknowledgment or state confirmation is returned. | Closed-loop confirmation |
| Feedback / Guidance | FG-1 | Local LLM Reasoning Layer | TTS Rendering / Voice Output | Explanation, guidance, or clarification text is sent to the voice-rendering layer. | TTS input |
| Feedback / Guidance | FG-2 | TTS Rendering / Voice Output | User | Spoken guidance is delivered to the user. | Final user-facing output |
| Feedback / Guidance | FG-3 | Context and Runtime State Aggregation | Local LLM Reasoning Layer | Runtime state is used to produce status explanations. | Runtime-aware guidance |
| Feedback / Guidance | FG-4 | Safe Deferral and Clarification Management | Local LLM Reasoning Layer | Clarification-needed state is used to generate next-input suggestions. | Clarification prompt basis |
| Feedback / Guidance | FG-5 | Caregiver Escalation | Local LLM Reasoning Layer | Approval-waiting or escalation status is used to generate guidance. | Escalation guidance |
| Feedback / Guidance | FG-6 | ACK Handling | Local LLM Reasoning Layer | Execution result state is used to generate completion/failure guidance. | Result guidance |
| Experiment Support | EX-1 | Scenario Orchestrator | MQTT Ingestion / State Intake | Scenario-driven synthetic events are injected into the hub-side path. | Experiment entry |
| Experiment Support | EX-2 | Simulation / Replay | MQTT Ingestion / State Intake | Replay state or synthetic context is injected into the hub-side path. | Replay path |
| Experiment Support | EX-3 | Fault Injection | MQTT Ingestion / State Intake | Fault conditions such as staleness or missing state are injected. | Fault path |
| Experiment Support | EX-4 | Context and Runtime State Aggregation | Progress / Result Publication | Runtime progress information may be reflected into experiment-visible progress publication. | Experiment observation |
| Experiment Support | EX-5 | Local Audit Logging | Progress / Result Publication | Audit artifacts may be collected for experiment output. | Result artifact |
| Experiment Support | EX-6 | ACK Handling | Progress / Result Publication | ACK/result summaries may be collected for experiment output. | Result summary |

---

## 4. Prohibited or misleading interfaces

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

---

## 5. Condensed interface groups for paper figures

For a more compact paper figure, the interfaces above may be grouped into the following summary flows.

### A. Input interfaces
- User → Bounded Input Node
- Context Nodes → Intake / Aggregation
- Emergency Nodes → Policy path

### B. Reasoning interfaces
- Aggregation → Local LLM Reasoning
- Local LLM Reasoning → Policy Router

### C. Control interfaces
- Policy Router → Deterministic Validator
- Validator → Approved Low-Risk Actuation
- Validator → Safe Deferral / Clarification
- Validator → Caregiver Escalation

### D. Execution interfaces
- Approved Low-Risk Actuation → Actuator Interface Nodes
- Caregiver Approval → Sensitive actuator path
- Actuator Interface Nodes → ACK Handling

### E. Guidance interfaces
- Runtime / deferral / ACK / escalation state → Local LLM Reasoning
- Local LLM Reasoning → TTS
- TTS → User

### F. Experiment-support interfaces
- Scenario / replay / fault injection → Intake
- Audit / ACK / runtime state → Result Publication

---

## 6. One-paragraph summary

The corrected interface interpretation is that ordinary bounded interaction uses context aggregation and local LLM reasoning before policy and validation, emergency sensing uses a policy-driven path rather than a primary LLM path, sensitive actuation requires caregiver approval after escalation, and user-facing explanations are generated by the LLM and delivered through TTS rather than directly by deferral or routing layers.

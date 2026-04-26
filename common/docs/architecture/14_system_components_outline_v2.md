# 14_system_components_outline_v2.md

## 1. Purpose

This document records the revised system-component interpretation used for:

- architecture reasoning,
- paper figure drafting,
- Section 2 writing,
- and future implementation guidance.

This revision reflects the following important corrections:

- the local LLM does not only recover likely user intent,
- it also generates runtime-aware user-facing guidance,
- safe deferral may lead to a bounded clarification interaction rather than ending the interaction immediately,
- Class 2 is interpreted as bounded clarification / transition handling rather than terminal caregiver escalation by default,
- and MQTT/payload governance is treated as a separate non-authoritative development/evaluation support path rather than as operational control authority.

This document is a system-architecture interpretation note and should be read together with:
- `common/docs/paper/04_section2_system_design_outline.md`
- `common/docs/required_experiments.md`
- `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/architecture/19_class2_clarification_architecture_alignment.md`
- `common/docs/architecture/20_scenario_data_flow_matrix.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- `common/mqtt/topic_registry.json`
- `common/mqtt/publisher_subscriber_matrix.md`
- `common/mqtt/topic_payload_contracts.md`
- `common/payloads/README.md`
- `CLAUDE.md`

Historical MQTT registry baseline:
- `common/mqtt/topic_registry.json`

---

## 2. Top-level system structure

### 2.1 User
The primary user of the system.

Role:
- provides bounded alternative input,
- receives TTS-based guidance,
- and may provide bounded follow-up clarification input.

### 2.2 Caregiver
The human approval authority for sensitive-actuation cases and unresolved Class 2 interactions.

Role:
- receives escalation notifications,
- approves or denies sensitive action requests,
- provides confirmation evidence where appropriate,
- and acts as a human-in-the-loop control boundary.

### 2.3 ESP32 Device Layer
The field device layer.

Role:
- bounded input capture,
- context sensing,
- visitor-arrival / doorbell context sensing,
- emergency sensing,
- and bounded actuator interfacing.

### 2.4 Mac mini Edge Hub
The main operational edge hub.

Role:
- local LLM reasoning,
- runtime-state aggregation,
- policy routing,
- deterministic validation,
- MQTT topic registry loading / contract checking for runtime consistency where used,
- payload validation support where used,
- safe deferral / clarification management,
- Class 2 Clarification Manager,
- caregiver escalation,
- TTS output,
- ACK handling,
- and local audit logging.

### 2.5 Raspberry Pi 5 Support Layer
The experiment-support layer.

Role:
- experiment and monitoring dashboard,
- scenario orchestration,
- replay,
- simulation,
- fault injection,
- Class 2 clarification transition evaluation,
- progress publication,
- result artifact publication,
- MQTT/payload governance backend support,
- governance dashboard UI support,
- topic/payload contract validation support,
- and payload example / publisher-subscriber role inspection.

Important interpretation:
- Raspberry Pi 5 remains an experiment, dashboard, governance-inspection, and evaluation support layer.
- It is not the primary operational hub.
- It does not hold policy, validator, Class 2 transition, caregiver approval, or actuator authority.
- It does not hold doorlock dispatch authority.
- It does not directly edit canonical policy/schema assets.
- It does not allow governance backend or dashboard UI to publish actuator or doorlock commands.
- It does not allow governance UI to directly edit registry files.

### 2.6 MQTT / Payload Governance Backend
The governance backend is a non-authoritative service layer for topic and payload management support.

Role:
- manages draft topic/payload registry edits,
- validates topic-payload contracts,
- validates clarification interaction payload boundaries,
- validates the dedicated `safe_deferral/clarification/interaction` topic contract where used,
- manages publisher/subscriber role assignments,
- validates payload examples against referenced schemas,
- runs interface-matrix alignment checks,
- generates topic/payload drift reports where implemented,
- exports proposed change reports,
- supports governance backend/UI separation validation,
- and supports dashboard UI interactions.

Important interpretation:
- it may create, edit, delete, validate, and export draft registry changes,
- but it does not directly modify canonical policy/schema authority,
- does not directly modify canonical policies or schemas,
- does not publish actuator commands,
- does not publish doorlock commands,
- does not spoof caregiver approval,
- does not override Policy Router or Deterministic Validator decisions,
- does not treat clarification payloads as validator approval, actuator authorization, emergency trigger evidence, or doorlock authorization,
- does not convert draft/proposed changes into live operational authority without review,
- and does not create doorlock execution authority.

### 2.7 Governance Dashboard UI
The governance dashboard UI is a presentation and interaction layer for MQTT/payload governance.

Role:
- displays the topic registry,
- supports create/edit/delete draft interactions through the governance backend,
- visualizes publisher/subscriber role assignments,
- visualizes payload validation results,
- visualizes clarification interaction payload validation results,
- visualizes `safe_deferral/clarification/interaction` as an evidence-only topic,
- visualizes interface-matrix alignment results,
- visualizes topic/payload drift warnings where implemented,
- visualizes UI/backend contract failure states,
- visualizes Class 2 clarification authority-boundary warnings,
- visualizes doorbell/doorlock boundary warnings,
- and displays proposed change reports.

Important interpretation:
- the UI must call the governance backend for create/update/delete/validation/export operations,
- the UI does not write registry files directly,
- does not alter canonical policies or schemas,
- does not publish operational control messages,
- does not publish operational control topics,
- does not expose unrestricted actuator consoles,
- does not expose direct doorlock command controls,
- does not expose clarification-to-actuation promotion controls,
- and does not dispatch doorlock or actuator commands.

---

## 3. ESP32 device-layer components

### 3.1 Bounded Input Node
Collects the user’s constrained input.

Examples:
- button input,
- single-hit input,
- bounded alternative input,
- candidate-selection input during Class 2 clarification.

Role:
- generates bounded input events,
- receives clarification follow-up input from the user,
- provides selection or confirmation evidence during Class 2 clarification,
- does not autonomously interpret the meaning into actuation.

### 3.2 Context Nodes
Provide non-emergency context information.

Examples:
- temperature,
- illuminance,
- device states,
- occupancy-adjacent status,
- doorbell / visitor-arrival context.

Role:
- provide context for intent recovery,
- provide context for runtime-aware explanation generation,
- provide visitor-response context when `doorbell_detected` is relevant.

Important interpretation:
- `doorbell_detected` is emitted as `environmental_context.doorbell_detected`.
- It does not authorize autonomous doorlock control.
- Doorlock state is not currently part of `context_schema.device_states`.

### 3.3 Emergency Nodes
Provide emergency-trigger information.

Examples:
- gas,
- smoke,
- fall,
- threshold-based emergency signals.

Role:
- generate emergency triggers,
- provide deterministic emergency evidence that may support Class 2-to-Class 0 transition.

Important interpretation:
- emergency handling is policy-driven,
- emergency signals are not routed through the local LLM as the primary decision path,
- `doorbell_detected` is not an emergency trigger,
- LLM candidate text alone must not trigger Class 0.

### 3.4 Actuator Interface Nodes
The device-side actuation layer.

Examples:
- lighting control node,
- governed sensitive-action interface node,
- warning interface node.

Role:
- execute only approved actions,
- return ACK or state confirmation.

Important interpretation:
- lighting actuator nodes may execute current Class 1 low-risk commands only after deterministic approval,
- doorlock interface nodes may exist as implementation-facing or experiment-facing components,
- but doorlock must not be treated as autonomous Class 1 low-risk authority under the current baseline.
- In compact paper figures, this layer should be described as bounded or governed sensitive-action interfacing rather than as autonomous doorlock execution.

---

## 4. Mac mini edge-hub components

### 4.1 MQTT Ingestion / State Intake
The intake layer for field events and device status.

Inputs may include:
- bounded input events,
- clarification follow-up input,
- context-node states,
- emergency-node events,
- actuator ACK or state updates.

Role:
- receives all local field-side signals into the edge hub,
- supports registry-aware MQTT intake where topic registry lookup is used.

### 4.2 Context and Runtime State Aggregation
A broader aggregation layer than simple sensing aggregation.

Possible aggregated elements include:
- bounded input,
- environmental context,
- device state,
- current interaction event,
- routing result,
- validator result,
- safe deferral state,
- escalation state,
- caregiver approval state,
- execution / ACK state,
- pending clarification state,
- clarification session context,
- expected next-input options.

Role:
- forms the integrated runtime view used by reasoning and control layers.

Important interpretation:
- Context Nodes feed this layer.
- Emergency Nodes may be reflected into runtime state, but the primary emergency decision path remains policy-driven.
- Doorlock state, manual approval state, ACK state, and Class 2 clarification interaction state should not be silently inserted into current pure-context `device_states`.

### 4.3 Local LLM Reasoning Layer
A broader reasoning layer than intent recovery alone.

This layer includes at least the following subroles.

#### 4.3.1 Intent Recovery
Role:
- recover likely intent candidates under constrained input,
- interpret sparse or ambiguous input using context.

#### 4.3.2 Explanation / Guidance Generation
Role:
- generate user-facing explanations based on the current interaction and runtime state.

Examples:
- input receipt confirmation,
- current status explanation,
- safe-deferral explanation,
- caregiver-approval waiting explanation,
- execution result explanation,
- emergency warning explanation.

#### 4.3.3 Clarification Prompt Generation
Role:
- generate bounded next-input suggestions when ambiguity can be reduced by follow-up user input,
- support iterative clarification rather than ending at one-shot deferral.

Examples:
- “If you mean the living room light, press once; if you mean the bedroom light, press twice.”
- “Press once to call the caregiver; press twice to request approval.”

Important interpretation:
- the LLM may hold a broad awareness of runtime state for explanation purposes,
- but it does not hold final execution authority,
- does not determine final Class 2 transition targets by itself,
- does not authorize actuation,
- and does not trigger emergency handling by itself.

### 4.4 Policy Router
Classifies and routes events according to policy.

Examples:
- Class 0 emergency,
- Class 1 bounded low-risk assistance,
- Class 2 clarification / transition handling.

Role:
- determines the primary control path,
- separates emergency handling from ordinary assistive interaction,
- receives Class 2 re-entry requests after confirmation, timeout, or deterministic evidence.

Important interpretation:
- emergency is handled through this policy-driven path,
- Class 2 clarification selection must re-enter policy routing rather than bypassing it.

### 4.5 Deterministic Validator
The final authority on admissibility of execution.

Role:
- checks policy/schema admissibility,
- filters model outputs or candidates,
- blocks unsafe autonomous sensitive actuation,
- enforces the final execution boundary.

Important interpretation:
- actual execution authority resides here together with policy,
- not inside the LLM,
- not inside the Class 2 Clarification Manager.
- In compact paper figures, Policy Router and Deterministic Validator may be visually grouped only if deterministic validation remains clearly described as the final admissibility boundary.

### 4.6 MQTT Topic Registry Loader / Contract Checker
The registry-consistency support layer for runtime and verification code.

Role:
- loads topic definitions from `common/mqtt/topic_registry.json`,
- treats `topic_registry.json` as a historical baseline unless explicitly used for compatibility checks,
- prevents topic string drift where registry lookup is practical,
- checks alignment with `common/docs/architecture/15_interface_matrix.md`,
- detects topic/payload hardcoding drift where implemented,
- checks publisher/subscriber assumptions,
- resolves payload family, schema, example payload, QoS, retain, runtime-mode flags, and authority-level information.

Important interpretation:
- this component supports communication consistency,
- but it does not create policy authority or actuator authority.

### 4.7 Payload Validation Helper
The payload-consistency support layer.

Role:
- validates schema-governed payloads,
- checks required `environmental_context.doorbell_detected` in valid context examples,
- validates Class 2 clarification interaction payloads where used,
- validates `safe_deferral/clarification/interaction` topic payloads where MQTT publication is used,
- flags missing or malformed payload fields,
- flags or rejects doorlock state inside current `pure_context_payload.device_states`,
- and supports test/dashboard/governance validation reports.

Important interpretation:
- this component supports schema and payload-boundary consistency,
- but it does not replace the canonical schemas under `common/schemas/`,
- and it does not promote clarification payloads into authorization payloads.

### 4.8 Approved Low-Risk Actuation Path
The execution path for approved low-risk actions.

Current example scope:
- lighting-related low-risk actions.

Role:
- dispatch bounded admissible actions to actuator nodes.

Important interpretation:
- this is not a general sensitive-actuation path,
- Class 2-to-Class 1 transitions still require Policy Router re-entry and Deterministic Validator approval,
- and doorlock must not be treated as automatically included here.
- In compact figures, this should be labeled as Class 1 bounded execution and currently lighting only.

### 4.9 Safe Deferral and Clarification Management
The management layer for cases where immediate autonomous execution is not justified.

#### 4.9.1 Safe Deferral
Role:
- prevents unsafe autonomous actuation,
- sets the interaction into a deferred state,
- generates structured unresolved reasons.

Examples:
- ambiguous target,
- insufficient context,
- unresolved candidate,
- policy restriction.

#### 4.9.2 Clarification-Needed Deferral
Role:
- identifies cases that can be recovered through additional bounded user input,
- keeps a pending clarification state,
- provides the basis for clarification prompt generation.

#### 4.9.3 Class 2 Clarification Manager
Role:
- manages Class 2 as bounded clarification / transition handling,
- requests bounded candidate choices from the LLM Guidance Layer or Input Context Mapper,
- presents candidate choices through TTS/Display,
- collects user/caregiver selection, timeout, or deterministic evidence,
- requests Policy Router re-entry,
- records candidate, selection, timeout, transition, and final safe outcome evidence.

When MQTT publication is used, Class 2 clarification interaction artifacts should use:

```text
safe_deferral/clarification/interaction
```

Topic contract:

```text
payload_family: clarification_interaction_payload
schema: common/schemas/clarification_interaction_schema.json
authority_level: class2_interaction_evidence_not_authority
```

Important interpretation:
- Class 2 Clarification Manager has no actuation authority,
- no final class-decision authority,
- no emergency-trigger authority,
- no validator-bypass authority,
- and its MQTT clarification interaction topic carries evidence, not authorization.

#### 4.9.4 Escalation-Required Deferral
Role:
- identifies cases that cannot be safely resolved by follow-up user input alone,
- forwards the interaction toward caregiver escalation.

Important interpretation:
- Safe Deferral itself does not “speak” to the user.
- It provides the structured state and reasons from which the LLM can generate user-facing guidance, and TTS can then render that guidance.

### 4.10 Caregiver Escalation
The handoff layer for sensitive or non-autonomously-resolvable actions.

Role:
- generates caregiver notifications,
- provides a manual confirmation path,
- supports human-in-the-loop handling of sensitive actuation.

Important interpretation:
- this is central for representative sensitive-actuation cases such as doorlock-related requests,
- and for unresolved Class 2 cases where user clarification is unavailable, ambiguous, timed out, or sensitive.

### 4.11 TTS Rendering / Voice Output
The voice-rendering layer for user-facing messages.

Role:
- renders explanation/guidance text into spoken output,
- informs the user of current status,
- provides next-input suggestions during clarification interactions.

Examples:
- “Your input has been received.”
- “The requested device is unclear.”
- “Press once for the living room light and twice for the bedroom light.”
- “Waiting for caregiver approval.”
- “The light has been turned on.”

Important interpretation:
- TTS is the rendering/output layer,
- while explanation and prompt generation occur in the LLM reasoning layer,
- and TTS output is guidance, not execution authority.

### 4.12 ACK Handling
The result-confirmation layer.

Role:
- receives actuator ACK,
- distinguishes success / timeout / mismatch,
- updates runtime state accordingly.

### 4.13 Local Audit Logging
The local recording layer for interpreted and executed outcomes.

Examples of logged content:
- interpretation summary,
- routing result,
- validator result,
- deferral / clarification state,
- clarification candidates,
- selection result,
- timeout result,
- transition target,
- escalation result,
- caregiver approval result,
- ACK result.

Important interpretation:
- audit logging is not the direct destination of raw emergency sensing,
- it records the processed outcomes produced by the hub-side control flow.

---

## 5. Raspberry Pi 5 support-layer components

### 5.1 Experiment and Monitoring Dashboard
Provides experiment operation and monitoring visibility.

Role:
- experiment selection,
- preflight readiness visibility,
- required-node connectivity/status display,
- start/stop control through orchestration layer,
- progress monitoring,
- result summary display,
- approval-status visibility only,
- Class 2 clarification/transition visibility,
- graph/CSV export visibility where available.

Important interpretation:
- it may initiate experiment execution through the orchestrator,
- but it does not bypass policy, validator, Class 2 re-entry, caregiver approval, ACK, or audit boundaries.

### 5.2 Scenario Orchestrator
Runs experiment scenarios.

Examples:
- visitor-response scenarios,
- intent-recovery comparison,
- clarification-interaction scenarios,
- Class 2 transition scenarios,
- sensitive-actuation validation scenarios.

Class 2 transition scenarios may use `class2_clarification_expectation` in scenario fixtures to record the expected clarification topic, schema, transition target, Policy Router re-entry requirement, validator requirement for Class 1, timeout/no-response behavior, and non-authorization boundary.

### 5.3 Simulation / Replay
Supports event and state replay.

Role:
- synthetic event injection,
- context replay,
- clarification-turn replay.

### 5.4 Fault Injection
Injects controlled fault conditions.

Examples:
- staleness,
- missing state,
- conflict,
- missing `doorbell_detected` as a strict schema/context fault case.

### 5.5 Progress / Result / Governance Reports
Provides experiment-state visibility and non-authoritative governance-report support.

Role:
- progress update,
- artifact publication,
- reproducibility support,
- validation report publication,
- governance report publication,
- Class 2 transition evaluation report publication.

Important interpretation:
- validation reports and governance reports are evidence/support artifacts,
- not validator authority or operational authorization.

### 5.6 Topic / Payload Contract Validation
Validates communication and payload references for experiment and governance tooling.

Role:
- topic registry validation,
- publisher/subscriber consistency checking,
- topic-to-payload contract validation,
- `safe_deferral/clarification/interaction` contract validation,
- payload example validation,
- clarification interaction payload validation,
- schema path and example path resolution,
- interface-matrix alignment validation,
- topic/payload hardcoding drift detection,
- dashboard/governance non-authority validation.

Important interpretation:
- this is validation and governance support,
- not operational policy authority.

### 5.7 MQTT / Payload Governance Backend
Provides backend operations for topic and payload governance.

Role:
- draft topic creation,
- draft topic editing,
- draft topic deletion,
- publisher/subscriber role management,
- payload family and schema/example linkage,
- clarification interaction payload boundary validation,
- dedicated clarification interaction topic validation,
- interface-matrix alignment validation,
- topic/payload drift report generation,
- governance backend/UI separation validation support,
- validation report generation,
- proposed change export.

Important interpretation:
- it may manage draft governance artifacts,
- but it does not directly edit canonical policy/schema authority,
- does not directly modify canonical policies or schemas,
- does not publish actuator or doorlock commands,
- does not spoof caregiver approval,
- does not promote clarification payloads into actuation authority,
- does not convert proposed changes into live authority without review,
- and does not create doorlock execution authority.

### 5.8 Governance Dashboard UI
Provides the UI surface for MQTT/payload governance.

Role:
- topic registry browsing,
- topic detail display,
- create/edit/delete draft interactions through backend APIs,
- publisher/subscriber role display and editing through backend APIs,
- payload validation result display,
- clarification interaction validation result display,
- dedicated clarification interaction topic visibility,
- interface-matrix alignment display,
- topic/payload drift warning display,
- UI/backend contract failure display,
- Class 2 clarification boundary warning display,
- doorbell/doorlock boundary warning display,
- proposed change report display.

Important interpretation:
- it is a UI layer only,
- not the backend service,
- not a policy authority,
- not an actuator console,
- does not directly edit registry files,
- does not directly publish operational control topics,
- does not expose direct doorlock command controls,
- and does not expose clarification-to-actuation promotion controls.

### 5.9 Payload Example Manager
Manages and validates payload examples/templates for governance support.

Role:
- list payload examples,
- list payload templates,
- validate schema-governed examples,
- validate clarification interaction examples,
- validate `class2_clarification_expectation` template blocks,
- generate draft examples for review,
- export validation reports.

Important interpretation:
- payload examples are reference assets,
- not policy authority or schema authority.

### 5.10 Publisher / Subscriber Role Manager
Manages allowed or known communication roles.

Role:
- list known publisher roles,
- list known subscriber roles,
- validate role assignment against topic authority level,
- distinguish operational roles from experiment-only roles,
- distinguish dashboard/governance roles from policy/validator/dispatcher roles,
- validate publishers/subscribers for `safe_deferral/clarification/interaction`.

Important interpretation:
- dashboard/governance roles must not be assigned direct actuator, caregiver approval, validator, or policy authority unless explicitly marked as controlled test-mode roles.
- Class 2 clarification roles must not be assigned direct actuator, emergency trigger, validator approval, or doorlock unlock authority.
- The RPi-side Class 2 transition verifier may subscribe to `safe_deferral/clarification/interaction` as an observer only. It must not create Class 2 transition authority, validator authority, caregiver approval authority, or actuation authority.

Important interpretation for the RPi layer as a whole:
- Raspberry Pi remains an experiment-support layer,
- not the primary operational hub.

---

## 6. Main control-flow interpretations

### 6.1 General assistive interaction path
User  
→ Bounded Input Node  
→ MQTT Ingestion / State Intake  
→ Context and Runtime State Aggregation  
→ Local LLM Reasoning Layer  
→ Policy Router  
→ Deterministic Validator  
→ Approved Low-Risk Actuation Path or Safe Deferral and Clarification Management  
→ TTS Rendering / Voice Output  
→ User  
→ ACK Handling  
→ Local Audit Logging

### 6.2 Clarification interaction path
Initial bounded input  
→ Context and Runtime State Aggregation  
→ Local LLM Reasoning Layer  
→ Policy Router / Deterministic Validator  
→ clarification-needed deferral  
→ Class 2 Clarification Manager  
→ LLM-generated next-input suggestion  
→ TTS Rendering / Voice Output  
→ user follow-up bounded input / caregiver confirmation / timeout / deterministic evidence  
→ MQTT Ingestion / State Intake  
→ updated Context and Runtime State Aggregation  
→ Policy Router re-entry  
→ Deterministic Validator when Class 1 is reached  
→ Class 1 bounded actuation, Class 0 emergency handling, continued safe deferral, or caregiver confirmation

Optional MQTT evidence publication for this path:

```text
safe_deferral/clarification/interaction
```

Important interpretation:
- this is not a purely one-shot system,
- it supports bounded multi-turn clarification when policy permits,
- clarification results do not bypass Policy Router or Deterministic Validator,
- and the dedicated clarification interaction topic is evidence/transition state only, not execution authority.

### 6.3 Emergency path
Emergency Nodes  
→ MQTT Ingestion / State Intake  
→ Policy Router  
→ Deterministic Validator / emergency-safe path  
→ required protective or escalation handling  
→ TTS / warning output as needed  
→ Local Audit Logging

Important interpretation:
- emergency does not depend on the LLM as the primary decision path,
- though emergency state may later be reflected into runtime-aware user guidance.
- if deterministic emergency evidence arrives during Class 2 clarification, it may support Class 2-to-Class 0 transition through Policy Router re-entry.

### 6.4 Sensitive-actuation path
Bounded Input + Context  
→ Context and Runtime State Aggregation  
→ Local LLM Reasoning Layer  
→ Policy Router  
→ Deterministic Validator  
→ Safe Deferral and Clarification Management or Caregiver Escalation  
→ Caregiver Approval  
→ Governed Manual Dispatcher  
→ Sensitive Actuator Path  
→ ACK Handling  
→ Local Audit Logging  
→ updated runtime-state-based explanation generation  
→ TTS Rendering / Voice Output  
→ User

### 6.5 MQTT / payload governance flow
User / Developer  
→ Governance Dashboard UI  
→ MQTT / Payload Governance Backend  
→ Topic Registry Loader / Payload Validator  
→ Draft Registry Change / Validation Report  
→ Review / Commit Workflow

Important interpretation:
- this flow does not publish actuator commands,
- does not modify canonical policy/schema truth directly,
- does not create doorlock execution authority,
- does not promote clarification payloads into validator approval or actuator authority,
- and does not bypass policy, validator, caregiver approval, ACK, or audit boundaries.
- interface-matrix alignment and topic-drift validation are verification/governance checks, not operational authorization mechanisms.

---

## 7. Concepts that should remain visible in the paper figure

The paper figure should preserve visibility of at least the following concepts:

- User
- Caregiver
- Bounded Input Node
- Context Nodes
- Doorbell / Visitor-Arrival Context Node where visitor-response evaluation is shown
- Emergency Nodes
- Actuator Interface Nodes
- Context and Runtime State Aggregation
- Local LLM Reasoning Layer
- Policy Router + Deterministic Validator
- Approved Low-Risk Actuation
- Safe Deferral and Clarification Management
- Class 2 Clarification Manager / bounded clarification transition loop
- Caregiver Escalation / Approval
- Governed manual dispatch for sensitive actions
- TTS Rendering / Voice Output
- Local ACK + Audit Logging
- Raspberry Pi experiment support
- Non-authoritative Raspberry Pi governance/report support

Optional development/evaluation support inset:
- MQTT Topic / Payload Registry
- MQTT-aware Interface Matrix
- MQTT / Payload Governance Backend
- Governance Dashboard UI
- Topic / Payload Validation
- Topic Drift Check
- Payload Example Validation
- Publisher / Subscriber Role Management
- Class 2 transition evaluation support
- Class 2 clarification interaction evidence topic: `safe_deferral/clarification/interaction`

---

## 8. Core conceptual distinctions that the figure should make explicit

### 8.1 LLM path
- bounded input,
- context aggregation,
- intent recovery,
- explanation generation,
- clarification prompt generation.

### 8.2 Policy-driven emergency path
- emergency nodes,
- policy routing / validation,
- no primary LLM dependency.

### 8.3 Sensitive-actuation path
- validator-bound,
- caregiver-mediated,
- approval required,
- governed manual dispatch,
- ACK and audit required.

### 8.4 Clarification interaction path
- safe deferral,
- Class 2 Clarification Manager,
- next-input suggestion,
- follow-up bounded input or caregiver confirmation,
- timeout/no-response handling,
- Policy Router re-entry,
- possible Class 1 / Class 0 / Safe Deferral / Caregiver Confirmation outcome,
- optional evidence publication through `safe_deferral/clarification/interaction`.

### 8.5 Feedback path
- runtime-aware explanation,
- TTS voice output,
- user guidance.

### 8.6 MQTT/payload governance path
- registry-driven topic/payload management,
- publisher/subscriber role validation,
- interface-matrix alignment,
- topic/payload drift detection,
- clarification interaction payload validation,
- dedicated clarification interaction topic validation,
- proposed-change review boundary,
- dashboard UI separated from backend service,
- no policy, validator, caregiver approval, or actuator authority,
- no doorlock execution authority creation through registry edits.

---

## 9. One-sentence summary

The revised v2 interpretation is:

> The local LLM recovers likely user intent and generates runtime-aware explanations and clarification prompts under constrained-input conditions, while actuation authority remains with policy routing, deterministic validation, Class 2 Policy Router re-entry, and caregiver-mediated escalation for sensitive actions; MQTT/payload governance supports registry-driven communication management and Class 2 clarification interaction evidence without becoming operational control authority.

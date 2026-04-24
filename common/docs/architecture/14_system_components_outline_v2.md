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
- and safe deferral may lead to a bounded clarification interaction rather than ending the interaction immediately.

This document is a system-architecture interpretation note and should be read together with:
- `common/docs/paper/04_section2_system_design_outline.md`
- `common/docs/required_experiments.md`
- `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`
- `CLAUDE.md`

---

## 2. Top-level system structure

### 2.1 User
The primary user of the system.

Role:
- provides bounded alternative input,
- receives TTS-based guidance,
- and may provide bounded follow-up clarification input.

### 2.2 Caregiver
The human approval authority for sensitive-actuation cases.

Role:
- receives escalation notifications,
- approves or denies sensitive action requests,
- and acts as a human-in-the-loop control boundary.

### 2.3 ESP32 Device Layer
The field device layer.

Role:
- bounded input capture,
- context sensing,
- emergency sensing,
- and actuator interfacing.

### 2.4 Mac mini Edge Hub
The main operational edge hub.

Role:
- local LLM reasoning,
- runtime-state aggregation,
- policy routing,
- deterministic validation,
- safe deferral / clarification management,
- caregiver escalation,
- TTS output,
- ACK handling,
- and local audit logging.

### 2.5 Raspberry Pi 5 Support Layer
The experiment-support layer.

Role:
- scenario orchestration,
- replay,
- simulation,
- fault injection,
- and result publication.

---

## 3. ESP32 device-layer components

### 3.1 Bounded Input Node
Collects the user’s constrained input.

Examples:
- button input,
- single-hit input,
- bounded alternative input.

Role:
- generates bounded input events,
- receives clarification follow-up input from the user,
- does not autonomously interpret the meaning into actuation.

### 3.2 Context Nodes
Provide non-emergency context information.

Examples:
- temperature,
- illuminance,
- device states,
- occupancy-adjacent status.

Role:
- provide context for intent recovery,
- provide context for runtime-aware explanation generation.

### 3.3 Emergency Nodes
Provide emergency-trigger information.

Examples:
- gas,
- smoke,
- fall,
- threshold-based emergency signals.

Role:
- generate emergency triggers.

Important interpretation:
- emergency handling is policy-driven,
- emergency signals are not routed through the local LLM as the primary decision path.

### 3.4 Actuator Interface Nodes
The device-side actuation layer.

Examples:
- lighting control node,
- representative doorlock interface node,
- warning interface node.

Role:
- execute only approved actions,
- return ACK or state confirmation.

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
- receives all local field-side signals into the edge hub.

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
- but it does not hold final execution authority.

### 4.4 Policy Router
Classifies and routes events according to policy.

Examples:
- Class 0 emergency,
- Class 1 bounded low-risk assistance,
- Class 2 escalation-related handling.

Role:
- determines the primary control path,
- separates emergency handling from ordinary assistive interaction.

Important interpretation:
- emergency is handled through this policy-driven path.

### 4.5 Deterministic Validator
The final authority on admissibility of execution.

Role:
- checks policy/schema admissibility,
- filters model outputs or candidates,
- blocks unsafe autonomous sensitive actuation,
- enforces the final execution boundary.

Important interpretation:
- actual execution authority resides here together with policy,
- not inside the LLM.

### 4.6 Approved Low-Risk Actuation Path
The execution path for approved low-risk actions.

Current example scope:
- lighting-related low-risk actions.

Role:
- dispatch bounded admissible actions to actuator nodes.

Important interpretation:
- this is not a general sensitive-actuation path,
- and doorlock must not be treated as automatically included here.

### 4.7 Safe Deferral and Clarification Management
The management layer for cases where immediate autonomous execution is not justified.

#### 4.7.1 Safe Deferral
Role:
- prevents unsafe autonomous actuation,
- sets the interaction into a deferred state,
- generates structured unresolved reasons.

Examples:
- ambiguous target,
- insufficient context,
- unresolved candidate,
- policy restriction.

#### 4.7.2 Clarification-Needed Deferral
Role:
- identifies cases that can be recovered through additional bounded user input,
- keeps a pending clarification state,
- provides the basis for clarification prompt generation.

#### 4.7.3 Escalation-Required Deferral
Role:
- identifies cases that cannot be safely resolved by follow-up user input alone,
- forwards the interaction toward caregiver escalation.

Important interpretation:
- Safe Deferral itself does not “speak” to the user.
- It provides the structured state and reasons from which the LLM can generate user-facing guidance, and TTS can then render that guidance.

### 4.8 Caregiver Escalation
The handoff layer for sensitive or non-autonomously-resolvable actions.

Role:
- generates caregiver notifications,
- provides a manual confirmation path,
- supports human-in-the-loop handling of sensitive actuation.

Important interpretation:
- this is central for representative sensitive-actuation cases such as doorlock-related requests.

### 4.9 TTS Rendering / Voice Output
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
- while explanation and prompt generation occur in the LLM reasoning layer.

### 4.10 ACK Handling
The result-confirmation layer.

Role:
- receives actuator ACK,
- distinguishes success / timeout / mismatch,
- updates runtime state accordingly.

### 4.11 Local Audit Logging
The local recording layer for interpreted and executed outcomes.

Examples of logged content:
- interpretation summary,
- routing result,
- validator result,
- deferral / clarification state,
- escalation result,
- caregiver approval result,
- ACK result.

Important interpretation:
- audit logging is not the direct destination of raw emergency sensing,
- it records the processed outcomes produced by the hub-side control flow.

---

## 5. Raspberry Pi 5 support-layer components

### 5.1 Scenario Orchestrator
Runs experiment scenarios.

Examples:
- visitor-response scenarios,
- intent-recovery comparison,
- clarification-interaction scenarios,
- sensitive-actuation validation scenarios.

### 5.2 Simulation / Replay
Supports event and state replay.

Role:
- synthetic event injection,
- context replay,
- clarification-turn replay.

### 5.3 Fault Injection
Injects controlled fault conditions.

Examples:
- staleness,
- missing state,
- conflict.

### 5.4 Progress / Result Publication
Provides experiment-state visibility.

Role:
- progress update,
- artifact publication,
- reproducibility support.

Important interpretation:
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
→ LLM-generated next-input suggestion  
→ TTS Rendering / Voice Output  
→ user follow-up bounded input  
→ MQTT Ingestion / State Intake  
→ updated Context and Runtime State Aggregation  
→ Local LLM Reasoning Layer  
→ Policy Router / Deterministic Validator  
→ low-risk actuation or continued deferral or escalation

Important interpretation:
- this is not a purely one-shot system,
- it supports bounded multi-turn clarification when policy permits.

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

### 6.4 Sensitive-actuation path
Bounded Input + Context  
→ Context and Runtime State Aggregation  
→ Local LLM Reasoning Layer  
→ Policy Router  
→ Deterministic Validator  
→ Safe Deferral and Clarification Management or Caregiver Escalation  
→ Caregiver Approval  
→ Sensitive Actuator Path  
→ ACK Handling  
→ Local Audit Logging  
→ updated runtime-state-based explanation generation  
→ TTS Rendering / Voice Output  
→ User

---

## 7. Concepts that should remain visible in the paper figure

The paper figure should preserve visibility of at least the following concepts:

- User
- Caregiver
- Bounded Input Node
- Context Nodes
- Emergency Nodes
- Actuator Interface Nodes
- Context and Runtime State Aggregation
- Local LLM Reasoning Layer
- Policy Routing + Validation
- Approved Low-Risk Actuation
- Safe Deferral and Clarification Management
- Caregiver Escalation / Approval
- TTS Rendering / Voice Output
- Local ACK + Audit Logging
- Raspberry Pi experiment support

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
- ACK and audit required.

### 8.4 Clarification interaction path
- safe deferral,
- next-input suggestion,
- follow-up bounded input,
- re-entry into the decision loop.

### 8.5 Feedback path
- runtime-aware explanation,
- TTS voice output,
- user guidance.

---

## 9. One-sentence summary

The revised v2 interpretation is:

> The local LLM recovers likely user intent and generates runtime-aware explanations and clarification prompts under constrained-input conditions, while actuation authority remains with policy routing, deterministic validation, and caregiver-mediated escalation for sensitive actions.

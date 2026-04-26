# 19. Class 2 Clarification Architecture Alignment

## 1. Purpose

This document records the Phase 1 architecture alignment for the revised Class 2 semantics.

It should be read together with:

- `common/docs/architecture/14_system_components_outline_v2.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/architecture/18_scenario_node_component_mapping.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE0_FROZEN_BASELINE_AUDIT.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_SCENARIO_POLICY_SCHEMA_VERIFY_UPDATE_PLAN_V2.md`

This document does not replace frozen policy/schema assets. It records the architecture interpretation that should guide the Phase 2 policy baseline update and subsequent schema/verifier/test updates.

---

## 2. Phase 1 alignment decision

Phase 0 found that the active policy table currently treats Class 2 primarily as caregiver escalation. The revised scenario interpretation requires a broader Class 2 model:

```text
Class 2 = clarification / transition state
```

The architecture interpretation is therefore:

```text
Class 2 is entered when the system cannot safely determine the user's intent from available context, or when a bounded interaction requires confirmation before routing. In Class 2, the system may generate bounded candidate choices, present them to the user or caregiver, collect confirmation or timeout evidence, and then transition to Class 1, Class 0, or Safe Deferral / Caregiver Confirmation.
```

This is a semantic clarification of the operational architecture, not a grant of additional LLM or actuator authority.

---

## 3. Relationship to existing architecture documents

### 3.1 Relationship to `14_system_components_outline_v2.md`

Document 14 already contains several compatible concepts:

- safe deferral may lead to bounded clarification rather than ending the interaction immediately;
- the local LLM generates runtime-aware user-facing guidance;
- the local LLM does not hold execution authority;
- the Mac mini Edge Hub includes safe deferral / clarification management.

This document makes the Class 2-specific interpretation explicit.

The following logical module should be considered part of the Mac mini Edge Hub:

```text
Class 2 Clarification Manager
```

It may be implemented as a submodule of the existing Safe Deferral and Clarification Management layer.

Recommended placement inside the Mac mini Edge Hub:

```text
Mac mini Edge Hub
├─ MQTT Ingestion / State Intake
├─ Context and Runtime State Aggregation
├─ Local LLM Reasoning Layer
├─ Policy Router
├─ Deterministic Validator
├─ Safe Deferral and Clarification Management
│  └─ Class 2 Clarification Manager
├─ Caregiver Escalation
├─ TTS Rendering / Voice Output
├─ Actuator Dispatcher / Governed Manual Dispatcher
├─ ACK Handling
└─ Local Audit Logging
```

### 3.2 Relationship to `15_interface_matrix.md`

Document 15 already includes the following compatible interfaces:

- user follow-up input through `UI-3` and `UI-4`;
- safe deferral / clarification through `PV-5` and `FG-4`;
- deferral requests over `safe_deferral/deferral/request`;
- caregiver escalation over `safe_deferral/escalation/class2`;
- caregiver confirmation over `safe_deferral/caregiver/confirmation`;
- audit traceability through `safe_deferral/audit/log`.

This document clarifies that these existing interfaces are sufficient for Phase 1 architecture alignment. New clarification-specific MQTT topics are not required at this phase.

### 3.3 Relationship to `16_system_architecture_figure.md`

Document 16 already describes:

- safe deferral and clarification management;
- local LLM-assisted intent interpretation;
- Policy Router plus Deterministic Validator as the final admissibility boundary;
- caregiver escalation and approval;
- TTS guidance;
- ACK and audit closure.

The figure should now be interpreted as supporting a Class 2 clarification loop:

```text
Ambiguous / insufficient input
→ Class 2 clarification state
→ bounded candidate choices
→ user/caregiver confirmation or timeout
→ Class 1, Class 0, or Safe Deferral / Caregiver Confirmation
```

The compact SVG does not need to draw every candidate-selection arrow if the caption and architecture text make this interpretation explicit.

### 3.4 Relationship to `17_payload_contract_and_registry.md`

Document 17 currently separates pure context payloads from dashboard, manual approval, ACK, audit states, and Class 2 clarification interaction payloads.

This alignment preserves that boundary:

```text
Class 2 clarification payloads must not be forced into pure_context_payload.
```

Clarification candidate choices, user selections, timeout results, and transition outcomes are interaction payloads or scenario/test artifacts, not pure context state.

Current clarification payload family:

```text
clarification_interaction_payload
```

Current clarification interaction schema:

```text
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
```

This schema governs Class 2 clarification interaction records and is distinct from `pure_context_payload` and `class_2_notification_payload`.

### 3.5 Relationship to `18_scenario_node_component_mapping.md`

Document 18 already separates physical nodes from software/system components and includes:

- Class 2 Clarification Manager;
- LLM Guidance Layer;
- Bounded Input Node;
- TTS/Voice Output Node;
- Device State Reporter Node;
- Policy Router;
- Deterministic Validator;
- Audit Log.

This document confirms that those mappings are the correct Phase 1 architecture interpretation for Class 2.

---

## 4. Class 2 Clarification Manager

### 4.1 Role

The Class 2 Clarification Manager is the logical module that manages insufficient-context or ambiguity-driven interaction before a final route is selected.

Its responsibilities are:

```text
- detect that Class 2 clarification is required;
- request bounded candidate generation from LLM Guidance Layer or Input Context Mapper;
- present candidate choices through TTS, display, or other accessible output;
- collect user response through Bounded Input Node, Voice Input, or caregiver confirmation;
- handle no-response or timeout;
- request re-routing after confirmation or deterministic evidence;
- ensure no autonomous actuation occurs during unresolved Class 2 state;
- ensure every candidate, selection, timeout, transition, and deferral is audit logged.
```

### 4.2 Inputs

Class 2 Clarification Manager may consume:

| Input | Source | Notes |
|---|---|---|
| Initial ambiguous event | Policy Router / Validator / Safe Deferral handler | Enters Class 2 clarification state |
| Runtime context summary | Context and Runtime State Aggregation | Used to choose bounded candidates |
| Deferral reason | Deterministic Validator / Safe Deferral handler | Explains why direct execution is blocked |
| Candidate choices | LLM Guidance Layer / Input Context Mapper | Guidance only, not authority |
| User selection | Bounded Input Node / Voice Input | Confirmation evidence |
| Caregiver confirmation | Caregiver Confirmation backend | Manual confirmation evidence |
| Timeout/no response | Interaction timer | Leads to Safe Deferral or caregiver confirmation |
| New emergency evidence | Emergency Node / Policy Router | May trigger Class 0 transition |

### 4.3 Outputs

Class 2 Clarification Manager may produce:

| Output | Destination | Notes |
|---|---|---|
| Candidate prompt request | LLM Guidance Layer | Bounded prompt generation |
| Candidate prompt | TTS/Display output path | User-facing guidance |
| Clarification state update | Context and Runtime State Aggregation | Pending state, selected option, timeout state |
| Re-routing request | Policy Router | After confirmation or new evidence |
| Safe deferral result | Safe Deferral handler | If ambiguity persists |
| Caregiver confirmation request | Caregiver Escalation / Notification | If user cannot resolve ambiguity |
| Audit event | Local Audit Logging | Required for traceability |

---

## 5. LLM boundary for Class 2

The LLM Guidance Layer may generate bounded candidate choices and user-facing wording.

Allowed:

```text
- summarize the current ambiguity;
- generate short candidate choices;
- convert candidate choices into accessible TTS/display wording;
- explain that the system is waiting for confirmation;
- explain why automatic execution is not yet performed.
```

Not allowed:

```text
- make the final class decision;
- authorize actuator execution;
- trigger Class 0 emergency handling by itself;
- approve sensitive actuation;
- override the Policy Router;
- bypass the Deterministic Validator;
- fabricate missing state;
- convert dashboard/governance evidence into operational authority.
```

Canonical boundary sentence:

```text
The LLM may generate candidates and guidance, but the final transition must be determined by user/caregiver confirmation or deterministic evidence and must pass policy/validator constraints before execution.
```

---

## 6. Class 2 transition targets

Class 2 can transition to three safe outcome families.

| Transition target | Condition | Example | Execution boundary |
|---|---|---|---|
| `CLASS_1` | User/caregiver confirms a bounded low-risk assistance request | User selects “조명 켜기” | Must pass low-risk catalog and Deterministic Validator |
| `CLASS_0` | Emergency confirmation, triple-hit, or deterministic sensor evidence | User selects “긴급 도움”, triple-hit occurs, fall/smoke/gas/high-temperature evidence arrives | Policy-driven emergency path; no LLM final decision |
| `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION` | No response, ambiguous response, persistent insufficient context, or unresolved conflict | User does not respond, candidates remain unresolved | No autonomous actuation |

Class 2 itself is therefore a routing state and interaction state, not a final actuation state.

---

## 7. Interface interpretation for Class 2

### 7.1 Entry into Class 2

Class 2 entry may occur from:

```text
- insufficient context;
- unresolved candidate ambiguity;
- stale policy-relevant state;
- missing critical state;
- conflict among candidate interpretations;
- validator block on autonomous execution;
- caregiver-required sensitive path.
```

Architecture path:

```text
Bounded Input / Context / Runtime State
→ Policy Router / Deterministic Validator
→ Safe Deferral and Clarification Management
→ Class 2 Clarification Manager
```

### 7.2 Candidate prompt generation

Architecture path:

```text
Class 2 Clarification Manager
→ LLM Guidance Layer or Input Context Mapper
→ bounded candidate choices
→ TTS/Display Output
→ User
```

Recommended existing topic use:

```text
safe_deferral/deferral/request
```

This topic already represents safe deferral events or bounded clarification requests.

### 7.3 User selection

Architecture path:

```text
User
→ Bounded Input Node or Voice Input Node
→ MQTT Ingestion / State Intake
→ Context and Runtime State Aggregation
→ Policy Router
```

Recommended existing topic use:

```text
safe_deferral/context/input
```

Follow-up input should re-enter the same bounded input plane rather than bypass policy routing.

### 7.4 Caregiver confirmation

Architecture path:

```text
Caregiver Notification / Escalation Interface
→ Caregiver confirmation
→ Governed manual path or re-routing
```

Recommended existing topic use:

```text
safe_deferral/caregiver/confirmation
```

Caregiver confirmation is not autonomous Class 1 approval. It is manual confirmation evidence for a governed path.

### 7.5 Timeout / no response

Architecture path:

```text
Class 2 Clarification Manager timeout
→ Safe Deferral or Caregiver Confirmation
→ Audit Log
```

No response must not result in autonomous actuation.

### 7.6 Audit traceability

Every Class 2 interaction should record:

```text
- initial ambiguous input;
- unresolved reason;
- candidate choices generated;
- presentation channel;
- selected candidate or timeout/no-response;
- transition target;
- validator result if Class 1 is reached;
- emergency evidence if Class 0 is reached;
- safe deferral or caregiver confirmation result;
- final execution or non-execution outcome.
```

Recommended existing topic use:

```text
safe_deferral/audit/log
```

---

## 8. Payload interpretation for Class 2

### 8.1 Payloads that remain unchanged

The following should remain unchanged in Phase 1:

```text
common/schemas/context_schema_v1_0_0_FROZEN.json
common/mqtt/topic_registry_v1_0_0.json
```

Reason:

```text
Class 2 clarification is an interaction/control payload family, not pure operational context.
Existing deferral, escalation, caregiver confirmation, and audit topics are sufficient for architecture-level representation.
```

### 8.2 Current schema-governed clarification interaction payload

The following payload family is the current Class 2 clarification interaction payload family:

```text
clarification_interaction_payload
```

It is governed by:

```text
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
```

This schema records clarification candidates, presentation channel, user/caregiver response, timeout result, transition target, and final safe outcome. It must remain separate from pure context payloads, notification payloads, validator outputs, actuation commands, and emergency triggers.

Representative fields:

```json
{
  "clarification_id": "string",
  "source_scenario": "SCN_CLASS2_INSUFFICIENT_CONTEXT",
  "unresolved_reason": "insufficient_context_or_ambiguous_candidates",
  "candidate_choices": [
    {
      "candidate_id": "C1_LIGHTING_ASSISTANCE",
      "prompt": "조명을 켤까요?",
      "candidate_transition_target": "CLASS_1",
      "requires_confirmation": true
    }
  ],
  "presentation_channel": "tts_or_display",
  "selection_result": {
    "selected_candidate_id": "C1_LIGHTING_ASSISTANCE",
    "selection_source": "bounded_input",
    "confirmed": true
  },
  "transition_target": "CLASS_1"
}
```

### 8.3 Boundary rule

Do not place Class 2 clarification state into:

```text
pure_context_payload.device_states
```

Do not place LLM-generated candidate text into:

```text
routing_metadata
```

Do not treat candidate prompt payloads as:

```text
validator approval
actuator command
doorlock authorization
emergency trigger
```

---

## 9. Figure interpretation update

The current paper figure does not need a new major block if it already contains:

```text
Safe Deferral and Clarification Management
Local LLM Reasoning Layer
Policy Router + Deterministic Validator
TTS / Voice Output
Caregiver Escalation / Approval
Audit Logging
```

However, captions and explanatory text should clarify:

```text
Class 2 is implemented as a clarification loop rather than a terminal failure path.
```

Suggested figure interpretation sentence:

```text
When the hub cannot safely determine the user's intent, the Safe Deferral and Clarification Management block enters a Class 2 clarification state, uses the LLM only to generate bounded candidate prompts, collects user or caregiver confirmation, and then re-enters policy routing for Class 1 bounded assistance, Class 0 emergency handling, or continued safe deferral.
```

---

## 10. Conflict fault and missing-state relationship

Class 2, conflict fault, and missing-state fault must remain distinguishable.

| Case | Meaning | Expected safe behavior |
|---|---|---|
| Class 2 insufficient context | The system cannot determine the user's intent from available context | Present bounded candidates and seek confirmation |
| Conflict fault | Multiple plausible candidates remain simultaneously admissible | Do not choose arbitrarily; seek confirmation or safe deferral |
| Missing-state fault | Required device/context state is absent | Do not assume missing state; recheck state or safe deferral |

Relationship:

```text
Conflict fault and missing-state fault may enter Class 2-like clarification or safe deferral handling, but they should remain explicitly described as fault causes.
```

This distinction is important for experiments and audit logs because the mitigation reason is different.

---

## 11. Architecture invariants after Phase 1

The following invariants should guide all later policy/schema/scenario/verifier/test work:

```text
1. Class 2 is a clarification/transition state, not a terminal failure by default.
2. The LLM may generate bounded candidate choices and explanation text only.
3. The LLM must not make final class decisions.
4. The LLM must not authorize actuation.
5. The LLM must not trigger emergency handling by itself.
6. User/caregiver confirmation or deterministic evidence is required before transition.
7. Class 1 transition must remain bounded to low-risk catalog actions and deterministic validation.
8. Class 0 transition must remain policy-driven by emergency confirmation, triple-hit, or sensor evidence.
9. Persistent ambiguity/no response must lead to Safe Deferral or Caregiver Confirmation.
10. Existing context schema should not be overloaded with clarification state.
11. Existing MQTT topics are sufficient for architecture-level representation at this phase.
12. All Class 2 candidate, selection, timeout, transition, and execution/non-execution outcomes must be audit logged.
```

---

## 12. Phase 1 outcome

Phase 1 architecture alignment does not require immediate SVG redesign or new MQTT topics.

It requires the following architecture interpretation to be adopted by subsequent phases:

```text
Class 2 is managed by the Mac mini Edge Hub as a safe clarification loop. It uses LLM guidance only for bounded candidate prompt generation, collects user/caregiver confirmation or deterministic evidence, and transitions to Class 1, Class 0, or Safe Deferral / Caregiver Confirmation without granting autonomous execution authority to the LLM.
```

This document should be treated as the bridge between the Phase 0 frozen-baseline audit and Phase 2 policy baseline update.

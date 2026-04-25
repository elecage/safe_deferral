# 16_system_architecture_figure.md

## System Architecture Figure and Interpretation

## 1. Purpose

This document is the consolidated architecture-figure document for the `safe_deferral` project.

It supersedes the previously split architecture-figure notes from the 16~24 document range, including:

- `common/docs/architecture/24_final_paper_architecture_figure.md`

The purpose of this document is to provide one stable reference for:

- the paper-oriented system architecture figure,
- the operational closed-loop interpretation,
- Mac mini / Raspberry Pi 5 / ESP32 / measurement-node role separation,
- low-risk vs sensitive-actuation routing,
- `doorbell_detected` visitor-response context,
- payload-boundary interpretation,
- MQTT topic / payload contract interpretation,
- MQTT/payload governance dashboard and backend boundary,
- and figure-caption guidance for the paper.

This document does **not** override frozen policies or schemas. If any conflict exists, the following remain authoritative or controlling references according to their scope:

- `common/policies/`
- `common/schemas/`
- `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`
- `common/docs/architecture/14_system_components_outline_v2.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/required_experiments.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`

---

## 2. Final paper figure

![Final paper architecture figure](./figures/system_layout_final_macmini_only_lshape.svg)

This figure should be treated as the current active Mac-mini-centered operational architecture figure.

However, the current SVG does not yet fully draw every Raspberry Pi support-layer connection, MQTT/payload governance flow, dashboard observation flow, experiment progress/result topic flow, registry-management interface, MQTT-aware interface matrix alignment check, topic/payload hardcoding drift check, payload validation report flow, or governance backend/UI separation validation flow.

Those elements are documented in this file and in `common/docs/architecture/15_interface_matrix.md`, and should be reflected in a future figure revision.

### Current figure status

The current SVG figure is the active operational figure for the present paper-writing and architecture-discussion stage.

It is strongest for explaining:

- ESP32 bounded physical nodes,
- Mac mini operational control loop,
- local LLM-assisted interpretation,
- deterministic policy/validation,
- safe deferral,
- caregiver-mediated sensitive-actuation handling,
- ACK and audit closure.

It is not yet a complete visual representation of:

- all Raspberry Pi support-layer MQTT connections,
- MQTT/payload governance backend flow,
- governance dashboard UI flow,
- publisher/subscriber role management,
- payload example management,
- topic registry CRUD/review workflow,
- MQTT-aware interface matrix alignment checks,
- topic/payload hardcoding drift checks,
- payload validation report flow,
- governance backend/UI separation validation.

These items are intentionally captured in the document explanation first and should be added visually in a later figure revision.

It emphasizes the operational closed loop across:

- bounded user input,
- context and emergency ingestion,
- local LLM-assisted intent interpretation,
- deterministic policy routing,
- deterministic validation,
- low-risk execution,
- context-integrity-based safe deferral,
- caregiver-mediated approval for sensitive actions,
- policy-constrained TTS/user feedback,
- and local acknowledgement plus audit closure.

The Raspberry Pi 5 region is retained as a support-side monitoring and experiment layer, not as the primary operational control authority.

---

## 3. High-level architecture regions

The figure should be read as four major regions.

| Region | Role | Authority boundary |
|---|---|---|
| ESP32 device layer | Bounded physical input, sensing, emergency/event detection, doorbell / visitor-arrival context sensing, actuator/warning interfaces | No high-level reasoning authority; no autonomous sensitive-actuation authority |
| Mac mini edge hub | Safety-critical operational hub for MQTT/state intake, local LLM, policy router, validator, safe deferral, caregiver escalation, ACK, audit, topic registry loading, and payload validation support | Primary operational authority under frozen policy/schema constraints; registry/payload helpers support consistency but do not create authority |
| Raspberry Pi 5 support region | Experiment dashboard, simulation, replay, fault injection, scenario orchestration, progress/result publication, MQTT/payload governance backend/UI support, topic/payload validation, payload example inspection, publisher/subscriber role review | Experiment/support visibility and governance inspection; not policy, validator, caregiver approval, execution, direct registry-file editing, canonical policy/schema editing, actuator command publishing, or doorlock command publishing authority |
| Optional measurement node | Out-of-band timing and latency capture | Measurement-only; not operational control plane |

---

## 4. ESP32 device layer

The ESP32 layer represents field-side interaction and actuation endpoints.

It may include:

- bounded button input node,
- emergency triple-hit input path,
- environmental sensing nodes,
- doorbell / visitor-arrival context node,
- lighting control node,
- optional gas/fire/fall sensing or event-interface nodes,
- planned doorlock or warning interface nodes.

Important interpretation:

1. ESP32 nodes are bounded physical nodes.
2. ESP32 nodes may emit events or states that are normalized into schema-valid payloads.
3. ESP32 nodes must not locally replace policy routing, validator logic, or caregiver approval.
4. ESP32 doorlock or warning interface nodes may exist for representative or caregiver-mediated evaluation, but must not reinterpret doorlock as autonomous Class 1 low-risk execution authority.

### Doorbell / visitor-arrival context

Doorbell or visitor-arrival context must be represented as:

```json
{
  "environmental_context": {
    "doorbell_detected": true
  }
}
```

or:

```json
{
  "environmental_context": {
    "doorbell_detected": false
  }
}
```

according to the scenario.

`doorbell_detected` is a required visitor-response context signal. It does **not** authorize autonomous doorlock control.

---

## 5. Mac mini edge hub

The Mac mini region is the operational control core.

Its L-shaped boundary intentionally includes the caregiver-approval region in the same host-level operational enclosure. This reflects the interpretation that caregiver approval handling is not external to the control loop, but a governed part of the operational architecture.

The Mac mini region includes:

- MQTT ingestion and state intake,
- context and runtime aggregation,
- local LLM reasoning,
- Policy Router,
- Deterministic Validator,
- MQTT topic registry loader / contract checker,
- payload validation helper,
- context-integrity-based safe deferral stage,
- caregiver escalation,
- caregiver approval handling,
- TTS rendering or user feedback generation,
- approved low-risk dispatch interface,
- ACK handling,
- local audit logging.

The topic registry loader and payload validation helper support:

- registry-based topic lookup where practical,
- publisher/subscriber contract checking,
- publisher/subscriber role consistency checking,
- interface-matrix alignment checking,
- topic/payload hardcoding drift detection where implemented,
- schema/payload boundary consistency,
- `doorbell_detected` required-field checks,
- and prevention of doorlock state drift into current pure-context `device_states`.

These helpers support communication consistency, schema/payload boundary checks, and governance/verification evidence. They do not replace policy/schema authority, do not create actuator authority, and do not function as operational authorization mechanisms.

The Mac mini may expose operational telemetry, audit summaries, and control-state topics consumed by the Raspberry Pi 5 dashboard. This exposure does not make the RPi dashboard a policy authority.

---

## 6. Raspberry Pi 5 support region

The Raspberry Pi 5 region is the support-side experiment and monitoring layer.

It may include:

- Monitoring / Experiment Dashboard,
- experiment support runtime,
- simulation and replay,
- virtual sensor and state generation,
- virtual `doorbell_detected` visitor-response context generation,
- virtual emergency event generation,
- fault injection,
- scenario orchestration,
- progress/status publication,
- result summaries,
- CSV/graph export,
- evaluation artifact generation,
- MQTT/payload governance backend,
- governance dashboard UI,
- topic/payload contract validation,
- interface-matrix alignment validation,
- topic/payload drift report generation,
- payload validation report generation,
- governance backend/UI separation validation,
- payload example manager,
- publisher/subscriber role manager.

The RPi dashboard is a support-side visibility and experiment-operations console.

The MQTT/payload governance backend and governance dashboard UI may be documented as part of the Raspberry Pi support-side toolchain even if their visual links are not yet drawn in the current SVG figure.

They may support:

- topic registry browsing,
- draft topic creation/edit/delete workflows,
- publisher/subscriber role review,
- payload family and schema/example linkage,
- payload example validation,
- interface-matrix alignment validation,
- topic/payload drift report generation,
- payload validation report generation,
- governance backend/UI separation validation,
- proposed change reports,
- live or replayed topic traffic inspection,
- doorbell/doorlock boundary warnings.

They are **not**:

- policy authority,
- validator authority,
- caregiver approval authority,
- primary operational hub,
- direct sensitive-actuation authority,
- direct doorlock dispatch authority,
- canonical schema/policy editing authority,
- direct registry-file editing authority through the UI,
- actuator or doorlock command publishing authority,
- caregiver approval spoofing authority,
- a path for draft/proposed changes to become live operational authority without review.

The RPi dashboard and orchestration layers may visualize visitor-response or doorlock-sensitive experiment state, including:

- `doorbell_detected` state,
- autonomous-unlock-blocked status,
- caregiver escalation state,
- manual approval state,
- ACK state,
- audit completeness state.

These dashboard states are observation/evaluation payloads, not canonical pure-context device states and not policy truth.

---

## 7. Optional measurement node region

STM32 timing nodes or equivalent dedicated timing devices may be used as out-of-band measurement infrastructure for class-wise latency experiments.

They are used for:

- timing capture,
- latency evidence collection,
- trigger/observe/actuation timestamp export,
- repeated-run reproducibility support.

They must not:

- publish operational control decisions,
- replace policy routing,
- replace validator behavior,
- directly control actuators as part of the operational path,
- be treated as ordinary operational physical nodes.

---

## 8. Operational closed-loop interpretation

The closed loop consists of the following steps.

### Step 1. Bounded input and context ingestion

Input may originate from:

- bounded physical button input,
- environmental sensing,
- emergency sensors/events,
- doorbell / visitor-arrival context,
- simulated RPi scenario input during experiments.

MQTT-facing interfaces should remain aligned with:

- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/docs/architecture/15_interface_matrix.md`

The currently documented MQTT-facing interfaces include context input, emergency events, LLM candidate action, validator output, safe deferral request, Class 2 escalation, caregiver confirmation, actuation command, actuation ACK, audit log, simulation context, fault injection, dashboard observation, experiment progress, and experiment result topics.

The normalized operational input must preserve the payload boundaries defined in:

- `common/docs/architecture/17_payload_contract_and_registry.md`

In particular:

- `routing_metadata` must not be mixed into LLM context,
- `pure_context_payload` must conform to `context_schema_v1_0_0_FROZEN.json`,
- every valid `environmental_context` must include `doorbell_detected`,
- doorlock state must not be inserted into current `device_states`.

### Step 2. Local LLM-assisted intent interpretation

The local LLM may assist with:

- intent recovery under constrained input,
- status explanations,
- safe-deferral reasons,
- bounded next-input suggestions.

The LLM must not become the execution authority.

The LLM output should be interpreted as a bounded candidate or interpretation artifact that must still pass deterministic policy and schema constraints.

### Step 3. Policy routing

The Policy Router performs deterministic class routing according to the frozen policy table.

Current major outcomes:

- Class 0 emergency override,
- Class 1 bounded low-risk assistance,
- Class 2 caregiver escalation.

The current canonical emergency family is:

- `E001`: high temperature threshold crossing,
- `E002`: emergency triple-hit bounded input,
- `E003`: smoke detected state trigger,
- `E004`: gas detected state trigger,
- `E005`: fall detected event trigger.

`doorbell_detected` is not a Class 0 emergency trigger.

### Step 4. Deterministic validation

The Deterministic Validator checks whether a proposed Class 1 candidate is admissible.

It enforces:

- schema validity,
- action-domain validity,
- single-admissible-action resolution,
- low-risk catalog membership,
- safe fallback under conflict or ambiguity.

Current autonomous Class 1 execution remains limited to:

- `light_on` → `living_room_light`,
- `light_on` → `bedroom_light`,
- `light_off` → `living_room_light`,
- `light_off` → `bedroom_light`.

Doorlock control is not current autonomous Class 1 execution.

### Step 5. Approved low-risk execution or safe deferral

If exactly one admissible low-risk action remains, the system may forward the approved action to the bounded dispatcher / actuator interface.

If ambiguity, insufficient context, schema problems, policy conflict, or unresolved multiple candidates remain, the system must prefer:

- safe deferral,
- bounded clarification,
- or Class 2 escalation,

rather than unsafe autonomous actuation.

### Step 6. Caregiver-mediated sensitive path

Sensitive requests, including doorlock-related requests, must not be routed as ordinary Class 1 autonomous low-risk execution.

Doorlock-sensitive outcomes should proceed through:

- Class 2 escalation,
- separately governed manual confirmation path,
- caregiver approval,
- ACK verification,
- local audit logging.

`doorbell_detected=true` may support visitor-response interpretation, but it does not authorize door unlock.

### Step 7. User feedback and TTS

The figure’s TTS/user-feedback path should be interpreted as policy-constrained output.

LLM-generated explanation or status text is not treated as directly speakable raw output. It should be constrained by policy routing, validator decisions, safe-deferral outcomes, and output profile guidance.

### Step 8. ACK and audit closure

Every execution path that results in actuation must support closed-loop outcome evidence.

Audit closure may include:

- route decision,
- LLM interpretation/candidate summary,
- validator decision,
- safe deferral or escalation reason,
- caregiver approval outcome when applicable,
- dispatch result,
- ACK result,
- final non-actuation or actuation outcome.

Audit records are evidence and traceability artifacts. They do not redefine policy truth.

### Step 9. MQTT/payload governance support path

The MQTT/payload governance support path is separate from the operational closed loop.

It may include:

- Governance Dashboard UI,
- MQTT/payload governance backend,
- topic registry loader / contract checker,
- payload example manager / validator,
- publisher/subscriber role manager,
- interface-matrix alignment reports,
- topic-drift reports,
- payload validation reports,
- draft registry change reports,
- proposed-change reports,
- review/commit workflow.

This path may inspect, validate, and propose communication-contract changes. It must not:

- publish actuator commands,
- publish doorlock commands,
- modify canonical policies/schemas directly,
- create doorlock execution authority,
- spoof caregiver approval,
- bypass deterministic validation,
- or treat dashboard observation as policy truth.

Interface-matrix alignment reports, topic-drift reports, payload validation reports, and proposed-change reports are governance/verification artifacts, not operational authorization mechanisms.

---

## 9. Payload interpretation in the figure

The architecture figure should be read with the following payload boundaries.

| Payload / state | Belongs where | Does not belong where |
|---|---|---|
| `routing_metadata` | Policy Router input wrapper, audit correlation, staleness handling | LLM prompt context |
| `pure_context_payload` | LLM-relevant physical/context input | Dashboard-only state, manual approval state, ACK state |
| `environmental_context.doorbell_detected` | Required visitor-response context | Doorlock authorization |
| current `device_states` | `living_room_light`, `bedroom_light`, `living_room_blind`, `tv_main` | Doorlock state |
| doorlock state | Experiment annotation, dashboard observation, audit artifact, manual confirmation path, future schema | Current `pure_context_payload.device_states` |
| manual approval state | Caregiver/manual confirmation path, experiment artifact, audit | Pure context payload |
| ACK state | Actuator result, audit, dashboard observation, experiment artifact | Pure context payload |
| dashboard observation state | RPi support-side visibility | Policy truth or validator authority |
| MQTT topic registry | `common/mqtt/`, governance backend, validation reports, review/commit workflow | Policy/schema authority or actuator authorization |
| payload examples/templates | `common/payloads/`, payload validation helper, governance backend, test/scenario scaffolds | Policy truth or schema authority |
| governance draft changes | Governance backend, validation report, review/commit workflow | Live runtime control or doorlock execution authority |
| interface-matrix alignment report | Governance backend, verification report, dashboard artifact | Operational authorization |
| topic-drift report | Governance backend, verification report, dashboard artifact | Policy truth or execution authority |
| payload validation report | Governance backend, verification report, dashboard artifact | Schema authority or actuation authority |

Detailed payload rules are defined in:

- `common/docs/architecture/17_payload_contract_and_registry.md`

Detailed interface and topic coverage are defined in:

- `common/docs/architecture/15_interface_matrix.md`

---

## 10. Figure elements not yet fully drawn

The current SVG does not yet fully draw:

- Raspberry Pi support-layer MQTT connections,
- dashboard observation topic flows,
- experiment progress/result topic flows,
- MQTT/payload governance backend,
- governance dashboard UI,
- publisher/subscriber role manager,
- payload example manager,
- topic registry CRUD/review workflow,
- MQTT-aware interface matrix alignment check,
- topic drift check,
- payload validation report flow,
- governance backend/UI separation validation flow.

These should be added in a future figure revision.

Until the SVG is revised, the explanatory text in this document and the MQTT-aware interface matrix in `common/docs/architecture/15_interface_matrix.md` should be used to interpret the full support-layer and governance-layer design.

---

## 11. Figure caption draft

Suggested paper caption:

> System architecture of the proposed privacy-aware edge smart-home system. Field-side ESP32 nodes provide bounded input, sensing, emergency-event, doorbell/visitor-arrival context, and actuator/warning interfaces. The Mac mini edge hub performs local context aggregation, LLM-assisted intent interpretation, deterministic policy routing, deterministic validation, registry-aware communication consistency checks, interface-matrix alignment, topic/payload drift detection, payload-boundary validation support, context-integrity-based safe deferral, caregiver-mediated escalation, ACK handling, and local audit logging. The Raspberry Pi 5 region provides support-side experiment orchestration, monitoring, simulation, fault injection, progress/result publication, evaluation artifact generation, and non-authoritative MQTT/payload governance tooling for topic registry inspection, payload validation, publisher/subscriber role review, interface-matrix alignment, topic/payload drift reporting, and validation report generation, without becoming policy or execution authority.

Shorter caption:

> Overall system architecture showing bounded physical input, local LLM-assisted interpretation, deterministic policy validation, safe deferral, caregiver-mediated sensitive actuation, local audit closure, and Raspberry Pi-based experiment monitoring with non-authoritative MQTT/payload governance support.

---

## 12. Paper interpretation notes

This figure supports the paper’s main claims because it shows:

1. LLM assistance is present but not authoritative.
2. Deterministic policy and validator stages remain central.
3. Safe deferral is a first-class outcome rather than an error state.
4. Sensitive actuation is separated from low-risk autonomous execution.
5. Caregiver approval is modeled as a governed path.
6. ACK and audit closure are part of the closed loop.
7. RPi dashboard/simulation is an experiment-support layer, not operational authority.
8. Payload boundaries are necessary to prevent state and authority drift.
9. MQTT/payload governance is separated from operational authority.
10. Topic/payload registry edits cannot create doorlock execution authority.
11. Some RPi/governance connections are documented but not yet drawn in the current SVG and should be added in a future figure revision.
12. Interface-matrix alignment and topic/payload drift checks are governance/verification evidence, not execution authority.
13. Governance dashboard UI and governance backend separation is part of the safety boundary.

---

## 13. Superseded / historical notes

This document consolidates the architecture-figure interpretation that was previously spread across multiple architecture files in the 16~24 range.

The most important prior document was:

- `common/docs/architecture/24_final_paper_architecture_figure.md`

If older architecture-figure notes conflict with this document, prefer this consolidated document together with:

- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/required_experiments.md`
- `common/docs/runtime/SESSION_HANDOFF.md`

---

## 14. Summary

The final architecture figure should be read as a closed-loop, policy-first, edge-local assistive control architecture.

The key interpretation is:

- ESP32 nodes provide bounded physical interaction and sensing.
- Mac mini is the safety-critical operational edge hub.
- The local LLM assists intent interpretation but does not authorize execution.
- Deterministic policy and validation control admissibility.
- Safe deferral and caregiver escalation prevent unsafe autonomous action.
- Doorbell context supports visitor-response interpretation but does not authorize doorlock control.
- Doorlock-sensitive execution remains caregiver-mediated or manually governed.
- RPi provides experiment/dashboard/simulation/fault-injection support without becoming authority.
- MQTT/payload governance tooling may inspect, validate, and propose communication-contract changes without becoming operational authority.
- Interface-matrix alignment, topic-drift checks, and payload validation reports support governance/verification only.
- Governance dashboard UI and backend service separation prevents registry-management tooling from becoming control authority.
- ACK and audit closure complete the safety argument.

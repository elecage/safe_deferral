# System Structure Figure Component Inventory

## 1. Purpose

This document completes Step 1 of
`common/docs/architecture/08_system_structure_figure_revision_plan.md`.

It compares the current SVG blocks in:

```text
common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg
```

against the current active architecture and records what should be kept,
renamed, split, removed, or added before the SVG is edited.

## 2. Inventory Decision Labels

| Label | Meaning |
| --- | --- |
| Keep | Keep the block mostly as-is |
| Rename | Keep the block but change label or wording |
| Split | Replace one current block with multiple clearer blocks |
| Move | Keep concept but move it to another area |
| Add | Add a missing block |
| Remove | Remove from the active figure |

## 3. Current Top-Level Areas

| Current SVG area | Current role | Decision | Target treatment |
| --- | --- | --- | --- |
| User | bounded input and voice-guided interaction | Keep | Keep as external actor on the left/top-left |
| Caregiver | approval authority for sensitive actuation | Rename | Keep as external actor, but connect through Telegram notification / confirmation |
| ESP32 Device Layer | field-side bounded input, sensing, emergency detection, actuator interfacing | Split | Separate actual physical nodes from experiment-only physical nodes |
| Mac mini Edge Hub | local reasoning, validation, TTS, caregiver approval, ACK, audit | Keep and restructure | Keep as central operational authority, but split internal blocks more accurately |
| Raspberry Pi 5 | monitoring, orchestration, governance, result publication | Split | Expand into current experiment app categories |
| STM32 / timing node | not present | Add | Add out-of-band timing / measurement support area |
| Canonical assets / contracts | not present | Add optional | Add small repository-governed reference band if layout space allows |

## 4. Physical Node Area

| Current SVG block | Current wording | Decision | Target block(s) |
| --- | --- | --- | --- |
| Bounded Input Node | button and alternative input | Keep | Actual physical node: Bounded Button Input Node |
| Context Nodes | environment and device-state sensing | Split | Environmental Context Node; Device State Reporter |
| Emergency Nodes | gas, smoke, fall, threshold emergency signals | Move / Split | Experiment-only gas, smoke/fire, fall nodes unless promoted; emergency evidence remains bounded input to Mac mini |
| Actuator Interface Nodes | lighting and governed sensitive-action interface | Split | Actual Lighting Control Node; Feedback Output Node; experiment-only Doorlock-Sensitive Interface Node |
| Doorbell / visitor context | not explicit | Add | Actual Doorbell / Visitor Context Node |
| Warning output | implied in actuator/emergency areas | Add | Feedback Output Node in actual nodes; Warning Experiment Node in experiment-only nodes |

## 5. Actual Physical Nodes To Show

The revised figure should include these actual baseline physical nodes:

| Target block | Reason |
| --- | --- |
| Bounded Button Input Node | Required user input surface |
| Environmental Context Node | Required context source |
| Doorbell / Visitor Context Node | Required for `doorbell_detected` visitor-response interpretation |
| Device State Reporter | Required to avoid missing/stale state ambiguity |
| Lighting Control Node | Current autonomous Class 1 low-risk actuator target |
| Feedback Output Node | TTS/display/buzzer/accessible feedback surface |

## 6. Experiment-Only Physical Nodes To Show

The revised figure should include these as a separate experiment-only group:

| Target block | Reason |
| --- | --- |
| Gas Sensor Experiment Node | Class 0 gas evidence experiments |
| Smoke / Fire Experiment Node | Class 0 smoke/fire evidence experiments |
| Fall-Detection Interface Node | Class 0 fall evidence experiments |
| Warning Output Experiment Node | Controlled warning-output experiments |
| Doorlock-Sensitive Interface Node | Representative sensitive-actuation evaluation |

The revised figure should not include a physical fault-injection node. Fault
injection should be shown in Raspberry Pi virtual behavior / fault injection
support.

## 7. Mac Mini Internal Blocks

| Current SVG block | Current wording | Decision | Target block(s) |
| --- | --- | --- | --- |
| MQTT Ingestion / State Intake | receives field-side events and registry-aware MQTT intake | Rename | MQTT / Context Intake |
| Context and Runtime State Aggregation | bounded input, context, runtime-state integration | Keep | State Aggregation |
| Local LLM Reasoning Layer | intent recovery, explanation, clarification prompt generation | Rename | Local LLM Adapter / Candidate Guidance |
| Policy Router + Deterministic Validator | deterministic routing and final admissibility boundary | Split | Policy Router; Deterministic Validator |
| Approved Low-Risk Actuation Path | Class 1 bounded execution, lighting only | Rename | Low-Risk Dispatcher, lighting only |
| Safe Deferral and Clarification Management | deferred state and clarification-needed | Split | Context-Integrity Safe Deferral; Class 2 Clarification Manager |
| Caregiver Escalation | manual confirmation path for sensitive actuation | Rename | Caregiver Notification / Confirmation Backend |
| Local ACK + Audit Logging | shared lower layer for hub-side outcomes | Split | ACK Handler; Audit Logging Service |
| Read-only telemetry | not present | Add | Read-only Telemetry Adapter for RPi tools |

## 8. Raspberry Pi Internal Blocks

| Current SVG block | Current wording | Decision | Target block(s) |
| --- | --- | --- | --- |
| Monitoring / Experiment Dashboard | runtime status, approval-status visibility, experiment monitoring | Rename | Web Experiment Dashboard |
| Experiment Support | scenario orchestration, replay, simulation, fault injection | Split | Experiment Manager; Scenario Manager; Virtual Node Manager; Virtual Behavior / Fault Injection Manager |
| Progress / Result / Governance Reports | progress, summaries, validation reports, artifacts | Split | Result Store / Analysis; MQTT / Payload Governance Support |
| MQTT / interface status | not explicit | Add | MQTT / Interface Status Manager |

The RPi area must remain visually non-authoritative. Arrows from RPi to Mac mini
should be labeled as controlled experiment input, observation, telemetry, or
governance support, not operational override.

## 9. Caregiver And Telegram Blocks

| Current SVG block | Current wording | Decision | Target block(s) |
| --- | --- | --- | --- |
| Caregiver | approval authority for sensitive actuation | Rename | Caregiver |
| Caregiver Approval | approval or denial for governed manual dispatch | Keep / Move | Keep near caregiver path |
| Telegram Bot API | not present | Add | Telegram Bot API transport between Mac mini backend and caregiver |

The caregiver path should show:

```text
Mac mini caregiver backend -> Telegram Bot API -> Caregiver
Caregiver response -> Telegram Bot API -> Mac mini caregiver backend
```

It must not imply that Telegram itself is policy, validator, or doorlock
authority.

## 10. STM32 Timing / Measurement Area

| Current SVG block | Decision | Target treatment |
| --- | --- | --- |
| none | Add | Add STM32 Timing / Measurement Node as out-of-band support |

The STM32 area should connect to:

- RPi experiment manager,
- result store / analysis,
- optional measurement export path.

It should not connect into Policy Router, Deterministic Validator, or dispatcher
as authority.

## 11. Canonical Assets / Contracts Area

| Current SVG block | Decision | Target treatment |
| --- | --- | --- |
| none | Add optional | Add small repository-governed references band if space allows |

Possible label:

```text
Canonical Assets / Contracts
policies, schemas, MQTT registry, payload contracts, scenario contracts
```

This area should be drawn as reference/configuration support, not as runtime
execution authority.

## 12. Current Arrow Groups To Replace

The current SVG uses several long paths that cross large areas or reuse similar
lanes. The revision should replace them by flow group.

| Current flow family | Problem | Target treatment |
| --- | --- | --- |
| ESP32 to Mac mini intake arrows | Some paths route through empty interior lanes and create future crossing risk | Use short left-to-center entry lanes into MQTT / Context Intake |
| LLM to Policy Router arrow | Current line climbs and crosses internal space | Use adjacent vertical or short horizontal lane |
| Policy branch arrows | Multiple right-side branches share similar lanes | Split Class 1, Class 2, and caregiver lanes |
| Actuation command path | Long route from Mac mini to left actuator block | Use dedicated lower operational dispatch lane |
| TTS / feedback arrows | Several feedback arrows converge near the same line | Use a separate feedback lane to Feedback Output Node |
| ACK path | Current ACK arrows share lower lanes | Use separate ACK lane to ACK Handler, then Audit |
| Caregiver approval path | Telegram missing; approval route looks direct | Insert Telegram transport and response lane |
| RPi monitoring path | Current RPi path is visually inside Mac mini L-shape | Move RPi to non-authoritative support area with observation/experiment lanes |
| STM32 timing path | Missing | Add dashed or distinct measurement lane to RPi result collection |

## 13. Keep / Rename / Split / Add Summary

| Action | Count | Items |
| --- | ---: | --- |
| Keep | 3 | User, State Aggregation, Caregiver Approval concept |
| Rename | 7 | Caregiver, MQTT Intake, Local LLM, Low-Risk Dispatcher, Caregiver Backend, Web Dashboard, Mac mini/RPi area labels |
| Split | 7 | ESP32 Device Layer, Context Nodes, Actuator Nodes, Policy Router + Validator, Safe Deferral + Clarification, ACK + Audit, RPi Experiment Support |
| Add | 8 | Doorbell/Visitor Context Node, Device State Reporter, Feedback Output Node, Telegram Bot API, Read-only Telemetry Adapter, MQTT/Interface Status Manager, STM32 Timing Node, optional Canonical Assets band |
| Remove | 1 | Physical fault-injection node from active baseline |

## 14. Step 1 Outcome

The current SVG should not be patched arrow-by-arrow in its existing layout.
The next step should be a block-only layout draft that places the required areas
without detailed arrows.

Recommended next revision step:

```text
Step 2. Layout draft
```

The layout draft should decide the canvas structure and block positions before
any final arrow routing is attempted.


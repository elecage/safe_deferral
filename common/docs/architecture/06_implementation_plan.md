# 06_implementation_plan.md

## Implementation Plan

## Project Goal
Build a policy-first, safety-oriented edge smart-home prototype with the Mac mini as the primary operational hub, while restricting LLM use to bounded intent interpretation, explanation support, and low-risk candidate generation under deterministic policy and validator control.

## Non-Goals
- No autonomous door unlocking
- No free-form LLM actuation
- No user-study implementation in this phase
- No cloud-dependent inference in the core architecture
- No hardcoded MQTT topic or payload-contract drift in runtime apps where registry-based loading is practical
- No dashboard or governance tool acting as policy, validator, caregiver approval, or actuator authority

## Architecture Scope
- The Mac mini hosts all core operational runtime services
- Raspberry Pi 5 is used as the experiment-side dashboard, multi-node simulation, virtual sensing, replay, fault-injection, scenario orchestration, progress/result publication, and closed-loop evaluation node
- ESP32 devices are used as embedded physical nodes for bounded button input, sensing, doorbell / visitor-arrival context generation, or actuator/warning interfacing within the applicable scope
- ESP32 development itself is prepared through a cross-platform host-side install / configure / verify workflow before real node firmware is generated
- Optional STM32 timing nodes or equivalent dedicated measurement nodes may be used for out-of-band class-wise latency evaluation
- The LLM assists bounded interpretation and candidate generation but is never the execution authority
- Shared frozen assets in the Git repository act as the single source of truth before runtime deployment
- MQTT topic contracts and payload examples/templates are shared reference assets used for implementation and validation, not policy authority

---

## Repository Scope

### Shared authority and reference assets
- `common/policies/`
- `common/schemas/`
- `common/mqtt/`
- `common/payloads/`
- `common/docs/`
- `common/terminology/`

### Authority interpretation
- `common/policies/` defines routing/action authority
- `common/schemas/` defines validation authority
- `common/mqtt/` defines MQTT topic, publisher/subscriber, and topic-payload communication contracts
- `common/payloads/` provides payload examples/templates for implementation, testing, simulation, and dashboard tooling
- `common/mqtt/` and `common/payloads/` must not override canonical policies or schemas

### Root-level dependency manifests
- `requirements-mac.txt`
- `requirements-rpi.txt`

### Mac mini operational assets
- `mac_mini/scripts/install/`
- `mac_mini/scripts/configure/`
- `mac_mini/scripts/verify/`
- `mac_mini/runtime/`
- `mac_mini/code/`

### Raspberry Pi simulation / dashboard / evaluation assets
- `rpi/scripts/install/`
- `rpi/scripts/configure/`
- `rpi/scripts/verify/`
- `rpi/code/`

### ESP32 embedded assets
- `esp32/scripts/install/`
- `esp32/scripts/configure/`
- `esp32/scripts/verify/`
- `esp32/code/`
- `esp32/firmware/`
- `esp32/docs/`

### End-to-end, experiment, and measurement assets
- `integration/tests/`
- `integration/scenarios/`
- `integration/measurement/`

### Repository interpretation principle
- `common/` contains the shared authority/reference layer
- `mac_mini/runtime/` and other deployed runtime locations contain synchronized runtime copies and host-local execution assets
- deployment-local runtime files must not be treated as canonical policy truth
- runtime apps should consume topic and payload references from `common/mqtt/` and `common/payloads/` rather than silently redefining them

---

## Core Operational Modules

### Mac mini hub-side modules
1. Policy Router
2. Deterministic Validator
3. Context-Integrity Safe Deferral Handler
4. Audit Logging Service / DB Access Layer
5. Outbound Notification Interface
6. Caregiver Confirmation Backend
7. MQTT Topic Registry Loader / Contract Checker
8. Payload Validation Helper

### Raspberry Pi experiment-side modules
9. Virtual Sensor Node Runtime
10. Virtual Emergency Sensor Runtime
11. Virtual `doorbell_detected` Visitor-Response Context Runtime
12. Fault Injection Harness
13. Scenario Orchestrator
14. Replay Runtime
15. Experiment and Monitoring Dashboard
16. MQTT / Payload Governance Inspector or Dashboard
17. Closed-loop Audit Evaluation Harness
18. Verification Utilities
19. Artifact Sync Utility
20. Time Sync Check Utility
21. Topic / Payload Contract Validation Utility
22. Progress / Result Publication Utility

### ESP32 bring-up and embedded modules when used
23. Cross-platform ESP-IDF install / configure / verify scaffolding
24. Minimal template project for sample-build validation
25. Button Node Firmware
26. Environmental / Safety Sensor Node Firmware
27. Doorbell / Visitor-Arrival Context Node Firmware
28. Actuator / Warning Interface Firmware

### Optional timing and measurement support when used
29. Out-of-band Timing Measurement Support
30. Timing Capture and Latency Evaluation Support

---

## Canonical Terminology

The canonical project term is:

**context-integrity-based safe deferral stage**

Deprecated label:
- `iCR-based safe deferral stage`

Older internal names may still appear in transitional assets or source-layer references, but new architecture-facing and implementation-facing naming should align with the current canonical term.

---

## Canonical Emergency Alignment

The implementation must remain aligned with the canonical policy-declared emergency trigger family.

At the current canonical policy level, the project recognizes:
- `E001`: high temperature threshold crossing
- `E002`: emergency triple-hit bounded input
- `E003`: smoke detected state trigger
- `E004`: gas detected state trigger
- `E005`: fall detected event trigger

Accordingly:
- physical sensing paths
- virtual emergency simulation
- fault injection logic
- verification logic
- routing outcome assertions

must remain semantically consistent with the same trigger set.

`doorbell_detected` is not part of the current emergency trigger family. It is visitor-response context and must not be interpreted as Class 0 emergency evidence or autonomous doorlock authority.

This implementation plan does not redefine emergency semantics.  
The authoritative trigger definitions remain in the shared policy table.

---

## Raspberry Pi Evaluation Boundary

Raspberry Pi 5 is **not part of the operational control plane**.

Its role is limited to experiment-side and evaluation-side support, including:
- experiment and monitoring dashboard
- normal-context simulation
- visitor-response context simulation using `environmental_context.doorbell_detected`
- emergency-triggering simulation
- fault injection
- scenario replay
- scenario orchestration
- progress/status publication
- result artifact generation/export
- MQTT/payload governance inspection when implemented
- closed-loop verification against audit outcomes
- artifact synchronization and time-sync checking as evaluation support functions

Accordingly, Raspberry Pi 5 must not host or replace the Mac mini hub-side operational runtime, including:
- Home Assistant
- Ollama
- Policy Router
- Deterministic Validator
- Context-Integrity Safe Deferral Handler
- hub-side operational audit authority
- validator approval authority
- caregiver approval authority
- direct actuator dispatch authority

All simulation and fault traffic generated by Raspberry Pi 5 should enter the system through the **same MQTT input plane** used by the bounded physical node layer, rather than bypassing the Policy Router directly.

Dashboard and governance-inspector traffic is allowed for visibility, validation, and experiment operation, but it must remain non-authoritative.

Closed-loop verification should be performed by:
1. publishing normal, emergency, visitor-response, or fault-injected test payloads,
2. observing the Mac mini audit decision stream or verification-safe audit subset,
3. comparing observed safe outcomes against expected scenario outcomes.

---

## Milestones

### M1. Frozen Specification Ready
Freeze the shared reference assets before implementation begins.

#### Required assets
- routing policy table
- low-risk action policy
- fault injection rules
- JSON schemas
- Class 2 notification payload schema
- canonical terminology
- environment variable templates
- installation/configuration/verification script set
- prompt set for implementation generation where applicable
- MQTT topic registry and publisher/subscriber matrix draft
- topic-payload contract references
- payload examples/templates for implementation, testing, simulation, and dashboard tooling

#### Representative frozen / reference files
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`
- `common/docs/architecture/12_prompts.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`

#### Optional or version-sensitive companion assets
- output profile assets
- auxiliary deployment templates
- reproducibility support assets

#### Completion criterion
The shared frozen/reference assets are committed in the repository and treated as the source of truth or source of reference according to their authority level.

---

### M2. Platform Ready
Prepare the Mac mini operational platform.

#### Tasks
- install and configure Home Assistant
- install and configure Mosquitto
- install Ollama and pull Llama 3.1
- prepare SQLite DB
- prepare notification configuration
- prepare runtime `.env` and deployment paths
- prepare runtime access to synchronized policy/schema assets
- prepare runtime access to MQTT topic registry and payload examples/templates when needed
- finalize `requirements-mac.txt` as the current baseline host-side Python dependency manifest

#### Primary repository locations
- `mac_mini/scripts/install/`
- `mac_mini/scripts/configure/`
- `mac_mini/runtime/`
- `requirements-mac.txt`

#### Completion criterion
All core services are present and configured on the Mac mini.

#### Boundary note
Host-local runtime files and deployed copies are necessary for execution, but they do not replace the canonical frozen policy/schema baseline under `common/`.

---

### M3. Core Runtime Ready
Implement the hub-side core decision pipeline.

#### Tasks
- implement Policy Router
- implement Deterministic Validator
- implement Context-Integrity Safe Deferral Handler
- implement Audit Logging Service integration
- implement MQTT topic registry loader / contract checker
- implement payload validation helper using `common/schemas/`, `common/mqtt/`, and `common/payloads/`
- prevent runtime apps from hardcoding MQTT topics or payload contracts where practical
- validate that all accepted context payloads include `environmental_context.doorbell_detected`
- validate that doorlock state is not accepted inside current `pure_context_payload.device_states`

#### Primary repository location
- `mac_mini/code/`

#### Completion criterion
The core decision pipeline can receive input, validate it, and produce auditable routing outcomes using registry-aligned topic and payload contracts.

---

### M4. External Communication Ready
Implement bounded external communication paths.

#### Tasks
- implement Telegram or mock outbound notification path
- implement caregiver confirmation path
- connect notification and confirmation logic to validator outcomes
- ensure Class 2 notification payloads remain schema-valid
- ensure caregiver confirmation payloads do not masquerade as autonomous Class 1 validator approval

#### Primary repository location
- `mac_mini/code/`

#### Completion criterion
The system can safely escalate approved external communication events without bypassing policy validation.

---

### M5. Physical Integration Ready
Prepare the ESP32 development environment and connect the operational hub to real or semi-real physical inputs and outputs.

#### Bring-up tasks before real node firmware
- finalize cross-platform ESP32 install scripts
- finalize cross-platform ESP32 configure scripts
- finalize cross-platform ESP32 verify scripts
- verify ESP-IDF CLI readiness on supported host platforms
- verify sample template build success
- prepare prompt-driven generation path for minimal template and node firmware

#### Current canonical physical-node validation targets
- connect ESP32 button node
- connect ESP32 lighting control node
- connect representative environmental sensing node used in the current canonical validation baseline
- connect ESP32 doorbell / visitor-arrival context node where visitor-response validation is included
- validate `environmental_context.doorbell_detected` generation and normalization
- validate Class 0 / Class 1 / Class 2 transitions
- validate safe deferral under incomplete or conflicting context
- validate bounded physical input/output behavior without bypassing policy control

#### Optional experimental physical-node targets
- connect ESP32 gas sensor node
- connect ESP32 fire detection sensor node
- connect ESP32 fall-detection interface node

#### Planned extension targets
- connect ESP32 doorlock or warning interface node beyond the current canonical low-risk action scope
- doorlock or warning interface logic must not be treated as autonomous Class 1 authority unless future frozen policy/schema revisions explicitly promote it

#### Canonical emergency alignment
Physical integration and validation must remain aligned with the canonical emergency family:
- `E001`
- `E002`
- `E003`
- `E004`
- `E005`

`doorbell_detected` is not an emergency trigger and must not authorize doorlock execution.

#### Primary repository locations
- `integration/tests/`
- `integration/scenarios/`
- `esp32/scripts/install/`
- `esp32/scripts/configure/`
- `esp32/scripts/verify/`
- `esp32/code/`
- `esp32/firmware/`
- `esp32/docs/`

#### Completion criterion
The ESP32 development environment is reproducibly ready, and end-to-end operational flows with bounded physical nodes are validated against the intended policy behavior within the applicable current, optional, and planned scope boundaries.

---

### M6. Evaluation Ready
Prepare the Raspberry Pi-based evaluation and experiment environment.

#### Tasks
- implement artifact synchronization from the shared frozen repository state
- verify checksum, version, or structural consistency of synchronized assets
- synchronize or reference MQTT topic registry and payload examples/templates where needed
- prepare Python venv and experiment-side runtime dependencies
- maintain `requirements-rpi.txt` as the current baseline experiment-side Python dependency manifest
- configure Raspberry Pi time synchronization against the Mac mini reference host or agreed LAN time reference
- implement experiment and monitoring dashboard
- implement dashboard-side topic/payload inspection if needed
- implement topic/payload contract validation checks
- implement multi-node virtual sensor/state runtime
- implement virtual `doorbell_detected` visitor-response context generation
- implement virtual emergency sensors
- implement deterministic and randomized fault injection
- implement scenario orchestrator and scenario replay support
- implement progress/status publication
- implement result artifact generation/export
- ensure all simulation and fault traffic enters through the same MQTT input plane used by operational inputs
- subscribe to a verification-safe audit stream or equivalent closed-loop audit channel
- compare observed routing and safe outcomes against expected scenario definitions
- run stale / missing / conflict / fail-safe experiments
- run visitor-response and doorlock-sensitive evaluation scenarios using `doorbell_detected`
- run scenario-based routing, safety, latency, and fault-handling experiments
- validate throughput, publish stability, and reproducibility of experiment-side execution
- prepare optional STM32 timing node or equivalent dedicated timing node
- run out-of-band class-wise latency measurement when measurement infrastructure is used

#### Primary repository locations
- `rpi/code/`
- `rpi/scripts/configure/`
- `rpi/scripts/verify/`
- `requirements-rpi.txt`
- `integration/scenarios/`
- `integration/measurement/`
- `integration/tests/`
- `common/mqtt/`
- `common/payloads/`

#### Raspberry Pi Verification / Acceptance Criteria
The Raspberry Pi 5 experiment environment is accepted only if the following conditions are satisfied.

##### A. Broker connectivity
- Raspberry Pi can connect to the Mac mini Mosquitto broker over the trusted LAN
- broker host, port, credentials, and topic namespace are correctly applied from `.env` or equivalent configuration
- publish tests succeed without manual reconfiguration

##### B. Throughput and publish stability
- 30-40 virtual nodes can publish concurrently without crashes
- publish loops remain within the configured interval bounds
- deterministic scenario execution does not silently skip intended message publication

##### C. Reproducibility
- deterministic fault scenarios generate the same fault metadata under the same settings
- scenario run summaries remain consistent across repeated runs of the same deterministic setup

##### D. Fault generation correctness
- all generated faults are derived from the frozen policy/schema artifacts rather than hardcoded values
- threshold-crossing emergency injections satisfy the intended minimal triggering predicates
- context-conflict injections include the expected safe-outcome labeling
- missing-state injections distinguish:
  1. policy-input omissions,
  2. validator/action-schema omissions
- emergency simulation and fault generation remain aligned with the canonical trigger family `E001`~`E005`
- missing `doorbell_detected` context may be used as a strict schema/fault case, but valid scenario payloads must include it

##### E. Artifact sync correctness
- local synchronized runtime copies match the shared frozen repository state by checksum, version, or structural verification
- experiment-side runtime modules consume the synchronized runtime copies rather than redefining local policy truth
- unattended synchronization does not block automated evaluation runs

##### F. Time sync validity
- Raspberry Pi uses the Mac mini reference host or agreed LAN time reference
- external WAN time dependency is not required for the experiment workflow
- clock offset is measured and logged before experiments
- measured offset stays within the configured target bound when the environment is considered healthy
- stale-fault margins are configured to exceed measured offset plus jitter by a sufficient margin

Note: the requirement is not an absolute fixed millisecond guarantee.  
The requirement is a measurable, recorded, and verifiable target bound.

##### G. Closed-loop automated verification
- the verification workflow publishes test or fault payloads and subscribes to a verification-safe audit stream
- observed routing or logging outcomes are automatically compared against expected safe outcomes
- Class 0, Safe Deferral, and Class 2 results can be asserted automatically
- pass/fail judgments can be produced without relying on manual screen inspection

##### H. Canonical asset consistency
- canonical policy/schema/rules consistency checks pass
- synchronized runtime copies remain version-consistent with the canonical frozen asset set
- evaluation-side validation logic does not silently drift from the shared baseline

##### I. Security and configuration hygiene
- broker credentials are not hardcoded in source files
- `.env` or equivalent external configuration is used
- topic namespace separation is preserved
- if local authentication is enabled, both successful and failed authentication behavior can be verified

##### J. MQTT / Payload contract consistency
- topic registry is readable and structurally valid
- publisher/subscriber matrix remains consistent with the topic registry
- topic-to-payload contract references resolve
- schema-governed payload examples validate against the referenced schema
- runtime or dashboard apps do not hardcode topic strings where registry lookup is practical

##### K. Dashboard non-authority boundary
- experiment dashboard displays status and result information without acting as policy authority
- MQTT/payload governance dashboard or inspector validates and visualizes contracts without overriding policy, validator, caregiver approval, or dispatch decisions
- dashboard observation payloads are not treated as policy truth

##### L. Doorbell / doorlock-sensitive scenario correctness
- valid visitor-response scenarios include `environmental_context.doorbell_detected`
- `doorbell_detected=true` affects visitor-response interpretation but does not authorize autonomous doorlock control
- doorlock state is not inserted into current `pure_context_payload.device_states`
- autonomous door unlock remains blocked under the current baseline
- doorlock-sensitive outcomes route to Class 2 escalation or governed manual confirmation with ACK and audit

#### Completion criterion
The system supports reproducible multi-node simulation, fault-injection experiments, dashboard-supported monitoring, closed-loop safe-outcome verification, topic/payload contract validation, and out-of-band latency evaluation when measurement infrastructure is used.

The Raspberry Pi evaluation path is considered accepted only when all of the following are satisfied:
1. MQTT connectivity PASS
2. artifact sync PASS
3. time sync check PASS
4. deterministic scenario reproducibility PASS
5. fault generation correctness PASS
6. publish stability PASS
7. closed-loop verification PASS
8. canonical asset consistency PASS
9. MQTT / payload contract consistency PASS
10. dashboard non-authority boundary PASS
11. doorbell / doorlock-sensitive scenario correctness PASS

---

## Implementation Principles

### A. Policy-first implementation
All runtime logic must respect frozen policy assets before any actuation-related decision path is allowed.

### B. Deterministic safety before bounded LLM assistance
The deterministic validator and safe deferral logic must remain authoritative.  
The LLM is only used for bounded interpretation, explanation support, or candidate generation under deterministic policy and validator control.

### C. Device-role separation
- Mac mini = operational hub
- Raspberry Pi 5 = experiment dashboard, multi-node simulation, fault injection, scenario replay, progress/result publication, and closed-loop evaluation node
- ESP32 = bounded physical node layer plus cross-platform bring-up workflow for node development
- STM32 timing node or equivalent = optional out-of-band latency measurement infrastructure

### D. Auditable outcomes
All meaningful routing and validation outcomes should be observable through logs, notifications, or audit channels.

### E. Repository-structured implementation
Code, scripts, frozen assets, embedded firmware, integration scenarios, MQTT contracts, payload examples/templates, and measurement assets should be placed according to the repository structure rather than mixed into a single flat project layout.

### F. Closed-loop evaluation discipline
Experiment-side execution should not bypass the operational decision path.  
Raspberry Pi-based simulation and fault injection must exercise the same input plane and must verify outcomes through observed audit behavior rather than assumed internal state.

### G. Deployment-local separation
Deployment-local configuration and runtime copies are necessary for execution, but they must not override the canonical frozen architecture baseline.

### H. Do not hardcode MQTT topics or payload contracts
Runtime apps, dashboard apps, and experiment tools should load topic names, publisher/subscriber rules, payload families, schema paths, and example references from `common/mqtt/topic_registry_v1_0_0.json` whenever practical.

### I. Keep dashboard and governance tooling non-authoritative
The experiment dashboard and MQTT/payload governance dashboard may inspect, validate, and visualize state, but must not override policy routing, validator decisions, caregiver approval, or actuation dispatch.

### J. Preserve payload boundaries
`doorbell_detected` belongs in `environmental_context`; doorlock state, manual approval state, and ACK state do not belong in current `pure_context_payload.device_states`.

---

## Final Delivery Objective

The final prototype should demonstrate that:
- the Mac mini can safely host the operational decision pipeline
- bounded LLM assistance is restricted to interpretation, explanation support, and approved low-risk candidate generation under deterministic policy and validator control
- incomplete, stale, or conflicting context leads to safe deferral rather than unsafe autonomous actuation
- ESP32-based bounded physical input/output paths can be integrated without bypassing policy control
- ESP32 bring-up and sample-build validation can be reproduced across supported host environments before real node firmware generation begins
- `environmental_context.doorbell_detected` can support visitor-response interpretation without authorizing autonomous doorlock control
- the Raspberry Pi-based evaluation environment can reproduce multi-node fault-handling behavior in a controlled and auditable way
- Raspberry Pi-based experiment traffic can be verified through closed-loop audit observation rather than bypassed control paths
- the experiment/dashboard environment can validate MQTT topic contracts and payload examples without becoming policy authority
- optional timing infrastructure can support trustworthy out-of-band class-wise latency measurement

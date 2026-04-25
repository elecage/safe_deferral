# 08_additional_required_work.md

## Additional Required Work

This document defines the additional supporting work required beyond the core frozen assets, scripts, and implementation modules.

It is intended to support:
- vibe-coding preparation
- implementation completeness
- reproducible deployment
- evaluation readiness
- operational recovery planning
- MQTT topic / payload contract governance
- dashboard-supported experiment and governance inspection

This document does not replace the canonical frozen baseline.  
Shared versioned assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

Current interface, communication, and payload references:
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`

---

## 1. Shared Frozen Asset and Reference Completeness

The following shared frozen assets and shared reference assets must exist before code generation or runtime implementation proceeds.

### Required authority assets
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

### Required communication / payload reference assets
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`
- `common/payloads/examples/`
- `common/payloads/templates/`

### Required documentation / terminology assets
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`
- `common/docs/architecture/12_prompts.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`

### Optional or version-sensitive companion assets
- output profile assets
- auxiliary deployment templates
- reproducibility support assets

### Requirement
These assets must be available before implementation-side code generation begins.

### Authority note
- `common/policies/` and `common/schemas/` remain policy and validation authority.
- `common/mqtt/` defines communication-contract references.
- `common/payloads/` provides payload examples/templates.
- `common/docs/architecture/15_interface_matrix.md` defines the MQTT-aware interface contract reference.
- MQTT contracts and payload examples must not override canonical policies or schemas.

---

## 2. Root-Level Dependency Manifest Readiness

The repository now includes host-side Python dependency manifests that should be maintained as additional required support assets.

### Required manifests
- `requirements-mac.txt`
- `requirements-rpi.txt`

### Requirement
- The manifests should remain aligned with the currently maintained install/runtime assumptions.
- They support host-side environment reproducibility.
- They do not redefine canonical shared policy or schema truth.
- They should include dependencies needed for topic registry loading, JSON schema validation, payload validation, MQTT testing, dashboard runtime, governance backend service, governance dashboard UI, result export, and validation report generation when those components are implemented.

---

## 3. Port Allocation Sheet

A dedicated port allocation reference should be created and maintained.

### Required items
- Home Assistant port
- Mosquitto port
- Ollama port
- hub-side FastAPI service ports
- notification or confirmation endpoint ports
- optional development-only local service ports
- optional ESP32 OTA or device-maintenance ports when used
- Raspberry Pi experiment dashboard port when implemented
- MQTT/payload governance backend service port when implemented
- governance dashboard UI port when implemented
- registry validation service port when implemented
- result export or artifact service port when implemented
- optional timing or measurement support interfaces when out-of-band latency evaluation is used

### Recommended location
- `common/docs/architecture/`
- or `common/docs/runtime/`

### Requirement note
Port allocation references support deployment consistency, but they do not define canonical policy truth.

Dashboard, governance backend, and governance UI ports must not imply policy, validator, caregiver approval, or actuator authority.

---

## 4. Environment Variable Sheet

A centralized environment-variable reference is required for both documentation and deployment consistency.

### Required items
- Telegram bot token
- Telegram chat ID
- SQLite DB path
- MQTT broker host and port
- MQTT credentials
- MQTT topic registry path
- payload examples/templates path
- topic namespace prefix
- dashboard observation topic
- experiment progress/result topics
- simulation mode flag
- governance dashboard enable flag
- governance backend API endpoint
- governance backend port
- governance dashboard UI port
- registry validation mode
- topic drift check mode
- payload validation mode
- Ollama endpoint
- timeout and grace-period settings
- deployment mode
- simulation-related variables
- audit topic variables
- time synchronization host and bounds
- ESP32-related topic namespace and device-ID conventions when embedded nodes are used
- ESP32-side broker connection assumptions when embedded nodes are used
- ESP32 workspace, `IDF_PATH`, `IDF_TOOLS_PATH`, target, sample-project, and build-log variables for cross-platform bring-up
- optional measurement profile or timing-capture settings when out-of-band latency evaluation is used

### Recommended location
- `common/docs/runtime/`
- linked to:
  - `mac_mini/scripts/configure/70_write_env_files.sh`
  - `rpi/scripts/configure/10_write_env_files_rpi.sh`
  - `esp32/scripts/configure/10_write_env_files_esp32.sh`
  - `esp32/scripts/configure/10_write_env_files_esp32_windows.ps1`
  - `integration/measurement/` when applicable

### Deployment-local separation principle
Environment-variable sheets document deployment consistency, but `.env`, credentials, tokens, host paths, and machine-specific configuration remain deployment-local assets.  
They must not be treated as canonical frozen policy truth.

Runtime apps, dashboard apps, and experiment tools should load topic strings and payload contract references from the configured registry path whenever practical, instead of hardcoding MQTT topics and payload assumptions.

Governance dashboard UI configuration must point to the governance backend service API and must not grant direct registry-file write access or operational control-topic publish authority.

---

## 5. Acceptance Criteria per Module

Each major module should have explicit acceptance criteria before it is considered complete.

### Mac mini operational modules

#### Policy Router
- deterministic class output for all representative scenario cases
- no invalid routing for incomplete input
- valid context payload requires `environmental_context.doorbell_detected`
- `routing_metadata` is not passed into bounded LLM context
- topic/payload contract assumptions are loaded from registry where practical
- routing reasons are observable

#### Deterministic Validator
- no high-risk action passes validation
- bounded parameter checks are enforced
- safe deferral is emitted when validation conditions are not satisfied
- `door_unlock` / `front_door_lock` is rejected as current Class 1 executable payload
- doorlock state is not accepted as current `device_states` authority

#### Context-Integrity Safe Deferral Handler
- bounded clarification flow operates correctly
- timeout handling is deterministic
- timeout or unresolved ambiguity escalates safely rather than enabling unsafe actuation
- safe deferral payloads preserve the boundaries defined in `common/docs/architecture/17_payload_contract_and_registry.md`

#### Outbound Notification Interface
- outbound escalation payload is emitted successfully
- payload structure is aligned with `class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- mock fallback works when external notification is not available

#### Caregiver Confirmation Backend
- confirmation remains restricted to governed, explicitly scoped actions
- caregiver confirmation is not treated as autonomous Class 1 validator approval
- doorlock-sensitive confirmation requires approval, ACK verification, and audit visibility when implemented
- no unrestricted actuation path is introduced

#### MQTT Topic Registry Loader / Contract Checker
- topic registry is readable
- required topic IDs or topic patterns resolve
- publisher/subscriber matrix remains consistent with the registry
- topic-to-payload contract references resolve
- MQTT-facing behavior remains aligned with `common/docs/architecture/15_interface_matrix.md`
- topic/payload hardcoding drift checks pass where implemented
- runtime apps do not hardcode topic strings where registry lookup is practical

#### Payload Validation Helper
- schema-governed payload examples validate against referenced schemas
- valid context examples include `environmental_context.doorbell_detected`
- invalid missing-`doorbell_detected` examples fail as expected
- doorlock state is rejected or flagged when placed inside current `pure_context_payload.device_states`

#### Audit Logging Service
- acts as the only DB writer
- no direct multi-writer SQLite access is allowed
- routing, validation, timeout, escalation, caregiver confirmation, and ACK events are captured
- doorbell / visitor-response outcomes are traceable when relevant
- doorlock-sensitive escalation/manual confirmation/ACK outcomes are traceable when relevant
- dashboard observation is not treated as audit authority

#### Dispatcher / ACK path
- execution success is confirmed only after state ACK
- no success is assumed from command transmission alone
- ACK payloads remain closed-loop evidence, not pure context input

### Raspberry Pi experiment modules

#### Virtual Sensor, Simulation, Dashboard, Governance, and Fault Injection Layer
- deterministic scenarios can be reproduced
- randomized stress injection can run independently
- experiment dashboard is available when implemented
- MQTT/payload governance backend service is available when implemented
- governance dashboard UI is available as a presentation and interaction layer when implemented
- topic/payload contract validation utility is available when implemented
- payload example manager / validator is available when implemented
- publisher/subscriber role manager is available when implemented
- governance dashboard UI cannot directly edit registry files
- governance dashboard UI cannot directly publish operational control topics
- governance backend cannot directly modify canonical policies/schemas
- governance tooling cannot publish actuator or doorlock commands
- governance backend/UI separation is verified
- topic/payload contract validation passes
- topic/payload hardcoding drift checks pass where implemented
- virtual `doorbell_detected` visitor-response context generation works when visitor-response scenarios are included
- visitor-response and doorlock-sensitive scenarios are evaluated
- `doorbell_detected=true` does not authorize autonomous doorlock control
- closed-loop audit verification can be triggered from injected faults
- repeatable large-scale multi-node simulation can be executed
- canonical policy/schema/rules consistency checks pass
- emergency simulation and fault generation remain aligned with canonical trigger family `E001`~`E005`

### ESP32 bring-up layer

#### Cross-platform ESP-IDF readiness
- install/configure/verify flow works on supported host environments
- `idf.py` is available after environment activation
- target selection works for the intended board family
- sample project can be prepared, reconfigured, and built successfully
- the bring-up workflow remains distinct from later real node-firmware implementation

### ESP32 embedded modules when used

#### Minimal Template Project
- minimal project builds successfully through the maintained ESP32 verify flow
- startup behavior is safe and non-autonomous
- template is suitable as a base for later node-specific firmware generation

#### Button Node Firmware
- bounded button inputs are transmitted with stable device identity and expected topic structure
- emergency-like and non-emergency button patterns are distinguishable as designed
- device behavior does not bypass policy control on the hub side

#### Doorbell / Visitor-Arrival Context Node Firmware
- doorbell / visitor-arrival node emits `environmental_context.doorbell_detected`
- emitted payload or normalized payload aligns with the current MQTT topic/payload contract assumptions
- doorbell context is not emitted as emergency evidence or doorlock authorization

#### Sensor / Actuator / Warning Interface Firmware
- device-side publish or subscribe behavior matches bounded topic and payload assumptions
- warning or actuator interface behavior remains bounded and policy-dependent
- doorlock/warning interface firmware does not locally reinterpret doorlock as autonomous Class 1 authority
- reconnect behavior is predictable after broker or power interruption

### Timing / Measurement Support when used

#### Out-of-band Latency Measurement Support
- timing capture points for Class 0 / Class 1 / Class 2 paths are documented
- measurement path remains separate from the operational decision path
- timing capture is reproducible across repeated runs
- class-wise latency output can be exported into paper-ready result formats when needed

### Recommended location
- `common/docs/architecture/`
- optionally mirrored into:
  - `integration/tests/`
  - `integration/scenarios/`
  - `integration/measurement/`
  - `esp32/docs/`

---

## 6. Test Data Package

A reusable test-data package should be created for implementation and verification.

### Required contents
- sample events
- sample contexts
- expected routing results
- expected validator outcomes
- representative fault-injection cases
- expected safe-deferral cases
- expected escalation cases
- representative Class 2 notification payload examples
- representative ESP32-linked bounded input/output cases when embedded nodes are used
- ESP32 sample-build or template-validation references where bring-up verification is part of the development package
- canonical policy/fault/schema consistency fixtures
- representative emergency trigger-aligned cases for `E001`~`E005`
- policy-router input non-visitor payload example
- policy-router input visitor/doorbell payload example
- dashboard observation payload example for doorlock-sensitive evaluation
- scenario fixture template
- missing `doorbell_detected` invalid/fault case
- `doorbell_detected=true` but autonomous unlock blocked case
- doorlock state not allowed in `device_states` case
- governance UI/backend separation test fixture
- unauthorized governance registry edit attempt
- governance actuator/doorlock publish-blocked case
- topic-drift check fixture
- interface-matrix alignment fixture
- class-wise latency experiment profiles when out-of-band measurement is used
- measurement result templates or capture reference formats when needed

### Recommended locations
- shared reusable examples/templates:
  - `common/payloads/examples/`
  - `common/payloads/templates/`
- executable/evaluation scenarios:
  - `integration/scenarios/`
- optionally:
  - `integration/tests/data/`
  - `integration/measurement/`

### Boundary note
`common/payloads/` provides reusable reference examples and templates.  
`integration/scenarios/` stores executable or evaluation-oriented scenario definitions.

---

## 7. Recovery and Reset Procedure

A reset and recovery procedure is required so the system can be returned to a clean state between experiments or after runtime faults.

### Required procedures
- how to restart services
- how to reset DB and log files
- how to rerun verification scripts cleanly
- how to resync frozen assets onto the Raspberry Pi
- how to reset simulation state before rerunning scenarios
- how to reset dashboard retained observation state when used
- how to reset governance draft changes
- how to clear governance validation reports
- how to rerun MQTT/payload registry validation after recovery
- how to rerun governance backend/UI separation checks
- how to rerun topic drift checks
- how to rebuild, reflash, or reset ESP32 firmware when embedded nodes are used
- how to rerun ESP32 install/configure/verify bring-up steps when the host-side SDK environment becomes inconsistent
- how to reset or restart timing/measurement sessions when out-of-band latency evaluation is used

### Recommended location
- `common/docs/runtime/`
- with references to:
  - `mac_mini/scripts/verify/`
  - `rpi/scripts/verify/`
  - `esp32/scripts/verify/`
  - `esp32/docs/`
  - `integration/measurement/`

---

## 8. Fault Injection Design Requirements

Fault injection behavior must remain dynamically grounded in shared frozen assets rather than hardcoded thresholds.

### Required rules
- thresholds and freshness limits must be parsed dynamically from policy and schema assets
- emergency injection and context conflict must be treated as separate test classes
- missing-state faults must distinguish:
  - policy-layer missing inputs
  - validator or action-schema missing fields
- stale, missing, conflict, and timeout conditions must be distinguishable in evaluation
- fault injection must remain aligned with canonical trigger family `E001`~`E005`
- missing `doorbell_detected` must be treated as a strict schema/context fault case
- `doorbell_detected=true` must not be treated as emergency evidence or unlock authorization

### Repository alignment
- frozen source of truth:
  - `common/policies/`
  - `common/schemas/`
- communication and payload references:
  - `common/mqtt/`
  - `common/payloads/`
- implementation and execution:
  - `rpi/code/`
  - `integration/scenarios/`
  - `integration/tests/`

---

## 9. MQTT Connectivity, Contract, and Isolation Requirements

MQTT connectivity must support local distributed evaluation while maintaining security and contract boundaries.

### Required rules
- the broker must be reachable from Raspberry Pi 5 over the same LAN
- the broker must be reachable from ESP32 embedded clients over the intended trusted local network when those nodes are used
- internet-originated inbound access must remain blocked
- optional local authentication and topic ACL should be supported
- verification should include both connectivity and isolation assumptions
- topic registry must be readable
- publisher/subscriber matrix must be consistent with the registry
- topic-to-payload references must resolve
- MQTT-facing behavior must remain aligned with `common/docs/architecture/15_interface_matrix.md`
- schema-governed payload examples must validate against referenced schemas
- topic/payload hardcoding drift checks must pass where implemented
- runtime apps, dashboard apps, and experiment tools should not hardcode topic strings where registry lookup is practical
- governance dashboard UI and governance backend service separation must be verified
- governance dashboard UI must not directly write registry files
- governance backend must not publish actuator or doorlock commands
- dashboard/governance topics must remain non-authoritative

### Repository alignment
- communication contracts:
  - `common/mqtt/`
- payload references:
  - `common/payloads/`
- implementation/configuration:
  - `mac_mini/scripts/configure/`
  - `rpi/scripts/configure/`
  - `esp32/scripts/configure/` when bring-up variables or connection assumptions are involved
  - `esp32/` implementation assets when applicable
- verification:
  - `mac_mini/scripts/verify/`
  - `rpi/scripts/verify/`
  - `esp32/scripts/verify/`
  - integration checks involving `esp32/` when applicable

---

## 10. Audit Logging Architecture Requirements

Audit logging must remain structurally safe and auditable.

### Required rules
- SQLite must run in WAL mode
- a dedicated Audit Logging Service must consume audit events asynchronously
- only the Audit Logging Service writes to SQLite
- log writers must not bypass the audit path
- routing, validation, safe deferral, timeout, escalation, caregiver confirmation, and ACK events should be traceable
- doorbell / visitor-response outcomes should be traceable when relevant
- doorlock-sensitive escalation, manual confirmation, dispatch, ACK, and final outcome should be traceable when implemented
- dashboard observation is not audit authority
- audit payloads remain evidence and traceability records, not policy truth
- ESP32-linked bounded input/output events should be traceable through the same audit path when embedded nodes are used
- a verification-safe audit subset or equivalent verification-safe audit stream should be available for closed-loop experiment-side evaluation
- measurement-support events may be logged for experiment traceability, but timing infrastructure must not become part of the operational control path

### Repository alignment
- configuration:
  - `mac_mini/scripts/configure/40_configure_sqlite.sh`
- verification:
  - `mac_mini/scripts/verify/40_verify_sqlite.sh`
- implementation:
  - `mac_mini/code/`
  - integration traces involving `esp32/` when applicable
  - `integration/measurement/` when applicable

---

## 11. Timing and Measurement Support Requirements

When class-wise latency evaluation is part of the experiment package, the timing and measurement layer should be explicitly documented.

### Required rules
- out-of-band latency capture should remain separate from the operational service plane
- timing capture points for Class 0 / Class 1 / Class 2 should be documented
- wiring assumptions or capture references should be recorded when hardware timing support is used
- result formats should be reusable for reproducible paper evaluation
- optional STM32 timing node or dedicated measurement node support notes should be maintained when used
- timing and measurement support must remain evaluation-only and must not become part of the operational control path

### Repository alignment
- measurement assets:
  - `integration/measurement/`
- supporting experiment assets:
  - `integration/scenarios/`

---

## 12. MQTT / Payload Governance Requirements

Future MQTT/payload governance tooling may be useful for implementation, experiment monitoring, regression prevention, and communication-contract review.

### Governance Backend Service Requirements
- provide controlled draft topic/payload create, update, delete, validation, and export operations
- expose an API consumed by the governance dashboard UI
- validate topic registry structure
- validate publisher/subscriber matrix consistency
- validate topic-to-payload contract references
- validate payload examples against schemas
- detect unauthorized or unexpected topic usage
- detect schema drift
- detect missing required fields such as `environmental_context.doorbell_detected`
- detect disallowed fields such as doorlock state inside current `pure_context_payload.device_states`
- export topic/payload coverage reports
- export proposed change reports
- preserve draft/proposed/committed distinction

### Governance Dashboard UI Requirements
- remain a presentation and interaction layer
- call the governance backend service for create/update/delete/validation/export operations
- browse topic registry entries
- view publisher/subscriber matrix
- inspect topic-to-payload contract references
- show payload validation results
- visualize live or replayed experiment topic traffic when available
- show unauthorized or unexpected topic usage warnings
- show dashboard observation state for experiments
- show doorbell/doorlock boundary warnings
- show validation and proposed change reports
- avoid direct registry-file editing
- avoid direct operational MQTT control-topic publishing

### Required validation checks
- governance backend/UI separation check
- direct registry edit prevention check
- direct operational control-topic publish prevention check
- canonical policy/schema direct-modification prevention check
- actuator/doorlock command publish-blocked check
- caregiver approval spoofing prevention check
- topic drift check
- interface matrix alignment check
- payload example validation check
- doorbell/doorlock boundary check

### Forbidden capabilities
- modifying canonical policies or schemas directly
- overriding Policy Router decisions
- overriding Deterministic Validator decisions
- spoofing caregiver approval outside controlled test mode
- directly publishing unrestricted actuation commands
- dispatching doorlock commands
- treating dashboard observation as policy truth
- treating audit records as policy authority
- converting draft/proposed registry changes into live operational authority without review

### Repository alignment
- governance contracts:
  - `common/mqtt/`
  - `common/payloads/`
  - `common/docs/architecture/15_interface_matrix.md`
  - `common/docs/architecture/17_payload_contract_and_registry.md`
  - `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- likely implementation targets:
  - `rpi/code/`
  - `rpi/scripts/verify/`
  - `integration/tests/`

---

## 13. Final Readiness Principle

The system should not be considered implementation-ready unless:
- shared frozen assets are complete
- shared communication and payload references are complete enough for the current implementation stage
- installation/configuration/verification assets are aligned
- root-level dependency manifests are aligned with maintained runtime assumptions
- module-level acceptance criteria are explicit
- reusable test data exists
- recovery procedures are documented
- fault injection rules are dynamically grounded in frozen assets
- canonical policy/schema/rules consistency checks pass
- MQTT topic registry and payload example consistency checks pass where implemented
- `common/docs/architecture/15_interface_matrix.md` alignment passes
- topic/payload hardcoding drift checks pass where implemented
- governance backend/UI separation is verified
- governance tooling cannot create operational authority
- audit logging remains single-writer and traceable
- dashboard/governance inspection tools remain non-authoritative
- `doorbell_detected` is handled as required visitor-response context, not emergency evidence or doorlock authorization
- doorlock state is not inserted into current `pure_context_payload.device_states`
- ESP32 bring-up requirements are documented before real firmware generation proceeds
- ESP32-related bounded physical node requirements are documented wherever embedded nodes are part of the target prototype
- timing and measurement infrastructure requirements are documented wherever out-of-band class-wise latency evaluation is part of the target experiment package

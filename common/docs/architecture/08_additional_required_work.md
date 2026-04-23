# 08_additional_required_work.md

## Additional Required Work

This document defines the additional supporting work required beyond the core frozen assets, scripts, and implementation modules.

It is intended to support:
- vibe-coding preparation
- implementation completeness
- reproducible deployment
- evaluation readiness
- operational recovery planning

This document does not replace the canonical frozen baseline.  
Shared versioned assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

---

## 1. Shared Frozen Asset Completeness

The following shared frozen assets must exist and be treated as the single source of truth before code generation or runtime implementation proceeds.

### Required shared assets
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`
- `common/docs/architecture/12_prompts.md`

### Optional or version-sensitive companion assets
- output profile assets
- auxiliary deployment templates
- reproducibility support assets

### Requirement
These assets must be frozen before implementation-side code generation begins.

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
- optional timing or measurement support interfaces when out-of-band latency evaluation is used

### Recommended location
- `common/docs/architecture/`
- or `common/docs/runtime/`

### Requirement note
Port allocation references support deployment consistency, but they do not define canonical policy truth.

---

## 4. Environment Variable Sheet

A centralized environment-variable reference is required for both documentation and deployment consistency.

### Required items
- Telegram bot token
- Telegram chat ID
- SQLite DB path
- MQTT broker host and port
- MQTT credentials
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

---

## 5. Acceptance Criteria per Module

Each major module should have explicit acceptance criteria before it is considered complete.

### Mac mini operational modules

#### Policy Router
- deterministic class output for all representative scenario cases
- no invalid routing for incomplete input
- routing reasons are observable

#### Deterministic Validator
- no high-risk action passes validation
- bounded parameter checks are enforced
- safe deferral is emitted when validation conditions are not satisfied

#### Context-Integrity Safe Deferral Handler
- bounded clarification flow operates correctly
- timeout handling is deterministic
- timeout or unresolved ambiguity escalates safely rather than enabling unsafe actuation

#### Outbound Notification Interface
- outbound escalation payload is emitted successfully
- payload structure is aligned with `class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- mock fallback works when external notification is not available

#### Caregiver Confirmation Backend
- confirmation remains restricted to bounded low-risk actions
- no unrestricted actuation path is introduced

#### Audit Logging Service
- acts as the only DB writer
- no direct multi-writer SQLite access is allowed
- routing, validation, timeout, escalation, and ACK events are captured

#### Dispatcher / ACK path
- execution success is confirmed only after state ACK
- no success is assumed from command transmission alone

### Raspberry Pi experiment modules

#### Virtual Sensor and Fault Injection Layer
- deterministic scenarios can be reproduced
- randomized stress injection can run independently
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

#### Sensor / Actuator / Warning Interface Firmware
- device-side publish or subscribe behavior matches bounded topic and payload assumptions
- warning or actuator interface behavior remains bounded and policy-dependent
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
- class-wise latency experiment profiles when out-of-band measurement is used
- measurement result templates or capture reference formats when needed

### Recommended location
- `integration/scenarios/`
- optionally:
  - `integration/tests/data/`
  - `integration/measurement/`

---

## 7. Recovery and Reset Procedure

A reset and recovery procedure is required so the system can be returned to a clean state between experiments or after runtime faults.

### Required procedures
- how to restart services
- how to reset DB and log files
- how to rerun verification scripts cleanly
- how to resync frozen assets onto the Raspberry Pi
- how to reset simulation state before rerunning scenarios
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

### Repository alignment
- frozen source of truth:
  - `common/policies/`
  - `common/schemas/`
- implementation and execution:
  - `rpi/code/`
  - `integration/scenarios/`
  - `integration/tests/`

---

## 9. MQTT Connectivity and Isolation Requirements

MQTT connectivity must support local distributed evaluation while maintaining security boundaries.

### Required rules
- the broker must be reachable from Raspberry Pi 5 over the same LAN
- the broker must be reachable from ESP32 embedded clients over the intended trusted local network when those nodes are used
- internet-originated inbound access must remain blocked
- optional local authentication and topic ACL should be supported
- verification should include both connectivity and isolation assumptions

### Repository alignment
- implementation/configuration:
  - `mac_mini/scripts/configure/`
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

## 12. Final Readiness Principle

The system should not be considered implementation-ready unless:
- shared frozen assets are complete
- installation/configuration/verification assets are aligned
- root-level dependency manifests are aligned with maintained runtime assumptions
- module-level acceptance criteria are explicit
- reusable test data exists
- recovery procedures are documented
- fault injection rules are dynamically grounded in frozen assets
- canonical policy/schema/rules consistency checks pass
- audit logging remains single-writer and traceable
- ESP32 bring-up requirements are documented before real firmware generation proceeds
- ESP32-related bounded physical node requirements are documented wherever embedded nodes are part of the target prototype
- timing and measurement infrastructure requirements are documented wherever out-of-band class-wise latency evaluation is part of the target experiment package

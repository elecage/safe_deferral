# 08_additional_required_work.md

## Additional Required Work

This document defines the additional supporting work required beyond the core frozen assets, scripts, and implementation modules.

It is intended to support:
- vibe-coding preparation
- implementation completeness
- reproducible deployment
- evaluation readiness
- operational recovery planning

---

## 1. Shared Frozen Asset Completeness

The following shared frozen assets must exist and be treated as the single source of truth before code generation or runtime implementation proceeds.

### Required shared assets
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_0_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/policies/output_profile_v1_0_0.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_0_0_FROZEN.json`
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

### Requirement
These assets must be frozen before implementation-side code generation begins.

---

## 2. Port Allocation Sheet

A dedicated port allocation reference should be created and maintained.

### Required items
- Home Assistant port
- Mosquitto port
- Ollama port
- hub-side FastAPI service ports
- notification or confirmation endpoint ports
- optional development-only local service ports

### Recommended location
- `common/docs/architecture/`
- or `common/docs/runtime/`

---

## 3. Environment Variable Sheet

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

### Recommended location
- `common/docs/runtime/`
- linked to:
  - `mac_mini/scripts/configure/70_write_env_files.sh`
  - `rpi/scripts/configure/10_write_env_files_rpi.sh`

---

## 4. Acceptance Criteria per Module

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
- expected payload is emitted successfully
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

### Recommended location
- `common/docs/architecture/`
- optionally mirrored into:
  - `integration/tests/`
  - `integration/scenarios/`

---

## 5. Test Data Package

A reusable test-data package should be created for implementation and verification.

### Required contents
- sample events
- sample contexts
- expected routing results
- expected validator outcomes
- representative fault-injection cases
- expected safe-deferral cases
- expected escalation cases

### Recommended location
- `integration/scenarios/`
- optionally:
  - `integration/tests/data/`

---

## 6. Recovery and Reset Procedure

A reset and recovery procedure is required so the system can be returned to a clean state between experiments or after runtime faults.

### Required procedures
- how to restart services
- how to reset DB and log files
- how to rerun verification scripts cleanly
- how to resync frozen assets onto the Raspberry Pi
- how to reset simulation state before rerunning scenarios

### Recommended location
- `common/docs/runtime/`
- with references to:
  - `mac_mini/scripts/verify/`
  - `rpi/scripts/verify/`

---

## 7. Fault Injection Design Requirements

Fault injection behavior must remain dynamically grounded in shared frozen assets rather than hardcoded thresholds.

### Required rules
- thresholds and freshness limits must be parsed dynamically from policy and schema assets
- emergency threshold crossing and context conflict must be treated as separate test classes
- missing-state faults must distinguish:
  - policy-layer missing inputs
  - validator or action-schema missing fields
- stale, missing, conflict, and timeout conditions must be distinguishable in evaluation

### Repository alignment
- frozen source of truth:
  - `common/policies/`
  - `common/schemas/`
- implementation and execution:
  - `rpi/code/`
  - `integration/scenarios/`

---

## 8. MQTT Connectivity and Isolation Requirements

MQTT connectivity must support local distributed evaluation while maintaining security boundaries.

### Required rules
- the broker must be reachable from Raspberry Pi 5 over the same LAN
- internet-originated inbound access must remain blocked
- optional local authentication and topic ACL should be supported
- verification should include both connectivity and isolation assumptions

### Repository alignment
- implementation/configuration:
  - `mac_mini/scripts/configure/`
- verification:
  - `mac_mini/scripts/verify/`
  - `rpi/scripts/verify/`

---

## 9. Audit Logging Architecture Requirements

Audit logging must remain structurally safe and auditable.

### Required rules
- SQLite must run in WAL mode
- a dedicated Audit Logging Service must consume audit events asynchronously
- only the Audit Logging Service writes to SQLite
- log writers must not bypass the audit path
- routing, validation, safe deferral, timeout, escalation, caregiver confirmation, and ACK events should be traceable

### Repository alignment
- configuration:
  - `mac_mini/scripts/configure/40_configure_sqlite.sh`
- verification:
  - `mac_mini/scripts/verify/40_verify_sqlite.sh`
- implementation:
  - `mac_mini/code/`

---

## 10. Final Readiness Principle

The system should not be considered implementation-ready unless:
- shared frozen assets are complete
- installation/configuration/verification assets are aligned
- module-level acceptance criteria are explicit
- reusable test data exists
- recovery procedures are documented
- fault injection rules are dynamically grounded in frozen assets
- audit logging remains single-writer and traceable
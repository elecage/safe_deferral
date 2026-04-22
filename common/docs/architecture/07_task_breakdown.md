# 07_task_breakdown.md

## Task Breakdown

This document defines the implementation-oriented task breakdown for the safe deferral system.

It is intended to support:
- vibe-coding workflows
- staged implementation
- repository-aligned development
- traceable progress from frozen assets to integration testing and evaluation

This document does not replace the canonical frozen baseline.  
Shared versioned assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

---

## T0. Freeze Shared Reference Assets

- [ ] Finalize routing policy assets under `common/policies/`
- [ ] Finalize schema assets under `common/schemas/`
- [ ] Finalize canonical terminology under `common/terminology/`
- [ ] Finalize supporting reference docs under `common/docs/`
- [ ] Ensure frozen shared artifacts are available as implementation reference inputs before code generation

### Representative canonical frozen assets
- [ ] `common/policies/policy_table_v1_1_2_FROZEN.json`
- [ ] `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- [ ] `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- [ ] `common/schemas/context_schema_v1_0_0_FROZEN.json`
- [ ] `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- [ ] `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- [ ] `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- [ ] `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- [ ] `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

### Optional or version-sensitive companion assets
- [ ] output profile assets
- [ ] auxiliary deployment templates
- [ ] reproducibility support assets

---

## T1. Finalize Shared Policy and Schema Specifications

- [ ] Finalize Class 0 / 1 / 2 routing policy logic
- [ ] Finalize allowed low-risk action definitions
- [ ] Finalize context-integrity safe deferral rules
- [ ] Finalize timeout and bounded confirmation rules
- [ ] Finalize JSON schemas for:
  - [ ] context input
  - [ ] policy router input
  - [ ] candidate action
  - [ ] validator output
  - [ ] Class 2 notification payload
- [ ] Finalize `fault_injection_rules`
- [ ] Finalize optional or version-sensitive companion asset constraints where used

---

## T2. Prepare Mac mini Core Platform

- [ ] Install Home Assistant
- [ ] Install Mosquitto
- [ ] Install Ollama
- [ ] Pull Llama 3.1
- [ ] Initialize SQLite
- [ ] Enable SQLite WAL mode
- [ ] Prepare runtime directories and environment scaffolding

### Repository focus
- `mac_mini/scripts/install/`
- `mac_mini/scripts/configure/`
- `mac_mini/runtime/`

---

## T3. Prepare Mac mini Python Runtime

- [ ] Create Python virtual environment
- [ ] Install FastAPI
- [ ] Install Pydantic
- [ ] Install paho-mqtt
- [ ] Install python-telegram-bot
- [ ] Install pytest
- [ ] Install uvicorn
- [ ] Verify package availability

### Repository focus
- `mac_mini/scripts/install/`
- `mac_mini/code/`

---

## T4. Implement Policy Router

- [ ] Define router input strictly from frozen assets
- [ ] Implement Class 0 routing rules
- [ ] Implement conservative handling for malformed or non-matching emergency-like inputs
- [ ] Implement context sufficiency checks
- [ ] Implement Class 2 escalation rules
- [ ] Ensure freshness/fault metadata is not passed into the bounded LLM execution context
- [ ] Add routing reason logging

### Repository focus
- `mac_mini/code/`

---

## T5. Implement Deterministic Validator

- [ ] Define candidate validation from frozen schema assets
- [ ] Implement schema validation
- [ ] Implement action-domain validation
- [ ] Implement bounded parameter checks
- [ ] Implement single-admissible-action resolution
- [ ] Implement safe deferral output
- [ ] Require state ACK feedback before confirming successful actuation
- [ ] Keep actuation execution delegated to dispatcher / actuator interface

### Repository focus
- `mac_mini/code/`

---

## T6. Implement Context-Integrity Safe Deferral Handler

- [ ] Define candidate-to-button or bounded clarification mapping
- [ ] Implement clarification prompt generation using bounded clarification only
- [ ] Implement timeout handling
- [ ] Emit timeout events back to the policy layer
- [ ] Ensure safe deferral remains the default fallback when context integrity cannot be recovered

### Repository focus
- `mac_mini/code/`

---

## T7. Implement Audit Logging

- [ ] Define SQLite schema
- [ ] Implement `Audit Logging Service` as the only DB writer
- [ ] Subscribe to `audit/log/#` or equivalent async audit channel
- [ ] Log routing events
- [ ] Log validator outcomes
- [ ] Log deferrals, timeouts, and escalations
- [ ] Log caregiver confirmation events
- [ ] Log actuation ACK events
- [ ] Prevent other services from writing directly to the SQLite file

### Repository focus
- `mac_mini/code/`

---

## T8. Implement External Notification and Confirmation

- [ ] Implement Class 2 notification payload generation aligned with `class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- [ ] Validate outbound escalation payload completeness against the canonical schema
- [ ] Implement Telegram / mock outbound alert sender
- [ ] Implement caregiver confirmation endpoint
- [ ] Restrict confirmation to bounded low-risk actions

### Repository focus
- `mac_mini/code/`

---

## T9. Implement Raspberry Pi Simulation and Evaluation Layer

- [ ] Create virtual context nodes
- [ ] Create virtual emergency nodes
- [ ] Create multi-node simulation runtime
- [ ] Create policy-driven deterministic fault cases
- [ ] Create randomized stress injection
- [ ] Prepare repeatable large-scale evaluation scenarios
- [ ] Parse shared frozen assets dynamically to derive:
  - [ ] thresholds
  - [ ] freshness bounds
  - [ ] minimal triggering predicates
  - [ ] required keys
- [ ] Implement the following fault categories separately:
  - [ ] policy-declared emergency injection
  - [ ] context conflict injection
  - [ ] sensor/state staleness injection
  - [ ] missing state injection
- [ ] Distinguish policy-input omissions from validator/action-schema omissions
- [ ] Distinguish policy-declared emergency cases from context-conflict cases
- [ ] Align emergency simulation and fault generation with canonical trigger family `E001`~`E005`
- [ ] Support closed-loop automated verification against expected safe outcomes

### Repository focus
- `rpi/code/`
- `integration/scenarios/`
- `integration/tests/`

---

## T10. Implement ESP32 Embedded Physical Node Layer

### Current canonical targets
- [ ] Implement bounded button input node firmware
- [ ] Implement lighting control node firmware when physical output is used
- [ ] Implement representative environmental sensing node firmware used in the current validation baseline
- [ ] Implement MQTT publish/subscription behavior required for bounded physical nodes
- [ ] Align broker connection parameters, topic namespaces, and device identifiers with the operational hub assumptions
- [ ] Keep embedded behavior bounded and policy-aligned rather than autonomous

### Optional experimental targets
- [ ] Implement gas sensor node firmware when physical sensing is used
- [ ] Implement fire detection sensor node firmware when physical sensing is used
- [ ] Implement fall-detection interface firmware when physical sensing is used

### Planned extension targets
- [ ] Implement doorlock or warning interface firmware when physical output is used beyond the current canonical low-risk scope

### Repository focus
- `esp32/code/`
- `esp32/firmware/`
- `esp32/docs/`

---

## T11. Implement Timing and Measurement Support

- [ ] Define out-of-band class-wise latency measurement plan
- [ ] Prepare optional STM32 timing node or equivalent dedicated measurement node when used
- [ ] Define timing capture points for Class 0 / Class 1 / Class 2 paths
- [ ] Define measurement wiring and trigger/capture assumptions
- [ ] Prepare timing capture scripts, notes, or result templates
- [ ] Ensure measurement infrastructure remains separate from the operational decision path

### Repository focus
- `integration/measurement/`

---

## T12. Verify MQTT Connectivity and Isolation

- [ ] Ensure Mosquitto is LAN-reachable for Raspberry Pi 5
- [ ] Ensure Mosquitto is LAN-reachable for ESP32 embedded clients when used
- [ ] Ensure internet-originated inbound access is blocked by firewall
- [ ] Add optional local authentication and/or topic ACL

### Repository focus
- `mac_mini/scripts/verify/`
- `rpi/scripts/verify/`

---

## T13. Verification and Testing

- [ ] Unit test Policy Router
- [ ] Unit test Deterministic Validator
- [ ] Unit test context-integrity safe deferral timeout transition
- [ ] Integration test Class 0
- [ ] Integration test Class 1
- [ ] Integration test Class 2
- [ ] Run fault-injection test suite
- [ ] Verify no unsafe autonomous actuation occurs under conflict, staleness, or missing-state conditions
- [ ] Verify closed-loop audit behavior under injected faults
- [ ] Verify canonical policy/fault/schema consistency tests pass
- [ ] Verify synchronized runtime copies remain version-consistent with the canonical frozen baseline
- [ ] Verify ESP32-linked bounded physical input/output behavior through integration tests when used
- [ ] Verify out-of-band class-wise latency measurement when timing infrastructure is used
- [ ] Verify timing capture path and measurement reproducibility when timing infrastructure is used

### Repository focus
- `mac_mini/scripts/verify/`
- `rpi/scripts/verify/`
- `integration/tests/`
- `integration/scenarios/`
- `integration/measurement/`

---

## Design Principles

- [ ] Shared frozen assets in `common/` must remain the single source of truth
- [ ] Mac mini remains the operational hub
- [ ] Raspberry Pi 5 remains the multi-node simulation and evaluation node
- [ ] ESP32 remains the embedded physical node layer for bounded input, sensing, or actuator/warning interfacing within the applicable scope
- [ ] Optional timing infrastructure remains evaluation-only and separate from the operational decision path
- [ ] Deterministic safety logic remains authoritative before bounded LLM assistance
- [ ] Safe deferral must be preferred over unsafe autonomous actuation
- [ ] Verification must be possible at both service level and closed-loop system level
- [ ] Deployment-local runtime files and synchronized copies must not override canonical frozen policy truth

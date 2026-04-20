# 07_task_breakdown.md

## Task Breakdown

This document defines the implementation-oriented task breakdown for the safe deferral system.

It is intended to support:
- vibe-coding workflows
- staged implementation
- repository-aligned development
- traceable progress from frozen assets to integration testing

---

## T0. Freeze Shared Reference Assets

- [ ] Finalize routing policy assets under `common/policies/`
- [ ] Finalize schema assets under `common/schemas/`
- [ ] Finalize canonical terminology under `common/terminology/`
- [ ] Finalize supporting reference docs under `common/docs/`
- [ ] Upload all frozen shared artifacts to the agent knowledge base before code generation

### Representative frozen assets
- [ ] `common/policies/policy_table_v1_1_2_FROZEN.json`
- [ ] `common/policies/low_risk_actions_v1_0_0_FROZEN.json`
- [ ] `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- [ ] `common/policies/output_profile_v1_0_0.json`
- [ ] `common/schemas/context_schema_v1_0_0_FROZEN.json`
- [ ] `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- [ ] `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- [ ] `common/schemas/validator_output_schema_v1_0_0_FROZEN.json`
- [ ] `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

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
- [ ] Finalize `fault_injection_rules`
- [ ] Finalize output profile constraints

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
- [ ] Implement ambiguous emergency downgrade rules
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
- [ ] Implement single-action resolution
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

- [ ] Create Telegram / mock payload schema
- [ ] Implement outbound alert sender
- [ ] Implement caregiver confirmation endpoint
- [ ] Restrict confirmation to bounded low-risk actions

### Repository focus
- `mac_mini/code/`

---

## T9. Implement Raspberry Pi Simulation Layer

- [ ] Create virtual context nodes
- [ ] Create virtual emergency nodes
- [ ] Create policy-driven deterministic fault cases
- [ ] Create randomized stress injection
- [ ] Parse shared frozen assets dynamically to derive:
  - [ ] thresholds
  - [ ] freshness bounds
  - [ ] minimal triggering predicates
  - [ ] required keys
- [ ] Implement the following fault categories separately:
  - [ ] threshold-crossing emergency injection
  - [ ] context conflict injection
  - [ ] sensor/state staleness injection
  - [ ] missing state injection
- [ ] Distinguish policy-input omissions from validator/action-schema omissions
- [ ] Distinguish threshold-crossing emergency cases from context-conflict cases

### Repository focus
- `rpi/code/`
- `integration/scenarios/`

---

## T10. Implement ESP32 Embedded Node Layer

- [ ] Implement bounded button input node firmware
- [ ] Implement MQTT publish/subscription behavior required for the button node
- [ ] Implement sensor node firmware when physical sensing is used
- [ ] Implement actuator or warning interface firmware when physical output is used
- [ ] Align broker connection parameters, topic namespaces, and device identifiers with the operational hub assumptions
- [ ] Keep embedded behavior bounded and policy-aligned rather than autonomous

### Repository focus
- `esp32/code/`
- `esp32/firmware/`
- `esp32/docs/`

---

## T11. Verify MQTT Connectivity and Isolation

- [ ] Ensure Mosquitto is LAN-reachable for Raspberry Pi 5
- [ ] Ensure internet-originated inbound access is blocked by firewall
- [ ] Add optional local authentication and/or topic ACL

### Repository focus
- `mac_mini/scripts/verify/`
- `rpi/scripts/verify/`

---

## T12. Verification and Testing

- [ ] Unit test Policy Router
- [ ] Unit test Deterministic Validator
- [ ] Unit test context-integrity safe deferral timeout transition
- [ ] Integration test Class 0
- [ ] Integration test Class 1
- [ ] Integration test Class 2
- [ ] Run fault-injection test suite
- [ ] Verify no unsafe autonomous actuation occurs under conflict, staleness, or missing-state conditions
- [ ] Verify closed-loop audit behavior under injected faults
- [ ] Verify ESP32-linked bounded physical input/output behavior through integration tests when used

### Repository focus
- `mac_mini/scripts/verify/`
- `rpi/scripts/verify/`
- `integration/tests/`
- `integration/scenarios/`

---

## Design Principles

- [ ] Shared frozen assets in `common/` must remain the single source of truth
- [ ] Mac mini remains the operational hub
- [ ] Raspberry Pi 5 remains the simulation and evaluation node
- [ ] ESP32 remains the embedded physical node layer for bounded input, sensing, or actuator/warning interfacing when used
- [ ] Deterministic safety logic remains authoritative before bounded LLM assistance
- [ ] Safe deferral must be preferred over unsafe autonomous actuation
- [ ] Verification must be possible at both service level and closed-loop system level
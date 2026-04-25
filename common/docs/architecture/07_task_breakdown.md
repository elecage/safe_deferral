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

Current communication and payload references:
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`

---

## T0. Freeze Shared Reference Assets

- [ ] Finalize routing policy assets under `common/policies/`
- [ ] Finalize schema assets under `common/schemas/`
- [ ] Finalize MQTT topic and publisher/subscriber contract references under `common/mqtt/`
- [ ] Finalize shared payload examples/templates under `common/payloads/`
- [ ] Finalize canonical terminology under `common/terminology/`
- [ ] Finalize supporting reference docs under `common/docs/`
- [ ] Ensure frozen shared artifacts and communication/payload references are available as implementation reference inputs before code generation

### Representative canonical frozen and reference assets
- [ ] `common/policies/policy_table_v1_1_2_FROZEN.json`
- [ ] `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- [ ] `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- [ ] `common/schemas/context_schema_v1_0_0_FROZEN.json`
- [ ] `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- [ ] `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- [ ] `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- [ ] `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- [ ] `common/mqtt/topic_registry_v1_0_0.json`
- [ ] `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- [ ] `common/mqtt/topic_payload_contracts_v1_0_0.md`
- [ ] `common/payloads/README.md`
- [ ] `common/docs/architecture/16_system_architecture_figure.md`
- [ ] `common/docs/architecture/17_payload_contract_and_registry.md`
- [ ] `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`
- [ ] `common/docs/architecture/12_prompts.md`

### Optional or version-sensitive companion assets
- [ ] output profile assets
- [ ] auxiliary deployment templates
- [ ] reproducibility support assets

### Authority note
- `common/policies/` and `common/schemas/` remain the policy and validation authority.
- `common/mqtt/` defines communication-contract references.
- `common/payloads/` provides payload examples/templates.
- MQTT contracts and payload examples must not override canonical policies or schemas.

---

## T1. Finalize Shared Policy, Schema, MQTT, and Payload Specifications

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
- [ ] Finalize MQTT topic registry draft
- [ ] Finalize publisher/subscriber matrix draft
- [ ] Finalize topic-to-payload contract references
- [ ] Finalize shared payload examples/templates
- [ ] Finalize optional or version-sensitive companion asset constraints where used
- [ ] Mark `common/mqtt/` and `common/payloads/` as reference layers, not policy/schema authority

---

## T2. Prepare Mac mini Core Platform

- [ ] Install Home Assistant
- [ ] Install Mosquitto
- [ ] Install Ollama
- [ ] Pull Llama 3.1
- [ ] Initialize SQLite
- [ ] Enable SQLite WAL mode
- [ ] Prepare runtime directories and environment scaffolding
- [ ] Prepare runtime access to synchronized policy/schema assets
- [ ] Prepare runtime access to MQTT topic registry and payload examples/templates when needed
- [ ] Maintain `requirements-mac.txt` as the current host-side Python dependency baseline

### Repository focus
- `mac_mini/scripts/install/`
- `mac_mini/scripts/configure/`
- `mac_mini/runtime/`
- `requirements-mac.txt`

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
- [ ] Verify JSON schema validation dependency availability
- [ ] Verify topic registry / payload helper dependency availability when implemented

### Repository focus
- `mac_mini/scripts/install/`
- `mac_mini/code/`
- `requirements-mac.txt`

---

## T4. Implement Policy Router

- [ ] Define router input strictly from frozen assets
- [ ] Load topic/payload assumptions from `common/mqtt/` where practical
- [ ] Validate Policy Router input using schema and payload boundary rules
- [ ] Reject, escalate, or safely defer malformed valid-path context missing `environmental_context.doorbell_detected`
- [ ] Implement Class 0 routing rules
- [ ] Implement conservative handling for malformed or non-matching emergency-like inputs
- [ ] Implement context sufficiency checks
- [ ] Implement Class 2 escalation rules
- [ ] Ensure freshness/fault metadata is not passed into the bounded LLM execution context
- [ ] Ensure `routing_metadata` is not passed into bounded LLM context
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
- [ ] Use low-risk catalog and validator schema as authority
- [ ] Reject `door_unlock` / `front_door_lock` as current Class 1 executable payload
- [ ] Ensure doorlock state is not accepted as current `device_states` authority
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
- [ ] Ensure safe deferral payloads follow `17_payload_contract_and_registry.md` boundaries

### Repository focus
- `mac_mini/code/`

---

## T7. Implement Audit Logging

- [ ] Define SQLite schema
- [ ] Implement `Audit Logging Service` as the only DB writer
- [ ] Subscribe to `audit/log/#` or equivalent async audit channel
- [ ] Align audit topic assumptions with `common/mqtt/topic_registry_v1_0_0.json` when implemented
- [ ] Log routing events
- [ ] Log validator outcomes
- [ ] Log deferrals, timeouts, and escalations
- [ ] Log caregiver confirmation events
- [ ] Log actuation ACK events
- [ ] Log doorbell / visitor-response and doorlock-sensitive outcomes when relevant
- [ ] Prevent other services from writing directly to the SQLite file

### Repository focus
- `mac_mini/code/`

---

## T8. Implement External Notification and Confirmation

- [ ] Implement Class 2 notification payload generation aligned with `class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- [ ] Validate outbound escalation payload completeness against the canonical schema
- [ ] Implement Telegram / mock outbound alert sender
- [ ] Implement caregiver confirmation endpoint
- [ ] Restrict confirmation to governed, explicitly scoped actions
- [ ] Do not treat caregiver confirmation as autonomous Class 1 validator approval
- [ ] Ensure doorlock-sensitive manual confirmation path includes approval, ACK verification, and audit visibility when implemented

### Repository focus
- `mac_mini/code/`

---

## T9. Implement Raspberry Pi Simulation, Dashboard, and Evaluation Layer

- [ ] Create virtual context nodes
- [ ] Create virtual `doorbell_detected` visitor-response context runtime
- [ ] Create virtual emergency nodes
- [ ] Create multi-node simulation runtime
- [ ] Create policy-driven deterministic fault cases
- [ ] Create randomized stress injection
- [ ] Create experiment and monitoring dashboard
- [ ] Create MQTT/payload governance inspector or dashboard
- [ ] Implement progress/status publication
- [ ] Implement result artifact export
- [ ] Prepare repeatable large-scale evaluation scenarios
- [ ] Parse shared frozen/reference assets dynamically to derive:
  - [ ] thresholds
  - [ ] freshness bounds
  - [ ] minimal triggering predicates
  - [ ] required keys
  - [ ] topic contracts
  - [ ] payload families
- [ ] Implement the following fault categories separately:
  - [ ] policy-declared emergency injection
  - [ ] context conflict injection
  - [ ] sensor/state staleness injection
  - [ ] missing state injection
  - [ ] missing `doorbell_detected` strict schema/fault case
- [ ] Distinguish policy-input omissions from validator/action-schema omissions
- [ ] Distinguish policy-declared emergency cases from context-conflict cases
- [ ] Align emergency simulation and fault generation with canonical trigger family `E001`~`E005`
- [ ] Run visitor-response and doorlock-sensitive evaluation scenarios
- [ ] Ensure `doorbell_detected=true` does not authorize autonomous doorlock control
- [ ] Support closed-loop automated verification against expected safe outcomes
- [ ] Maintain `requirements-rpi.txt` as the current experiment-side Python dependency baseline

### Repository focus
- `rpi/code/`
- `integration/scenarios/`
- `integration/tests/`
- `common/mqtt/`
- `common/payloads/`
- `requirements-rpi.txt`

---

## T10. Prepare ESP32 Cross-Platform Bring-Up Layer

### Cross-platform SDK/toolchain bring-up
- [ ] Finalize macOS ESP32 install scripts
- [ ] Finalize Linux ESP32 install scripts
- [ ] Finalize Windows ESP32 install scripts
- [ ] Verify ESP-IDF installation flow across supported host environments
- [ ] Verify export activation flow across supported host environments

### Cross-platform configure/verify scaffolding
- [ ] Finalize POSIX ESP32 configure scripts
- [ ] Finalize Windows ESP32 configure scripts
- [ ] Finalize POSIX ESP32 verify scripts
- [ ] Finalize Windows ESP32 verify scripts
- [ ] Verify sample project preparation flow
- [ ] Verify sample build success flow

### Prompt-driven firmware generation readiness
- [ ] Finalize ESP32 firmware generation prompts in `12_prompts.md`
- [ ] Finalize minimal template generation prompt
- [ ] Finalize node-specific firmware prompts for:
  - [ ] button input node
  - [ ] lighting control node
  - [ ] representative environmental sensing node
  - [ ] doorbell / visitor-arrival context node
  - [ ] optional experimental gas node
  - [ ] optional experimental fire node
  - [ ] optional experimental fall-detection interface node
  - [ ] planned extension warning / doorlock interface node

### Repository focus
- `esp32/scripts/install/`
- `esp32/scripts/configure/`
- `esp32/scripts/verify/`
- `esp32/docs/`
- `common/docs/architecture/12_prompts.md`

---

## T11. Implement ESP32 Embedded Physical Node Layer

### Minimal template and current canonical targets
- [ ] Generate minimal ESP-IDF template project
- [ ] Implement bounded button input node firmware
- [ ] Implement lighting control node firmware when physical output is used
- [ ] Implement representative environmental sensing node firmware used in the current validation baseline
- [ ] Implement doorbell / visitor-arrival context node firmware when visitor-response validation is included
- [ ] Emit `environmental_context.doorbell_detected` through registry-aligned MQTT topic/payload contract
- [ ] Implement MQTT publish/subscription behavior required for bounded physical nodes
- [ ] Align broker connection parameters, topic namespaces, and device identifiers with the operational hub assumptions
- [ ] Keep embedded behavior bounded and policy-aligned rather than autonomous

### Optional experimental targets
- [ ] Implement gas sensor node firmware when physical sensing is used
- [ ] Implement fire detection sensor node firmware when physical sensing is used
- [ ] Implement fall-detection interface firmware when physical sensing is used

### Planned extension targets
- [ ] Implement doorlock or warning interface firmware when physical output is used beyond the current canonical low-risk scope
- [ ] Ensure doorlock or warning interface firmware does not locally reinterpret doorlock as autonomous Class 1 authority

### Repository focus
- `esp32/code/`
- `esp32/firmware/`
- `esp32/docs/`

---

## T12. Implement Timing and Measurement Support

- [ ] Define out-of-band class-wise latency measurement plan
- [ ] Prepare optional STM32 timing node or equivalent dedicated measurement node when used
- [ ] Define timing capture points for Class 0 / Class 1 / Class 2 paths
- [ ] Define measurement wiring and trigger/capture assumptions
- [ ] Prepare timing capture scripts, notes, or result templates
- [ ] Ensure measurement infrastructure remains separate from the operational decision path

### Repository focus
- `integration/measurement/`

---

## T13. Verify MQTT Connectivity, Contract Consistency, and Isolation

- [ ] Ensure Mosquitto is LAN-reachable for Raspberry Pi 5
- [ ] Ensure Mosquitto is LAN-reachable for ESP32 embedded clients when used
- [ ] Ensure internet-originated inbound access is blocked by firewall
- [ ] Add optional local authentication and/or topic ACL
- [ ] Verify MQTT topic registry readability
- [ ] Verify publisher/subscriber matrix consistency
- [ ] Verify topic-to-payload contract references
- [ ] Verify payload examples validate against schemas where applicable
- [ ] Verify runtime apps do not hardcode topic strings where registry lookup is practical
- [ ] Verify dashboard/governance topics are non-authoritative

### Repository focus
- `mac_mini/scripts/verify/`
- `rpi/scripts/verify/`
- `integration/tests/`
- `common/mqtt/`
- `common/payloads/`

---

## T14. Verification and Testing

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
- [ ] Verify MQTT/payload contract consistency
- [ ] Verify `doorbell_detected` required field in valid context payloads
- [ ] Verify `doorbell_detected` is not an emergency trigger
- [ ] Verify `doorbell_detected` does not authorize autonomous doorlock control
- [ ] Verify doorlock state is absent from current `pure_context_payload.device_states`
- [ ] Verify dashboard/governance inspector is non-authoritative
- [ ] Verify synchronized runtime copies remain version-consistent with the canonical frozen baseline
- [ ] Verify ESP-IDF CLI and sample build readiness on supported ESP32 host environments
- [ ] Verify ESP32-linked bounded physical input/output behavior through integration tests when used
- [ ] Verify out-of-band class-wise latency measurement when timing infrastructure is used
- [ ] Verify timing capture path and measurement reproducibility when timing infrastructure is used

### Repository focus
- `mac_mini/scripts/verify/`
- `rpi/scripts/verify/`
- `esp32/scripts/verify/`
- `integration/tests/`
- `integration/scenarios/`
- `integration/measurement/`

---

## Design Principles

- [ ] Shared frozen assets in `common/` must remain the single source of truth according to authority level
- [ ] `common/policies/` and `common/schemas/` remain policy and validation authority
- [ ] `common/mqtt/` and `common/payloads/` are reference layers, not policy authority
- [ ] Mac mini remains the operational hub
- [ ] Raspberry Pi 5 remains the dashboard, multi-node simulation, fault-injection, replay, and evaluation node
- [ ] ESP32 remains the embedded physical node layer for bounded input, sensing, visitor-response context generation, or actuator/warning interfacing within the applicable scope
- [ ] ESP32 bring-up must be reproducible across supported host environments before real node firmware generation proceeds
- [ ] Optional timing infrastructure remains evaluation-only and separate from the operational decision path
- [ ] Deterministic safety logic remains authoritative before bounded LLM assistance
- [ ] Safe deferral must be preferred over unsafe autonomous actuation
- [ ] Verification must be possible at both service level and closed-loop system level
- [ ] Runtime apps, dashboard apps, and experiment tools should not hardcode MQTT topic strings or payload contracts where registry lookup is practical
- [ ] Payload boundaries must follow `common/docs/architecture/17_payload_contract_and_registry.md`
- [ ] Dashboard and governance tools must remain non-authoritative
- [ ] Deployment-local runtime files and synchronized copies must not override canonical frozen policy truth

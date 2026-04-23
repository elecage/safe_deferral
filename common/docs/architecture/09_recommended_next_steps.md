# 09_recommended_next_steps.md

## Recommended Immediate Next Steps

This document defines the recommended immediate next steps for the safe deferral project.

It is intended to guide:
- project bootstrap work
- repository initialization
- frozen asset preparation
- staged implementation readiness
- vibe-coding startup order

This document does not replace the canonical frozen baseline.  
Shared versioned assets under `common/` remain the source of truth for policy, schema, terminology, and related canonical references.

---

## 1. Confirm the Frozen Reference Baseline Is Complete

Before implementation proceeds further, confirm that the shared frozen assets under `common/` are complete and treated as the single source of truth.

### Priority targets
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

### Goal
Ensure the shared frozen assets and implementation-generation prompt set form a stable baseline before additional code generation proceeds.

---

## 2. Confirm the Architecture Document Set Is Internally Aligned

The architecture reference documents under `common/docs/architecture/` should be treated as a cross-checked set rather than as isolated notes.

### Priority documents
- installation target classification
- Mac mini build sequence
- deployment structure
- project directory structure
- automation strategy
- implementation plan
- task breakdown
- additional required work
- recommended next steps

### Goal
Provide a stable and internally aligned reference set for implementation planning, repository maintenance, and vibe-coding prompts.

---

## 3. Keep the Repository Structure and Dependency Manifests Stable

The repository structure should now be maintained as a staged, device-aware layout rather than repeatedly restructured.

### Required top-level areas
- `common/`
- `mac_mini/`
- `rpi/`
- `esp32/`
- `integration/`

### Important integration sub-areas
- `integration/tests/`
- `integration/scenarios/`
- `integration/measurement/`

### Root-level dependency manifests
- `requirements-mac.txt`
- `requirements-rpi.txt`

### Goal
Ensure shared assets, Mac mini scripts/code, Raspberry Pi scripts/code, ESP32 scripts/code/firmware, and integration assets remain clearly separated and reproducible.

---

## 4. Keep Install / Configure / Verify Script Sets as the Primary Bring-Up Path

The staged script workflow should remain the primary bring-up path for each layer.

### Required script groups
- `mac_mini/scripts/install/`
- `mac_mini/scripts/configure/`
- `mac_mini/scripts/verify/`
- `rpi/scripts/install/`
- `rpi/scripts/configure/`
- `rpi/scripts/verify/`
- `esp32/scripts/install/`
- `esp32/scripts/configure/`
- `esp32/scripts/verify/`

### Measurement workflow readiness
- `integration/measurement/`
- optional timing-node support notes
- latency capture references
- reproducible measurement templates

### Goal
Ensure implementation continues only on top of a reproducible staged bring-up path.

---

## 5. Maintain the Python Runtime Foundations

The host-side Python runtime foundation should remain aligned with the maintained dependency manifests and installation scripts.

### Immediate actions
- keep Mac mini Python virtual environment and `requirements-mac.txt` aligned
- keep Raspberry Pi Python virtual environment and `requirements-rpi.txt` aligned
- verify runtime package availability after dependency changes
- avoid undocumented drift between dependency manifests and install scripts

### Goal
Ensure the host-side runtime foundation remains stable before more hub-side and experiment-side code is implemented.

---

## 6. Keep the Mac mini Operational Platform Stable

The Mac mini operational platform should now be treated as an actively maintained base rather than a one-time setup target.

### Immediate services
- Home Assistant
- Mosquitto MQTT Broker
- Ollama
- Llama 3.1 model
- SQLite
- notification path

### Immediate checks
- broker reachability for Raspberry Pi and ESP32 on the trusted LAN
- SQLite WAL and single-writer assumptions
- deployed runtime asset consistency with `common/`
- environment-variable and secret handling hygiene

### Goal
Keep the Mac mini in a service-ready operational state before expanding hub-side implementation.

---

## 7. Begin or Continue Hub-side Implementation in Dependency Order

Once the frozen assets, architecture documents, repository layout, script layers, runtime foundation, and core services are stable, hub-side implementation should proceed in dependency order.

### First implementation targets
1. Policy Router
2. Deterministic Validator
3. Context-Integrity Safe Deferral Handler
4. Audit Logging Service
5. Outbound Notification Interface
6. Caregiver Confirmation Backend

### Goal
Ensure implementation proceeds on top of a stable, reproducible, policy-first foundation.

---

## 8. Treat ESP32 Bring-Up as Complete Enough to Move to Code Generation

The project is no longer at the stage where ESP32 is only a future documentation concern.

The following are already in place conceptually and should now serve as the base for code generation:
- cross-platform install scaffolding
- cross-platform configure scaffolding
- cross-platform verify scaffolding
- ESP32 execution-order documentation
- firmware-generation prompts in `12_prompts.md`

### Immediate next ESP32 steps
- generate the minimal ESP-IDF template project using the maintained prompt
- validate that the generated template fits the current `esp32/scripts/configure/` and `esp32/scripts/verify/` flow
- then generate current canonical node firmware in order:
  1. button input node
  2. lighting control node
  3. representative environmental sensing node

### Optional follow-on targets
- gas sensor node
- fire detection sensor node
- fall-detection interface node
- warning / doorlock interface node

### Goal
Move from ESP32 development-environment readiness to actual bounded node implementation without bypassing the current scaffolding.

---

## 9. Keep the Raspberry Pi Evaluation Path Bounded and Reproducible

The Raspberry Pi path should remain focused on simulation, fault injection, and closed-loop evaluation.

### Immediate targets
- multi-node virtual sensor/state runtime
- virtual emergency sensor runtime
- fault injection harness
- repeatable scenario orchestrator
- closed-loop automated verification support
- canonical policy/schema/rules consistency checks
- canonical emergency trigger alignment for `E001`~`E005`

### Goal
Ensure the evaluation path supports scalable fault-injection experiments without becoming part of the operational decision path.

---

## 10. Keep Timing and Measurement as an Optional Evaluation Track

When the target experiment package includes class-wise latency measurement, keep the timing infrastructure path explicit and separate.

### Immediate targets
- optional STM32 timing node or equivalent dedicated measurement node
- out-of-band class-wise latency capture notes
- measurement result templates for reproducible evaluation
- timing capture path validation

### Goal
Ensure latency evaluation remains trustworthy and reproducible without becoming part of the operational decision path.

---

## Final Principle

Do not begin broad implementation expansion unless:
- shared frozen assets are committed and stable
- architecture documents are aligned
- repository structure is stable
- install/configure/verify scripts remain in place as the primary bring-up path
- the Mac mini operational platform is ready
- core services pass independent verification
- root-level dependency manifests remain aligned with maintained runtime assumptions
- ESP32 bring-up is stable enough to support prompt-driven code generation
- Raspberry Pi evaluation assumptions remain bounded to simulation/fault/evaluation tasks
- measurement infrastructure assumptions are documented when out-of-band class-wise latency evaluation is part of the target experiment package
- deployment-local runtime files and synchronized copies are prevented from overriding canonical frozen policy truth

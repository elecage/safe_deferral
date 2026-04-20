# 12_prompts.md

## Vibe-Coding Prompt Set

The following prompts are intended for Google Antigravity or similar agent-first development tools.

They are designed to generate implementation artifacts that conform to:
- the frozen shared assets
- the current repository structure
- the canonical terminology of the project
- the Mac mini / Raspberry Pi / ESP32 role separation

---

## Common Instruction Block (apply to all prompts)

```text
Before writing any code, first submit an Implementation Plan for review and wait for approval.

After implementation, provide:
1. a concise walkthrough of all changes,
2. the exact files created or modified,
3. test results as evidence,
4. any known limitations or follow-up tasks.

Do not invent schemas, thresholds, policy rules, timeout values, topic namespaces, device identifiers, or action domains.
Always read them from the provided frozen artifacts first.

The following frozen artifacts must be loaded into the agent knowledge base before implementation:
- common/policies/policy_table_v1_1_2_FROZEN.json
- common/policies/low_risk_actions_v1_0_0_FROZEN.json
- common/policies/fault_injection_rules_v1_4_0_FROZEN.json
- common/policies/output_profile_v1_0_0.json
- common/schemas/context_schema_v1_0_0_FROZEN.json
- common/schemas/candidate_action_schema_v1_0_0_FROZEN.json
- common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json
- common/schemas/validator_output_schema_v1_0_0_FROZEN.json
- common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md

All parsing, validation, and generation logic must conform to those artifacts.
Do not use deprecated terminology such as:
- iCR
- iCR Handler
- iCR mapping

Use the canonical term:
context-integrity-based safe deferral stage
```

---

## Prompt 1. Implement Policy Router

```text
Implement a Python FastAPI service called `policy_router`.

Target repository area:
- mac_mini/code/

Requirements:
- The service receives normalized event/context JSON input.
- It deterministically routes each event into CLASS_0, CLASS_1, or CLASS_2.
- It must NOT call the LLM directly except when routing result is CLASS_1 and llm_invocation_allowed=true.
- Emergency routing has the highest priority.
- Ambiguous emergency-like button patterns must be downgraded to CLASS_2.
- Context insufficiency must route to CLASS_2.
- The output must include:
  - route_class
  - route_reason
  - llm_invocation_allowed
  - policy_constraints
- Add structured logging for all routing decisions.
- Use Pydantic for schemas.
- IMPORTANT:
  - Implement deterministic hard-routing only.
  - Do not include freshness, fault status, or validation metadata in the LLM execution context.
  - Read thresholds and routing rules from the frozen policy and schema artifacts instead of hardcoding them.
- Include unit tests for:
  1. emergency sensor event
  2. valid emergency gesture
  3. ambiguous emergency pattern
  4. context sufficient event
  5. context insufficient event
```

---

## Prompt 2. Implement Deterministic Validator

```text
Implement a Python module/service called `deterministic_validator`.

Target repository area:
- mac_mini/code/

Requirements:
- Input is allowed only from CLASS_1 flow.
- It receives:
  - LLM candidate actions
  - allowed low-risk action domain
  - current device state
  - bounded parameter rules
- It must perform:
  1. schema validation
  2. action-domain validation
  3. bounded parameter validation
  4. single-admissible-action resolution
- Outputs must be one of:
  - EXECUTE_APPROVED
  - SAFE_DEFERRAL
  - ESCALATE_CLASS_2
  - REJECT
- If multiple admissible candidates remain, output SAFE_DEFERRAL with at most 2 or 3 bounded options.
- It must never allow high-risk actions.
- IMPORTANT:
  - The Validator is NOT the actuator.
  - It approves only a single admissible low-risk action and passes the approved action to a dispatcher / actuator interface.
  - It must require state ACK feedback before confirming successful actuation and before final success logging.
  - It must not directly control hardware.
  - Read allowed actions and bounded ranges from the frozen policy artifacts instead of hardcoding them.
- Use Pydantic schemas and provide unit tests.
```

---

## Prompt 3. Implement Context-Integrity Safe Deferral Handler

```text
Implement a Python FastAPI service called `context_integrity_safe_deferral_handler`.

Target repository area:
- mac_mini/code/

Requirements:
- Input is a SAFE_DEFERRAL event plus 2 or 3 bounded candidate options.
- The service converts candidate options into bounded clarification instructions.
- Primary clarification modality is button input:
  - 1 hit = option A
  - 2 hits = option B
  - 3 hits = option C (optional)
- No free-form question generation is allowed.
- If timeout occurs, emit a timeout_event that can be consumed by the policy router for CLASS_2 escalation.
- IMPORTANT:
  - Do not generate open-ended dialogue.
  - The clarification flow must remain strictly bounded and button-based.
  - The service must implement the context-integrity-based safe deferral stage, not a generic chat interaction path.
- Include tests for:
  - valid 2-option mapping
  - valid 3-option mapping
  - timeout handling
  - invalid candidate option count
```

---

## Prompt 4. Implement Audit Logging Service

```text
Implement a dedicated `audit_logging_service` for the edge smart-home prototype.

Target repository area:
- mac_mini/code/

Requirements:
- SQLite must run in WAL mode.
- Multiple services must NOT write directly to the same SQLite file.
- The Audit Logging Service must be the only DB writer.
- Other services publish audit events asynchronously via MQTT topic audit/log/# or an equivalent internal queue.
- The Audit Logging Service consumes and persists them sequentially.
- Create tables for:
  - routing_events
  - validator_results
  - deferral_events
  - timeout_events
  - escalation_events
  - caregiver_actions
  - actuation_ack_events
- Provide a Python module with simple functions to insert and query records.
- Each log entry should include:
  - timestamp
  - event_id
  - class_label
  - reason
  - payload summary
- Include a script to initialize the schema.
- Include unit tests for DB creation and insert/query behavior.
```

---

## Prompt 5. Implement Outbound Notification Interface

```text
Implement a Python notification service for caregiver escalation and emergency dispatch.

Target repository area:
- mac_mini/code/

Requirements:
- Support Telegram Bot API first.
- Support a mock fallback mode.
- Input payload should include:
  - event summary
  - context summary
  - unresolved reason
  - manual confirmation options when applicable
- Provide a clean Python interface:
  - send_class0_alert(payload)
  - send_class2_escalation(payload)
- Include tests for payload validation and dry-run mode.
```

---

## Prompt 6. Implement Caregiver Confirmation Backend

```text
Implement a caregiver confirmation backend for bounded remote actions.

Target repository area:
- mac_mini/code/

Requirements:
- It must accept confirmation only for predefined low-risk actions.
- High-risk actions must be rejected.
- The interface may be driven by Telegram inline button callbacks or a mock API endpoint.
- Confirmation results must be logged through the audit logging channel rather than by direct SQLite multi-writer access.
- Return values should clearly distinguish:
  - CONFIRMED_LOW_RISK_ACTION
  - REJECTED_HIGH_RISK_ACTION
  - INVALID_CONFIRMATION
- Include unit tests for authorization-bounded behavior.
```

---

## Prompt 7. Implement Virtual Sensor Nodes

```text
Implement Python-based virtual MQTT sensor publishers for Raspberry Pi 5.

Target repository area:
- rpi/code/

Requirements:
- Publish periodic context data for:
  - temperature
  - illuminance
  - occupancy
  - device states
  - doorbell event
- Each virtual node must have:
  - unique node_id
  - topic namespace
  - configurable publish interval
- Provide a launcher that can start 30-40 virtual nodes.
- Include deterministic sample profiles for repeatable experiments.
- Read schema field definitions from the frozen context schema artifact.
```

---

## Prompt 8. Implement Virtual Emergency Sensors

```text
Implement Python-based virtual emergency sensor publishers for Raspberry Pi 5.

Target repository area:
- rpi/code/

Requirements:
- Simulate:
  - gas leak
  - smoke/fire
  - possible fall
- Publish threshold-exceeding events to MQTT.
- Support deterministic scenario replay for experiments.
- Include a small set of predefined emergency scenarios.
- Derive triggering conditions from the frozen policy artifacts instead of hardcoding them.
```

---

## Prompt 9. Implement Fault Injector Harness

```text
Implement a Python fault injector harness for the virtual MQTT sensor network.

Target repository areas:
- rpi/code/
- integration/scenarios/

Requirements:
- Do NOT hardcode arbitrary fault values in scripts.
- Dynamically derive thresholds, freshness bounds, required keys, and admissible action constraints from the frozen policy and schema artifacts.
- Implement fault categories separately:

  A. Threshold-crossing emergency injection
  - Purpose: verify immediate routing to CLASS_0.
  - Generation rule: derive the minimal triggering predicate of each emergency rule from the routing policy artifact.
  - If the rule is single-threshold based, exceed that threshold explicitly.
  - If the rule is composite, generate the minimal sensor combination required to satisfy the policy condition.

  B. Context conflict injection
  - Purpose: verify safe handling when multiple mutually admissible low-risk candidates remain unresolved.
  - Generation rule: inject conflicting conditions such that multiple bounded low-risk action candidates remain simultaneously admissible for the same actuator.
  - The expected safe outcome must also be derived from policy rules:
    - SAFE_DEFERRAL + context-integrity-based safe deferral handling if clarification is allowed
    - CLASS_2 escalation if required context remains insufficient
  - Under no condition should autonomous physical actuation occur.

  C. Sensor/State staleness injection
  - Purpose: verify fail-safe behavior under freshness violations.
  - Generation rule: inject timestamps that exceed freshness limits defined in the routing policy artifact for any freshness-critical sensor input or device-state field.

  D. Missing state injection
  - Purpose: verify conservative safe behavior under incomplete context.
  - Generation rule: intentionally omit required keys defined in the frozen context schema artifact.
  - Distinguish:
    1. policy-layer missing inputs, which must block Class 1 entry and force CLASS_2,
    2. validator/action-schema omissions, which must prevent execution and trigger SAFE_DEFERRAL or CLASS_2 according to policy.

- Support two modes:
  1. deterministic scripted fault cases
  2. randomized stress injection
- Fault metadata must be recorded so that experiments are reproducible.
- Provide a CLI interface for selecting fault profiles.
```

---

## Prompt 10. Implement Integration Test Runner

```text
Implement an integration test runner for the safety-oriented edge smart-home architecture.

Target repository areas:
- integration/tests/
- integration/scenarios/

Requirements:
- Execute scenario-based tests covering:
  - CLASS_0 emergency override
  - CLASS_1 bounded low-risk assistance
  - SAFE_DEFERRAL + context-integrity-based safe deferral handling
  - CLASS_2 caregiver escalation
- Load expected outcomes from scenario definition files.
- Compare observed route/validator outputs against expected outputs.
- Produce a machine-readable summary and a markdown report.
- Verify that no unsafe autonomous actuation occurs during conflict, staleness, or missing-state scenarios.
```

---

## Prompt 11. Generate Install Scripts

```text
Generate bash scripts for the safe deferral project setup.

Requirements:
- Respect the repository structure:
  - mac_mini/scripts/install/
  - rpi/scripts/install/
- Use the current frozen script naming and structure where applicable.
- Support:
  - Home Assistant
  - Mosquitto
  - Ollama
  - Python venv creation
  - Python dependency installation
  - Raspberry Pi runtime preparation
  - time synchronization client installation
- Scripts must be idempotent where possible.
- Use clear log messages and fail fast on errors.
- Do not collapse Mac mini and Raspberry Pi install workflows into a single flat script directory.
```

---

## Prompt 12. Generate Configuration Scripts

```text
Generate bash scripts that deploy configuration for the safe deferral architecture.

Requirements:
- Respect the repository structure:
  - mac_mini/scripts/configure/
  - rpi/scripts/configure/
- Configure:
  - Mosquitto
  - Home Assistant
  - Ollama model setup
  - SQLite schema initialization
  - environment variables
  - frozen policy and schema deployment
  - Telegram or mock notification settings
  - Raspberry Pi simulation runtime
  - Raspberry Pi fault profile setup
- Use template-based or deployment-target-aware file generation where possible.
- Do not hardcode secrets into tracked files.
- Inject configuration files into target runtime paths rather than fixed hardcoded paths.
- Add deployment-mode-dependent restart/reload steps where needed.
- Configure Mosquitto to remain LAN-reachable for Raspberry Pi while keeping WAN-originated inbound blocked by firewall.
- Preserve SQLite single-writer assumptions.
```

---

## Prompt 13. Implement ESP32 Embedded Node Firmware

```text
Implement bounded ESP32 firmware and supporting notes for the safe deferral prototype.

Target repository areas:
- esp32/code/
- esp32/firmware/
- esp32/docs/

Requirements:
- Support one or more bounded embedded node roles as needed:
  - button input node
  - sensor node
  - actuator or warning interface node
- Keep ESP32 behavior bounded and policy-dependent rather than autonomous.
- Align broker host assumptions, topic namespace, and device identity conventions with the documented hub-side architecture.
- Do not invent payload fields or routing rules that are not grounded in the frozen shared assets.
- Document firmware build, flash, reset, and reconnect assumptions.
- When generating code, prefer a structure that can fit PlatformIO or Arduino-style workflows.
- Include a small verification checklist for:
  - broker connectivity on the trusted local network
  - expected topic publish/subscribe behavior
  - bounded button or device behavior
  - recovery after reset or reconnect
```

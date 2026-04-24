## Prompt 21. Implement ESP32 Lighting Control Node Firmware

```text
Implement bounded ESP32 firmware for a lighting control node.

Target repository areas:
- esp32/code/
- esp32/firmware/
- esp32/docs/

Requirements:
- The firmware must represent a bounded lighting actuator interface node.
- It must receive only bounded low-risk commands that are already approved upstream by the deterministic validator and dispatcher path.
- It must not invent local autonomy or bypass the policy/validator chain.
- It must not accept out-of-domain commands.
- Support explicit GPIO or relay output configuration suitable for lighting control experiments.
- Include a device-state ACK path or equivalent local confirmation mechanism so that successful actuation can be reported upstream.
- Keep output behavior conservative on boot and reconnect:
  - no unintended toggle on startup,
  - no unsafe default-on state.
- If command payload schemas are needed, derive them from aligned project assets and supporting docs rather than inventing them.
- Document:
  - GPIO / relay assumptions,
  - safe default state,
  - ACK semantics,
  - reconnect behavior,
  - manual test steps for ON/OFF or similarly bounded lighting actions.
- Prefer ESP-IDF structure compatible with the current ESP32 environment scaffolding.
```

---

## Prompt 22. Implement ESP32 Representative Environmental Sensing Node Firmware

```text
Implement bounded ESP32 firmware for a representative environmental sensing node used in the current validation baseline.

Target repository areas:
- esp32/code/
- esp32/firmware/
- esp32/docs/

Requirements:
- The firmware must publish bounded environmental sensing data that fits the current validation baseline.
- Examples may include one or more of:
  - temperature,
  - illuminance,
  - occupancy-adjacent bounded signals,
  - simple device-state reporting,
  but do not invent unsupported schema fields.
- Sensor payloads must align with the frozen context schema and aligned project documents.
- Sampling and publish behavior must be deterministic and easy to replay in evaluation contexts.
- Include safe handling for sensor initialization failure, unavailable readings, and stale data conditions.
- Do not interpret sensed values into local autonomous actuator behavior.
- Document:
  - supported sensor model assumptions,
  - calibration assumptions if any,
  - publish interval behavior,
  - invalid reading handling,
  - reconnect behavior,
  - simple validation procedure against the hub-side pipeline.
- Prefer ESP-IDF structure compatible with the current ESP32 environment scaffolding.
```

---

## Prompt 23. Implement ESP32 Gas Sensor Node Firmware (Optional Experimental Target)

```text
Implement bounded ESP32 firmware for an optional experimental gas sensor node.

Target repository areas:
- esp32/code/
- esp32/firmware/
- esp32/docs/

Requirements:
- Treat this node as an optional experimental target, not as the current canonical baseline unless explicitly promoted by aligned project documents.
- The firmware must publish gas-related sensing events or bounded states only in ways that remain consistent with the frozen policy/schema artifacts.
- Do not invent ad hoc emergency semantics or payload fields.
- If gas emergency triggering is involved, keep the node’s behavior aligned with canonical trigger family expectations rather than embedding local autonomous emergency logic.
- Sensor failure, warm-up, drift, and invalid readings must be handled conservatively.
- Local firmware may classify raw hardware readiness states, but must not replace hub-side policy routing.
- Document:
  - assumed gas sensor hardware,
  - warm-up / stabilization behavior,
  - invalid reading behavior,
  - publish cadence,
  - reconnect behavior,
  - test steps for safe experimental validation.
- Prefer ESP-IDF structure compatible with the current ESP32 environment scaffolding.
```

---

## Prompt 24. Implement ESP32 Fire Detection Sensor Node Firmware (Optional Experimental Target)

```text
Implement bounded ESP32 firmware for an optional experimental fire detection sensor node.

Target repository areas:
- esp32/code/
- esp32/firmware/
- esp32/docs/

Requirements:
- Treat this node as an optional experimental target, not as the current canonical baseline unless explicitly promoted by aligned project documents.
- The firmware must publish bounded smoke/fire-related sensing events or states consistent with the frozen policy/schema artifacts.
- Do not invent out-of-schema payload fields or ungrounded emergency classifications.
- If smoke/fire emergency signaling is included, ensure the node’s outputs remain aligned with the canonical routing trigger family rather than embedding policy replacement logic locally.
- Sensor initialization failure, warm-up behavior, and invalid readings must be handled conservatively.
- The node may expose bounded readiness or health status, but it must not autonomously dispatch unrelated actuator behavior.
- Document:
  - assumed sensor hardware,
  - warm-up behavior,
  - invalid reading handling,
  - publish cadence,
  - reconnect behavior,
  - safe validation steps.
- Prefer ESP-IDF structure compatible with the current ESP32 environment scaffolding.
```

---

## Prompt 25. Implement ESP32 Fall-Detection Interface Node Firmware (Optional Experimental Target)

```text
Implement bounded ESP32 firmware for an optional experimental fall-detection interface node.

Target repository areas:
- esp32/code/
- esp32/firmware/
- esp32/docs/

Requirements:
- Treat this node as an optional experimental target, not as the current canonical baseline unless explicitly promoted by aligned project documents.
- The node may interface with an IMU, thresholding module, or bounded upstream fall-detection signal source.
- It must not invent arbitrary fall payloads that violate the frozen schema.
- When fall events are emitted, align them with the current policy/schema interpretation used elsewhere in the system.
- Keep local behavior bounded:
  - basic signal acquisition,
  - bounded event emission,
  - health/status reporting,
  - no autonomous unrelated actuation.
- Handle sensor ambiguity, initialization failure, and reconnect behavior conservatively.
- Document:
  - assumed IMU or fall interface hardware,
  - bounded detection/interface assumptions,
  - event emission behavior,
  - invalid signal handling,
  - simple validation procedure against the hub-side event path.
- Prefer ESP-IDF structure compatible with the current ESP32 environment scaffolding.
```

---

## Prompt 26. Implement ESP32 Warning or Doorlock Interface Node Firmware (Planned Extension Target)

```text
Implement bounded ESP32 firmware for a planned-extension warning interface node or doorlock interface node.

Target repository areas:
- esp32/code/
- esp32/firmware/
- esp32/docs/

Requirements:
- Treat this node as a planned extension target, not as part of the current canonical baseline unless explicitly promoted by aligned project documents.
- The node must remain bounded and policy-dependent.
- For warning interface behavior:
  - support bounded warning output such as buzzer, light, or simple alert indicator,
  - avoid inventing local autonomy that bypasses hub-side policy.
- For doorlock interface behavior:
  - keep safety assumptions explicit,
  - do not allow unbounded or high-risk actuation semantics,
  - require clear upstream authorization assumptions.
- The firmware must document conservative startup state, reconnect behavior, and ACK or status reporting assumptions.
- Do not invent unsupported payloads, routing rules, or action domains.
- Document:
  - hardware assumptions,
  - safe default state,
  - bounded command assumptions,
  - ACK/status semantics,
  - validation steps suitable for extension-stage experiments.
- Prefer ESP-IDF structure compatible with the current ESP32 environment scaffolding.
```

---

## Prompt 27. Implement Experiment Preflight Readiness Backend

```text
Implement an experiment preflight readiness backend for the safe deferral project.

Target repository areas:
- integration/measurement/
- integration/tests/
- mac_mini/code/ (only if a runtime-facing adapter is needed)

Requirements:
- The implementation must evaluate whether a selected experiment is READY, DEGRADED, BLOCKED, or UNKNOWN before execution.
- Treat this layer as an operational/evaluation support layer, not as policy authority.
- Load experiment dependency definitions from repository-managed metadata rather than hardcoding them throughout the code.
- Support dependency categories such as:
  - required operational nodes
  - required services
  - required topics
  - required runtime assets
  - required measurement nodes
  - required result-export conditions
- The design must preserve the distinction between:
  - operational nodes and services,
  - out-of-band measurement nodes.
- Measurement nodes must not be treated as authoritative control nodes.
- Support blocked reason codes such as:
  - NODE_OFFLINE
  - SERVICE_UNREACHABLE
  - ASSET_MISSING
  - MQTT_UNREACHABLE
  - EDGE_CONTROLLER_APP_UNAVAILABLE
  - MEASUREMENT_NODE_UNAVAILABLE
  - RESULT_STORE_NOT_WRITABLE
- Include a machine-readable readiness report format.
- Include unit tests for:
  - all dependencies ready
  - operational dependency blocked
  - measurement dependency degraded case
  - unknown state handling
- Keep the implementation aligned with:
  - integration/measurement/experiment_preflight_readiness_design.md
  - integration/measurement/class_wise_latency_profiles.md
- Do not invent policy semantics or reinterpret canonical emergency classes.
```

---

## Prompt 28. Implement STM32 Nucleo-H723ZG Measurement Node Firmware and Export Path

```text
Implement firmware and supporting documentation for an STM32 Nucleo-H723ZG out-of-band measurement node.

Target repository areas:
- integration/measurement/
- optional implementation area if created for STM32-specific source/assets

Requirements:
- Treat the STM32 node as an out-of-band measurement node, not as an operational control node.
- The node’s purpose is to support:
  - timing capture,
  - latency evidence collection,
  - trigger/observe/actuation timestamp export,
  - repeated-run reproducibility support.
- It must NOT:
  - publish operational control decisions,
  - replace policy routing,
  - replace validator behavior,
  - directly control actuators as part of the operational path.
- The implementation should target STM32 Nucleo-H723ZG specifically.
- Support deterministic measurement session behavior such as:
  - startup self-check,
  - timer/capture initialization,
  - edge timestamp capture,
  - raw timestamp export,
  - measurement readiness/status indication.
- Prefer a conservative firmware structure that is easy to audit and extend.
- Provide or document a recommended export path such as:
  - UART / USB CDC raw timestamp export,
  - bounded measurement status reporting,
  - CSV-friendly output structure.
- If host-side parsing or CSV conversion helpers are created, place them in the measurement support layer, not in the operational control path.
- Keep the design aligned with:
  - integration/measurement/stm32_nucleo_h723zg_measurement_node.md
  - integration/measurement/experiment_preflight_readiness_design.md
- Include a validation checklist for:
  - board boot success,
  - timer initialization success,
  - capture edge detection success,
  - export success,
  - no operational control side effects.
- Do not invent latency thresholds or measurement claims that are not grounded in aligned project docs.
```

## Prompt 29. Implement Intent Recovery Comparison Baseline Runner

```text
Implement an intent recovery comparison baseline runner for constrained alternative-input scenarios.

Target repository areas:
- integration/tests/
- integration/scenarios/
- rpi/code/ (only if replay/input simulation support is needed)
- mac_mini/code/ (only if a runtime adapter is needed)

Requirements:
- The purpose of this component is to compare three interpretation strategies under constrained-input conditions:
  1. Direct Mapping Baseline
  2. Rule-only Context Baseline
  3. Proposed LLM-assisted Intent Recovery
- The implementation must evaluate interpretation quality, not unrestricted actuation coverage.
- It must not bypass policy, schema, or validator boundaries.
- The runner must load scenario definitions from repository-managed files rather than hardcoding cases.
- Each scenario should support:
  - bounded input event
  - environmental context
  - device state context
  - intended interpretation label
  - optional expected safe outcome label
- The Direct Mapping Baseline should:
  - map bounded input directly to a predefined action or escalation path
  - use minimal or no contextual disambiguation
- The Rule-only Context Baseline should:
  - use deterministic rules over context and device states
  - avoid free-form semantic interpretation
- The Proposed LLM-assisted path should:
  - consume bounded input plus context
  - produce bounded interpretation candidates
  - remain policy/validator constrained for all executable outcomes
- The runner must compute at least:
  - Intent Recovery Accuracy
  - Top-k Candidate Containment
  - Over-escalation Rate
  - Unnecessary Safe Deferral Rate
  - Unsafe Interpretation Promotion Rate
- The output must include:
  - per-scenario comparison rows
  - aggregate metrics
  - machine-readable JSON summary
  - markdown table summary suitable for paper drafting
- Keep the evaluation aligned with:
  - common/docs/required_experiments.md
  - common/docs/paper/01_paper_contributions.md
- Include unit tests for:
  - baseline selection
  - metric computation
  - aggregate summary generation
  - scenario parsing


---

## Prompt 30. Generate Constrained-Input Intent Recovery Scenario Set

```text
## Prompt 30. Generate Constrained-Input Intent Recovery Scenario Set

```text
Generate a constrained-input intent recovery scenario set for comparative evaluation.

Target repository areas:
- integration/scenarios/
- integration/tests/data/

Requirements:
- Create repository-managed scenario files for evaluating intent recovery under constrained alternative input.
- Do not invent arbitrary action domains outside the frozen policy/schema baseline.
- The scenario set must support comparison between:
  - Direct Mapping Baseline
  - Rule-only Context Baseline
  - LLM-assisted Intent Recovery
- Each scenario file should include:
  - scenario_id
  - bounded input event description
  - contextual state payload
  - intended interpretation label
  - optional expected safe outcome
  - notes on ambiguity or insufficiency
- Include scenario families such as:
  1. same bounded input, different environmental context
  2. same bounded input, different device state context
  3. ambiguity that should lead to safe deferral
  4. ambiguity that should lead to caregiver escalation
  5. visitor-response / doorbell situations with multiple candidate interpretations
  6. cases where direct mapping over-escalates
  7. cases where rule-only logic fails to recover intended interpretation
- Preserve the distinction between:
  - intended interpretation label
  - executable action outcome
- Do not encode unrestricted autonomous door unlock as an allowed result.
- Prefer deterministic and reproducible scenario files suitable for repeated evaluation.
- Include at least:
  - a small canonical scenario pack
  - an extended scenario pack
- Provide a short README describing:
  - scenario schema
  - label semantics
  - how the scenarios support paper contribution evaluation

---

## Prompt 32. Implement Sensitive Actuation Visitor-Response Evaluation Flow

```text
## Prompt 32. Implement Sensitive Actuation Visitor-Response Evaluation Flow

```text
Implement a visitor-response sensitive-actuation evaluation flow for doorlock-related interpretation and escalation testing.

Target repository areas:
- integration/tests/
- integration/scenarios/
- mac_mini/code/ (only if a runtime adapter or mock orchestration bridge is needed)

Requirements:
- The purpose of this component is to evaluate whether visitor-response situations are handled safely under the current architecture interpretation.
- The flow must support scenarios where the system may interpret candidate intentions such as:
  - notify only
  - call caregiver
  - request bounded clarification
  - possible unlock intent
- The implementation must verify that:
  - unrestricted autonomous unlock does not occur
  - sensitive outcomes are routed to caregiver escalation
  - manual approval is required for doorlock-related execution
  - ACK and audit outcomes can be recorded in evaluation artifacts
- Treat doorlock as a sensitive actuation case, not as a standard autonomous low-risk action.
- Support mock or simulated caregiver approval states such as:
  - approved
  - denied
  - timeout
  - invalid approval
- Support mock ACK outcomes such as:
  - success
  - timeout
  - mismatch
- Generate evaluation outputs for:
  - autonomous unlock blocked verification
  - caregiver escalation correctness
  - approval-path correctness
  - ACK completeness
  - audit completeness
- Keep the design aligned with:
  - common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md
  - common/docs/required_experiments.md
  - common/docs/paper/01_paper_contributions.md
- Include unit or integration tests for:
  - blocked autonomous unlock
  - caregiver escalation path
  - approval required before dispatch
  - ACK-required comple

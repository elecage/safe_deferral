# 12_prompts_nodes_and_evaluation.md

## Node, Measurement, and Evaluation Prompt Set

This document contains the prompt set for:

- ESP32 node firmware generation
- STM32 timing / measurement support
- experiment-readiness support
- constrained-input evaluation
- Class 2 clarification and transition evaluation
- sensitive-actuation evaluation

The common repository-wide prompt assumptions are indexed from:
- `common/docs/architecture/12_prompts.md`
- `common/docs/architecture/12_prompts_core_system.md`

Prompt numbering is intentionally preserved from the original combined prompt document.

---

## Prompt 17. Implement ESP32 Embedded Node Firmware

```text
Implement bounded ESP32 firmware and supporting notes for the safe deferral prototype.

Target repository areas:
- esp32/code/
- esp32/firmware/
- esp32/docs/

Requirements:
- Support one or more bounded embedded node roles as needed, while respecting scope distinctions:
  - current canonical targets:
    - button input node
    - lighting control node
    - representative environmental sensing node used in the current validation baseline
  - optional experimental targets:
    - gas sensor node
    - fire detection sensor node
    - fall-detection interface node
  - planned extension targets:
    - doorlock or warning interface node
- Keep ESP32 behavior bounded and policy-dependent rather than autonomous.
- Align broker host assumptions, topic namespace, and device identity conventions with the documented hub-side architecture.
- Do not invent payload fields or routing rules that are not grounded in the frozen shared assets.
- Document firmware build, flash, reset, and reconnect assumptions.
- When generating code, prefer an ESP-IDF project structure and workflow aligned with the current `esp32/scripts/install/`, `esp32/scripts/configure/`, and `esp32/scripts/verify/` scaffolding.
- Include a small verification checklist for:
  - broker connectivity on the trusted local network
  - expected topic publish/subscribe behavior
  - bounded button or device behavior
  - recovery after reset or reconnect
```

---

## Prompt 18. Implement Timing and Measurement Support

```text
Implement optional timing and measurement support for out-of-band class-wise latency evaluation.

Target repository area:
- integration/measurement/

Requirements:
- Treat the timing and measurement layer as evaluation-only support, never as part of the operational control path.
- It must not become part of the operational control plane.
- Support optional STM32 timing node or equivalent dedicated measurement node assumptions when used.
- Define or generate:
  - class-wise latency experiment profiles
  - timing capture point descriptions for CLASS_0 / CLASS_1 / CLASS_2
  - measurement workspace notes
  - capture result templates
  - reproducibility-oriented measurement summaries
- Do not invent timing thresholds or measurement criteria unless grounded in the project’s aligned documents and frozen assets.
- Keep all measurement support compatible with repeatable paper evaluation workflows.
- Include checks or templates for:
  - capture path consistency
  - reproducible repeated-run summaries
  - exportable latency result formats
```

---

## Prompt 19. Generate ESP32 Minimal Template Project

```text
Generate a minimal ESP-IDF template project for the safe deferral prototype.

Target repository areas:
- esp32/firmware/templates/minimal_node/
- esp32/docs/

Requirements:
- Create the smallest buildable ESP-IDF project that fits the current repository structure.
- The template must build successfully through the current ESP32 configure/verify flow.
- Include at minimum:
  - CMakeLists.txt
  - main/CMakeLists.txt
  - main/main.c
- Optional files may be added only when justified:
  - sdkconfig.defaults
  - idf_component.yml
  - README.md
- The template must:
  - boot successfully,
  - log a clear startup message,
  - avoid autonomous actuation,
  - avoid any invented application-level policy logic.
- Prefer a simple main loop or task that is safe, deterministic, and easy to extend.
- Keep the code free of project-specific MQTT topics, policy thresholds, or actuator assumptions unless those are explicitly loaded from aligned project assets.
- Document:
  - expected target selection,
  - build command,
  - flash command,
  - serial monitor command.
- Include a verification checklist confirming that the template is suitable for:
  - `idf.py set-target ...`
  - `idf.py reconfigure`
  - `idf.py build`
```

---

## Prompt 20. Implement ESP32 Button Input Node Firmware

```text
Implement bounded ESP32 firmware for a button input node.

Target repository areas:
- esp32/code/
- esp32/firmware/
- esp32/docs/

Requirements:
- The firmware must represent a bounded physical button-input node.
- The node’s purpose is to emit policy-consistent button events or bounded clarification/emergency input patterns.
- Do not invent emergency semantics beyond what is allowed by the canonical policy artifacts.
- Distinguish clearly between:
  - bounded clarification button input used by the context-integrity-based safe deferral stage,
  - bounded emergency input semantics if and only if those semantics are grounded in the current policy artifacts.
- Support explicit GPIO configuration for one or more buttons.
- Include software debouncing and safe handling for repeated presses.
- Support deterministic event emission suitable for auditability and reproducibility.
- Align payload fields, event codes, and device identity conventions with the frozen shared assets and aligned docs.
- Do not hardcode arbitrary topic namespaces or payload field names.
- Keep the firmware bounded:
  - it may publish or report button events,
  - it must not interpret them into autonomous actuator commands.
- Prefer ESP-IDF style project structure compatible with the current ESP32 install/configure/verify scripts.
- Include notes for:
  - GPIO mapping,
  - debounce assumptions,
  - reset/reconnect behavior,
  - broker reconnect behavior,
  - test procedure for 1-hit / 2-hit / 3-hit bounded input patterns when policy-aligned.
```

---

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
  - `doorbell_detected` visitor-response context signal,
  - simple device-state reporting,
  but do not invent unsupported schema fields.
- Sensor payloads must align with the frozen context schema and aligned project documents.
- `doorbell_detected` must be represented as `environmental_context.doorbell_detected` and must not authorize autonomous doorlock control.
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

---

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
  - environmental context including `doorbell_detected` where visitor-response interpretation is relevant
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
- Visitor-response scenarios should represent doorbell context using `environmental_context.doorbell_detected`. This field is an interpretation context signal and must not authorize autonomous doorlock control.
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
```

---

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
- Visitor-response scenarios must represent doorbell context using `environmental_context.doorbell_detected` from the frozen context schema.
- `doorbell_detected` is an interpretation context signal and must not authorize autonomous doorlock control.
- Include scenario families such as:
  1. same bounded input, different environmental context
  2. same bounded input, different device state context
  3. ambiguity that should lead to safe deferral
  4. ambiguity that should lead to caregiver escalation
  5. visitor-response / `doorbell_detected` situations with multiple candidate interpretations
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
```

---

## Prompt 31. Implement Class 2 Clarification Transition Evaluation Flow

```text
Implement a Class 2 clarification transition evaluation flow for ambiguous or insufficient-context scenarios.

Target repository areas:
- integration/tests/
- integration/scenarios/
- rpi/code/ if scenario replay, simulation, or dashboard support is needed
- mac_mini/code/ only if a runtime adapter or mock bridge is needed

Requirements:
- The purpose of this component is to verify that Class 2 behaves as a bounded clarification and transition state, not as autonomous actuation or terminal caregiver escalation by default.
- Class 2 entry scenarios should include:
  - ambiguous bounded input,
  - insufficient context,
  - unresolved low-risk candidates,
  - no response / timeout,
  - emergency confirmation after initial ambiguity,
  - caregiver confirmation when unresolved or sensitive.
- The flow must validate `clarification_interaction_payload` records against:
  - common/schemas/clarification_interaction_schema.json
- The flow must verify all of the following branches:

  Class 2 → Class 1 transition test:
  - ambiguous lighting request
  - bounded clarification candidate selected
  - Policy Router re-entry
  - Deterministic Validator approval
  - lighting actuator command only after approval
  - lighting actuator ACK observed
  - audit log complete

  Class 2 → Class 0 transition test:
  - ambiguous distress input
  - emergency confirmation or deterministic emergency evidence
  - Policy Router re-entry
  - Class 0 local emergency action
  - no LLM emergency trigger authority
  - audit log complete

  Class 2 → Safe Deferral / Caregiver Confirmation test:
  - no response, timeout, persistent ambiguity, or sensitive unresolved request
  - no inferred intent
  - no actuator dispatch
  - safe deferral or caregiver confirmation outcome logged

- The flow must ensure that LLM-generated candidate text is not treated as:
  - final class decision,
  - validator approval,
  - actuator authorization,
  - emergency trigger evidence,
  - doorlock unlock approval.
- The output must include:
  - per-scenario transition result,
  - expected vs observed route comparison,
  - clarification payload validation result,
  - audit completeness summary,
  - machine-readable JSON summary,
  - markdown summary suitable for paper/evaluation reporting.
- Keep the design aligned with:
  - common/docs/architecture/19_class2_clarification_architecture_alignment.md
  - common/docs/architecture/20_scenario_data_flow_matrix.md
  - common/docs/architecture/17_payload_contract_and_registry.md
- Include unit or integration tests for:
  - Class 2 → Class 1 selected lighting candidate,
  - Class 2 → Class 0 emergency confirmation,
  - Class 2 → Safe Deferral timeout,
  - invalid clarification payload containing actuator authorization,
  - candidate text not promoted to executable authority.
```

---

## Prompt 32. Implement Sensitive Actuation Visitor-Response Evaluation Flow

```text
Implement a visitor-response sensitive-actuation evaluation flow for doorlock-related interpretation and escalation testing.

Target repository areas:
- integration/tests/
- integration/scenarios/
- mac_mini/code/ (only if a runtime adapter or mock orchestration bridge is needed)

Requirements:
- The purpose of this component is to evaluate whether visitor-response situations are handled safely under the current architecture interpretation.
- Visitor-response scenarios must represent doorbell context using `environmental_context.doorbell_detected`.
- `doorbell_detected` may affect interpretation confidence or routing explanation, but it must not authorize autonomous doorlock control.
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
  - doorbell-context-aware interpretation
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
  - `doorbell_detected=true` vs `doorbell_detected=false` interpretation difference where applicable
  - blocked autonomous unlock
  - caregiver escalation path
  - approval required before dispatch
  - ACK-required completion handling
```

---

## Prompt 33. Implement Experiment Dashboard Control Surface for Sensitive-Actuation Evaluation

```text
Implement an experiment dashboard control surface for the safe deferral project.

Target repository areas:
- rpi/code/ or the RPi dashboard-oriented repository area
- integration/measurement/ (only if result-export integration is needed)
- mac_mini/code/ only for telemetry, audit-summary, or control-state APIs/topics consumed by the RPi dashboard

Requirements:
- Treat the dashboard as a Raspberry Pi 5-hosted experiment operations and monitoring console rather than a low-level debug tool or policy authority.
- The dashboard should support:
  - experiment selection
  - preflight readiness visibility
  - required-node connectivity/status visibility
  - start/stop control
  - progress monitoring
  - result summary
  - graph/CSV export hooks when available
- It must support doorlock-sensitive experiment visibility such as:
  - `doorbell_detected` visitor-response context state
  - autonomous unlock blocked status
  - caregiver escalation state
  - manual approval state
  - ACK state
  - audit completeness state
- Do not implement unrestricted doorlock control UI as if it were a standard low-risk autonomous action.
- The dashboard may initiate experiment execution through the experiment/orchestration layer, but it must not bypass policy, validator, caregiver approval, or audit boundaries.
- Keep the design aligned with:
  - common/docs/required_experiments.md
  - common/docs/paper/01_paper_contributions.md
  - common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md
- If backend support is required, keep Raspberry Pi 5 as the experiment dashboard host. Mac mini may expose governed operational telemetry, audit summaries, and control-state APIs/topics consumed by the RPi dashboard, but it must not become the experiment dashboard authority.
- Include tests or verification notes for:
  - experiment readiness display
  - required-node state display
  - `doorbell_detected` visitor-response state display
  - experiment start/stop flow
  - sensitive-actuation status panel rendering
  - result export path rendering when available
```

---

## Prompt 34. Implement Developer Test-App Flow for Doorlock-Sensitive and Intent-Recovery Evaluation

```text
Implement a developer/test-app flow for fine-grained experiment control and debug visibility.

Target repository areas:
- rpi/code/ or a test-app-oriented experiment support area when used for experiment/debug control
- mac_mini/code/ only if governed operational telemetry, mock bridge, or runtime adapter support is needed
- integration/tests/
- integration/scenarios/

Requirements:
- Treat the test app as a developer/research control surface rather than the main RPi-hosted operations dashboard.
- The test app should support finer-grained interactions such as:
  - raw scenario invocation
  - direct mapping vs rule-only vs LLM-assisted baseline selection
  - visitor-response mock event injection using `environmental_context.doorbell_detected`
  - caregiver approval mock state injection
  - ACK success/timeout/mismatch simulation
  - raw payload/log/debug visibility
- The test app may overlap with the dashboard, but it must expose more experiment/debug detail.
- It must not be treated as an unrestricted actuator console.
- Do not implement direct door unlock controls that bypass the current sensitive-actuation interpretation.
- Keep the flow aligned with:
  - common/docs/required_experiments.md
  - common/docs/paper/01_paper_contributions.md
  - common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md
- Keep developer/test-app control clearly separated from the RPi-hosted experiment dashboard. If Mac mini APIs are used, they should expose governed operational telemetry or mock control endpoints without bypassing policy, validator, caregiver approval, or audit boundaries.
- Include tests or verification notes for:
  - baseline selector behavior
  - `doorbell_detected` mock injection
  - mock approval state injection
  - ACK mock behavior
  - raw scenario execution
  - debug/log visibility
```

---

## Prompt 35. Extend Scenario Orchestrator for Doorlock-Sensitive and Visitor-Response Evaluation

```text
Extend or implement scenario orchestration support for doorlock-sensitive and visitor-response experiment families.

Target repository areas:
- rpi/code/
- integration/scenarios/
- integration/tests/

Requirements:
- Treat Raspberry Pi 5 as the natural host for experiment dashboard support, scenario execution, simulation, replay, fault-injection support, progress/status publication, and result artifact generation.
- The orchestrator must support sequence-based sensitive-actuation scenarios rather than only single isolated events.
- At minimum, support:
  - visitor-response scenario family selection
  - bounded input or `doorbell_detected` trigger/context injection
  - contextual state bundle setup using the frozen context schema
  - expected safe outcome declaration
  - caregiver approval state variants:
    - approved
    - denied
    - timeout
    - invalid approval
  - ACK outcome variants:
    - success
    - timeout
    - mismatch
  - audit/result artifact collection
- The orchestrator should publish progress/state information in a way that the RPi-hosted dashboard and any developer/test-app layers can observe.
- Mac mini may expose safety-critical operational telemetry, audit summaries, and control-state topics for the RPi dashboard, but Mac mini must remain the operational edge hub rather than the experiment dashboard host.
- Keep the role distinction explicit:
  - Raspberry Pi 5 = experiment dashboard, orchestration, replay, fault-injection support, progress/status publication, and result artifact generation
  - Mac mini = safety-critical operational edge hub exposing telemetry/audit/control-state topics for the RPi dashboard
- Do not reinterpret doorlock as a standard autonomous low-risk action during orchestration.
- Do not treat `doorbell_detected` as doorlock unlock authorization.
- Keep the design aligned with:
  - common/docs/required_experiments.md
  - common/docs/paper/01_paper_contributions.md
  - common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md
- Include tests or verification notes for:
  - visitor-response family loading
  - `doorbell_detected` context injection
  - approval-state branch execution
  - ACK branch execution
  - result artifact generation
  - progress/status publication
```

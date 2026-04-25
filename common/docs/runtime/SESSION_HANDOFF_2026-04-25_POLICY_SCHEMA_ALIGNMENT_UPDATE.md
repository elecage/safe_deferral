# SESSION_HANDOFF_2026-04-25_POLICY_SCHEMA_ALIGNMENT_UPDATE.md

## Purpose

This handoff records the architecture, policy, and schema alignment work completed during the 2026-04-25 review session.

The session focused on resolving inconsistencies around:

- Raspberry Pi 5 dashboard placement,
- Class 1 low-risk autonomous action scope,
- caregiver confirmation versus sensitive actuation approval,
- context-state versus actuation-admissibility boundaries,
- dynamic fault-injection references to JSON Schema required fields,
- and the interpretation of Class 2 manual confirmation paths.

This handoff should be used as the next-session starting point before modifying architecture docs, runtime code, dashboard orchestration, or experiment scenarios.

---

## 1. Architectural baseline confirmed

The final paper architecture reference remains:

- `common/docs/architecture/24_final_paper_architecture_figure.md`
- `common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg`

The confirmed interpretation is:

- **Mac mini Edge Hub** remains the safety-critical operational control core.
- **ESP32 Device Layer** remains the field-side bounded input, sensing, emergency detection, and actuator-interface layer.
- **Raspberry Pi 5 Support Region** hosts support-side experiment, monitoring, orchestration, and result-publication functions.
- **Caregiver approval handling** remains part of the governed Mac mini operational loop, not an unrestricted external execution bypass.
- **TTS output** must be interpreted as policy-constrained spoken output, not direct raw LLM emission.

---

## 2. Dashboard placement decision

The dashboard should be interpreted as an **RPi-hosted experiment and monitoring console**.

The Raspberry Pi 5 dashboard is responsible for:

- experiment selection,
- node-readiness visibility,
- scenario progress monitoring,
- closed-loop result summaries,
- CSV/graph/evaluation artifact export,
- support-side monitoring and experiment visibility.

The dashboard is **not** the policy authority, validator authority, caregiver-approval authority, or primary operational hub.

Mac mini may expose operational telemetry, audit summaries, and control-state topics consumed by the Raspberry Pi 5 experiment dashboard, but Mac mini does not host the experiment and monitoring dashboard itself.

### Updated architecture classification file

File updated:

- `common/docs/architecture/01_installation_target_classification.md`

Key changes:

- Added `Experiment and Monitoring Dashboard` as a Raspberry Pi 5 development/experiment tool.
- Reworded Raspberry Pi 5 as the experiment-side node for simulation, fault injection, scenario orchestration, closed-loop verification, and dashboard-based experiment monitoring.
- Added a Mac mini boundary note that it may expose telemetry/control-state topics to the RPi dashboard but does not host the experiment dashboard.
- Added RPi dashboard runtime/dependencies to the RPi experiment-side runtime list.

Commit:

- `2f6486eb037f1fc7447ebfa171023655c9c75ab7`

---

## 3. Policy and schema review scope

The following policy files were reviewed:

1. `common/policies/policy_table_v1_1_2_FROZEN.json`
2. `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
3. `common/policies/output_profile_v1_1_0.json`
4. `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`

The following schema files were reviewed:

1. `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
2. `common/schemas/context_schema_v1_0_0_FROZEN.json`
3. `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`
4. `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
5. `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`

All files were checked against the final paper architecture interpretation and the current Class 1 low-risk action boundary.

---

## 4. Canonical Class 1 low-risk boundary

The authoritative Class 1 autonomous low-risk action scope remains limited to:

- `light_on` → `living_room_light`
- `light_on` → `bedroom_light`
- `light_off` → `living_room_light`
- `light_off` → `bedroom_light`

The authoritative low-risk action catalog remains:

- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`

The summarized `allowed_actions_taxonomy` inside `policy_table_v1_1_2_FROZEN.json` remains for readability, but it must not override the dedicated low-risk catalog.

Doorlock control, door opening, warning/sensitive interfaces, blinds, TV, gas valve, stove, mobility device, medication device, and similar sensitive or non-catalog actions are **not** Class 1 autonomous low-risk actions in the current frozen baseline.

---

## 5. Sensitive actuation interpretation

A key alignment decision from this session:

> Sensitive actuation requests, including doorlock control, must not be represented as Class 1 autonomous candidate actions and must not be approved as low-risk executable payloads.

Sensitive actuation may still be used as a representative evaluation scenario, but it must be interpreted as a governed path involving:

- Class 2 escalation, or
- a separately governed manual confirmation path, or
- caregiver-mediated approval under explicit policy.

It must not be treated as direct LLM-driven execution, direct low-risk execution, or a low-risk catalog extension without a future explicit frozen policy revision.

---

## 6. Files updated during this session

### 6.1 `fault_injection_rules_v1_4_0_FROZEN.json`

File:

- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`

Issue found:

The `dynamic_references` paths for required context keys did not match the actual JSON Schema structure in `context_schema_v1_0_0_FROZEN.json`.

Previous paths:

```json
"required_environmental_keys": "$.environmental_context.required",
"required_device_keys": "$.device_states.required"
```

Corrected paths:

```json
"required_environmental_keys": "$.properties.environmental_context.required",
"required_device_keys": "$.properties.device_states.required"
```

Commit:

- `c81b85111ee65402dea73a5104eaea704f8705d0`

Current verification note:

- Main branch now contains the corrected paths.

---

### 6.2 `low_risk_actions_v1_1_0_FROZEN.json`

File:

- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`

Change made:

Clarified that caregiver confirmation support for Class 1 low-risk assistance must remain inside the low-risk catalog, while sensitive actuation approval requires a separate explicit policy and manual confirmation path.

Current key note:

```json
"caregiver_confirmation_boundary": "Caregiver confirmation support for Class 1 low-risk assistance must not authorize actions outside this catalog. Sensitive actuation approval, if implemented, must be governed by a separate explicit policy and manual confirmation path."
```

Commit:

- `3e89e7ac99db74849a876dcadde832c80ea948eb`

Current verification note:

- Main branch contains the updated boundary note.

---

### 6.3 `output_profile_v1_1_0.json`

File:

- `common/policies/output_profile_v1_1_0.json`

Change made:

Clarified that Class 1 caregiver confirmation remains bounded by the canonical low-risk catalog, and caregiver-mediated sensitive approval must not be treated as autonomous low-risk execution.

Current key note:

```json
"caregiver_confirmation_note": "Class 1 caregiver confirmation support remains bounded by the canonical low-risk action catalog. Caregiver-mediated approval for sensitive actions, if implemented, belongs to a separate governed manual confirmation path and must not be treated as autonomous low-risk execution."
```

Commit:

- `0b247b764b5b79b96283065ff1f8b43bde1dc714`

Current verification note:

- Main branch contains the updated caregiver confirmation note.

---

### 6.4 `context_schema_v1_0_0_FROZEN.json`

File:

- `common/schemas/context_schema_v1_0_0_FROZEN.json`

Change made:

Clarified that `device_states` represents observable state and does not imply Class 1 autonomous actuation admissibility.

Current key description:

```json
"description": "Object map of observable smart home device states representing current state. Presence in this schema does not imply autonomous Class 1 actuation admissibility; allowed actuation targets are governed by the low-risk action catalog."
```

Commit:

- `1553a15cca9c340d0f2914208ffe7317ac18be9d`

Current verification note:

- Main branch contains the updated `device_states` description.

---

### 6.5 `candidate_action_schema_v1_0_0_FROZEN.json`

File:

- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`

Change made:

Clarified that the LLM output sandbox is limited to a single Class 1 low-risk candidate action or safe deferral, and sensitive actuation requests must not be represented as autonomous candidate actions.

Current key description:

```json
"description": "Local LLM output sandbox boundary for a single Class 1 low-risk candidate action or safe deferral. Sensitive actuation requests are outside this schema and must not be represented as autonomous candidate actions."
```

Commit:

- `e7c0f7ffeffb4fb049423929a6a2a79f7c6cd0bd`

Current verification note:

- Main branch contains the updated candidate action boundary description.

---

### 6.6 `validator_output_schema_v1_1_0_FROZEN.json`

File:

- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`

Change made:

Clarified that actions outside the authoritative low-risk catalog, including doorlock control, must not be approved as executable payloads.

Current key description:

```json
"description": "Strict internal payload generated by the Deterministic Validator. Dictates deterministic routing to the actuator dispatcher, context-integrity safe deferral handler, or Class 2 escalation. Candidate actions outside the authoritative low-risk catalog, including sensitive actuation requests such as doorlock control, must not be approved in executable_payload and must be routed to Class 2 escalation or a separately governed manual confirmation path."
```

Commit:

- `803baf204e99cb13a601470391c733b088549c39`

Current verification note:

- Main branch contains the updated validator sensitive-actuation boundary description.

---

### 6.7 `class_2_notification_payload_schema_v1_0_0_FROZEN.json`

File:

- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

Change made:

Clarified that `manual_confirmation_path` may describe a governed manual confirmation path, but does not itself authorize autonomous low-risk execution or sensitive actuation.

Current key description:

```json
"description": "Instruction or route by which a caregiver can review, confirm, deny, or intervene. This field may describe a governed manual confirmation path, but does not by itself authorize autonomous low-risk execution or sensitive actuation."
```

Commit:

- `44d1b135034893093afbf9869ead8faa14033d45`

Current verification note:

- Main branch contains the updated manual confirmation path description.

---

### 6.8 `policy_table_v1_1_2_FROZEN.json`

File:

- `common/policies/policy_table_v1_1_2_FROZEN.json`

Change made:

Added a top-level implementation note clarifying that sensitive actuation requests are outside Class 1 autonomous low-risk scope in this policy version.

Current key note:

```json
"sensitive_actuation_note": "Sensitive actuation requests, including doorlock control, are not part of the Class 1 autonomous low-risk action scope in this policy version. Such requests must not be approved as low-risk executable payloads and must be handled through Class 2 escalation or a separately governed manual confirmation path."
```

Commit:

- `be217f96d61fc9055cb5ac6167f15459f67bdd47`

Current verification note:

- Main branch contains the new `sensitive_actuation_note`.

---

## 7. File reviewed but not modified

### `policy_router_input_schema_v1_1_1_FROZEN.json`

File:

- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`

Result:

- Reviewed and left unchanged.
- Its separation of `routing_metadata` and `pure_context_payload` remains appropriate.
- `pure_context_payload` remains the only LLM-prompt-composable context reference.
- `routing_metadata.network_status` remains routing/fallback metadata and should not be used as LLM reasoning content.

Potential future note, not yet applied:

- Consider adding a description stating that `routing_metadata` must not be passed into the LLM prompt.
- Consider clarifying that `routing_metadata.ingest_timestamp_ms` differs from `pure_context_payload.trigger_event.timestamp_ms`.

These are optional documentation refinements, not current inconsistencies.

---

## 8. Current policy/schema consistency conclusion

After the above changes, the policy/schema set now consistently supports the following interpretation:

1. Class 1 autonomous execution is restricted to the authoritative low-risk light-control catalog.
2. Local LLM candidate output is sandboxed to Class 1 low-risk actions or safe deferral.
3. The deterministic validator cannot approve actions outside the low-risk catalog as executable payloads.
4. Context schema device state presence does not imply actuation admissibility.
5. Doorlock and other sensitive actuation requests are outside Class 1 autonomous scope.
6. Sensitive actuation must route to Class 2 escalation or a separately governed manual confirmation path.
7. Class 2 `manual_confirmation_path` is an instruction/route field, not an execution-authority field.
8. Fault injection dynamic references now match the actual context JSON Schema structure.

---

## 9. Implications for dashboard and orchestration

The Raspberry Pi 5 dashboard and orchestration layer should reflect the above constraints.

Recommended dashboard/orchestration behavior:

- Show Class 1 approved execution only for the current low-risk light actions.
- Treat sensitive actuation requests as escalation/manual-confirmation scenarios, not as low-risk actuator dispatch scenarios.
- For conflict/fault scenarios, mark as PASS when observed outcome is one of the allowed safe outcomes.
- For `FAULT_CONFLICT_01_GHOST_PRESS`, PASS should include either:
  - `safe_deferral`, or
  - `class_2_escalation`.
- FAIL should include any autonomous `actuator_dispatcher` result for ambiguity/conflict profiles.
- For Class 2 payload display, show `manual_confirmation_path` as a review/intervention route, not as a direct execution command.
- For sensitive actuation scenarios, dashboard UI should visually distinguish:
  - low-risk confirmation,
  - Class 2 escalation,
  - caregiver-mediated sensitive approval,
  - and final actuator ACK closure.

---

## 10. Implications for future doorlock experiments

Doorlock may remain useful as a representative sensitive actuation evaluation case, but it must be framed correctly.

Correct interpretation:

- Doorlock is **not** part of Class 1 autonomous low-risk execution.
- LLM may assist in intent recovery or explanation, but it must not emit a door-unlock candidate under `candidate_action_schema_v1_0_0_FROZEN.json`.
- The validator must not generate an `approved` executable payload for doorlock control.
- Doorlock-related requests must route to Class 2 escalation or a separately governed caregiver-mediated approval path.
- Any eventual sensitive approval path must include explicit policy, manual confirmation semantics, audit correlation, and ACK closure.

Do not add doorlock to the low-risk catalog unless the research direction intentionally changes and a future frozen policy revision is created.

---

## 11. Recommended next steps

### 11.1 Documentation alignment

Review and update, if needed:

- `README.md`
- `CLAUDE.md`
- `common/docs/runtime/SESSION_HANDOFF.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-24_DASHBOARD_TEST_APP_AND_ORCHESTRATION_UPDATE.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-24_PROMPT_REFACTOR_AND_EVAL_UPDATE.md`
- any dashboard/orchestration design documents

Primary goal:

- Ensure all documents reflect the now-consistent boundary between Class 1 low-risk confirmation and sensitive actuation manual approval.
- Ensure dashboard placement remains Raspberry Pi 5 support-side experiment and monitoring console.

### 11.2 Runtime validation

Run or create verification checks to confirm:

- all edited JSON files remain parseable,
- schema references are still resolvable,
- candidate action validation still rejects non-light actions,
- validator output validation still rejects sensitive executable payloads,
- fault injection required-key dynamic references now resolve to the context schema required lists.

### 11.3 Experiment orchestration alignment

Update experiment runner/dashboard logic to ensure:

- `manual_confirmation_path` is rendered as an approval/review path, not an execution command,
- sensitive actuation scenarios cannot be misclassified as Class 1 low-risk,
- Class 2 escalation artifacts include audit correlation whenever available,
- PASS/FAIL logic respects profiles with multiple allowed safe outcomes.

---

## 12. Important caution for the next session

Do not introduce a new Class 1 action or target merely because it appears in `context_schema.device_states`.

The source of truth for autonomous Class 1 actuation remains:

- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`

Do not allow doorlock, blind, TV, gas valve, stove, or warning/sensitive interfaces into `candidate_action_schema` or `validator_output_schema.executable_payload` unless a deliberate future policy revision is created.

---

## 13. Summary

This session completed policy/schema alignment around the current safe-deferral architecture.

The system is now consistently documented at the policy/schema level as:

- LLM-assisted but not LLM-authorized,
- deterministic-validator-gated,
- low-risk-catalog-bounded,
- ACK-confirmed,
- Class-2-escalation-capable,
- safe-deferral-first under ambiguity,
- and sensitive-actuation-separated from autonomous low-risk execution.

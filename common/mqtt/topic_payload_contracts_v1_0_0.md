# topic_payload_contracts_v1_0_0.md

## MQTT Topic Payload Contracts

Status: **DRAFT**

This document explains the payload expectations for each MQTT topic family.

Machine-readable topic registry:

- `common/mqtt/topic_registry_v1_0_0.json`

Payload boundary reference:

- `common/docs/architecture/17_payload_contract_and_registry.md`

MQTT-aware interface reference:

- `common/docs/architecture/15_interface_matrix.md`

Experiment and governance verification reference:

- `common/docs/required_experiments.md`

This document does not override canonical policies or schemas. It describes communication contracts and payload expectations.

---

## 1. Operational input topics

### `safe_deferral/context/input`

Expected payload family:

- `policy_router_input`

Schema:

- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`

Example:

- `common/payloads/examples/policy_router_input_non_visitor.json`
- `common/payloads/examples/policy_router_input_visitor_doorbell.json`

Rules:

- Must contain `source_node_id`, `routing_metadata`, and `pure_context_payload`.
- `routing_metadata.network_status` must use the schema enum: `online`, `offline`, or `degraded`.
- `pure_context_payload.trigger_event.timestamp_ms` must be used; do not use legacy `event_timestamp_ms`.
- Button examples should use `single_click`, `double_click`, `long_press`, or `triple_hit`; do not use legacy `single_hit`.
- `pure_context_payload.environmental_context.doorbell_detected` is required.
- `routing_metadata` must not be mixed into LLM prompt context.
- RPi may publish only in controlled simulation/experiment mode.

### `safe_deferral/emergency/event`

Expected payload family:

- `policy_router_input_or_emergency_context`

Schema:

- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`

Example:

- `common/payloads/examples/policy_router_input_emergency_temperature.json`

Rules:

- Must align with emergency family E001~E005.
- `doorbell_detected` is not emergency evidence.
- Emergency publication should be audited.
- Temperature emergency examples should use `trigger_event.event_type="sensor"`, `trigger_event.event_code="threshold_exceeded"`, and temperature values satisfying the policy predicate.

---

## 2. Model and validator topics

### `safe_deferral/llm/candidate_action`

Expected payload family:

- `candidate_action`

Schema:

- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`

Example:

- `common/payloads/examples/candidate_action_light_on.json`

Rules:

- LLM candidate output is not execution authority.
- The validator remains the execution-admissibility authority.
- `proposed_action` must be `light_on`, `light_off`, or `safe_deferral`.
- `target_device` must be `living_room_light`, `bedroom_light`, or `none`.
- `door_unlock` is not an allowed current Class 1 candidate action.

### `safe_deferral/validator/output`

Expected payload family:

- `validator_output`

Schema:

- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`

Example:

- `common/payloads/examples/validator_output_execute_approved_light.json`

Rules:

- Approved executable payload must stay within the frozen low-risk catalog.
- Doorlock executable payload is not allowed in the current baseline.
- Non-approved outcomes should route to safe deferral or Class 2 escalation as appropriate.
- `approved` outputs must route to `actuator_dispatcher` and include `executable_payload`.
- `safe_deferral` and `rejected_escalation` outputs must not include executable payloads.

---

## 3. Safe deferral and escalation topics

### `safe_deferral/deferral/request`

Expected payload family:

- `safe_deferral_event`

Schema:

- none yet; future schema recommended

Example:

- `common/payloads/examples/safe_deferral_request_two_options.json`

Rules:

- Bounded clarification only.
- No free-form question generation.
- Ambiguity must not produce unsafe autonomous actuation.
- The payload may describe candidate options for user clarification, but it does not authorize actuation.

### `safe_deferral/escalation/class2`

Expected payload family:

- `class_2_notification_payload`

Schema:

- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

Example:

- `common/payloads/examples/class_2_notification_doorlock_sensitive.json`

Rules:

- Used for caregiver escalation.
- `manual_confirmation_path` describes a governed review/confirm/deny/intervene path.
- `manual_confirmation_path` is not autonomous execution authority.
- Doorlock-sensitive notifications may explain a manual confirmation route, but must not bypass validator, caregiver approval, ACK, or audit boundaries.

---

## 4. Manual confirmation and actuation topics

### `safe_deferral/caregiver/confirmation`

Expected payload family:

- `manual_confirmation_payload`

Schema:

- none yet; future schema recommended

Example:

- `common/payloads/examples/manual_confirmation_doorlock_approved.json`

Rules:

- Belongs to a separately governed manual confirmation path.
- Must not be confused with Class 1 autonomous validator approval.
- Mock publishers are allowed only in controlled test mode.
- Doorlock-related approvals, if represented, must remain outside the current autonomous Class 1 low-risk catalog.

### `safe_deferral/actuation/command`

Expected payload family:

- `actuation_command_payload`

Schema:

- none yet; future schema recommended

Example:

- `common/payloads/examples/actuation_command_light_on.json`

Rules:

- Publisher must be a Mac mini dispatcher path.
- Low-risk commands require validator approval.
- Doorlock commands require governed manual confirmation path under current interpretation.
- Dashboard/test-app/governance tooling must not directly publish unrestricted actuation commands.

### `safe_deferral/actuation/ack`

Expected payload family:

- `actuation_ack_payload`

Schema:

- none yet; future schema recommended

Example:

- `common/payloads/examples/actuation_ack_success.json`

Rules:

- ACK is closed-loop evidence.
- ACK is not pure context input.
- ACK should be audit-visible.

---

## 5. Audit topics

### `safe_deferral/audit/log`

Expected payload family:

- `audit_event_payload`

Schema:

- none yet; future schema recommended

Example:

- `common/payloads/examples/audit_event_route_decision.json`

Rules:

- Mac mini audit logging service should remain the only database writer.
- Audit events are evidence and traceability records.
- Audit events are not policy authority.

---

## 6. Experiment and dashboard topics

### `safe_deferral/sim/context`

Expected payload family:

- `policy_router_input_or_context_fixture`

Example:

- `common/payloads/examples/policy_router_input_visitor_doorbell.json`

Rules:

- RPi simulation only.
- Must be gated so simulation traffic does not accidentally masquerade as uncontrolled operational input.
- Payloads containing `pure_context_payload` must obey `context_schema_v1_0_0_FROZEN.json`.

### `safe_deferral/fault/injection`

Expected payload family:

- `fault_injection_payload`

Example:

- `common/payloads/examples/fault_injection_missing_doorbell_context.json`

Rules:

- Controlled experiment only.
- Fault generation must derive constraints from frozen policy/schema/rules assets.
- Missing `doorbell_detected` may be used as a strict schema/fault case.
- `FAULT_CONTRACT_DRIFT_01` is a governance/verification fault and must not be treated as an operational control path.

### `safe_deferral/dashboard/observation`

Expected payload family:

- `dashboard_observation_payload`

Example:

- `common/payloads/examples/dashboard_observation_doorlock_sensitive.json`

Rules:

- Dashboard observation is visibility only.
- Dashboard observation is not policy truth.
- Doorlock state shown here is observation/experiment state, not `context_schema.device_states`.

### `safe_deferral/experiment/progress`

Expected payload family:

- `experiment_progress_payload`

Example:

- `common/payloads/examples/experiment_progress_running.json`

Rules:

- Experiment status only.
- No operational control authority.

### `safe_deferral/experiment/result`

Expected payload family:

- `result_export_payload`

Example:

- `common/payloads/examples/result_export_summary.json`

Rules:

- Result artifact only.
- Must trace to scenario IDs, run IDs, and expected outcomes.

---

## 7. Governance validation artifacts

Package G may generate the following non-operational artifacts:

- interface-matrix alignment report,
- topic-drift report,
- payload validation report,
- governance backend/UI separation report,
- proposed-change review report.

Rules:

- These artifacts are evidence only.
- They must not be operational MQTT control topics.
- They must not create policy authority, schema authority, validator authority, caregiver approval authority, audit authority, actuator authority, or doorlock execution authority.
- Proposed changes must go through review/commit workflow before becoming repository references.

---

## 8. Future schema candidates

The following topic payload families are likely candidates for future schema formalization:

- `safe_deferral_event`
- `manual_confirmation_payload`
- `actuation_command_payload`
- `actuation_ack_payload`
- `audit_event_payload`
- `dashboard_observation_payload`
- `experiment_progress_payload`
- `result_export_payload`
- `governance_change_report_payload`
- `interface_matrix_alignment_report_payload`
- `topic_drift_report_payload`
- `payload_validation_report_payload`

Do not create these schemas casually. Add them only when implementation or evaluation needs stable machine-readable contracts.

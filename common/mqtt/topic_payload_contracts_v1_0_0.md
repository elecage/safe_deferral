# topic_payload_contracts_v1_0_0.md

## MQTT Topic Payload Contracts

Status: **DRAFT**

This document explains the payload expectations for each MQTT topic family.

Machine-readable topic registry:

- `common/mqtt/topic_registry_v1_0_0.json`

Payload boundary reference:

- `common/docs/architecture/17_payload_contract_and_registry.md`

---

## 1. Operational input topics

### `safe_deferral/context/input`

Expected payload family:

- `policy_router_input`

Schema:

- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`

Rules:

- Must contain `pure_context_payload`.
- `pure_context_payload.environmental_context.doorbell_detected` is required.
- `routing_metadata` must not be mixed into LLM prompt context.
- RPi may publish only in controlled simulation/experiment mode.

### `safe_deferral/emergency/event`

Expected payload family:

- `policy_router_input_or_emergency_context`

Schema:

- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`

Rules:

- Must align with emergency family E001~E005.
- `doorbell_detected` is not emergency evidence.
- Emergency publication should be audited.

---

## 2. Model and validator topics

### `safe_deferral/llm/candidate_action`

Expected payload family:

- `candidate_action`

Schema:

- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`

Rules:

- LLM candidate output is not execution authority.
- The validator remains the execution-admissibility authority.
- `door_unlock` is not an allowed current Class 1 candidate action.

### `safe_deferral/validator/output`

Expected payload family:

- `validator_output`

Schema:

- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`

Rules:

- Approved executable payload must stay within the frozen low-risk catalog.
- Doorlock executable payload is not allowed in the current baseline.
- Non-approved outcomes should route to safe deferral or Class 2 escalation as appropriate.

---

## 3. Safe deferral and escalation topics

### `safe_deferral/deferral/request`

Expected payload family:

- `safe_deferral_event`

Schema:

- none yet; future schema recommended

Rules:

- Bounded clarification only.
- No free-form question generation.
- Ambiguity must not produce unsafe autonomous actuation.

### `safe_deferral/escalation/class2`

Expected payload family:

- `class_2_notification_payload`

Schema:

- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

Rules:

- Used for caregiver escalation.
- `manual_confirmation_path` describes a governed review/confirm/deny/intervene path.
- `manual_confirmation_path` is not autonomous execution authority.

---

## 4. Manual confirmation and actuation topics

### `safe_deferral/caregiver/confirmation`

Expected payload family:

- `manual_confirmation_payload`

Schema:

- none yet; future schema recommended

Rules:

- Belongs to a separately governed manual confirmation path.
- Must not be confused with Class 1 autonomous validator approval.
- Mock publishers are allowed only in controlled test mode.

### `safe_deferral/actuation/command`

Expected payload family:

- `actuation_command_payload`

Schema:

- none yet; future schema recommended

Rules:

- Publisher must be a Mac mini dispatcher path.
- Low-risk commands require validator approval.
- Doorlock commands require governed manual confirmation path under current interpretation.
- Dashboard/test-app must not directly publish unrestricted actuation commands.

### `safe_deferral/actuation/ack`

Expected payload family:

- `actuation_ack_payload`

Schema:

- none yet; future schema recommended

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

Rules:

- Mac mini audit logging service should remain the only database writer.
- Audit events are evidence and traceability records.
- Audit events are not policy authority.

---

## 6. Experiment and dashboard topics

### `safe_deferral/sim/context`

Expected payload family:

- `policy_router_input_or_context_fixture`

Rules:

- RPi simulation only.
- Must be gated so simulation traffic does not accidentally masquerade as uncontrolled operational input.
- Payloads containing `pure_context_payload` must obey `context_schema_v1_0_0_FROZEN.json`.

### `safe_deferral/fault/injection`

Expected payload family:

- `fault_injection_payload`

Rules:

- Controlled experiment only.
- Fault generation must derive constraints from frozen policy/schema/rules assets.
- Missing `doorbell_detected` may be used as a strict schema/fault case.

### `safe_deferral/dashboard/observation`

Expected payload family:

- `dashboard_observation_payload`

Rules:

- Dashboard observation is visibility only.
- Dashboard observation is not policy truth.
- Doorlock state shown here is observation/experiment state, not `context_schema.device_states`.

### `safe_deferral/experiment/progress`

Expected payload family:

- `experiment_progress_payload`

Rules:

- Experiment status only.
- No operational control authority.

### `safe_deferral/experiment/result`

Expected payload family:

- `result_export_payload`

Rules:

- Result artifact only.
- Must trace to scenario IDs, run IDs, and expected outcomes.

---

## 7. Future schema candidates

The following topic payload families are likely candidates for future schema formalization:

- `safe_deferral_event`
- `manual_confirmation_payload`
- `actuation_command_payload`
- `actuation_ack_payload`
- `audit_event_payload`
- `dashboard_observation_payload`
- `experiment_progress_payload`
- `result_export_payload`

Do not create these schemas casually. Add them only when implementation or evaluation needs stable machine-readable contracts.

# topic_payload_contracts.md

## MQTT Topic Payload Contracts

Status: **DRAFT**

This document explains the payload expectations for each MQTT topic family.

Current machine-readable topic registry:

- `common/mqtt/topic_registry.json`

Historical topic registry baseline:

- `common/history/mqtt/topic_registry.json`

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

- `common/schemas/policy_router_input_schema.json`

Example:

- `common/payloads/examples/policy_router_input_non_visitor.json`
- `common/payloads/examples/policy_router_input_visitor_doorbell.json`
- `common/payloads/examples/policy_router_input_paper_eval_all_modes.json` — Package A trial with all four optional `routing_metadata` experiment-mode fields set (illustrates the four orthogonal paper-eval comparison spaces).

Rules:

- Must contain `source_node_id`, `routing_metadata`, and `pure_context_payload`.
- `routing_metadata.network_status` must use the schema enum: `online`, `offline`, or `degraded`.
- `pure_context_payload.trigger_event.timestamp_ms` must be used; do not use legacy `event_timestamp_ms`.
- Button examples should use `single_click`, `double_click`, `long_press`, or `triple_hit`; do not use legacy `single_hit`.
- `pure_context_payload.environmental_context.doorbell_detected` is required.
- `routing_metadata` must not be mixed into LLM prompt context.
- RPi may publish only in controlled simulation/experiment mode.
- `routing_metadata` carries four optional experiment-mode fields (defaults apply when unset; production deployments leave them unset). These are honored only by the Class 1 intent-recovery branch (the first) and Class 2 Clarification Manager (the other three). They never enter the LLM prompt and never affect Class 0 emergency routing or validator authority. Plan refs: PR #79 (intent recovery), doc 10 §3.3 P2.3 + PR #101 (candidate source), doc 12 §14 + PR #110 (ordering), doc 12 §9 Phase 5 + PR #111 (interaction model).

| Field | Enum | Honored by | Affects |
|---|---|---|---|
| `experiment_mode` | `direct_mapping` / `rule_only` / `llm_assisted` | Mac mini Class 1 intent recovery (`_handle_class1`) | Which intent-recovery branch picks the candidate |
| `class2_candidate_source_mode` | `static_only` / `llm_assisted` | `Class2ClarificationManager.start_session` | Whether the LLM is consulted for candidate generation |
| `class2_scan_ordering_mode` | `source_order` / `deterministic` | `Class2ClarificationManager.start_session` (only when `input_mode='scanning'`) | Whether `class2_scan_ordering_rules` permutes the candidate list |
| `class2_input_mode` | `direct_select` / `scanning` | `Class2ClarificationManager.start_session` | Whether the manager presents candidates one-at-a-time (AAC scanning) or all-at-once |

### `safe_deferral/emergency/event`

Expected payload family:

- `policy_router_input_or_emergency_context`

Schema:

- `common/schemas/policy_router_input_schema.json`

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

- `common/schemas/candidate_action_schema.json`

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

- `common/schemas/validator_output_schema.json`

Example:

- `common/payloads/examples/validator_output_execute_approved_light.json`

Rules:

- Approved executable payload must stay within the frozen low-risk catalog.
- Doorlock executable payload is not allowed in the current baseline.
- Non-approved outcomes should route to safe deferral or Class 2 escalation as appropriate.
- `class_2_escalation` remains a compatibility routing label for Class 2 clarification/escalation routing, not terminal escalation only.
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

- `common/schemas/class2_notification_payload_schema.json`

Example:

- `common/payloads/examples/class_2_notification_doorlock_sensitive.json`

Rules:

- Used for Class 2 clarification notification, caregiver escalation notification, or unresolved-state notification.
- Class 2 notification is not terminal failure by itself.
- Class 2 may lead to Class 1, Class 0, Safe Deferral, or Caregiver Confirmation after confirmation, timeout/no-response, or deterministic evidence.
- `manual_confirmation_path` describes a governed review/confirm/deny/intervene path.
- `manual_confirmation_path` is not autonomous execution authority.
- Doorlock-sensitive notifications may explain a manual confirmation route, but must not bypass validator, caregiver approval, ACK, or audit boundaries.

### `safe_deferral/clarification/interaction`

Expected payload family:

- `clarification_interaction_payload`

Schema:

- `common/schemas/clarification_interaction_schema.json`

Example:

- `common/payloads/examples/clarification_interaction_two_options_pending.json` — direct-select session, single-turn (legacy/baseline).
- `common/payloads/examples/clarification_interaction_scanning_yes_first.json` — scanning session that accepted the first option, with `input_mode='scanning'` + `scan_history` + `scan_ordering_applied` (deterministic ranking ran).
- `common/payloads/examples/clarification_interaction_multi_turn_refinement.json` — multi-turn session: parent C1_LIGHTING_ASSISTANCE picked, refinement turn picked REFINE_BEDROOM, terminal CLASS_1. `refinement_history` populated.

Rules:

- Candidate choices are bounded guidance only.
- User/caregiver selection is confirmed-candidate evidence; CLASS_1 selections re-enter the Deterministic Validator with the bounded candidate and never bypass it.
- Timeout/no-response must not infer intent.
- `transition_target` must not directly authorize actuation.
- `CLASS_1` transition still requires Deterministic Validator approval.
- `CLASS_0` transition requires deterministic emergency evidence or explicit emergency confirmation.
- Doorlock authorization is not allowed through this payload.
- This payload must not be confused with `class_2_notification_payload`, `validator_output`, `actuation_command_payload`, or `pure_context_payload`.
- The record carries five optional fields recording HOW the session was conducted. All five are informational and backward-compatible (legacy single-turn direct_select records validate unchanged). None changes validator gating, low-risk catalog, or emergency normalization. Plan refs: doc 09 + PR #101 (candidate_source), doc 12 §4.4–§4.6 in `04_class2_clarification.md` (input_mode / scan_history / scan_ordering_applied), doc 11 Phase 6.0 (refinement_history).

| Field | Type | Purpose |
|---|---|---|
| `candidate_source` | enum `llm_generated` / `default_fallback` / `static_only_forced` | Provenance of the candidate set. `static_only_forced` distinguishes "runner explicitly disabled LLM" from "LLM tried and failed". |
| `input_mode` | enum `direct_select` / `scanning` | Class 2 interaction model. Absence = treated as `direct_select` for legacy records. |
| `scan_history` | array of `{option_index, candidate_id, response: yes/no/silence/dropped, elapsed_ms, input_source}` | Per-option turn log when scanning ran. Empty / absent for direct_select. |
| `scan_ordering_applied` | object `{rule_source, matched_bucket, applied_overrides, final_order}` | Recorded only when `class2_scan_ordering_mode='deterministic'` ran. |
| `refinement_history` | array of `{turn_index, parent_candidate_id, refinement_question, selected_candidate_id, selection_source, selection_timestamp_ms}` | Recorded only when multi-turn refinement (doc 11) ran. Today bounded to one entry (max one refinement turn). |

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
- Payloads containing `pure_context_payload` must obey `context_schema.json`.

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

## 7.5 Adapter-internal schemas (not on any MQTT topic)

The following schemas govern in-process payloads exchanged between Mac mini
components and **never appear on any MQTT topic**. They are listed here so
governance / verification tooling does not mistakenly treat them as wire
contracts:

- `common/schemas/class2_candidate_set_schema.json` — output of
  `LocalLlmAdapter.generate_class2_candidates()` consumed by
  `Class2ClarificationManager.start_session(...)` for Class 2
  candidate-source provenance and bounded-variability echo. The
  on-the-wire artifact for Class 2 clarification remains the
  `clarification_interaction_payload` governed by
  `clarification_interaction_schema.json` (§3 above).

These adapter-internal schemas have no publisher, no subscriber, and no
topic. They are validation contracts for in-process function-call data.

---

## 8. Future schema candidates

The following topic payload families are likely candidates for future schema formalization:

- `safe_deferral_event`
- `clarification_interaction_payload` examples and helper schemas if runtime/test needs require additional machine-readable contracts beyond `clarification_interaction_schema.json`
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

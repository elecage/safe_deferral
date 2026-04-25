# 17_payload_contract_and_registry.md

## Payload Contract and Registry

## 1. Purpose

This document defines the current payload taxonomy, ownership boundary, schema coverage, and implementation guidance for the `safe_deferral` project.

The goal is to prevent drift between:

- policy/schema assets,
- runtime payloads,
- MQTT topic-payload contracts,
- publisher/subscriber role assumptions,
- scenario fixtures,
- dashboard/test-app payloads,
- governance validation reports,
- interface-matrix alignment checks,
- topic/payload hardcoding drift reports,
- audit artifacts,
- and paper experiment descriptions.

This document is a **payload registry and interpretation guide**. It does not override the frozen policy/schema assets.

Authoritative policy/schema truth remains in:

- `common/policies/`
- `common/schemas/`

This document should be read together with:

- `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`
- `common/docs/architecture/14_system_components_outline_v2.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/payloads/README.md`

---

## 2. Why this registry is needed

The project uses several different payload families across the operational and experimental layers.

Examples:

- Policy Router input payload
- pure context payload
- trigger event payload
- environmental context payload
- device state payload
- LLM candidate action payload
- validator output payload
- Class 2 notification payload
- manual confirmation payload
- actuation ACK payload
- audit event payload
- fault injection payload
- scenario fixture payload
- dashboard observation payload
- experiment annotation payload
- governance change report
- interface-matrix alignment report
- topic-drift report
- payload validation report

These payloads must not be mixed casually.

Recent alignment work introduced `environmental_context.doorbell_detected` as a required visitor-response context field and clarified that doorlock state is not currently part of `context_schema.device_states`. This exposed the need for a single registry that explains where each payload belongs.

---

## 3. Payload authority levels

Payloads in this project are divided into three authority levels.

## 3.1 Schema-governed payloads

These payloads have explicit JSON Schema contracts under `common/schemas/`.

If a runtime payload belongs to this class, implementations should validate it strictly against the corresponding schema.

Current schema-governed payloads:

- Policy Router input payload
- normalized context envelope / pure context payload
- LLM candidate action payload
- validator output payload
- Class 2 notification payload

## 3.2 Policy/rules-governed payloads

These payloads derive behavior from policy or rules assets under `common/policies/`.

They may not always have a standalone schema, but they must follow the policy/rules contract.

Examples:

- low-risk action admissibility
- routing policy interpretation
- emergency trigger profile
- fault injection profile
- output/channel guidance

## 3.3 Experiment/runtime/governance artifact payloads

These payloads are used for evaluation, dashboard visibility, auditability, test orchestration, governance reporting, or review workflows.

They may not yet have formal frozen schemas. They must remain clearly separated from canonical policy/schema truth.

Examples:

- scenario fixture metadata
- experiment annotation
- dashboard observation state
- mock caregiver approval state
- mock ACK state
- audit summary artifact
- result export payload
- governance change report
- interface-matrix alignment report
- topic-drift report
- payload validation report

These payloads must not redefine policy truth, silently expand autonomous actuation authority, or become operational authorization mechanisms.

---

## 4. Current payload registry

| Payload family | Typical location / producer | Consumer | Governing asset | Authority level | Notes |
|---|---|---|---|---|---|
| Policy Router Input | Mac mini input adapter, integration adapter, future MQTT intake | Policy Router | `policy_router_input_schema_v1_1_1_FROZEN.json` | Schema-governed | Wrapper containing `source_node_id`, `routing_metadata`, and `pure_context_payload` |
| Routing Metadata | Mac mini input adapter | Policy Router only | `policy_router_input_schema_v1_1_1_FROZEN.json` | Schema-governed | Operational metadata. Must not be mixed directly into LLM prompt context |
| Pure Context Payload | Mac mini input adapter, RPi simulation, ESP32-derived context aggregation | Policy Router / bounded LLM path | `context_schema_v1_0_0_FROZEN.json` | Schema-governed | Only payload section that may form LLM-relevant physical/context input |
| Trigger Event | ESP32, RPi simulation, Mac mini adapter | Policy Router | `context_schema_v1_0_0_FROZEN.json` | Schema-governed | Includes event type/code/timestamp. Timestamp is for staleness and reproducibility, not LLM hallucination fuel |
| Environmental Context | ESP32 sensors, RPi simulation, Mac mini context aggregation | Policy Router / bounded LLM path | `context_schema_v1_0_0_FROZEN.json` | Schema-governed | Includes temperature, illuminance, occupancy, smoke, gas, and `doorbell_detected` |
| Device States | Context aggregator, RPi simulation | Policy Router / validator context | `context_schema_v1_0_0_FROZEN.json` | Schema-governed | Current fields: `living_room_light`, `bedroom_light`, `living_room_blind`, `tv_main`. Doorlock state is not included |
| Low-risk Action Catalog | Frozen policy asset | Validator / implementation | `low_risk_actions_v1_1_0_FROZEN.json` | Policy-governed | Authoritative autonomous Class 1 action scope |
| LLM Candidate Action | Local LLM bounded assistance path | Deterministic Validator | `candidate_action_schema_v1_0_0_FROZEN.json` | Schema-governed | Current autonomous action candidates must remain within schema and low-risk catalog |
| Validator Output | Deterministic Validator | Dispatcher / safe deferral / escalation path | `validator_output_schema_v1_1_0_FROZEN.json` | Schema-governed | Approved executable payload must remain bounded to current low-risk scope |
| Class 2 Notification Payload | Escalation service | Caregiver notification channel | `class_2_notification_payload_schema_v1_0_0_FROZEN.json` | Schema-governed | Includes summary, unresolved reason, and manual confirmation path |
| Output Profile | Notification/output layer | Notification service / UI guidance | `output_profile_v1_1_0.json` | Companion policy asset | Output/channel guidance; does not override schemas or routing policy |
| Fault Injection Profile | RPi fault injector | RPi orchestration / Mac mini policy path | `fault_injection_rules_v1_4_0_FROZEN.json` + policy/schema assets | Policy/rules-governed | Dynamic references must follow current policy/schema JSONPath contracts |
| Scenario Fixture Payload | `integration/scenarios/`, `integration/tests/data/`, future RPi fixtures | Integration runner / orchestrator | This registry + relevant schemas | Experiment artifact | Must conform to canonical schemas where embedding schema-governed payload sections |
| Experiment Annotation Payload | Scenario packs, test results, dashboard/test-app | Evaluation tools | This registry / future schema | Experiment artifact | May carry doorlock state, approval state, ACK state outside `pure_context_payload.device_states` |
| Manual Confirmation Payload / State | Caregiver confirmation backend, dashboard/test app mock | Caregiver flow / audit | Future schema recommended | Runtime / experiment artifact | Must not be treated as Class 1 autonomous executable authorization |
| Actuation ACK Payload / State | Actuator interface, validator/audit, dashboard/test app mock | Audit / closed-loop verifier | Future schema recommended | Runtime / experiment artifact | ACK is closed-loop evidence, not pure context input |
| Audit Event Payload | Mac mini services | Audit Logging Service | Current DB/audit service contract; future schema recommended | Runtime artifact | Single-writer audit path; not policy authority |
| Dashboard Observation Payload | RPi dashboard / Mac mini telemetry bridge | Human/operator dashboard | Future dashboard contract recommended | Experiment/runtime artifact | Visibility only; not policy/validator/caregiver authority |
| Result Export Payload | RPi orchestration / dashboard | Paper/evaluation analysis | Future result schema recommended | Experiment artifact | CSV/JSON summaries must trace back to canonical scenario IDs and fault IDs |
| Governance Change Report | MQTT/payload governance backend | Maintainer / review workflow | `15_interface_matrix.md` + `common/mqtt/` + `common/payloads/` | Governance artifact | Proposed changes only; not live operational authority |
| Interface-Matrix Alignment Report | Governance backend / verification script | Dashboard / maintainer / CI | `15_interface_matrix.md` | Governance/verification artifact | Evidence only; not operational authorization |
| Topic-Drift Report | Governance backend / verification script | Dashboard / maintainer / CI | `common/mqtt/` + implementation scan rules | Governance/verification artifact | Detects hardcoding drift; not policy authority |
| Payload Validation Report | Payload validator / governance backend | Dashboard / maintainer / CI | `common/schemas/` + `common/payloads/` | Governance/verification artifact | Validation evidence; not schema authority |

---

## 5. Canonical payload boundaries

## 5.1 `pure_context_payload`

`pure_context_payload` is the normalized physical/context input envelope.

It contains:

- `trigger_event`
- `environmental_context`
- `device_states`

It is governed by:

- `common/schemas/context_schema_v1_0_0_FROZEN.json`

Important rules:

1. It must not contain routing metadata.
2. It must not contain dashboard-only state.
3. It must not contain manual approval state.
4. It must not contain ACK state.
5. It must not contain out-of-schema device states.
6. It is the only current context envelope intended to ground LLM-relevant physical/context interpretation.

## 5.2 `routing_metadata`

`routing_metadata` belongs to the Policy Router input wrapper.

It may include:

- `audit_correlation_id`
- `ingest_timestamp_ms`
- `network_status`

Rules:

1. It is operational routing metadata.
2. It should not be directly mixed into LLM prompt context.
3. It may be used for safety fallback, staleness handling, audit correlation, and reproducibility.

## 5.3 `environmental_context`

`environmental_context` currently includes:

- `temperature`
- `illuminance`
- `occupancy_detected`
- `smoke_detected`
- `gas_detected`
- `doorbell_detected`

Rules:

1. `doorbell_detected` is required.
2. Non-visitor scenarios should normally set `doorbell_detected=false`.
3. Visitor-response scenarios may set `doorbell_detected=true` when a recent doorbell or visitor-arrival signal exists.
4. `doorbell_detected=true` is not doorlock unlock authorization.
5. `doorbell_detected` is not a current Class 0 emergency trigger.

## 5.4 `device_states`

Current `device_states` fields are:

- `living_room_light`
- `bedroom_light`
- `living_room_blind`
- `tv_main`

Rules:

1. Doorlock state is not currently part of `device_states`.
2. Do not insert `doorlock`, `front_door_lock`, `door_lock_state`, or similar fields into `pure_context_payload.device_states`.
3. Presence in `device_states` does not automatically imply autonomous Class 1 actuation authority.
4. Autonomous Class 1 authority is governed by the low-risk action catalog and validator schema.

---

## 6. MQTT topic and payload contract rules

MQTT topic registry entries define communication contracts, not policy authority.

Topic-to-payload mappings must remain aligned with:

- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`
- `common/docs/architecture/15_interface_matrix.md`

A topic entry may reference a payload family, schema path, and example payload, but this does not make the topic a policy or execution authority.

Rules:

1. MQTT topics are communication contracts.
2. Publisher/subscriber roles define allowed communication roles, not policy authority.
3. Topic-to-payload mappings must not silently expand the schema-governed payload boundary.
4. Runtime apps, dashboard apps, governance tooling, and experiment tools should avoid hardcoded topic or payload-contract drift where registry/configuration lookup is practical.
5. Doorlock-related topic entries must explicitly preserve manual-confirmation, ACK, audit, and dashboard-observation boundaries.
6. Doorlock-related topic entries must not imply autonomous Class 1 door-unlock authority unless future frozen policy/schema revisions explicitly promote that behavior.
7. Governance validation artifacts may report topic/payload issues, but they do not authorize operational execution.

---

## 7. Doorbell and doorlock payload rules

## 7.1 Doorbell context

Doorbell or visitor-arrival context must be represented as:

```json
{
  "environmental_context": {
    "doorbell_detected": true
  }
}
```

or:

```json
{
  "environmental_context": {
    "doorbell_detected": false
  }
}
```

depending on the scenario.

Do not invent unrelated fields such as:

```json
{
  "doorbell": "pressed",
  "visitor_present": true,
  "front_door_bell": "ringing"
}
```

unless a future schema revision explicitly introduces them.

## 7.2 Doorlock state

Doorlock state must not currently be placed inside:

```json
{
  "pure_context_payload": {
    "device_states": {
      "doorlock": "locked"
    }
  }
}
```

Current alternatives:

- experiment annotation,
- mock approval state,
- dashboard-side observation field,
- audit artifact,
- manual confirmation path internal state,
- future schema revision.

Example experiment-side representation:

```json
{
  "experiment_annotation": {
    "doorlock_state": "locked",
    "manual_approval_state": "pending",
    "ack_state": "not_dispatched"
  }
}
```

This is an experiment annotation, not part of the current pure context schema.

## 7.3 Door unlock intent

Door unlock intent may appear as an **intended interpretation label** in visitor-response evaluation.

It must not appear as a current Class 1 candidate action or validator executable payload.

Allowed interpretation use:

```json
{
  "intended_interpretation_label": "possible_unlock_intent",
  "expected_safe_outcome": "class_2_escalation_or_manual_confirmation"
}
```

Disallowed current Class 1 action use:

```json
{
  "action": "door_unlock",
  "target_device": "front_door_lock"
}
```

unless future frozen policy/schema revisions explicitly authorize it.

---

## 8. Manual confirmation, ACK, and audit payload rules

## 8.1 Manual confirmation

Manual confirmation payloads/states are not currently part of `pure_context_payload`.

They belong to a separately governed caregiver/manual-confirmation path.

They may be represented in:

- caregiver confirmation backend state,
- dashboard/test-app mock state,
- experiment annotation,
- audit event,
- future dedicated schema.

Manual confirmation must not be confused with autonomous Class 1 validator approval.

## 8.2 ACK state

ACK state is closed-loop execution evidence.

It belongs to:

- actuator interface response,
- validator/dispatcher result handling,
- audit logging,
- dashboard observation,
- experiment result artifact,
- future ACK schema.

ACK state must not be inserted into `pure_context_payload` as ordinary environmental or device context unless a future schema explicitly defines such behavior.

## 8.3 Audit payloads

Audit payloads are runtime records.

They may include summaries of:

- routing decisions,
- LLM candidate outputs,
- validator outputs,
- safe deferral decisions,
- Class 2 escalation,
- caregiver approval outcome,
- dispatch result,
- ACK result,
- final experiment outcome.

Audit records are evidence and traceability artifacts. They are not policy authority.

---

## 9. Scenario fixture and dashboard payload rules

## 9.1 Scenario fixtures

Scenario fixtures may contain schema-governed payload fragments, experiment annotations, expected outcomes, and result metadata.

Rules:

1. If a fixture contains `pure_context_payload`, that section must conform to `context_schema_v1_0_0_FROZEN.json`.
2. Every valid `environmental_context` must include `doorbell_detected`.
3. Non-visitor scenario fixtures should set `doorbell_detected=false`.
4. Visitor-response fixtures may set `doorbell_detected=true`.
5. Do not put doorlock state into `pure_context_payload.device_states`.
6. Put doorlock/approval/ACK state in experiment annotation or mock state sections.
7. Scenario fixtures are evaluation assets, not policy truth.

## 9.2 Dashboard observation payloads

Dashboard observation payloads may show:

- experiment ID,
- scenario ID,
- readiness state,
- progress state,
- `doorbell_detected` state,
- autonomous-unlock-blocked status,
- caregiver escalation state,
- manual approval state,
- ACK state,
- audit completeness,
- result summary.

Rules:

1. Dashboard observation payloads are visibility artifacts.
2. They are not policy authority.
3. They must not bypass Mac mini policy routing, validator decisions, caregiver approval, ACK verification, or audit logging.
4. If dashboard payloads carry doorlock state, that state is dashboard-side observation or experiment status, not current `device_states` context.

---

## 10. Governance payload and report rules

Governance payloads and reports support MQTT/payload inspection, validation, draft editing, review, and regression prevention.

Rules:

1. Governance dashboard UI may display topic registry state, payload validation results, publisher/subscriber role assignments, proposed-change states, interface-matrix alignment results, topic-drift warnings, and doorbell/doorlock boundary warnings.
2. Governance dashboard UI must call the governance backend for create/update/delete/validation/export operations.
3. Governance dashboard UI must not directly edit registry files.
4. Governance dashboard UI must not publish operational control topics.
5. Governance dashboard UI must not expose unrestricted actuator consoles or direct doorlock command controls.
6. Governance backend may generate reports, draft changes, validation summaries, and proposed-change exports.
7. Governance backend must not directly modify canonical policies/schemas.
8. Governance backend must not publish actuator or doorlock commands.
9. Governance backend must not spoof caregiver approval.
10. Governance backend must not override the Policy Router or Deterministic Validator.
11. Governance backend must not convert draft/proposed changes into live authority without review.
12. Governance change reports, interface-matrix alignment reports, topic-drift reports, and payload validation reports are evidence artifacts, not operational authorization mechanisms.

---

## 11. Current formal schema coverage

Current formal schemas:

- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

Current policy/rules assets:

- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/policies/output_profile_v1_1_0.json`

Candidate future schemas:

- `manual_confirmation_payload_schema_v1_0_0.json`
- `actuation_ack_payload_schema_v1_0_0.json`
- `audit_event_schema_v1_0_0.json`
- `dashboard_observation_payload_schema_v1_0_0.json`
- `experiment_annotation_schema_v1_0_0.json`
- `scenario_fixture_schema_v1_0_0.json`
- `result_export_schema_v1_0_0.json`
- `governance_change_report_schema_v1_0_0.json`
- `interface_matrix_alignment_report_schema_v1_0_0.json`
- `topic_drift_report_schema_v1_0_0.json`
- `payload_validation_report_schema_v1_0_0.json`

These future schemas should not be introduced casually. They should be added only when implementation or evaluation requires a stable machine-readable contract.

---

## 12. Payload validation recommendations

Implementations should apply validation at the correct layer.

### Mac mini

Validate:

- Policy Router input wrapper,
- pure context payload,
- candidate actions,
- validator output,
- Class 2 notification payload,
- topic-to-payload contract resolution where runtime topics are used,
- interface-matrix alignment where applicable.

Do not let Mac mini runtime accept out-of-schema context by silently expanding `device_states`.

### Raspberry Pi 5

Validate:

- generated scenario payloads,
- virtual sensor payloads,
- fault injection payloads,
- dashboard observation contracts when formalized,
- result export contracts when formalized,
- governance change reports,
- interface-matrix alignment reports,
- topic-drift reports,
- payload validation reports,
- governance backend/UI separation checks.

RPi payload generation must follow current schemas, policies, MQTT contracts, and governance boundaries, but RPi does not become policy authority.

### ESP32

ESP32 nodes should emit bounded events/states that can be normalized into schema-valid context payloads.

ESP32 should not locally reinterpret payloads into policy decisions or autonomous sensitive actuation.

### Integration tests

Integration fixtures should be checked for:

- required `doorbell_detected`,
- absence of doorlock state in current `device_states`,
- no Class 1 `door_unlock` candidate,
- no validator executable payload for doorlock,
- correct Class 2/manual confirmation expectation for sensitive outcomes,
- topic/payload contract consistency,
- interface-matrix alignment,
- topic/payload hardcoding drift,
- governance report artifacts do not create authority.

---

## 13. Non-negotiable payload rules

1. `routing_metadata` is not LLM context.
2. `pure_context_payload` must conform to `context_schema_v1_0_0_FROZEN.json`.
3. `environmental_context.doorbell_detected` is required.
4. `doorbell_detected` is visitor-response context, not doorlock authorization.
5. `doorbell_detected` is not a current emergency trigger.
6. Doorlock state is not currently part of `device_states`.
7. Manual approval state is not `pure_context_payload`.
8. ACK state is not `pure_context_payload`.
9. Dashboard observation state is not policy truth.
10. Scenario fixture metadata is not policy truth.
11. Class 1 executable payload must stay within the frozen low-risk catalog and validator schema.
12. Sensitive actuation must route through Class 2 escalation or separately governed manual confirmation with ACK and audit.
13. If a future payload needs to become authoritative, add or revise the relevant schema/policy and update experiments, prompts, README, CLAUDE, and handoff addenda together.
14. MQTT topic entries are communication contracts, not policy authority.
15. Topic-to-payload mappings must remain aligned with `common/docs/architecture/15_interface_matrix.md` and `common/mqtt/`.
16. Governance change reports, interface-matrix alignment reports, topic-drift reports, and payload validation reports are evidence artifacts, not operational authorization mechanisms.
17. Governance dashboard UI must not directly edit registry files or publish operational control topics.
18. Governance backend must not modify canonical policies/schemas, publish actuator/doorlock commands, spoof caregiver approval, override Policy Router or Deterministic Validator decisions, or convert proposed changes into live authority without review.

---

## 14. Downstream documents to keep aligned

After this registry is introduced or updated, keep the following downstream assets aligned with the payload boundaries defined here:

1. remaining architecture documents or addenda not yet reviewed after this version
2. `common/docs/required_experiments.md`
3. `common/mqtt/topic_registry_v1_0_0.json`
4. `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
5. `common/mqtt/topic_payload_contracts_v1_0_0.md`
6. `common/payloads/README.md`
7. `integration/README.md`
8. `integration/scenarios/README.md`
9. `integration/scenarios/scenario_manifest_rules.md`
10. `integration/scenarios/scenario_review_guide.md`
11. `integration/tests/README.md`
12. `rpi/docs/README.md`
13. `mac_mini/docs/README.md`
14. `esp32/docs/README.md`
15. `README.md`
16. `CLAUDE.md`
17. `common/docs/runtime/SESSION_HANDOFF.md`

The review goal is to ensure that every document uses the payload boundaries, MQTT topic-payload contract rules, and governance report boundaries defined here consistently.

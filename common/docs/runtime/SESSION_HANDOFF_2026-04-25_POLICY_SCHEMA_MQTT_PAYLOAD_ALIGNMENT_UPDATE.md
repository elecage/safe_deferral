# SESSION_HANDOFF_2026-04-25_POLICY_SCHEMA_MQTT_PAYLOAD_ALIGNMENT_UPDATE.md

## Purpose

This addendum records the latest alignment pass across architecture documents, required experiments, README/CLAUDE guidance, frozen policy/schema assets, MQTT contracts, and payload examples/templates.

This addendum supersedes older handoff wording where older notes conflict with the following current interpretation.

---

## Scope of completed work

The following areas were reviewed and updated:

1. Architecture documents `13` through `17`.
2. `common/docs/required_experiments.md`.
3. Top-level `README.md`.
4. Agent/developer guidance in `CLAUDE.md`.
5. JSON policy files under `common/policies/`.
6. JSON schema files under `common/schemas/`.
7. MQTT contract documents under `common/mqtt/`.
8. Payload examples/templates under `common/payloads/`.

The main alignment goal was to make the following interpretation consistent everywhere:

- Mac mini is the safety-critical operational edge hub.
- Raspberry Pi 5 is experiment/dashboard/orchestration/simulation/fault-injection and non-authoritative MQTT/payload governance support.
- ESP32 is the bounded physical node layer.
- LLM output is interpretation/candidate support only, not execution authority.
- Current Class 1 autonomous low-risk scope is lighting only.
- `doorbell_detected` is visitor-response context only.
- Doorlock is sensitive actuation and is not current autonomous Class 1.
- MQTT/payload governance artifacts are verification evidence only, not runtime authority.

---

## Updated architecture documents

### `13_doorlock_access_control_and_caregiver_escalation.md`

Updated to clarify:

- doorlock is a sensitive actuation domain,
- `doorbell_detected` does not authorize unlock,
- LLM must not hold final unlock authority,
- doorlock-sensitive outcomes require caregiver escalation or separately governed manual confirmation,
- ACK and local audit remain required,
- MQTT/payload governance tooling cannot create doorlock execution authority,
- governance dashboard UI and governance backend service must remain separated,
- doorlock-related MQTT topics must align with `15_interface_matrix.md`, topic registry, publisher/subscriber matrix, and topic-payload contracts.

### `14_system_components_outline_v2.md`

Updated to clarify:

- Mac mini operational hub duties,
- RPi experiment/governance support duties,
- governance backend operations,
- governance dashboard UI restrictions,
- topic registry loader / contract checker responsibilities,
- interface-matrix alignment and topic/payload drift checks,
- paper figure concepts including MQTT-aware interface matrix, topic drift check, and payload example validation.

### `15_interface_matrix.md`

Updated to act as the MQTT-aware interface contract reference.

Additions include:

- references to `13`, `16`, `17`, MQTT docs, and `common/payloads`,
- interface-matrix alignment and topic/payload drift as governance/verification checks,
- GV-8 interface-matrix alignment check,
- GV-9 topic drift check,
- governance validation artifact table,
- prohibited interfaces for UI direct registry edit, direct doorlock control, unrestricted actuator console, governance backend direct doorlock publish, and report-to-authority confusion.

### `16_system_architecture_figure.md`

Updated to clarify:

- active figure interpretation is this document, not legacy `24_final_paper_architecture_figure.md`,
- current SVG does not yet fully draw all RPi/governance flows,
- future figure should include interface-matrix alignment, topic/payload drift detection, payload validation report flow, and governance backend/UI separation validation,
- Mac mini helpers perform consistency checks but do not create authority,
- RPi governance support remains non-authoritative,
- caption and paper notes include governance validation artifacts.

### `17_payload_contract_and_registry.md`

Updated to define payload boundary and governance report boundary.

Additions include:

- MQTT topic-payload contract rules,
- governance payload/report rules,
- governance change report, interface-matrix alignment report, topic-drift report, and payload validation report in the payload registry,
- future schema candidates for governance reports,
- non-negotiable rules that MQTT topic entries and governance reports do not create policy/schema/execution authority,
- downstream documents that must remain aligned.

---

## Updated experiment baseline

### `common/docs/required_experiments.md`

Updated as the experiment baseline manifest.

Major additions:

- Communication / Payload / Governance Reference Assets section.
- Package G: `MQTT / Payload Contract and Governance Boundary Validation`.
- `FAULT_CONTRACT_DRIFT_01` as a governance/verification fault profile.
- Topic/payload drift detection as a required robustness metric.
- Doorlock-sensitive package now includes topic contract boundary verification and governance tooling non-authority verification.
- Table 6 for MQTT/payload contract and governance-boundary validation.
- Governance metrics:
  - Topic Registry Consistency Rate,
  - Payload Contract Resolution Rate,
  - Payload Example Validation Pass Rate,
  - Topic/Payload Drift Detection Rate,
  - Governance Boundary Violation Count,
  - Unauthorized Control Publish Attempt Block Rate.

Important interpretation:

- Package G is system-integrity and governance-boundary verification.
- Package G is not operational actuation validation.
- Governance reports are evidence only.

---

## Updated top-level and agent guidance

### `README.md`

Updated to include:

- MQTT/payload contract governance as a core objective,
- `common/mqtt/` and `common/payloads/` in repository structure,
- Package G verification scenario,
- governance dashboard UI/backend separation,
- governance reports as evidence artifacts only,
- key reference documents.

### `CLAUDE.md`

Updated to include:

- active architecture reference moved from old `24_final...` to `16_system_architecture_figure.md`,
- `13`, `15`, `16`, `17` added as high-priority references,
- `12_prompts_mqtt_payload_governance.md` added to prompt structure,
- MQTT/payload governance interpretation,
- governance dashboard UI/backend separation,
- Package G implementation/verification criteria,
- coding rules for registry/configuration lookup where practical,
- absolute prohibitions against governance UI/backend becoming control authority,
- document conflict priority order.

Historical note:

- `common/docs/architecture/24_final_paper_architecture_figure.md` is no longer active architecture reference.
- Active architecture-figure interpretation is `common/docs/architecture/16_system_architecture_figure.md`.

---

## Updated policies and schemas

### Updated policy files

- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/output_profile_v1_1_0.json`

### Updated schema file

- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

### Important policy/schema changes

`fault_injection_rules_v1_4_0_FROZEN.json` now includes:

- MQTT/payload governance dependencies,
- dynamic references to MQTT and architecture docs,
- `FAULT_CONTRACT_DRIFT_01`,
- expected outcome `governance_verification_fail_no_runtime_authority`,
- explicit separation between governance/verification faults and operational control faults.

`policy_table_v1_1_2_FROZEN.json` now includes:

- MQTT/payload governance report boundary note.

`low_risk_actions_v1_1_0_FROZEN.json` now includes:

- doorlock boundary note,
- doorbell/visitor-arrival context cannot promote doorlock into low-risk catalog,
- governance reports cannot expand low-risk action authority.

`output_profile_v1_1_0.json` now includes:

- `governance_validation` as a recommended event group,
- governance reports as evidence artifacts only.

`class_2_notification_payload_schema_v1_0_0_FROZEN.json` now clarifies:

- Class 2 payload may describe escalation/manual confirmation for sensitive actuation,
- `manual_confirmation_path` is a review route only,
- it does not create execution authority or bypass validator/caregiver approval/ACK/audit boundaries.

---

## Updated MQTT contract layer

Updated files:

- `common/mqtt/README.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`

### MQTT layer interpretation

`common/mqtt/` defines communication contracts only.

It does not create:

- policy authority,
- schema authority,
- validator authority,
- caregiver approval authority,
- audit authority,
- actuator authority,
- doorlock execution authority.

### New or clarified MQTT concepts

- Package G validation coverage.
- Referenced example payload existence checks.
- Schema-governed payload validation checks.
- Interface-matrix alignment checks.
- Topic/payload hardcoding drift detection.
- Governance backend/UI separation checks.
- Governance report non-authority checks.
- `FAULT_CONTRACT_DRIFT_01` as governance/verification only.

### Governance validation artifacts

The following artifacts are now explicitly described:

- interface-matrix alignment report,
- topic-drift report,
- payload validation report,
- governance backend/UI separation report,
- proposed-change review report.

They are evidence artifacts only and are not operational MQTT control topics.

---

## Updated payload example/template layer

Updated files and directories:

- `common/payloads/README.md`
- `common/payloads/examples/`
- `common/payloads/templates/scenario_fixture_template.json`

### Fixed schema mismatches

The following legacy/example mismatches were fixed:

- `network_status: "local"` or `"local_controlled_simulation"` changed to valid schema enum `"online"`.
- legacy `single_hit` changed to `single_click`.
- legacy `event_timestamp_ms` changed to `timestamp_ms`.
- candidate action example changed from `action` to `proposed_action`.

### Added or aligned payload examples

The payload layer now includes examples for:

- non-visitor policy-router input,
- visitor doorbell policy-router input,
- emergency temperature policy-router input,
- light-on candidate action,
- approved light validator output,
- Class 2 doorlock-sensitive notification,
- safe deferral request with two options,
- manual confirmation doorlock approved example,
- actuation command light-on example,
- actuation ACK success example,
- audit route decision example,
- fault injection missing doorbell context example,
- dashboard observation doorlock-sensitive example,
- experiment progress running example,
- result export summary example,
- scenario fixture template.

### Payload boundary reminders

- Payload examples are references, not policy truth.
- Schema-governed example sections must validate against `common/schemas/`.
- Every valid context example must include `environmental_context.doorbell_detected`.
- Doorlock state must not be inserted into `pure_context_payload.device_states`.
- Manual approval state and ACK state must not be inserted into `pure_context_payload`.
- Dashboard observation state is visibility only.
- Governance reports are evidence only.

---

## Current non-negotiable interpretation after this pass

1. Current autonomous Class 1 remains lighting only.
2. `doorbell_detected` is required visitor-response context, not unlock authorization.
3. Doorlock remains sensitive actuation, not autonomous Class 1.
4. Doorlock state is excluded from current `context_schema.device_states`.
5. LLM candidate action output is not execution authority.
6. Validator approved executable payload remains constrained to the low-risk catalog.
7. Class 2 `manual_confirmation_path` is a review route, not execution authority.
8. MQTT topic entries are communication contracts, not policy authority.
9. Topic-payload mappings are contract references, not schema or execution authority.
10. Governance reports are evidence artifacts only.
11. Governance dashboard UI must not directly edit registry files or publish operational control topics.
12. Governance backend must not directly modify canonical policies/schemas, publish actuator/doorlock commands, spoof caregiver approval, override Policy Router/Deterministic Validator, or convert proposed changes into live authority without review.
13. `FAULT_CONTRACT_DRIFT_01` is governance/verification only and must not be interpreted as an operational actuation path.

---

## Implementation reminders for next session

When implementing MQTT-facing runtime, dashboard, governance, or experiment tooling, check the following first:

1. `common/docs/architecture/15_interface_matrix.md`
2. `common/docs/architecture/17_payload_contract_and_registry.md`
3. `common/mqtt/topic_registry_v1_0_0.json`
4. `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
5. `common/mqtt/topic_payload_contracts_v1_0_0.md`
6. `common/payloads/README.md`
7. `common/docs/required_experiments.md`
8. `CLAUDE.md`

For Package G, implement checks for:

- topic registry readability,
- publisher/subscriber matrix consistency,
- topic-to-payload contract resolution,
- referenced example payload existence,
- schema validation for schema-governed examples,
- interface-matrix alignment,
- topic/payload hardcoding drift detection,
- governance backend/UI separation,
- governance report non-authority.

---

## Known next alignment targets

The following areas should be reviewed next if continuing the alignment pass:

1. `integration/README.md`
2. `integration/scenarios/README.md`
3. `integration/scenarios/scenario_manifest_rules.md`
4. `integration/scenarios/scenario_review_guide.md`
5. `integration/tests/README.md` or test runner files if present
6. `mac_mini/docs/README.md`
7. `rpi/docs/README.md`
8. `esp32/docs/README.md`

Focus for next alignment:

- ensure scenario fixtures use `timestamp_ms`, not legacy `event_timestamp_ms`,
- ensure button events use `single_click`, not legacy `single_hit`,
- ensure every valid context payload includes `doorbell_detected`,
- ensure MQTT topic strings are registry-aligned where practical,
- ensure Package G and `FAULT_CONTRACT_DRIFT_01` are reflected in integration docs,
- ensure dashboard/test app/orchestration do not become operational authority.

---

## Representative commits from this pass

Important commits created during this pass include:

- architecture/document alignment commits for `13` through `17`, README, CLAUDE, and required experiments,
- policy/schema alignment commits including `FAULT_CONTRACT_DRIFT_01`,
- MQTT/payload contract and example alignment commits,
- payload example creation commits.

Use Git history on `main` around 2026-04-25 for exact commit list if needed.

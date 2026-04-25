# common/mqtt

## Purpose

This directory stores MQTT topic, publisher/subscriber, and topic-payload contract references for the `safe_deferral` project.

It is intended to make MQTT communication explicit and reviewable across:

- Mac mini operational services,
- Raspberry Pi experiment/dashboard/orchestration support,
- ESP32 bounded physical nodes,
- optional measurement/export tooling,
- integration tests and scenario replay,
- MQTT/payload governance backend and dashboard UI,
- Package G system-integrity and governance-boundary validation.

This directory does **not** override canonical policies or schemas.

Authoritative sources remain:

- `common/policies/`
- `common/schemas/`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/required_experiments.md`

---

## Current files

- `topic_registry_v1_0_0.json`
  - Machine-readable MQTT topic registry.
  - Lists topic patterns, publisher roles, subscriber roles, payload family, schema/example references, authority level, QoS, retain behavior, and notes.

- `publisher_subscriber_matrix_v1_0_0.md`
  - Human-readable publisher/subscriber matrix.
  - Useful for implementation planning, review, debugging, and governance UI rendering.

- `topic_payload_contracts_v1_0_0.md`
  - Human-readable topic-to-payload contract notes.
  - Explains payload boundaries, schema references, example references, and forbidden interpretations.

---

## Authority boundary

MQTT topics do not create policy authority by themselves.

In particular:

- dashboard topics are visibility artifacts, not policy truth;
- audit topics are evidence/traceability artifacts, not policy truth;
- RPi simulation/fault topics are experiment support, not operational authority;
- caregiver confirmation topics must not be confused with Class 1 autonomous validator approval;
- actuation ACK topics are closed-loop evidence, not pure context input;
- topic registry entries are communication contracts, not routing or execution authority;
- topic-payload mappings are contract references, not schema authority;
- interface-matrix alignment reports, topic-drift reports, payload validation reports, and proposed-change reports are governance/verification evidence, not operational authorization mechanisms.

---

## Non-negotiable MQTT rules

1. Topic contracts must identify allowed publishers and subscribers.
2. Every topic must identify its payload family.
3. Schema-governed payloads must reference the relevant schema under `common/schemas/`.
4. Example payloads should reference files under `common/payloads/examples/` when available.
5. Dashboard/test-app topics must not bypass Mac mini policy routing, deterministic validation, caregiver approval, ACK verification, or audit logging.
6. RPi may publish simulation/fault topics only in controlled experiment/simulation mode.
7. `environmental_context.doorbell_detected` remains context only and must not authorize autonomous doorlock control.
8. Doorlock-related sensitive outcomes must route through Class 2 escalation or separately governed manual confirmation with ACK and audit.
9. Governance dashboard UI must call the governance backend for create/update/delete/validation/export operations.
10. Governance dashboard UI must not directly edit registry files, publish operational control topics, expose unrestricted actuator consoles, or expose direct doorlock command controls.
11. Governance backend must not directly modify canonical policies/schemas, publish actuator or doorlock commands, spoof caregiver approval, override the Policy Router or Deterministic Validator, or convert draft/proposed changes into live authority without review.
12. `FAULT_CONTRACT_DRIFT_01` and related Package G checks are governance/verification checks, not operational fault paths.

---

## Package G validation coverage

The MQTT/payload governance validation package should check at least:

- topic registry readability,
- publisher/subscriber matrix consistency,
- topic-to-payload contract resolution,
- referenced example payload existence,
- schema validation for schema-governed examples,
- interface-matrix alignment,
- topic/payload hardcoding drift detection,
- governance backend/UI separation,
- governance report non-authority.

Recommended evidence artifacts:

- interface-matrix alignment report,
- topic-drift report,
- payload validation report,
- governance backend/UI separation report,
- proposed-change review report.

These reports are evidence artifacts only.

---

## Future dashboard / web app note

A future MQTT/payload management web app or dashboard may be useful for:

- browsing topic contracts,
- checking publisher/subscriber coverage,
- validating example payloads,
- visualizing live topic traffic during experiments,
- detecting schema drift,
- detecting topic/payload hardcoding drift,
- auditing stale or unauthorized topics,
- exporting topic/payload coverage reports,
- exporting proposed-change review reports.

However, such a dashboard must remain a **governance, inspection, and validation tool**.
It must not become policy authority, validator authority, caregiver approval authority, audit authority, direct actuator control authority, or doorlock execution authority.

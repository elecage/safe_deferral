# common/mqtt

## Purpose

This directory stores MQTT topic, publisher/subscriber, and topic-payload contract references for the `safe_deferral` project.

It is intended to make MQTT communication explicit and reviewable across:

- Mac mini operational services,
- Raspberry Pi experiment/dashboard/orchestration support,
- ESP32 bounded physical nodes,
- optional measurement/export tooling,
- integration tests and scenario replay.

This directory does **not** override canonical policies or schemas.

Authoritative sources remain:

- `common/policies/`
- `common/schemas/`
- `common/docs/architecture/17_payload_contract_and_registry.md`

---

## Current files

- `topic_registry_v1_0_0.json`
  - Machine-readable MQTT topic registry.
  - Lists topic patterns, publisher roles, subscriber roles, payload family, schema/example references, authority level, QoS, retain behavior, and notes.

- `publisher_subscriber_matrix_v1_0_0.md`
  - Human-readable publisher/subscriber matrix.
  - Useful for implementation planning, review, and debugging.

- `topic_payload_contracts_v1_0_0.md`
  - Human-readable topic-to-payload contract notes.
  - Explains payload boundaries and forbidden interpretations.

---

## Authority boundary

MQTT topics do not create policy authority by themselves.

In particular:

- dashboard topics are visibility artifacts, not policy truth;
- audit topics are evidence/traceability artifacts, not policy truth;
- RPi simulation/fault topics are experiment support, not operational authority;
- caregiver confirmation topics must not be confused with Class 1 autonomous validator approval;
- actuation ACK topics are closed-loop evidence, not pure context input.

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

---

## Future dashboard / web app note

A future MQTT/payload management web app or dashboard may be useful for:

- browsing topic contracts,
- checking publisher/subscriber coverage,
- validating example payloads,
- visualizing live topic traffic during experiments,
- detecting schema drift,
- auditing stale or unauthorized topics,
- exporting topic/payload coverage reports.

However, such a dashboard must remain a **governance, inspection, and validation tool**.
It must not become policy authority, validator authority, caregiver approval authority, or direct actuator control authority.

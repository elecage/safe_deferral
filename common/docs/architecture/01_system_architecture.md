# System Architecture

## 1. Purpose

This document summarizes the active system architecture for `safe_deferral`.
It replaces the need to start from multiple older topology, deployment, figure,
and component-outline notes.

## 2. System Goal

The system supports limited-input users by interpreting context and bounded user
signals, routing requests through deterministic policy and validation, and
executing only approved low-risk actions autonomously.

The architecture is designed so that LLM output can help with interpretation and
guidance without becoming execution authority.

## 3. Top-Level Roles

| Area | Current role |
| --- | --- |
| User | Provides limited input, selections, confirmations, and contextual intent |
| Caregiver | Handles sensitive escalation and manual confirmation paths |
| Actual physical nodes | Bounded physical input, environmental context, emergency events, lighting, warning, and sensitive-interface nodes |
| Mac mini operational hub | Primary policy routing, deterministic validation, local LLM runtime, audit, notification, MQTT broker/runtime services |
| Raspberry Pi 5 | Experiment-side simulation, dashboard, fault injection, replay, result export, non-authoritative governance support |
| Optional timing node | Independent measurement support for latency and timing validation when needed |

## 4. Mac Mini Operational Hub

The Mac mini is the safety-critical operational edge hub. It owns:

- MQTT ingestion and normalized state intake,
- context/runtime state aggregation,
- local LLM adapter for bounded candidate generation and guidance,
- Policy Router execution,
- Deterministic Validator execution,
- safe deferral and Class 2 clarification coordination,
- caregiver notification integration,
- approved low-risk dispatcher path,
- audit logging,
- runtime deployment of canonical policy/schema/MQTT/payload assets.

The Mac mini may consume synchronized or deployed runtime copies, but canonical
truth remains in `common/`.

## 5. Raspberry Pi 5 Support Layer

The Raspberry Pi is not the operational policy hub. It supports:

- controlled simulation and replay,
- experiment-only virtual node hosting,
- fault injection,
- experiment orchestration,
- dashboard and result visualization,
- result export,
- non-authoritative MQTT/payload governance tooling,
- mirrored runtime asset checks.

RPi-hosted virtual nodes may emulate:

- bounded input nodes,
- environmental sensor nodes,
- emergency sensor/event nodes,
- doorbell or visitor-arrival context nodes,
- fault-injection publishers,
- dashboard observation publishers,
- mock actuator/ACK nodes for closed-loop experiments.

These virtual nodes are experiment sources and observers. They may publish
controlled MQTT traffic only through registry-aligned topics and payload
families, and they must identify their simulated source identity in scenario,
audit, or result artifacts.

RPi tooling must not replace Mac mini policy authority, validator authority,
caregiver approval authority, audit authority, actuator authority, or doorlock
execution authority.

## 6. Actual Physical Nodes

Actual physical nodes may be implemented with ESP32 or another bounded embedded
platform. They may provide:

- bounded user input,
- environmental context,
- emergency event input,
- lighting actuator behavior,
- warning output,
- visitor/doorbell context,
- representative sensitive actuator interfaces when explicitly governed.

Actual physical nodes must not locally reinterpret sensitive behavior as
autonomous Class 1 authority. Doorlock-sensitive work remains governed by the
safety boundaries in `02_safety_and_authority_boundaries.md`.

## 7. Closed-Loop Operational Path

The normal operational flow is:

1. Input/context/emergency event enters through actual physical nodes,
   RPi-hosted virtual nodes, controlled RPi simulation, or Mac mini ingestion.
2. Mac mini aggregates runtime state and normalizes the policy-router input.
3. LLM may produce bounded candidate guidance where applicable.
4. Policy Router classifies the route.
5. Deterministic Validator checks admissibility for executable low-risk actions.
6. Approved low-risk commands are dispatched.
7. Actuator ACK and audit evidence are recorded.
8. Ambiguous, sensitive, stale, missing, or conflicting cases move to Class 2,
   safe deferral, caregiver escalation, or emergency handling as appropriate.

## 8. Figure and Layout References

Current figure assets live under:

- `common/docs/architecture/figures/`
- `common/docs/architecture/figures/OV/specs/`

The figure is illustrative. If a figure conflicts with canonical policy, schema,
MQTT, payload, or safety-boundary documents, the canonical assets and active
architecture documents control.

## 9. Source Notes

This active summary consolidates the stable material from:

- `common/docs/archive/architecture_legacy/01_installation_target_classification.md`
- `common/docs/archive/architecture_legacy/02_mac_mini_build_sequence.md`
- `common/docs/archive/architecture_legacy/03_deployment_structure.md`
- `common/docs/archive/architecture_legacy/04_project_directory_structure.md`
- `common/docs/archive/architecture_legacy/14_system_components_outline_v2.md`
- `common/docs/archive/architecture_legacy/16_system_architecture_figure.md`

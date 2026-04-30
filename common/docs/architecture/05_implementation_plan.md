# Implementation Plan

## 1. Purpose

This document summarizes the implementation state and remaining work.

## 2. Implementation State (as of 2026-04-30)

The core implementation is complete. All major RPi experiment-side services
and the Mac mini operational hub components are implemented and tested.

### RPi Experiment Layer — Complete

| Component | Module | Status |
|---|---|---|
| ExperimentManager | `rpi/code/experiment_manager/` | ✅ |
| ResultStore | `rpi/code/result_store/` | ✅ |
| ScenarioManager | `rpi/code/scenario_manager/` | ✅ |
| VirtualNodeManager | `rpi/code/virtual_node_manager/` | ✅ |
| ObservationStore | `rpi/code/observation_store.py` | ✅ |
| MqttStatusMonitor | `rpi/code/mqtt_status/` | ✅ |
| PreflightManager | `rpi/code/preflight/` | ✅ |
| GovernanceBackend + UI | `rpi/code/governance/` | ✅ |
| Experiment Package A~G (definitions, fault profiles) | `rpi/code/experiment_package/` | ✅ |
| PackageRunner (trial orchestration) | `rpi/code/experiment_package/runner.py` | ✅ |
| TrialStore + metrics | `rpi/code/experiment_package/trial_store.py` | ✅ |
| NodePresenceRegistry | `rpi/code/node_presence/` | ✅ |
| Dashboard (port 8888) + Browser UI | `rpi/code/dashboard/` | ✅ |
| Entry point | `rpi/code/main.py` | ✅ |

### Mac Mini Operational Hub — Complete

Policy Router, Deterministic Validator, Class 2 Clarification Manager,
low-risk dispatcher, ACK handler, caregiver escalation, audit logging,
MQTT intake, LLM adapter, and Telegram notification are implemented
under `mac_mini/`.

### Physical Nodes — Partial

ESP32 bounded input, context, emergency event, doorbell/visitor context,
and actuator nodes are implemented under `esp32/`. Physical devices
publish to `safe_deferral/node/presence` on connect (online) and
via MQTT LWT on disconnect (offline).

### STM32 Timing Node — Optional/Not started

USB-serial (CP2102 → /dev/ttyUSB0) out-of-band GPIO latency measurement.
Per `required_experiments.md §6.5`: "바람직하다" (desirable, not required).
Software MQTT pipeline latency (ingest_timestamp_ms → snapshot_ts_ms)
is paper-valid when STM32 is absent. Label results accordingly.

## 3. Canonical Asset Baseline

The active architecture document set:

1. `00_architecture_index.md`
2. `01_system_architecture.md`
3. `02_safety_and_authority_boundaries.md`
4. `03_payload_and_mqtt_contracts.md`
5. `04_class2_clarification.md`
6. `05_implementation_plan.md` (this file)
7. `06_deployment_and_scripts.md`
8. `07_scenarios_and_evaluation.md`
9. `08_system_structure_figure_revision_plan.md`

Canonical policy/schema/MQTT assets:

- `common/policies/policy_table.json`
- `common/policies/low_risk_actions.json`
- `common/policies/fault_injection_rules.json`
- `common/schemas/context_schema.json`
- `common/schemas/validator_output_schema.json`
- `common/mqtt/topic_registry.json`

## 4. Experiment Package System

Packages A~G measure different paper claims. Each package runs trials
via the PackageRunner, which:

1. Applies a FaultProfile transform to a base payload from a VirtualNode.
2. Embeds `audit_correlation_id` in `routing_metadata`.
3. Publishes via VirtualNodeManager (registry-validated topics only).
4. Polls ObservationStore for the echoed correlation_id (15 s timeout).
5. Records result in TrialStore with observed route_class, validation_status,
   pass/fail verdict, and latency_ms.

FaultProfile thresholds are loaded dynamically from `policy_table.json`
via `RpiAssetLoader` — no hardcoded thresholds.

Fault profiles (9 total):

| ID | Type | Expected outcome |
|---|---|---|
| FAULT_EMERGENCY_01_TEMP | Temperature above threshold | CLASS_0 |
| FAULT_STALENESS_01 | Stale timestamp | safe_deferral |
| FAULT_SCHEMA_INVALID_01 | Missing required field | safe_deferral |
| FAULT_TRIGGER_MISMATCH_01 | Trigger mismatch | CLASS_2 or safe_deferral |
| FAULT_CONFLICT_01 | Simultaneous conflict | CLASS_2 |
| FAULT_GHOST_PRESS_01 | Ghost press | safe_deferral |
| FAULT_ENV_SENSOR_FAULT_01 | Faulty environment sensor | safe_deferral |
| FAULT_DOORBELL_MISSING_01 | Missing doorbell context | CLASS_2 or safe_deferral |
| FAULT_CONTRACT_DRIFT_01 | Unregistered topic (governance test) | Governance artifact |

## 5. Node Presence System

Both physical (ESP32) and virtual (RPi) nodes publish to
`safe_deferral/node/presence` (retain=true, qos=1).

- ESP32: explicit online on connect; offline via MQTT LWT.
- VirtualNodeManager: online on `start_node()`; offline on `stop_node()/delete_node()`.

NodePresenceRegistry receives all messages and tracks status, source,
node_type, and staleness (2-minute threshold) for all nodes uniformly.

PreflightManager uses NodePresenceRegistry for two optional (non-blocking) checks:
`physical_nodes_present` and `stm32_present`. Absence of either → DEGRADED,
not BLOCKED; experiments may proceed with clearly labelled limitations.

## 6. Remaining Work

- **STM32 timing support** (optional): USB-serial latency capture module
  under `rpi/code/stm32_timing/` with pyserial.
- **ESP32 LWT wiring**: confirm LWT payload format matches presence schema
  in all ESP32 firmware builds.
- **NodePresenceRegistry unit tests**: add `test_node_presence_registry_*`
  cases to `rpi/code/tests/test_rpi_components.py`.
- **E2E experiment validation**: run a full package trial sequence with
  Mac mini connected and verify correlation_id matching end-to-end.
- **Paper result export**: run packages A/B/C with sufficient trials,
  export Markdown tables from `/package_runs/{id}/export/markdown`.

## 7. Source Notes

This document consolidates the current implementation state. Historical
cleanup planning is archived under:

- `common/docs/archive/documentation_cleanup/`
- `common/docs/archive/architecture_legacy/`

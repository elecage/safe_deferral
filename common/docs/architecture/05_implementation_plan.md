# Implementation Plan

## 1. Purpose

This document summarizes the active implementation and cleanup sequence.

## 2. Current Cleanup State

The current phase is documentation and contract cleanup. Python code has been
removed for now so that the canonical policy, schema, MQTT, payload, scenario,
and architecture baseline can stabilize before implementation resumes.

Completed cleanup work:

- documentation and asset restructure plan recorded,
- canonical asset rename map recorded,
- active policy/schema/MQTT assets renamed to stable filenames,
- superseded policy/schema/MQTT assets moved under `common/history/`,
- `common/asset_manifest.json` added,
- active references migrated to canonical asset names,
- Python files removed for the current cleanup phase.

## 3. Current Priority

The current priority is to reduce architecture-document duplication and establish
the active document set:

1. `00_architecture_index.md`
2. `01_system_architecture.md`
3. `02_safety_and_authority_boundaries.md`
4. `03_payload_and_mqtt_contracts.md`
5. `04_class2_clarification.md`
6. `05_implementation_plan.md`
7. `06_deployment_and_scripts.md`
8. `07_scenarios_and_evaluation.md`

## 4. Next Cleanup Steps

1. Update root guidance so `README.md` and `CLAUDE.md` point to the active
   architecture index.
2. Simplify `CLAUDE.md` into a compact coding-agent operating guide.
3. Decide whether older `01` through `20` architecture notes should move to
   `common/docs/archive/architecture_legacy/` or remain in place as legacy source
   notes.
4. Consolidate scenario guidance so `integration/scenarios/` remains the active
   scenario-contract area without duplicating architecture prose.
5. Update `common/docs/runtime/SESSION_HANDOFF.md` after the cleanup batch is
   complete.

## 5. Implementation Resume Gate

Before Python or service implementation is reintroduced, confirm:

- active docs reference only canonical asset names,
- active scenario JSON uses canonical asset names,
- `common/asset_manifest.json` reflects active and historical asset locations,
- `CLAUDE.md` is short enough to function as a coding-agent guide,
- Class 2 clarification topic and schema references are aligned,
- doorbell and doorlock boundaries are stated once in the active safety document,
- MQTT/payload governance is clearly non-authoritative.

## 6. Future Implementation Work

When implementation resumes, the likely order is:

1. Mac mini runtime skeleton and policy-router input handling.
2. Deterministic validator and low-risk action dispatch.
3. Class 2 clarification manager.
4. MQTT topic registry loader and payload validation support.
5. Audit and ACK path.
6. RPi controlled simulation, fault injection, dashboard, and result export.
7. ESP32 bounded input/context/actuator sample firmware.
8. Integration scenario runner and measurement support.

## 7. Source Notes

This active summary consolidates the stable material from:

- `06_implementation_plan.md`
- `07_task_breakdown.md`
- `08_additional_required_work.md`
- `09_recommended_next_steps.md`
- `00_documentation_and_asset_restructure_plan.md`

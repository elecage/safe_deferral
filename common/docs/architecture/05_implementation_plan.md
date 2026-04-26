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
- active architecture document set established,
- legacy architecture notes marked as source notes,
- scenario and experiment guidance aligned with the active architecture set,
- `CLAUDE.md` simplified into a compact coding-agent operating guide,
- prompt set reorganized by implementation target category,
- Python files removed for the current cleanup phase,
- runtime handoff index updated with the cleanup addendum.

## 3. Current Baseline

The active architecture document set is:

1. `00_architecture_index.md`
2. `01_system_architecture.md`
3. `02_safety_and_authority_boundaries.md`
4. `03_payload_and_mqtt_contracts.md`
5. `04_class2_clarification.md`
6. `05_implementation_plan.md`
7. `06_deployment_and_scripts.md`
8. `07_scenarios_and_evaluation.md`

## 4. Remaining Cleanup Steps

The documentation and contract cleanup baseline is now stable enough for a final
review or a deliberate next pass.

Remaining cleanup should be handled as separate, intentional batches:

1. Optional archive move for legacy architecture notes if preserving them in
   place becomes distracting.
2. Reintroduction of implementation code after the resume gate below is
   explicitly satisfied.

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

1. Mac mini runtime skeleton and operational intake.
2. Policy Router, Deterministic Validator, Class 2 Clarification Manager,
   low-risk dispatcher, ACK, caregiver, and audit path.
3. RPi experiment manager, virtual-node manager, virtual fault-injection and
   behavior manager, scenario manager, MQTT/interface status manager, result
   store, and web dashboard.
4. Actual physical nodes for bounded input, context, visitor context, lighting,
   feedback, and state reporting.
5. Experiment-only physical nodes for gas, smoke/fire, fall, warning, and
   doorlock-sensitive cases. Fault injection remains virtual by default.
6. STM32 out-of-band timing, synchronization, readiness, and measurement export
   support.

## 7. Source Notes

This active summary consolidates the stable material from:

- `06_implementation_plan.md`
- `07_task_breakdown.md`
- `08_additional_required_work.md`
- `09_recommended_next_steps.md`
- `00_documentation_and_asset_restructure_plan.md`

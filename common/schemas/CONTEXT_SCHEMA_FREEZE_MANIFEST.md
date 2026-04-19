# Phase 0 Freeze Manifest for context_schema

## Asset
- File: `context_schema_v1_0_0_FROZEN.json`
- Freeze status: **FROZEN**
- Frozen at: 2026-03-28 13:46:28 UTC

## Purpose
This file is the frozen Phase 0 context-envelope schema used as a shared implementation contract for:

- Policy Router input normalization
- LLM-safe context preparation
- Raspberry Pi 5 fault injection
- Scenario orchestration
- Verification utilities
- Schema validation during integration tests

## Freeze Decision
This schema is approved as the baseline context schema for the current prototype generation.
It must not be modified in place.

## Change Control Rules
- Do not rename keys directly in this file.
- Do not add new required fields directly in this file.
- Do not change enum semantics directly in this file.
- Any structural change requires a new versioned file, for example:
  - `context_schema_v1_0_1.json`
  - `context_schema_v1_1_0.json`

## Operational Notes
- `timestamp_ms` is preserved for Policy Router freshness validation and fault-injection reproducibility.
- `timestamp_ms` must be excluded or masked during LLM prompt composition.
- This schema intentionally excludes system/network evaluation metadata.
- System/network metadata should be layered in `policy_router_input_schema.json`, not in this file.

## Recommended Companion Frozen Assets
- `policy_table_v1_1_2_FROZEN.json`
- `candidate_action_schema.json`
- `policy_router_input_schema.json`
- `validator_output_schema.json`
- `fault_injection_rules.json`

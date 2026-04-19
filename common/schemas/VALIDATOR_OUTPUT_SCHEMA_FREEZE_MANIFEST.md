# Phase 0 Freeze Manifest for validator_output_schema

## Asset
- File: `validator_output_schema_v1_0_0_FROZEN.json`
- Freeze status: **FROZEN**
- Frozen at: 2026-03-28 14:07:34 UTC

## Purpose
This file is the frozen Phase 0 validator-output schema used as the implementation contract for:
- Deterministic Validator output formatting
- Actuator Dispatcher handoff
- iCR Handler handoff
- Class 2 escalation handoff
- Audit logging
- Integration testing

## Freeze Decision
This schema is approved as the baseline validator-output schema for the current prototype generation.
It must not be modified in place.

## Change Control Rules
- Do not rename keys directly in this file.
- Do not change validation_status enums directly in this file.
- Do not change cross-field constraints directly in this file.
- Any structural change requires a new versioned file.

## Recommended Companion Frozen Assets
- `policy_table_v1_1_2_FROZEN.json`
- `context_schema_v1_0_0_FROZEN.json`
- `candidate_action_schema_v1_0_0_FROZEN.json`
- `policy_router_input_schema.json`
- `fault_injection_rules.json`

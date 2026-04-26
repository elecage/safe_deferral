# SESSION_HANDOFF_2026-04-26_DOCUMENTATION_CONTRACT_CLEANUP_UPDATE.md

## Purpose

This addendum records the documentation and contract cleanup batch completed on
2026-04-26. It supersedes older handoff wording when older handoffs refer to
versioned active asset filenames, active `FROZEN` filenames, deleted Python
verification tools, or the older numbered architecture documents as the primary
read path.

## Cleanup Summary

The active repository baseline now uses stable canonical asset filenames without
version strings or `FROZEN` in active policy, schema, and MQTT paths.

Current canonical assets are indexed from:

- `common/asset_manifest.json`
- `common/docs/architecture/00_architecture_index.md`
- `CLAUDE.md`

Superseded policy, schema, and MQTT assets live under `common/history/`.
Historical runtime handoff files remain under `common/docs/runtime/` and may
retain old references as historical record.

## Active Architecture Baseline

Use this active architecture read path for current work:

1. `common/docs/architecture/00_architecture_index.md`
2. `common/docs/architecture/01_system_architecture.md`
3. `common/docs/architecture/02_safety_and_authority_boundaries.md`
4. `common/docs/architecture/03_payload_and_mqtt_contracts.md`
5. `common/docs/architecture/04_class2_clarification.md`
6. `common/docs/architecture/05_implementation_plan.md`
7. `common/docs/architecture/06_deployment_and_scripts.md`
8. `common/docs/architecture/07_scenarios_and_evaluation.md`

The older `01` through `20` architecture notes remain in place as legacy/source
notes and carry banners pointing back to the active index. New work should
update the active architecture set first.

## Scenario And Experiment Baseline

`integration/scenarios/` remains the active scenario-contract area. Active
scenario JSON, scenario Markdown, fixtures, measurement documents, and
experiment registry references should use canonical asset paths.

Class 2 clarification work should use:

- topic: `safe_deferral/clarification/interaction`
- schema: `common/schemas/clarification_interaction_schema.json`
- payload family: `clarification_interaction_payload`

RPi virtual nodes, monitoring, scenario orchestration, fault injection,
dashboard support, and result export are experiment support functions. They do
not create policy, validator, caregiver approval, actuator, or doorlock
authority.

## Python Code Status

Python implementation and verifier code was removed during this cleanup phase.
Do not refer to deleted Python runners, verifiers, or comparators as active
tools. Reintroduce implementation code only after the documentation, scenario,
and canonical asset baseline is stable.

## Prompt Set Status

Prompt documents are not yet fully consolidated. For now:

- `common/docs/architecture/12_prompts.md` is the prompt-set index.
- `12_prompts_core_system.md`,
  `12_prompts_mqtt_payload_governance.md`, and
  `12_prompts_nodes_and_evaluation.md` are legacy/source prompt notes.
- Prompt cleanup should be handled as a later deliberate pass, with the active
  architecture and canonical assets treated as the source of truth.

## Safety And Authority Reminders

- LLM output is candidate guidance only.
- Current autonomous Class 1 execution is limited to the canonical low-risk
  lighting catalog in `common/policies/low_risk_actions.json`.
- `doorbell_detected` is required context for visitor-response interpretation
  but is not doorlock authorization.
- Doorlock remains a sensitive actuation case outside autonomous Class 1 unless
  future canonical policy/schema changes explicitly grant that authority.
- MQTT topics, payload examples, dashboard observations, governance reports,
  experiment fixtures, and deployment-local files do not create operational
  authority.

## Validation Performed

The cleanup batch was validated with:

- active-reference scans for versioned and `FROZEN` asset filename patterns,
- JSON and YAML parse checks,
- `git diff --check`,
- confirmation that no `.py` files remain in the repository.

## Local Commit Trail

This cleanup was recorded in local commits, including:

- `6410648 docs: plan documentation and asset cleanup`
- `29a8c52 docs: define canonical asset rename map`
- `cd750e1 chore: rename canonical policy schema and mqtt assets`
- `1871ae3 docs: migrate active references to canonical assets`
- `9dbda17 docs: consolidate architecture and experiment guidance`
- `60056c9 docs: mark legacy architecture notes`
- `d258161 docs: align scenarios and experiments with active architecture`
- `9d609e9 docs: simplify coding agent guidance`

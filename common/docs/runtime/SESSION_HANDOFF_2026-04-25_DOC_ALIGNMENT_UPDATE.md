# SESSION_HANDOFF_2026-04-25_DOC_ALIGNMENT_UPDATE.md

## Purpose

This handoff records the documentation-alignment work completed after the policy/schema alignment pass.

Read after:

- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_POLICY_SCHEMA_ALIGNMENT_UPDATE.md`

This file captures the latest decisions and repository updates for:

- `CLAUDE.md`
- `README.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-24_DASHBOARD_TEST_APP_AND_ORCHESTRATION_UPDATE.md`

This handoff intentionally does **not** rewrite the full master `SESSION_HANDOFF.md`. The master handoff is long and contains historical implementation/runtime notes. A full master consolidation should be done as a separate controlled cleanup pass.

---

## 1. Current authoritative interpretation

### Mac mini

Mac mini is the **safety-critical operational edge hub**.

Its role includes:

- MQTT/state intake
- context aggregation
- local LLM reasoning
- policy routing
- deterministic validation
- context-integrity safe deferral handling
- caregiver escalation/approval handling
- ACK/audit logging
- telemetry, audit-summary, and control-state topic exposure for the Raspberry Pi 5 dashboard

Mac mini should not be interpreted as the experiment dashboard host under the current architecture.

### Raspberry Pi 5

Raspberry Pi 5 is the **experiment-side support region and dashboard host**.

Its role includes:

- Monitoring / Experiment Dashboard
- scenario orchestration
- simulation/replay
- fault injection
- virtual node driving
- progress/status publication
- result summary
- graph/CSV export
- evaluation artifact generation

The RPi-hosted dashboard is a support-side visibility and experiment-operations console. It is **not** policy authority, validator authority, caregiver approval authority, or the primary operational hub.

### ESP32

ESP32 remains the field-side bounded physical node layer for bounded input, sensing, emergency/event detection, and actuator/warning interfaces.

---

## 2. Current Class 1 and sensitive-actuation boundary

Current Class 1 autonomous low-risk execution remains limited to the authoritative low-risk catalog:

- `light_on` → `living_room_light`
- `light_on` → `bedroom_light`
- `light_off` → `living_room_light`
- `light_off` → `bedroom_light`

The authoritative source is:

- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`

Doorlock control, door opening, blinds, TV, gas valve, stove, medication device, mobility device, and other sensitive or non-catalog actions are **not** Class 1 autonomous low-risk actions in the current baseline.

Doorlock may be used as a representative sensitive-actuation evaluation case, but it must not be:

- emitted as a Class 1 LLM candidate action,
- approved as `validator_output_schema.executable_payload`, or
- treated as autonomous low-risk execution.

Sensitive actuation requests must route to Class 2 escalation or a separately governed manual confirmation path.

---

## 3. Documentation files updated

### 3.1 `CLAUDE.md`

Commit:

- `d583307eb829aa6608668685fc6c7f32b306951a`

Main changes:

- Replaced the older Mac-mini-centered dashboard interpretation with the current RPi-hosted dashboard interpretation.
- Clarified that Mac mini is the safety-critical operational edge hub.
- Clarified that Raspberry Pi 5 hosts the experiment and monitoring dashboard.
- Added dashboard responsibilities: experiment selection, preflight readiness visibility, status visibility, progress monitoring, result summary, graph/CSV/evaluation artifact export.
- Clarified that the dashboard is not policy authority, validator authority, caregiver approval authority, or the primary operational hub.
- Strengthened doorlock/sensitive-actuation boundaries.
- Clarified that doorlock must not be added to `candidate_action_schema` or `validator_output_schema.executable_payload` as autonomous low-risk execution.
- Added `SESSION_HANDOFF_2026-04-25_POLICY_SCHEMA_ALIGNMENT_UPDATE.md` to the handoff addendum list.
- Updated recommended read order to include `24_final_paper_architecture_figure.md` and `01_installation_target_classification.md`.
- Reworded the FROZEN-file rule: FROZEN files must not be modified arbitrarily, but policy/schema inconsistencies or final architecture baseline mismatches may be corrected with explicit review records and commit rationale.

---

### 3.2 Dashboard/test-app/orchestration addendum

File:

- `common/docs/runtime/SESSION_HANDOFF_2026-04-24_DASHBOARD_TEST_APP_AND_ORCHESTRATION_UPDATE.md`

Commit:

- `f8b096b5232f50695556b47f77c6c3a43f5b7eea`

Main changes:

- Added that the document was realigned with the later decision that the dashboard is Raspberry Pi 5-hosted.
- Replaced the earlier Mac mini dashboard-host interpretation.
- Reframed dashboard as Raspberry Pi 5-hosted experiment operations and monitoring console.
- Reframed Mac mini as safety-critical operational edge hub.
- Reframed Raspberry Pi 5 as dashboard/orchestration/simulation/replay/fault-injection/result-publication support region.
- Added that the dashboard consumes Mac mini operational telemetry/audit/control-state data but is not the authority.
- Added policy/schema boundary notes for doorlock-sensitive orchestration.
- Added a `Superseded interpretation` section explaining that earlier Mac mini dashboard-host wording is superseded.

---

### 3.3 `README.md`

Commit:

- `b728cffdbf960636a954e03a7bf412087a80120d`

Main changes:

- Added a `Current Safety Boundary` section.
- Explicitly listed current Class 1 autonomous low-risk action combinations.
- Identified `common/policies/low_risk_actions_v1_1_0_FROZEN.json` as the authoritative low-risk source.
- Clarified that doorlock, blinds, TV, gas valve, stove, medication device, mobility device, and other sensitive/non-catalog actions are not Class 1 autonomous low-risk actions.
- Clarified that doorlock may be a representative sensitive-actuation evaluation case but must not be emitted as a Class 1 LLM candidate or approved as validator executable payload.
- Updated Class 1 and Class 2 explanations to reflect current policy/schema boundaries.
- Updated caregiver escalation explanation: `manual_confirmation_path` is not itself execution authority.
- Updated experimental infrastructure interpretation: Mac mini is the safety-critical operational hub and Raspberry Pi 5 is the experiment/dashboard support region.
- Updated repository structure so `rpi/` includes experiment/dashboard runtime.

---

## 4. Handoff-family handling decision

The `SESSION_HANDOFF` family should not be aggressively rewritten midstream.

Rationale:

- `SESSION_HANDOFF.md` is long and contains historical runtime, implementation, and verification notes.
- Several addenda already record milestone-specific changes.
- Full consolidation risks accidentally losing useful history or reintroducing stale assumptions.

Preferred approach:

1. Keep the master handoff as a long-running summary for now.
2. Add topic/date-specific addenda for major updates.
3. After core README/CLAUDE/dashboard docs are aligned, perform a separate master consolidation pass.
4. During consolidation, preserve history but mark superseded interpretations clearly.

This document is part of that addendum strategy.

---

## 5. Addenda that should be read together

Future sessions should read these addenda together when dealing with architecture, dashboard, policy/schema, or sensitive-actuation work:

- `common/docs/runtime/SESSION_HANDOFF_2026-04-24_PROMPT_REFACTOR_AND_EVAL_UPDATE.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-24_DASHBOARD_TEST_APP_AND_ORCHESTRATION_UPDATE.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_POLICY_SCHEMA_ALIGNMENT_UPDATE.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_DOC_ALIGNMENT_UPDATE.md`

The most recent two are especially important:

- `SESSION_HANDOFF_2026-04-25_POLICY_SCHEMA_ALIGNMENT_UPDATE.md`
- `SESSION_HANDOFF_2026-04-25_DOC_ALIGNMENT_UPDATE.md`

Together, they record the current policy/schema and documentation alignment state.

---

## 6. Current consistency state

After this documentation pass, the following files are aligned with the current interpretation:

- `README.md`
- `CLAUDE.md`
- `common/docs/architecture/01_installation_target_classification.md`
- `common/docs/architecture/24_final_paper_architecture_figure.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-24_DASHBOARD_TEST_APP_AND_ORCHESTRATION_UPDATE.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_POLICY_SCHEMA_ALIGNMENT_UPDATE.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_DOC_ALIGNMENT_UPDATE.md`
- all reviewed policy/schema files listed in the policy/schema alignment handoff

The master `SESSION_HANDOFF.md` still contains older historical wording and should be treated as useful but not fully consolidated with the latest addenda.

If conflict exists between the master handoff and this addendum, prefer this newer addendum for dashboard placement and sensitive-actuation boundaries.

---

## 7. Remaining recommended cleanup

### 7.1 Master handoff consolidation

Recommended later cleanup:

- Update `common/docs/runtime/SESSION_HANDOFF.md` so it clearly references the latest addenda.
- Mark older Mac mini dashboard-host interpretations as superseded.
- Add a short current-state section summarizing:
  - RPi dashboard placement
  - Mac mini operational hub role
  - current Class 1 low-risk scope
  - sensitive-actuation routing boundary
  - latest policy/schema alignment

Do not attempt this casually. The file is long and contains historical implementation notes.

### 7.2 Search for stale dashboard wording

Future session should search the repository for stale phrases such as:

- `Mac mini = dashboard`
- `Mac mini centered on UI/control`
- `Raspberry Pi does not necessarily need to host a UI`
- `dashboard UI or dashboard-facing integration`

### 7.3 Check prompt documents

Priority files:

- `common/docs/architecture/12_prompts.md`
- `common/docs/architecture/12_prompts_core_system.md`
- `common/docs/architecture/12_prompts_nodes_and_evaluation.md`

### 7.4 Check doorlock-specific architecture doc

Review:

- `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`

Check especially that it does not imply direct Class 1 autonomous door unlock.

---

## 8. Non-negotiable interpretation for next work

1. Class 1 autonomous execution remains limited to the frozen light-control low-risk catalog.
2. Doorlock and other sensitive actuation must not be added to LLM candidate schema or validator executable payload without a deliberate future frozen policy revision.
3. `manual_confirmation_path` is a review/intervention route, not an execution-authority field.
4. Mac mini is the operational safety-critical edge hub.
5. Raspberry Pi 5 hosts the experiment and monitoring dashboard.
6. The RPi dashboard is support-side visibility/experiment control, not policy authority.
7. Dashboard, test app, and scenario orchestration must preserve policy/schema authority boundaries.

---

## 9. Recommended next task

The next highest-value task is to search and review the prompt and doorlock-specific architecture documents for stale wording.

Recommended order:

1. `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`
2. `common/docs/architecture/12_prompts.md`
3. `common/docs/architecture/12_prompts_core_system.md`
4. `common/docs/architecture/12_prompts_nodes_and_evaluation.md`

Only after those are checked should the master `SESSION_HANDOFF.md` be consolidated.

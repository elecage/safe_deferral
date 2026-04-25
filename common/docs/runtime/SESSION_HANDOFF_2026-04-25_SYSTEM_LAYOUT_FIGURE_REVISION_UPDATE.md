# SESSION_HANDOFF_2026-04-25_SYSTEM_LAYOUT_FIGURE_REVISION_UPDATE.md

Date: 2026-04-25
Scope: paper-oriented system layout SVG and architecture-document alignment
Status: Figure revision Phase F1 through F7 completed; original SVG replaced; related architecture docs aligned

## 1. Purpose

This addendum records the completed system-layout paper-figure revision and the follow-up alignment updates to the architecture documents.

The active paper-oriented system block diagram is now:

- `common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg`

The figure has been updated from the reviewed `paper_ready` draft and should be treated as the current active system architecture figure for paper writing and architecture discussion.

## 2. Primary references

Read these together for figure interpretation:

- `common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg`
- `common/docs/architecture/14_system_components_outline_v2.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/runtime/SESSION_HANDOFF.md`

The earlier planning document remains available for process history:

- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_SYSTEM_LAYOUT_FIGURE_REVISION_PLAN.md`

This update document supersedes the planning document for current figure status.

## 3. Completed figure-revision workflow

The original SVG was not overwritten during review phases. The following draft SVGs were created under:

- `common/docs/architecture/figures/drafts/`

Draft sequence:

1. `system_layout_final_macmini_only_lshape_revA_title_boundary.svg`
2. `system_layout_final_macmini_only_lshape_revB_rpi_boundary.svg`
3. `system_layout_final_macmini_only_lshape_revC_control_boundary.svg`
4. `system_layout_final_macmini_only_lshape_revD_esp32_boundary.svg`
5. `system_layout_final_macmini_only_lshape_revE_governance_support.svg`
6. `system_layout_final_macmini_only_lshape_revF_contract_checking.svg`
7. `system_layout_final_macmini_only_lshape_paper_ready.svg`

After review, the `paper_ready` draft was applied to:

- `common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg`

## 4. Completed commits

### Planning and draft generation

1. `16c4f65abd70e5ca6b0f7541079e442088459fd4` — `docs: add system layout figure revision plan`
2. `a939074e4e0d32434f309e4bee4f34151326b087` — `docs: index system layout figure revision plan`
3. `7b19873f91324aaa444061ae573f886f7777a4d2` — `docs: add revA system layout figure draft`
4. `636494bd05ca736a6504746c218521cbbad3ecaa` — `docs: add revB system layout figure draft`
5. `2cd33385a2f3eb64ea78a48809a36b41e232b5c8` — `docs: add revC system layout figure draft`
6. `cf4aadd5e43ca8b72246dcad5a320c3bc274892b` — `docs: add revD system layout figure draft`
7. `a3cf56cfc5da299d93308dffde3f4c9ca071f182` — `docs: add revE system layout figure draft`
8. `2057f72924f9b28ebb8e79eb2d0dfca69afda64f` — `docs: add revF system layout figure draft`
9. `3e84ace250921ae6064c7aa1be89a312daaa1a69` — `docs: add paper-ready system layout figure draft`

### Original figure replacement and document alignment

10. `e29edd741f4bd5ec42d70d85221313c5e61e73bf` — `docs: update system layout paper figure`
11. `721ed6f3d76d002e92fdd69bbe981bc3c874adf6` — `docs: align component outline with paper figure`
12. `33f3bb6f2a4c19d951cd1e54cdc456107eeba0c7` — `docs: align interface matrix with paper figure`
13. `6ef4b4580659a0eef89f07b1a4ef99b958f356f6` — `docs: align architecture figure interpretation`

## 5. Current active figure interpretation

The active SVG now represents the following high-level architecture:

- ESP32 device layer as bounded physical nodes.
- User bounded input and voice-guided interaction.
- Field-side context, emergency, and bounded actuator-interface nodes.
- Mac mini as the operational edge hub.
- Registry-aware MQTT ingestion / state intake.
- Context and runtime-state aggregation.
- Local LLM reasoning for intent recovery, explanation, and clarification support.
- Policy Router + Deterministic Validator as the final admissibility boundary.
- Approved low-risk actuation as Class 1 bounded execution, currently lighting only.
- Safe Deferral and Clarification Management.
- Caregiver Escalation.
- Caregiver Approval for governed manual dispatch.
- Local ACK + Audit Logging.
- Raspberry Pi 5 as non-authoritative monitoring, orchestration, governance-check, and result-publication support.
- Raspberry Pi Progress / Result / Governance Reports.

## 6. Non-negotiable boundaries preserved by the figure

1. Mac mini remains the safety-critical operational edge hub.
2. Raspberry Pi remains non-authoritative experiment, monitoring, orchestration, governance-check, and result-publication support.
3. ESP32 remains bounded physical node / bounded actuator-interfacing infrastructure.
4. The local LLM does not hold execution authority.
5. Policy Router and Deterministic Validator may be visually grouped, but deterministic validation remains the final admissibility boundary.
6. Class 1 autonomous low-risk execution remains currently lighting only.
7. Doorlock-sensitive behavior is not represented as autonomous Class 1 execution.
8. Caregiver approval does not directly drive actuator hardware. Sensitive execution is interpreted as `Caregiver Approval -> Governed Manual Dispatcher -> Actuator Interface Nodes`.
9. MQTT/payload governance and registry-aware intake are support/verification/communication-consistency mechanisms, not operational authorization mechanisms.
10. RPi dashboard observation and governance reports are visibility/evidence artifacts, not policy truth.
11. `doorbell_detected` remains visitor-response context only and does not authorize autonomous doorlock control.

## 7. Key wording changes in the active SVG

### Title and subtitle

The figure title now uses paper-oriented wording:

```text
Privacy-Aware Edge Smart-Home Architecture with Safe Deferral
```

The subtitle now describes role separation:

```text
Mac mini hosts local reasoning, deterministic validation, caregiver-mediated sensitive actuation, TTS, ACK handling, and audit logging; Raspberry Pi provides non-authoritative experiment and monitoring support.
```

### Raspberry Pi boundary

The RPi dashboard now uses:

```text
approval-status visibility only
```

The RPi support label now includes:

```text
non-authoritative monitoring,
orchestration, governance checks,
and result publication
```

The RPi result/report block now uses:

```text
Progress / Result /
Governance Reports
```

### Mac mini control boundary

The policy/validation block now uses:

```text
Policy Router +
Deterministic Validator
```

and describes:

```text
final admissibility boundary
```

### Low-risk boundary

The low-risk block now states:

```text
Class 1 bounded execution
currently lighting only
```

### Sensitive-action boundary

The caregiver approval block now states:

```text
approval or denial for
governed manual dispatch
```

### ESP32 boundary

The actuator interface block now states:

```text
lighting and governed
sensitive-action interface
```

The ESP32 layer description now states:

```text
bounded actuator interfacing
```

### MQTT intake

The Mac mini MQTT intake block now states:

```text
receives field-side events and
registry-aware MQTT intake
```

## 8. Architecture-document updates completed

### `14_system_components_outline_v2.md`

Updated to align with the active figure:

- Added registry-aware MQTT intake to Mac mini MQTT Ingestion / State Intake.
- Replaced autonomous-looking ESP32 doorlock wording with governed sensitive-action interface / bounded actuator interfacing language.
- Added compact-figure grouping note for Policy Router + Deterministic Validator.
- Clarified that deterministic validation remains the final admissibility boundary.
- Clarified Approved Low-Risk Actuation as currently lighting only.
- Added approval-status visibility only to the RPi dashboard description.
- Renamed progress/result support to Progress / Result / Governance Reports.
- Added governed manual dispatch to sensitive-actuation path.
- Updated paper-figure concept list and conceptual distinction sections.

### `15_interface_matrix.md`

Updated to align with the active figure:

- Added review-note clarification that `safe_deferral/context/input` is a field-side or controlled-simulation input plane.
- Clarified that Mac mini primarily ingests/aggregates `safe_deferral/context/input` rather than acting as its ordinary field-side publisher.
- Updated compact topic coverage for `safe_deferral/context/input` publishers:
  - `esp32.bounded_input_node`
  - `esp32.context_node`
  - `rpi.simulation_runtime_controlled_mode`
- Split sensitive actuation row into:
  - `AC-2a`: Caregiver Approval -> Governed Manual Dispatcher
  - `AC-2b`: Governed Manual Dispatcher -> Actuator Interface Nodes
- Added direct Caregiver Approval -> Actuator path as a prohibited/misleading interface unless governed manual dispatch is included.
- Updated experiment support destination wording to Progress / Result / Governance Reports.
- Updated actuation command publisher wording to include governed manual dispatcher.
- Added compact figure grouping note for Policy Router + Deterministic Validator.

### `16_system_architecture_figure.md`

Updated to align with the active figure:

- Declares the active SVG as the current paper-oriented architecture figure.
- Lists what the current SVG compactly represents.
- Distinguishes compactly represented items from support/governance flows not fully drawn.
- Adds registry-aware MQTT intake to the Mac mini interpretation.
- Adds governed manual dispatch handling to the Mac mini and sensitive path interpretation.
- Adds RPi approval-status visibility only and Progress / Result / Governance Reports.
- Adds field-side publisher interpretation for `safe_deferral/context/input`.
- Updates figure-caption drafts to include governed manual dispatch and non-authoritative governance-report support.
- Updates paper interpretation notes and final summary.

## 9. Current document consistency status

The following files should now be treated as mutually aligned:

- `common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg`
- `common/docs/architecture/14_system_components_outline_v2.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`

Current aligned interpretation:

```text
ESP32 = bounded physical node / bounded actuator interfacing
Mac mini = operational edge hub / registry-aware intake / deterministic validation
RPi = non-authoritative monitoring, orchestration, governance checks, result publication
Class 1 autonomous execution = currently lighting only
Sensitive action = caregiver approval + governed manual dispatch
MQTT/payload governance = validation/report/support, not execution authority
```

## 10. Known remaining caveats

1. The SVG is a compact paper figure. It does not fully draw every Raspberry Pi support-layer, governance backend, dashboard UI, payload manager, publisher/subscriber role manager, or drift-report flow.
2. Detailed governance/backend flows remain textual in `14`, `15`, and `16` until a separate support/governance figure is created.
3. The RPi-to-other-layer connection lines remain intentionally omitted or compacted in the current figure.
4. The `figures/drafts/` files are review artifacts and should not be treated as the active figure.
5. The active figure path is the non-draft SVG under `common/docs/architecture/figures/`.

## 11. Next likely work items

1. If needed, create a separate detailed MQTT/payload governance support figure.
2. If needed, create a separate sequence diagram for governed manual dispatch.
3. If the paper needs a simplified monochrome or journal-style version, produce it as a new draft first.
4. If the figure is exported to PNG/PDF, keep the SVG as the editable source of truth.
5. If future policy/schema changes expand Class 1 low-risk actions or add doorlock state to context schema, update the figure, `14`, `15`, `16`, `17`, policies/schemas, required experiments, and runtime handoff together.

# SESSION_HANDOFF_2026-04-25_SYSTEM_LAYOUT_FIGURE_REVISION_PLAN.md

Date: 2026-04-25
Scope: paper-oriented system layout SVG revision
Status: Planning baseline before figure edits

## 1. Target figure

Primary SVG under review:

- `common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg`

Primary architecture references:

- `common/docs/architecture/14_system_components_outline_v2.md`
- `common/docs/architecture/15_interface_matrix.md`

Related boundaries:

- `common/docs/runtime/SESSION_HANDOFF.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_ESP32_SCRIPT_ALIGNMENT_UPDATE.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_RPI_SCRIPT_ALIGNMENT_UPDATE.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_MAC_MINI_INSTALL_CONFIG_VERIFY_ALIGNMENT_UPDATE.md`

## 2. Purpose

This document freezes the planned revision process for the paper-oriented system block diagram before any SVG changes are applied.

The goal is to revise the figure so that it is suitable for paper use and remains aligned with the current architecture interpretation.

The revision should not change project authority boundaries. It should only improve figure wording, clarity, and consistency.

## 3. Non-negotiable figure interpretation

The figure must preserve the following system boundaries:

1. Mac mini is the safety-critical operational edge hub.
2. Raspberry Pi 5 is a non-authoritative experiment, monitoring, orchestration, simulation, replay, fault-injection, result-publication, and governance-check support layer.
3. ESP32 is a bounded physical node layer.
4. The local LLM does not hold execution authority.
5. Policy routing and deterministic validation remain the control boundary for admissibility.
6. Class 1 autonomous low-risk actuation remains limited to the current frozen low-risk catalog, effectively lighting actions in the current baseline.
7. Doorlock-related paths are sensitive and must not appear as autonomous Class 1 execution.
8. Caregiver approval must be represented as part of a governed manual/sensitive-action path, not as unrestricted direct actuator control.
9. MQTT/payload governance and interface-matrix checks are support/verification functions, not operational authorization mechanisms.
10. `doorbell_detected` is visitor-response context only and must not be visually or textually implied as emergency evidence or unlock authorization.

## 4. Review findings driving the plan

The current SVG is broadly aligned with the architecture, but the following issues should be corrected before paper use:

1. Title/subtitle/footer include drawing-process language such as `L-Shaped Boundary`, `requested orthogonal path`, and `final paper figure`.
2. Raspberry Pi dashboard text includes `caregiver-state visibility`, which can be misread as caregiver approval authority.
3. Raspberry Pi support layer does not explicitly say `non-authoritative`.
4. Raspberry Pi governance/report support is not visible or is underrepresented.
5. `Policy Routing + Validation` visually compresses two important roles without clearly saying deterministic validation is the final admissibility boundary.
6. `Approved Low-Risk Actuation Path` does not explicitly say the current baseline is lighting-only.
7. ESP32 `doorlock-sensitive path` text may look like an ESP32 doorlock execution authority.
8. `Caregiver Approval -> Actuator Interface Nodes` can be misread as direct caregiver-to-actuator control without a governed manual dispatch path.
9. Mac mini MQTT/payload registry or contract-checking support is not visible, although it may be represented compactly rather than as a full separate block.

## 5. Revision workflow rule

Each figure edit phase should produce a separate review SVG before replacing the original.

Do not overwrite the original SVG until the user approves the final revision.

Recommended draft directory:

- `common/docs/architecture/figures/drafts/`

Recommended draft filenames:

- `system_layout_final_macmini_only_lshape_revA_title_boundary.svg`
- `system_layout_final_macmini_only_lshape_revB_rpi_boundary.svg`
- `system_layout_final_macmini_only_lshape_revC_control_boundary.svg`
- `system_layout_final_macmini_only_lshape_revD_esp32_boundary.svg`
- `system_layout_final_macmini_only_lshape_revE_governance_support.svg`
- `system_layout_final_macmini_only_lshape_revF_contract_checking.svg`
- `system_layout_final_macmini_only_lshape_paper_ready.svg`

Each phase should follow this loop:

1. Apply one narrowly scoped figure change.
2. Save a new draft SVG file.
3. Provide the user with a download/review link.
4. Wait for user review before applying the next phase.
5. Only after final approval, replace the original SVG and commit the final change.

## 6. Phase F1 — Paper title, subtitle, and footer cleanup

Target:

- top title
- subtitle
- bottom footer text

Problematic current wording:

```text
System Layout with Mac mini L-Shaped Boundary
Caregiver Approval → Actuator is redrawn to follow the requested orthogonal path...
This final paper figure includes...
requested orthogonal caregiver-approval execution path
```

Planned replacement title:

```text
Privacy-Aware Edge Smart-Home Architecture with Safe Deferral
```

Planned replacement subtitle:

```text
Mac mini hosts local reasoning, deterministic validation, caregiver-mediated sensitive actuation, TTS, ACK handling, and audit logging; Raspberry Pi provides non-authoritative experiment and monitoring support.
```

Planned replacement footer:

```text
Raspberry Pi support is non-authoritative; operational control, validation, caregiver-mediated execution, ACK handling, and audit remain on the Mac mini edge hub.
```

Draft output:

- `common/docs/architecture/figures/drafts/system_layout_final_macmini_only_lshape_revA_title_boundary.svg`

User review points:

- Is the title suitable for a paper figure?
- Is the subtitle too long?
- Does the footer duplicate what should be in the paper caption?

## 7. Phase F2 — Raspberry Pi non-authority wording

Targets:

- Raspberry Pi dashboard text
- Raspberry Pi layer label text

Problematic current phrase:

```text
caregiver-state visibility
```

Planned dashboard wording:

```text
runtime status, event view,
approval-status visibility only,
and experiment monitoring
```

Planned Raspberry Pi label wording:

```text
non-authoritative monitoring,
orchestration, governance checks,
and result publication
```

Draft output:

- `common/docs/architecture/figures/drafts/system_layout_final_macmini_only_lshape_revB_rpi_boundary.svg`

User review points:

- Does Raspberry Pi read clearly as a support layer only?
- Does `approval-status visibility only` avoid implying approval authority?
- Does the text still fit visually?

## 8. Phase F3 — Control and validation boundary clarification

Targets:

- `Policy Routing + Validation`
- `Approved Low-Risk Actuation Path`
- `Caregiver Approval`

Planned policy block wording:

```text
Policy Router +
Deterministic Validator
deterministic routing and
final admissibility boundary
```

Planned low-risk actuation wording:

```text
Approved Low-Risk
Actuation Path
Class 1 bounded execution
currently lighting only
```

Alternative low-risk wording if space is tight:

```text
Class 1 bounded execution
for approved lighting actions
```

Planned caregiver approval wording:

```text
Caregiver Approval
approval or denial for
governed manual dispatch
```

Draft output:

- `common/docs/architecture/figures/drafts/system_layout_final_macmini_only_lshape_revC_control_boundary.svg`

User review points:

- Does deterministic validation appear as the final execution boundary?
- Does low-risk actuation avoid implying doorlock inclusion?
- Does caregiver approval avoid looking like unrestricted direct actuator control?

## 9. Phase F4 — ESP32 bounded actuator wording

Target:

- ESP32 `Actuator Interface Nodes` block
- optional ESP32 layer footer text

Problematic current wording:

```text
lighting and representative
doorlock-sensitive path
```

Planned wording:

```text
lighting and governed
sensitive-action interface
```

Alternative wording:

```text
lighting and bounded
sensitive-action interface
```

Optional ESP32 layer footer wording:

```text
field-side bounded input, sensing,
emergency detection, and
bounded actuator interfacing
```

Draft output:

- `common/docs/architecture/figures/drafts/system_layout_final_macmini_only_lshape_revD_esp32_boundary.svg`

User review points:

- Does ESP32 still represent actuator interfacing?
- Does it avoid implying autonomous doorlock authority?

## 10. Phase F5 — Raspberry Pi governance/report support compression

Target:

- Raspberry Pi `Progress / Result Publication` block or nearby text

Current wording:

```text
Progress / Result
Publication
progress visibility, summaries,
and experiment artifacts
```

Planned wording:

```text
Progress / Result /
Governance Reports
progress, summaries,
validation reports,
and experiment artifacts
```

Alternative wording:

```text
Progress / Result
and Governance Reports
progress visibility, summaries,
topic/payload validation,
and experiment artifacts
```

Draft output:

- `common/docs/architecture/figures/drafts/system_layout_final_macmini_only_lshape_revE_governance_support.svg`

User review points:

- Does governance support appear as support/reporting rather than authority?
- Does the block remain readable?

## 11. Phase F6 — Mac mini MQTT/payload contract checking representation

This phase is optional and should be reviewed carefully to avoid overloading the figure.

Target option A:

- no SVG change; leave contract checking to the text and caption.

Target option B, preferred minimal change:

Modify `MQTT Ingestion / State Intake` helper text from:

```text
receives field-side input,
state, emergency, and ACK events
```

To:

```text
receives field-side events and
registry-aware MQTT intake
```

Target option C, more explicit but more visually complex:

Add a small Mac mini support block:

```text
MQTT / Payload
Contract Checking
registry loading,
schema validation,
and drift support
```

Draft output:

- `common/docs/architecture/figures/drafts/system_layout_final_macmini_only_lshape_revF_contract_checking.svg`

User review points:

- Is registry/payload support important enough to show in the figure?
- Does the figure become too crowded?

## 12. Phase F7 — Final paper-ready SVG

Target final review file:

- `common/docs/architecture/figures/drafts/system_layout_final_macmini_only_lshape_paper_ready.svg`

Final replacement target after approval:

- `common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg`

Final checklist:

- [ ] No drawing-process wording remains.
- [ ] Raspberry Pi is explicitly non-authoritative.
- [ ] ESP32 is explicitly bounded.
- [ ] Mac mini is operational authority host.
- [ ] LLM does not appear to have actuation authority.
- [ ] Policy Router + Deterministic Validator boundary is clear.
- [ ] Low-risk path does not imply doorlock inclusion.
- [ ] Caregiver approval is shown as governed manual dispatch.
- [ ] ACK + Audit remain Mac mini hub-side functions.
- [ ] Governance support appears as validation/reporting/support, not control authority.
- [ ] Doorbell context is not represented as unlock authorization.

## 13. Document-side follow-up notes

Potential later updates to `14_system_components_outline_v2.md`:

- Add a compact-paper-figure note that RPi governance-related components may be collapsed into a single non-authoritative support/report block.
- Clarify that the MQTT/Payload Governance Backend may be represented inside the RPi support layer in compact figures unless explicitly deployed elsewhere.

Potential later updates to `15_interface_matrix.md`:

- Revisit the `safe_deferral/context/input` primary publisher entry. The current table lists `mac_mini.context_aggregator` as a primary publisher; a more natural operational interpretation may be `esp32.bounded_input_node`, `esp32.context_node`, and controlled RPi simulation publishers.
- Consider splitting `Caregiver Approval -> Actuator Interface Nodes` into `Caregiver Approval -> Governed Manual Dispatcher -> Actuator Interface Nodes`, or explicitly naming the governed manual dispatcher in the row.
- Add a note that compact paper figures may visually group Policy Router and Deterministic Validator, provided deterministic validation remains the final admissibility boundary.

These document-side changes should be handled separately from the SVG review loop unless the user explicitly requests simultaneous updates.

## 14. Frozen decision

This plan freezes the intended paper-figure revision strategy before editing the SVG. The next work item should begin with Phase F1 and produce a downloadable draft SVG for user review before any further changes are applied.

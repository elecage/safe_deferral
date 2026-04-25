# OV Style Guide

## 1. Purpose

This style guide defines the visual grammar for scenario-level Operational View (OV) figures under:

```text
common/docs/architecture/figures/OV/
```

The goal is to keep all scenario figures visually consistent, technically clear, and safe from misleading authority implications.

---

## 2. Canvas and layout

Use a 16:9 canvas.

Recommended working size:

```text
1920 x 1080 px
```

Recommended paper-ready export:

```text
3840 x 2160 px
```

Default composition:

```text
Top: scenario title and route class
Center-left: fixed Korean apartment background with node overlay
Right: compact data-flow / policy-flow panel
Bottom: topic, payload, schema, and expected outcome strip
```

---

## 3. Background style

Canonical background style:

```text
clean semi-isometric technical illustration of a Korean apartment interior
```

Required background characteristics:

```text
- light neutral background;
- low visual noise;
- no people by default;
- no baked-in text labels;
- no dramatic lighting;
- no random clutter;
- clear room zones for entrance, living room, kitchen, bedroom, bathroom, and balcony;
- enough negative space for SVG labels and arrows.
```

---

## 4. Layering model

Use this visual layer order:

| Layer | Content | Format |
|---|---|---|
| 0 | Canonical Korean apartment background | PNG or SVG |
| 1 | Fixed passive node markers | SVG |
| 2 | Scenario-specific active node highlights | SVG |
| 3 | Event/situation icons | SVG |
| 4 | Data-flow arrows and labels | SVG |
| 5 | Policy/schema/topic panels | SVG text/shapes |
| 6 | Expected outcome and audit markers | SVG |

Only scenario overlays should change between scenario figures.

---

## 5. Color palette

Use the following color mapping unless explicitly superseded by a later style guide version.

| Meaning | Color | Hex |
|---|---|---|
| Normal context | Blue | `#1976D2` |
| Class 0 emergency | Red | `#D32F2F` |
| Class 1 low-risk assistance | Green | `#2E7D32` |
| Class 2 clarification | Amber | `#F9A825` |
| Fault / safe deferral | Purple | `#6A1B9A` |
| Audit / traceability | Gray | `#616161` |
| LLM guidance | Teal | `#00897B` |
| Validator | Navy | `#1565C0` |
| Blocked unsafe path | Dark red | `#B71C1C` |
| Neutral inactive node | Neutral gray | `#9E9E9E` |

---

## 6. Node visual rules

| Node state | Visual rule |
|---|---|
| Inactive node | Gray icon, low-opacity marker, no glow |
| Active source node | Colored border and small status dot |
| Active receiving component | Colored border, subtle highlight |
| Fault-related node | Purple outline or warning badge |
| Emergency source | Red outline and emergency badge |
| Validator | Shield/check icon in navy |
| Audit log | Gray log icon or database icon |
| LLM guidance layer | Teal speech-bubble icon and guidance-only label |

Do not make the LLM visual larger or more authoritative than the Policy Router or Deterministic Validator.

---

## 7. Arrow visual rules

| Flow type | Visual rule |
|---|---|
| MQTT message | Solid arrow |
| Internal runtime call | Dashed arrow |
| Candidate/guidance flow | Teal dashed arrow |
| Validator approval | Navy or green arrow with check marker |
| Actuation command | Green solid arrow after validator approval |
| ACK loop | Return arrow from actuator to ACK/audit |
| Emergency evidence | Red solid arrow |
| Deferral / blocked flow | Purple or red dashed line with pause/X icon |
| Audit logging | Thin gray arrow to audit log |

Arrows should be labeled with topic or interface names only when legible.

Use short labels such as:

```text
context/input
emergency/event
validator/output
actuation/command
actuation/ack
audit/log
```

---

## 8. Scenario title format

Use this title format:

```text
OV-XX — Scenario Name
Route: CLASS_N / Fault family / Expected outcome
```

Examples:

```text
OV-01 — Class 1 Bounded Low-Risk Assistance
Route: CLASS_1 → Validator → Lighting Command → ACK
```

```text
OV-07 — Class 2 Insufficient Context Clarification
Route: CLASS_2 → Candidate Prompt → Confirmation/Timeout → Transition or Safe Deferral
```

---

## 9. Label rules

Labels should be clear but short.

Preferred label style:

```text
Node Name
(topic or payload family)
```

Example:

```text
Policy Router
policy_table_v1_2_0
```

Avoid long JSON schema filenames in the main apartment view. Put full filenames in the bottom strip or metadata.

---

## 10. Authority-boundary rules

All OV figures must preserve these visual boundaries:

1. LLM guidance must not look like an execution decision.
2. Candidate prompts must not look like validator output.
3. Policy Router must not visually bypass Deterministic Validator for Class 1 actuation.
4. `safe_deferral/actuation/command` must appear only after validator approval or governed manual confirmation.
5. Doorbell/Visitor Context Node must not look like door unlock authority.
6. Dashboard/governance/test layers must not look like operational control authority.
7. Fault scenarios must show blocked/recheck/deferral paths rather than hidden failure.
8. Audit must appear as evidence logging, not as a control component.

---

## 11. Scenario-specific visual focus

| Figure | Visual focus |
|---|---|
| OV-00 | Ordinary context and audit path |
| OV-01 | Validated low-risk lighting command and ACK |
| OV-02 | High-temperature emergency evidence |
| OV-03 | Triple-hit bounded input emergency evidence |
| OV-04 | Smoke emergency evidence |
| OV-05 | Gas emergency evidence |
| OV-06 | Fall detection emergency evidence |
| OV-07 | Class 2 candidate clarification and transition choices |
| OV-08 | Stale state blocked and deferred |
| OV-09 | Multiple candidate conflict and confirmation requirement |
| OV-10 | Missing required state, recheck, and safe deferral |

---

## 12. Export rules

SVG is the editable source of truth for overlays and final composition.

PNG is the rendered output for documents, slides, and manuscripts.

Recommended exports:

```text
1920x1080 PNG for internal documents
3840x2160 PNG for paper-ready figures
```

Do not manually edit exported PNG files unless the edit is also reflected in the SVG source or metadata.

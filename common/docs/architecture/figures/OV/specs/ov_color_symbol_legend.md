# OV Color and Symbol Legend

## 1. Purpose

This legend defines the shared color and symbol vocabulary for Operational View (OV) figures under:

```text
common/docs/architecture/figures/OV/
```

Use this legend together with:

```text
common/docs/architecture/figures/OV/specs/ov_style_guide.md
common/docs/architecture/figures/OV/specs/ov_node_coordinate_map.json
common/docs/architecture/figures/OV/specs/ov_scenario_figure_manifest.json
```

---

## 2. Color palette

| Meaning | Color name | Hex | Use |
|---|---|---|---|
| Normal context | Blue | `#1976D2` | Baseline context/input flows |
| Class 0 emergency | Red | `#D32F2F` | Emergency evidence and emergency route |
| Class 1 low-risk assistance | Green | `#2E7D32` | Validated low-risk assistance and approved lighting command |
| Class 2 clarification | Amber | `#F9A825` | Clarification, candidate prompts, transition state |
| Fault / safe deferral | Purple | `#6A1B9A` | Stale, conflict, missing-state, blocked/recheck/defer flows |
| Audit / traceability | Gray | `#616161` | Audit log, evidence trail, non-control records |
| LLM guidance | Teal | `#00897B` | Candidate/guidance text only |
| Validator | Navy | `#1565C0` | Deterministic validation and approval boundary |
| Blocked unsafe path | Dark red | `#B71C1C` | Prohibited or unsafe flow |
| Neutral inactive node | Neutral gray | `#9E9E9E` | Passive or inactive nodes |
| Background line | Light gray | `#E0E0E0` | Subtle background outlines |
| Panel background | Very light gray | `#F5F5F5` | Right-side flow panels and bottom strips |

---

## 3. Symbol vocabulary

| Concept | Symbol suggestion | Meaning |
|---|---|---|
| Context input | small sensor dot / blue pulse | ordinary context signal |
| Emergency evidence | red warning triangle | Class 0 evidence |
| Bounded input | button icon | constrained user input |
| Triple-hit | button icon with `x3` | repeated emergency input pattern |
| Smoke | smoke cloud icon | E003 evidence |
| Gas | gas plume icon | E004 evidence |
| High temperature | thermometer icon | E001 evidence |
| Fall | person/fall marker or floor alert icon | E005 evidence |
| Doorbell/visitor context | doorbell icon | visitor context only |
| LLM guidance | speech bubble | bounded candidate/guidance, no authority |
| Policy Router | route/switch icon | route classification |
| Validator | shield/check icon | deterministic admissibility boundary |
| Actuator command | arrow to device | approved command only |
| ACK | return arrow/check | closed-loop evidence |
| Safe deferral | pause/shield icon | no autonomous execution |
| Audit | log/database icon | evidence trace |
| Caregiver notification | mobile/cloud icon | external notification or confirmation |
| Blocked action | red X | prohibited action or unsafe path |

---

## 4. Class-specific visual rules

| Class / condition | Primary color | Required visual cue |
|---|---|---|
| Baseline | Blue | normal input and audit path |
| Class 1 | Green | validator check before actuation command |
| Class 0 | Red | emergency evidence source and emergency route |
| Class 2 | Amber | candidate prompt and confirmation/timeout branch |
| Stale fault | Purple | stale marker, blocked direct actuation, recheck/deferral |
| Conflict fault | Purple + Amber | multiple candidates and confirmation requirement |
| Missing-state fault | Purple | missing-state marker and recheck/deferral |

---

## 5. Arrow legend

| Arrow style | Meaning |
|---|---|
| Solid blue arrow | ordinary context/input MQTT flow |
| Solid red arrow | emergency evidence flow |
| Solid green arrow | approved Class 1 actuation command |
| Dashed navy arrow | internal policy/validator processing |
| Dashed teal arrow | LLM guidance/candidate flow |
| Dashed purple arrow | safe deferral, fault handling, recheck, or clarification path |
| Thin gray arrow | audit logging or evidence trace |
| Return arrow | ACK or confirmation feedback |
| Red dashed arrow with X | blocked/prohibited path |

---

## 6. Required boundary labels

Use short boundary labels when space allows:

```text
Guidance only
No actuation authority
Validator required
Audit only
Visitor context only
Controlled test only
No autonomous doorlock
No direct dashboard control
```

Do not over-label the apartment view. Use the right-side panel or bottom strip for long boundary text.

---

## 7. Doorbell/visitor context rule

Doorbell/visitor visuals must not imply:

```text
- emergency trigger authority;
- door-unlock authority;
- Class 1 autonomous door action;
- caregiver approval by default.
```

Preferred label:

```text
Doorbell / Visitor Context
visitor context only
```

---

## 8. LLM guidance rule

LLM visuals must always indicate that the LLM is not the final authority.

Preferred label:

```text
LLM Guidance
candidate only
```

Do not draw a direct arrow from LLM Guidance Layer to Actuator Dispatcher or Actuator Node.

LLM candidate/guidance flow should pass through:

```text
Policy Router / Deterministic Validator / Class 2 Clarification Manager
```

as appropriate for the scenario.

---

## 9. Dashboard/governance/test rule

Dashboard, governance, RPi simulation, and test components must be visually separated from the operational control path.

Preferred visual treatment:

```text
- dashed boundary box;
- label: controlled test / visibility only;
- no direct solid actuation command arrow.
```

---

## 10. Audit rule

Audit should appear in every scenario figure as traceability.

Audit arrows should be thin and gray.

Audit must not appear as an authority component that approves action.

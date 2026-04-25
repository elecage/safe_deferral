# SESSION_HANDOFF_2026-04-25_OV_FIGURE_DEVELOPMENT_PLAN.md

Date: 2026-04-25
Scope: Development plan for scenario-level Operational View (OV) figures
Status: Plan recorded. No OV figure assets were created in this step.

## 1. Purpose

This addendum records the development plan for scenario-level operational concept figures, hereafter called OV figures.

Planned output directory:

```text
common/docs/architecture/figures/OV/
```

Goal:

```text
Create a consistent set of scenario-level operational concept diagrams using a fixed Korean apartment indoor background and scenario-specific overlays.
```

Each OV figure should show:

```text
- Korean apartment indoor environment;
- fixed node locations;
- scenario-specific event/situation;
- transmitting node/component;
- receiving node/component;
- interface/topic/payload flow;
- relevant policy/schema boundary;
- expected handling outcome.
```

---

## 2. Core design decision

Do not rely only on an image-generation seed for consistency.

Use this reproducibility hierarchy:

```text
1. Canonical background asset fixed in the repository.
2. Fixed node coordinate map.
3. Scenario-specific SVG overlays.
4. Recorded generation prompt, seed, and metadata.
```

Reason:

```text
Even if a generation seed is recorded, image-generation outputs may vary across model versions or rendering environments. The actual stable baseline should be the approved canonical background file and fixed overlay coordinates.
```

---

## 3. Planned folder structure

Create this structure in a future phase:

```text
common/docs/architecture/figures/OV/
  README.md

  base/
    ov_base_korean_apartment_v1.png
    ov_base_korean_apartment_v1.svg
    ov_base_korean_apartment_v1.metadata.json

  overlays/
    ov_overlay_node_positions_v1.svg
    ov_overlay_node_positions_v1.json
    ov_overlay_legend_v1.svg

  scenarios/
    OV_00_baseline.png
    OV_00_baseline.svg
    OV_01_class1_baseline.png
    OV_01_class1_baseline.svg
    OV_02_class0_e001_high_temperature.png
    OV_02_class0_e001_high_temperature.svg
    OV_03_class0_e002_triple_hit.png
    OV_03_class0_e002_triple_hit.svg
    OV_04_class0_e003_smoke.png
    OV_04_class0_e003_smoke.svg
    OV_05_class0_e004_gas.png
    OV_05_class0_e004_gas.svg
    OV_06_class0_e005_fall.png
    OV_06_class0_e005_fall.svg
    OV_07_class2_insufficient_context.png
    OV_07_class2_insufficient_context.svg
    OV_08_stale_fault.png
    OV_08_stale_fault.svg
    OV_09_conflict_fault.png
    OV_09_conflict_fault.svg
    OV_10_missing_state_fault.png
    OV_10_missing_state_fault.svg

  specs/
    ov_style_guide.md
    ov_generation_prompt_template.md
    ov_scenario_figure_manifest.json
    ov_node_coordinate_map.json
    ov_color_symbol_legend.md
```

Use the ASCII folder name `OV` for compatibility with GitHub, LaTeX, CI, and image conversion tools.

---

## 4. Canonical background plan

The fixed background should be:

```text
A clean semi-isometric technical illustration of a modern Korean apartment interior.
```

Required visible zones:

```text
- entrance / 현관
- living room / 거실
- kitchen / 주방
- bedroom / 침실
- bathroom / 욕실
- balcony / 베란다
```

Style:

```text
- academic technical illustration;
- light gray / warm neutral background;
- low visual noise;
- no people by default;
- no text labels embedded in the background;
- clear space for overlay arrows and labels;
- node placeholders may be lightly indicated but scenario labels should be in overlays.
```

Important rule:

```text
Text labels should be in SVG overlays, not baked into the base background image.
```

---

## 5. Fixed seed plan

Project-level seed values:

```text
OV_STYLE_SEED = 20260425
OV_BASE_BACKGROUND_SEED = 20260425
OV_OVERLAY_STYLE_SEED = 20260425
```

Seed caveat to record in metadata:

```text
Seed is recorded for reproducibility, but the canonical background file is the actual visual baseline.
```

---

## 6. Base generation prompt template

Future file:

```text
common/docs/architecture/figures/OV/specs/ov_generation_prompt_template.md
```

Recommended base prompt:

```text
A clean semi-isometric technical illustration of a modern Korean apartment interior, showing entrance, living room, kitchen, bedroom, bathroom, and balcony in one coherent view. Minimal warm neutral colors, low visual noise, no people, fixed IoT node placeholders on walls and ceilings, clear space for overlay arrows and labels, academic paper figure style.
```

Recommended negative prompt:

```text
No text labels, no random people, no clutter, no dramatic lighting, no photorealistic mess, no distorted floorplan, no duplicated rooms, no door lock emphasis, no emergency scene by default, no visible brand logos.
```

Recommended canvas:

```text
16:9, 1920x1080 for working figures
3840x2160 for paper-ready export if needed
```

---

## 7. Fixed node placement plan

Node coordinates should be stored in:

```text
common/docs/architecture/figures/OV/specs/ov_node_coordinate_map.json
```

Initial coordinate draft for a 1920x1080 canvas:

```json
{
  "mac_mini_edge_hub": { "x": 960, "y": 610 },
  "mqtt_broker_runtime": { "x": 960, "y": 540 },
  "bounded_input_node": { "x": 420, "y": 690 },
  "context_node": { "x": 760, "y": 410 },
  "doorbell_visitor_context_node": { "x": 260, "y": 420 },
  "temperature_sensor_node": { "x": 720, "y": 350 },
  "smoke_sensor_node": { "x": 780, "y": 300 },
  "gas_sensor_node": { "x": 820, "y": 560 },
  "fall_detection_node": { "x": 610, "y": 720 },
  "lighting_actuator_node": { "x": 1120, "y": 310 },
  "tts_voice_output_node": { "x": 1080, "y": 650 },
  "display_output_node": { "x": 1220, "y": 620 },
  "warning_output_node": { "x": 1260, "y": 360 },
  "caregiver_notification_interface": { "x": 1580, "y": 240 },
  "policy_router": { "x": 1370, "y": 500 },
  "deterministic_validator": { "x": 1460, "y": 590 },
  "class2_clarification_manager": { "x": 1440, "y": 690 },
  "actuator_dispatcher": { "x": 1340, "y": 740 },
  "audit_log": { "x": 1540, "y": 820 }
}
```

These are starting coordinates only and should be refined after the canonical background is approved.

---

## 8. Common visual grammar

| Element | Visual rule |
|---|---|
| Active node | Highlighted border and colored status dot |
| Inactive node | Gray icon or low-opacity marker |
| Data transmission | Solid arrow |
| Internal processing | Dashed arrow |
| Blocked/unsafe path | Red X or red dashed blocked line |
| Safe deferral | Pause icon or shield-pause symbol |
| Audit | Log icon / gray trail |
| LLM guidance | Speech bubble, explicitly marked guidance-only |
| Validator | Shield/check icon |
| Actuation command | Green command arrow after validation |
| ACK | Return arrow from actuator to ACK/audit |
| Caregiver notification | Mobile/cloud icon outside apartment boundary |

---

## 9. Color and symbol guide

Future file:

```text
common/docs/architecture/figures/OV/specs/ov_color_symbol_legend.md
```

Recommended colors:

```json
{
  "normal_context": "#1976D2",
  "class0_emergency": "#D32F2F",
  "class1_low_risk": "#2E7D32",
  "class2_clarification": "#F9A825",
  "fault_safe_deferral": "#6A1B9A",
  "audit": "#616161",
  "llm_guidance": "#00897B",
  "validator": "#1565C0",
  "blocked": "#B71C1C",
  "neutral_node": "#9E9E9E"
}
```

Class-level visual mapping:

| Class / condition | Color family | Meaning |
|---|---|---|
| Baseline / normal context | Blue | ordinary context flow |
| Class 1 | Green | low-risk assistance after validation |
| Class 0 | Red | emergency evidence and emergency handling |
| Class 2 | Amber | clarification / transition state |
| Fault | Purple / dark orange | blocked, recheck, or safe deferral |
| Audit | Gray | traceability only |
| LLM guidance | Teal | guidance/candidate only, no authority |

---

## 10. Scenario figure list

| Figure ID | Scenario | Scenario file | Main visual situation |
|---|---|---|---|
| OV-00 | Baseline | `integration/scenarios/baseline_scenario_skeleton.json` | Ordinary indoor context input and audit |
| OV-01 | Class 1 baseline | `integration/scenarios/class1_baseline_scenario_skeleton.json` | User requests low-risk lighting assistance; validated lighting command |
| OV-02 | Class 0 E001 | `integration/scenarios/class0_e001_scenario_skeleton.json` | High temperature detected in living/kitchen area |
| OV-03 | Class 0 E002 | `integration/scenarios/class0_e002_scenario_skeleton.json` | User triple-hit input on bounded input node |
| OV-04 | Class 0 E003 | `integration/scenarios/class0_e003_scenario_skeleton.json` | Smoke detected near kitchen ceiling |
| OV-05 | Class 0 E004 | `integration/scenarios/class0_e004_scenario_skeleton.json` | Gas detected near kitchen/gas range |
| OV-06 | Class 0 E005 | `integration/scenarios/class0_e005_scenario_skeleton.json` | Fall detected in living room or bedroom area |
| OV-07 | Class 2 insufficient context | `integration/scenarios/class2_insufficient_context_scenario_skeleton.json` | Ambiguous request leads to candidate clarification |
| OV-08 | Stale fault | `integration/scenarios/stale_fault_scenario_skeleton.json` | Stale sensor/context data blocked and deferred |
| OV-09 | Conflict fault | `integration/scenarios/conflict_fault_scenario_skeleton.json` | Multiple plausible candidates require confirmation |
| OV-10 | Missing-state fault | `integration/scenarios/missing_state_scenario_skeleton.json` | Required state missing; recheck or safe deferral |

---

## 11. Recommended per-figure metadata

Each scenario figure should eventually have a metadata JSON file:

```text
common/docs/architecture/figures/OV/scenarios/OV_07_class2_insufficient_context.metadata.json
```

Metadata should include:

```text
figure_id
scenario_id
scenario_file
background
style_seed
active_nodes
topics
schemas
expected_outcome
manual_edit_notes
```

---

## 12. Recommended OV README structure

Future file:

```text
common/docs/architecture/figures/OV/README.md
```

Recommended sections:

```text
# Operational View Figures

## Purpose
## Canonical background
## Fixed seed and generation metadata
## Figure index
## Node coordinate map
## Scenario figure list
## Style rules
## Authority boundaries
## Regeneration workflow
```

---

## 13. Development phases

### Phase OV-0 — Plan record

Current phase.

Output:

```text
common/docs/runtime/SESSION_HANDOFF_2026-04-25_OV_FIGURE_DEVELOPMENT_PLAN.md
```

### Phase OV-1 — Folder and spec scaffold

Create:

```text
common/docs/architecture/figures/OV/README.md
common/docs/architecture/figures/OV/specs/ov_style_guide.md
common/docs/architecture/figures/OV/specs/ov_generation_prompt_template.md
common/docs/architecture/figures/OV/specs/ov_node_coordinate_map.json
common/docs/architecture/figures/OV/specs/ov_scenario_figure_manifest.json
```

No actual figure drawing in OV-1.

### Phase OV-2 — Canonical background creation

Create or approve:

```text
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.png
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.metadata.json
```

Review criteria:

```text
- Korean apartment feeling;
- reusable across all scenarios;
- low visual noise;
- enough blank space for overlays;
- no embedded text labels;
- no misleading doorlock emphasis;
- suitable for academic paper figures.
```

### Phase OV-3 — Node position overlay

Create:

```text
common/docs/architecture/figures/OV/overlays/ov_overlay_node_positions_v1.svg
common/docs/architecture/figures/OV/specs/ov_node_coordinate_map.json
```

Fix node coordinates after background approval.

### Phase OV-4 — Scenario SVG drafts

Recommended order:

```text
1. OV-00 baseline
2. OV-01 Class 1 baseline
3. OV-07 Class 2 insufficient context
4. OV-02~OV-06 Class 0 E001~E005
5. OV-08~OV-10 fault scenarios
```

### Phase OV-5 — PNG export

Export:

```text
common/docs/architecture/figures/OV/scenarios/*.svg
common/docs/architecture/figures/OV/scenarios/*.png
```

Recommended resolutions:

```text
1920x1080 for document/screen use
3840x2160 for paper-ready export if needed
```

### Phase OV-6 — Document linking

Link OV figures from:

```text
common/docs/architecture/20_scenario_data_flow_matrix.md
common/docs/architecture/scenario_data_flows/20_00_interface_role_alignment.md
common/docs/paper/...
```

---

## 14. Implementation cautions

1. Do not bake text labels into the base background.
2. Keep labels in SVG overlay layers.
3. Store node coordinates in JSON.
4. Use one canonical background for all scenarios.
5. Vary only scenario overlays.
6. Keep Class 0, Class 1, Class 2, fault, audit, LLM, validator, and blocked-path colors consistent.
7. LLM must always be visually represented as guidance-only.
8. Doorbell/Visitor Context Node must not look like door unlock authority.
9. Dashboard/governance/test layers must not look like operational control authority.
10. Store metadata for every scenario figure.
11. If image-generation tools are used, record prompt, seed, tool/model, date, and manual edit notes.
12. SVG should remain the editable source of truth for overlays.
13. PNG should be treated as exported render output.

---

## 15. Next recommended step

Proceed to Phase OV-1:

```text
Create OV folder and spec scaffold only.
```

Do not create the actual apartment background or scenario figures until the scaffold is reviewed.

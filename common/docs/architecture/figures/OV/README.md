# Operational View (OV) Figures

## 1. Purpose

This directory will contain scenario-level Operational View (OV) figures for the `safe_deferral` project.

The OV figures are intended to show how the system operates in a Korean apartment indoor environment for each scenario.

Each figure should make the following visible:

```text
scenario situation → active nodes/components → interface/topic flow → policy/schema boundary → expected outcome
```

This directory currently contains the scaffold and specification files only. Actual background images and scenario figures are intentionally deferred to later phases.

---

## 2. Directory structure

Planned structure:

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
    OV_00_baseline.svg
    OV_00_baseline.png
    OV_01_class1_baseline.svg
    OV_01_class1_baseline.png
    OV_02_class0_e001_high_temperature.svg
    OV_02_class0_e001_high_temperature.png
    OV_03_class0_e002_triple_hit.svg
    OV_03_class0_e002_triple_hit.png
    OV_04_class0_e003_smoke.svg
    OV_04_class0_e003_smoke.png
    OV_05_class0_e004_gas.svg
    OV_05_class0_e004_gas.png
    OV_06_class0_e005_fall.svg
    OV_06_class0_e005_fall.png
    OV_07_class2_insufficient_context.svg
    OV_07_class2_insufficient_context.png
    OV_08_stale_fault.svg
    OV_08_stale_fault.png
    OV_09_conflict_fault.svg
    OV_09_conflict_fault.png
    OV_10_missing_state_fault.svg
    OV_10_missing_state_fault.png

  specs/
    ov_style_guide.md
    ov_generation_prompt_template.md
    ov_node_coordinate_map.json
    ov_scenario_figure_manifest.json
    ov_color_symbol_legend.md
```

---

## 3. Canonical-background rule

All OV figures should share the same canonical Korean apartment background.

Reproducibility hierarchy:

```text
1. Fixed canonical background file.
2. Fixed node coordinate map.
3. Scenario-specific SVG overlays.
4. Recorded prompt, seed, tool/model, and metadata.
```

The seed is recorded for traceability, but the approved canonical background file is the actual visual baseline.

---

## 4. Fixed seed values

Use these values across OV work unless a later addendum intentionally supersedes them:

```text
OV_STYLE_SEED = 20260425
OV_BASE_BACKGROUND_SEED = 20260425
OV_OVERLAY_STYLE_SEED = 20260425
```

---

## 5. Figure index

| Figure ID | Scenario | Scenario file | Planned output |
|---|---|---|---|
| OV-00 | Baseline | `integration/scenarios/baseline_scenario_skeleton.json` | `scenarios/OV_00_baseline.svg`, `scenarios/OV_00_baseline.png` |
| OV-01 | Class 1 baseline | `integration/scenarios/class1_baseline_scenario_skeleton.json` | `scenarios/OV_01_class1_baseline.svg`, `scenarios/OV_01_class1_baseline.png` |
| OV-02 | Class 0 E001 | `integration/scenarios/class0_e001_scenario_skeleton.json` | `scenarios/OV_02_class0_e001_high_temperature.svg`, `scenarios/OV_02_class0_e001_high_temperature.png` |
| OV-03 | Class 0 E002 | `integration/scenarios/class0_e002_scenario_skeleton.json` | `scenarios/OV_03_class0_e002_triple_hit.svg`, `scenarios/OV_03_class0_e002_triple_hit.png` |
| OV-04 | Class 0 E003 | `integration/scenarios/class0_e003_scenario_skeleton.json` | `scenarios/OV_04_class0_e003_smoke.svg`, `scenarios/OV_04_class0_e003_smoke.png` |
| OV-05 | Class 0 E004 | `integration/scenarios/class0_e004_scenario_skeleton.json` | `scenarios/OV_05_class0_e004_gas.svg`, `scenarios/OV_05_class0_e004_gas.png` |
| OV-06 | Class 0 E005 | `integration/scenarios/class0_e005_scenario_skeleton.json` | `scenarios/OV_06_class0_e005_fall.svg`, `scenarios/OV_06_class0_e005_fall.png` |
| OV-07 | Class 2 insufficient context | `integration/scenarios/class2_insufficient_context_scenario_skeleton.json` | `scenarios/OV_07_class2_insufficient_context.svg`, `scenarios/OV_07_class2_insufficient_context.png` |
| OV-08 | Stale fault | `integration/scenarios/stale_fault_scenario_skeleton.json` | `scenarios/OV_08_stale_fault.svg`, `scenarios/OV_08_stale_fault.png` |
| OV-09 | Conflict fault | `integration/scenarios/conflict_fault_scenario_skeleton.json` | `scenarios/OV_09_conflict_fault.svg`, `scenarios/OV_09_conflict_fault.png` |
| OV-10 | Missing-state fault | `integration/scenarios/missing_state_scenario_skeleton.json` | `scenarios/OV_10_missing_state_fault.svg`, `scenarios/OV_10_missing_state_fault.png` |

---

## 6. Specification files

| File | Purpose |
|---|---|
| `specs/ov_style_guide.md` | Defines visual grammar, layout, symbols, labels, and authority-boundary rules |
| `specs/ov_generation_prompt_template.md` | Stores canonical background prompt, negative prompt, seed, and metadata template |
| `specs/ov_node_coordinate_map.json` | Stores fixed node coordinates for a 1920x1080 coordinate system |
| `specs/ov_scenario_figure_manifest.json` | Lists planned figures, scenario files, active nodes, topics, schemas, and expected outcomes |
| `specs/ov_color_symbol_legend.md` | Planned color and symbol legend; may be created or expanded later |

---

## 7. Authority boundaries

OV figures must not visually imply authority that the system does not have.

Required boundaries:

```text
- LLM guidance is guidance only, not actuation authority.
- Policy Router does not bypass the Deterministic Validator for Class 1 actuation.
- Class 0 requires deterministic emergency evidence or user/caregiver emergency confirmation.
- Class 2 is a clarification/transition state, not simply terminal failure.
- Doorbell/Visitor Context Node is visitor context only, not emergency evidence or doorlock authority.
- Dashboard/governance/test layers are visibility or controlled-test artifacts, not operational control authority.
- Safe deferral, blocked paths, and missing/conflict/stale causes must remain auditable.
```

---

## 8. Regeneration workflow

Future figure regeneration should follow this order:

```text
1. Review ov_generation_prompt_template.md.
2. Generate or update the base background only if intentionally creating a new background version.
3. Record prompt, seed, tool/model, date, and manual edit notes in metadata.
4. Update ov_node_coordinate_map.json only after checking all scenario overlays.
5. Generate scenario SVG overlays using the fixed coordinate map.
6. Export PNG files from SVG after review.
7. Update this README and manifest if figure IDs or file names change.
```

---

## 9. Current status

Status after Phase OV-1:

```text
- Scaffold exists.
- Specification files exist.
- No canonical background image has been created yet.
- No scenario SVG/PNG figure has been created yet.
```

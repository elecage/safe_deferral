# SESSION_HANDOFF_2026-04-25_OV_PHASE1_SCAFFOLD_UPDATE.md

Date: 2026-04-25
Scope: Phase OV-1 scaffold creation for scenario-level Operational View figures
Status: Completed.

## 1. Purpose

This addendum records completion of Phase OV-1 from:

```text
common/docs/runtime/SESSION_HANDOFF_2026-04-25_OV_FIGURE_DEVELOPMENT_PLAN.md
```

Phase OV-1 creates the folder scaffold and specification files for future Operational View (OV) figures.

No actual apartment background image, scenario SVG, or scenario PNG figure was created in this phase.

---

## 2. Created files

Created:

```text
common/docs/architecture/figures/OV/README.md
common/docs/architecture/figures/OV/specs/ov_style_guide.md
common/docs/architecture/figures/OV/specs/ov_generation_prompt_template.md
common/docs/architecture/figures/OV/specs/ov_node_coordinate_map.json
common/docs/architecture/figures/OV/specs/ov_scenario_figure_manifest.json
common/docs/architecture/figures/OV/specs/ov_color_symbol_legend.md
```

Note:

```text
The plan originally required README plus four spec files. The color/symbol legend was also created because it was part of the planned OV/specs structure and is needed for consistent scenario overlays.
```

---

## 3. Commits

Created files were committed individually through the GitHub connector.

Known commit SHAs:

```text
README.md: 2a26ca17ee559518e917542ab8e96542f6687e12
ov_generation_prompt_template.md: ea2e502d1a0bb0c3b1ebf70019a4968bb8869134
ov_color_symbol_legend.md: efadd4519a6e32136db7bab751b7c3dd5a5de5a9
```

Other scaffold files were also created in this phase:

```text
ov_style_guide.md
ov_node_coordinate_map.json
ov_scenario_figure_manifest.json
```

---

## 4. README contents

Created:

```text
common/docs/architecture/figures/OV/README.md
```

Main sections:

```text
1. Purpose
2. Directory structure
3. Canonical-background rule
4. Fixed seed values
5. Figure index
6. Specification files
7. Authority boundaries
8. Regeneration workflow
9. Current status
```

The README defines the planned OV figure set:

```text
OV-00 baseline
OV-01 Class 1 baseline
OV-02 Class 0 E001 high temperature
OV-03 Class 0 E002 triple-hit emergency input
OV-04 Class 0 E003 smoke detected
OV-05 Class 0 E004 gas detected
OV-06 Class 0 E005 fall detected
OV-07 Class 2 insufficient context
OV-08 stale fault
OV-09 conflict fault
OV-10 missing-state fault
```

---

## 5. Style guide contents

Created:

```text
common/docs/architecture/figures/OV/specs/ov_style_guide.md
```

Main contents:

```text
- 16:9 canvas rule
- 1920x1080 working size
- 3840x2160 paper-ready export target
- default layout structure
- canonical background style
- layer model
- color palette
- node visual rules
- arrow visual rules
- scenario title format
- label rules
- authority-boundary rules
- scenario-specific visual focus
- export rules
```

---

## 6. Prompt template contents

Created:

```text
common/docs/architecture/figures/OV/specs/ov_generation_prompt_template.md
```

Main contents:

```text
- fixed seed values
- base background prompt
- negative prompt
- required apartment zones
- canvas/export target
- background metadata template
- scenario overlay prompt pattern
- prohibited prompt outcomes
```

Fixed seed values:

```text
OV_STYLE_SEED = 20260425
OV_BASE_BACKGROUND_SEED = 20260425
OV_OVERLAY_STYLE_SEED = 20260425
```

Important reproducibility rule:

```text
Seed is recorded for reproducibility, but the approved canonical background file is the actual visual baseline.
```

---

## 7. Node coordinate map contents

Created:

```text
common/docs/architecture/figures/OV/specs/ov_node_coordinate_map.json
```

Purpose:

```text
Provide fixed draft node coordinates for a 1920x1080 canvas.
```

Node keys include:

```text
mac_mini_edge_hub
mqtt_broker_runtime
bounded_input_node
context_node
doorbell_visitor_context_node
temperature_sensor_node
smoke_sensor_node
gas_sensor_node
fall_detection_node
lighting_actuator_node
tts_voice_output_node
display_output_node
warning_output_node
caregiver_notification_interface
policy_router
deterministic_validator
class2_clarification_manager
llm_guidance_layer
actuator_dispatcher
ack_handling
audit_log
health_check_routine
safe_deferral_manager
rpi_scenario_orchestrator
```

Caution recorded in the file:

```text
Coordinates are draft coordinates and must be refined after canonical background approval.
```

---

## 8. Scenario figure manifest contents

Created:

```text
common/docs/architecture/figures/OV/specs/ov_scenario_figure_manifest.json
```

Purpose:

```text
Machine-readable draft manifest for planned OV figures.
```

Each figure entry includes:

```text
figure_id
slug
scenario_name
scenario_file
planned_svg
planned_png
route_family
main_visual_situation
active_nodes
topics
payload_families
schemas_or_policies
expected_outcome
```

Covered figures:

```text
OV-00 through OV-10
```

---

## 9. Color/symbol legend contents

Created:

```text
common/docs/architecture/figures/OV/specs/ov_color_symbol_legend.md
```

Main contents:

```text
- color palette
- symbol vocabulary
- class-specific visual rules
- arrow legend
- required boundary labels
- doorbell/visitor context rule
- LLM guidance rule
- dashboard/governance/test rule
- audit rule
```

Key visual safety constraints:

```text
- LLM guidance is candidate/guidance only.
- Doorbell/visitor context is not emergency or doorlock authority.
- Dashboard/governance/test components must not look like operational control authority.
- Audit must not look like an approval/control component.
```

---

## 10. Files intentionally not created

Not created in Phase OV-1:

```text
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.png
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.svg
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.metadata.json
common/docs/architecture/figures/OV/overlays/*.svg
common/docs/architecture/figures/OV/scenarios/*.svg
common/docs/architecture/figures/OV/scenarios/*.png
common/docs/architecture/figures/OV/scenarios/*.metadata.json
```

Reason:

```text
Phase OV-1 is scaffold/specification only. Background and scenario figures are deferred to later phases.
```

---

## 11. Next recommended phase

Proceed to Phase OV-2:

```text
Canonical background creation / approval
```

Expected Phase OV-2 outputs:

```text
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.png
common/docs/architecture/figures/OV/base/ov_base_korean_apartment_v1.metadata.json
```

Recommended Phase OV-2 review criteria:

```text
- Korean apartment feeling;
- reusable across all scenarios;
- low visual noise;
- enough blank space for overlays;
- no embedded text labels;
- no misleading doorlock emphasis;
- suitable for academic paper figures.
```

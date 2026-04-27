# System Structure Figure Text, Label, And Legend Pass

## 1. Purpose

This document completes Step 9 of
`common/docs/architecture/08_system_structure_figure_revision_plan.md`.

The SVG now includes concise local flow labels, a legend, and final
authority-boundary footer:

```text
common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg
```

## 2. Legend Added

A compact legend was added below the canonical assets / contracts band. It
identifies the main arrow categories:

- Mac mini operational
- Class 2 / caregiver
- governed manual dispatch
- RPi experiment
- STM32 measurement

The legend uses the same arrow styles as the figure so readers do not have to
infer line semantics from color and dash patterns alone.

## 3. Footer Updated

The footer now states the final authority boundary instead of a step-specific
message:

```text
Mac mini retains operational authority; Telegram, RPi, and STM32 provide
confirmation, experiment support, and measurement evidence only.
```

## 4. Flow Label Cleanup

Flow labels were shortened and repositioned so they do not compete with block
titles or internal descriptions. In particular:

- long dispatch labels were reduced to concise local labels;
- RPi-side telemetry and virtual-input labels were separated vertically;
- audit-related labels were separated from each other near the ACK/Audit lane;
- measurement labels were shortened where the STM32 lane is compact.

The legend carries arrow-style semantics, so the figure itself can avoid
paragraph-like explanations inside narrow routing lanes.

## 5. Validation Performed

Validation completed:

- SVG XML parse passed.
- Flow-label bounding-box overlap check passed for major blocks.
- `git diff --check` passed.

## 6. Next Step

Proceed to:

```text
Step 10. Render validation
```

Step 10 render validation is recorded in:

```text
figure_revision/10_render_validation.md
```

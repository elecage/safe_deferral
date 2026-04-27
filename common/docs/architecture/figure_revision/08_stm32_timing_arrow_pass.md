# System Structure Figure STM32 Timing Arrow Pass

## 1. Purpose

This document completes Step 8 of
`common/docs/architecture/08_system_structure_figure_revision_plan.md`.

The SVG now includes STM32 timing and measurement evidence flow:

```text
common/docs/architecture/figures/system_layout.svg
```

## 2. Arrows Added

### Timing capture inside STM32 support

The figure now shows:

```text
Physical / ESP32 signal taps
-> Capture Channels
-> Timestamping Core
-> Measurement Export
```

The capture channels are shown before the STM32 measurement node because they
represent tapped timing signals from physical nodes or physical-node
interfaces. The timestamping core is an internal component of the STM32 timing
support node; it timestamps and packages that evidence for export.

### Measurement export to RPi results

The figure now routes:

```text
Measurement Export -> RPi Result Store / Analysis
```

This represents out-of-band latency and timing evidence export into the
experiment result collection path.

## 3. Arrows Intentionally Not Added

This pass does not add:

- STM32-to-Policy Router arrows,
- STM32-to-Deterministic Validator arrows,
- STM32-to-Low-Risk Dispatcher arrows,
- STM32-to-caregiver or Telegram arrows,
- STM32-to-physical-actuator arrows.

STM32 remains measurement support, not operational authority.

## 4. Routing Notes

The new measurement export path stays below the Mac mini operational hub and
routes to RPi result collection. It is styled separately from operational,
caregiver, and RPi virtual experiment input arrows.

## 5. Validation Performed

Validation completed:

- SVG XML parse passed.
- `git diff --check` passed.

## 6. Next Step

Proceed to:

```text
Step 9. Text and legend pass
```

Step 9 should shorten labels where needed and add a concise legend for the
different arrow semantics without turning the figure into a dense explanation
panel.

Current follow-up output:

- `figure_revision/09_text_and_legend_pass.md`

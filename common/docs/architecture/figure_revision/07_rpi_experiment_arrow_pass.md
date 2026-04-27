# System Structure Figure RPi Experiment Arrow Pass

## 1. Purpose

This document completes Step 7 of
`common/docs/architecture/08_system_structure_figure_revision_plan.md`.

The SVG now includes Raspberry Pi experiment-support and observation overlays:

```text
common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg
```

## 2. Mac Mini Telemetry Source

Before drawing RPi observation, the figure now connects:

```text
Audit Logging / ACK evidence -> Read-Only Telemetry Adapter
```

This makes the telemetry adapter an explicit read-only view over Mac mini
evidence, not an orphan adapter.

## 3. Arrows Added

### RPi experiment orchestration

The figure now shows RPi-internal orchestration paths:

```text
Experiment Manager
-> Scenario Manager
-> Virtual Node Manager
-> Virtual Behavior / Fault Injection
```

It also routes:

```text
Result Store / Analysis -> MQTT / Payload Governance Support
```

These arrows stay inside the Raspberry Pi experiment support area.

### Virtual experiment input

The figure now routes:

```text
Virtual Behavior / Fault Injection -> Mac mini MQTT / Context Intake
```

This represents controlled experiment input entering the same Mac mini intake
boundary used by field-side input. It does not bypass Policy Router,
Deterministic Validator, or dispatch authority.

### Read-only telemetry

The figure now routes:

```text
Read-Only Telemetry Adapter -> Web Experiment Dashboard
```

This represents observation from Mac mini evidence toward RPi tools. It does not
grant RPi authority to publish actuation commands or override validation.

## 4. Arrows Intentionally Not Added

This pass does not add:

- RPi-to-dispatcher arrows,
- RPi-to-validator override arrows,
- RPi-to-caregiver authority arrows,
- STM32 measurement export arrows,
- canonical asset reference arrows.

Those remain separate or intentionally absent to preserve authority boundaries.

## 5. Routing Notes

The new arrows use these lanes:

| Flow | Lane |
| --- | --- |
| Mac mini telemetry source | lower Mac mini evidence lane into telemetry adapter |
| RPi internal orchestration | gaps inside the RPi support area |
| Virtual experiment input | right-side gap, top lane, then Mac mini intake edge |
| Read-only telemetry | gap between Mac mini and RPi, into dashboard edge |

The virtual experiment input and read-only telemetry paths use blue dashed
styles to distinguish experiment/observation flows from operational dispatch.

## 6. Validation Performed

Validation completed:

- SVG XML parse passed.
- `git diff --check` passed.

## 7. Next Step

Proceed to:

```text
Step 8. STM32 timing arrow pass
```

Step 8 should add STM32 timing capture and measurement export flow without
connecting STM32 to Mac mini policy routing or actuator dispatch as authority.

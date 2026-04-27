# Session Handoff: System Layout Finalization Update

Date: 2026-04-27

## Summary

The paper-oriented system layout figure has been finalized as the representative
architecture diagram.

## Changes Completed

- Renamed the final system layout SVG:

```text
common/docs/architecture/figures/system_layout.svg
```

- Updated active architecture, figure-revision, runtime handoff, and archive
  references to use the new `system_layout.svg` filename.
- Added paper-facing figure caption and Section 2.2 body text to:

```text
common/docs/paper/04_section2_system_design_outline.md
```

- Removed `12_prompts_experiment_physical_nodes.md` from the active prompt set
  and moved it to:

```text
common/docs/archive/architecture_legacy/12_prompts_experiment_physical_nodes.md
```

- Updated the active architecture index and prompt index so the active prompt
  categories are:

```text
12_prompts_mac_mini_components.md
12_prompts_rpi_experiment_apps.md
12_prompts_physical_nodes.md
12_prompts_stm32_time_sync_node.md
```

- Updated the component inventory so it no longer describes a separate
  experiment-only physical-node authority category.

## Current Interpretation

- Mac mini remains the operational authority for policy routing, validation,
  dispatch, caregiver notification/confirmation handling, ACK, and audit.
- Raspberry Pi remains non-authoritative experiment, dashboard, virtual-node,
  result, and governance-support infrastructure.
- STM32 remains out-of-band timing and measurement support.
- Telegram remains notification and response-collection transport only.
- Actual physical nodes are one bounded physical-node category.

## Validation

Validation completed:

- No remaining repository references to the old SVG filename.
- `system_layout.svg` XML parse passed.
- PNG render of `system_layout.svg` succeeded.
- `ov_node_coordinate_map.json` JSON parse passed.
- `git diff --check` passed.

## Next Suggested Work

The next figure-related work should prepare publication exports, such as PDF or
high-resolution PNG, from:

```text
common/docs/architecture/figures/system_layout.svg
```

# System Structure Figure Documentation Update

## 1. Purpose

This document completes Step 11 of
`common/docs/architecture/08_system_structure_figure_revision_plan.md`.

The final figure changed several architecture interpretations while it was being
revised. Active documents were updated so the written architecture now matches
the rendered system layout.

## 2. Interpretation Updates Applied

The following figure-driven decisions were propagated to active documentation:

- Telegram is notification and response-collection transport, not remote
  control.
- Raspberry Pi remains non-authoritative experiment support.
- STM32 remains out-of-band timing and measurement support.
- Physical nodes are one bounded physical-node category, not separate actual
  and experiment-only authority groups.
- Doorlock appears as a governed sensitive interface, not a doorbell-authorized
  autonomous Class 1 actuator.
- Device-state reporting is a function of relevant nodes, not a standalone
  physical block in the paper-oriented system layout.
- Lighting terminology now uses `Lighting Control Node` where the final figure
  does.

## 3. Documents Updated

Updated active architecture and prompt documents:

- `CLAUDE.md`
- `README.md`
- `common/docs/architecture/01_system_architecture.md`
- `common/docs/architecture/02_safety_and_authority_boundaries.md`
- `common/docs/architecture/12_prompts.md`
- `common/docs/architecture/12_prompts_physical_nodes.md`
- `common/docs/archive/architecture_legacy/12_prompts_experiment_physical_nodes.md`
- `common/docs/architecture/figures/OV/specs/ov_node_coordinate_map.json`

Updated paper-facing documents:

- `common/docs/paper/04_section2_system_design_outline.md`
- `common/docs/paper/scenarios/*.md` where terminology needed to align with the
  final figure.

## 4. Notes

The superseded experiment-physical-node prompt file remains in the repository as
a historical transition note, but it is no longer listed as an active prompt set
in `12_prompts.md`.

Older figure-revision inventory files may still mention intermediate names as
planning history. Active implementation should follow the active architecture
documents, active prompt index, and final rendered SVG.

## 5. Validation Performed

Validation completed:

- active-document search for stale remote-control wording passed;
- active-document search for older lighting-actuator wording passed;
- active-document search for active `Experiment-Only Physical Nodes` references
  leaves only explicit superseded/historical notes;
- `git diff --check` passed.

## 6. Result

The system structure figure revision sequence is now complete. Future work
should treat:

```text
common/docs/architecture/figures/system_layout.svg
```

as the current paper-oriented system layout figure.

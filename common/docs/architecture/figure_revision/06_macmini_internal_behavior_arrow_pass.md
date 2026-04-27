# System Structure Figure Mac Mini Internal Behavior Arrow Pass

## 1. Purpose

This document completes the revised Step 6 of
`common/docs/architecture/08_system_structure_figure_revision_plan.md`.

The SVG now prioritizes Mac mini internal behavior before Raspberry Pi
experiment-host flows:

```text
common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg
```

## 2. Why This Step Comes Before RPi Flows

The Mac mini is the operational authority boundary. Its internal routing,
validation, LLM-support, deferral, caregiver, ACK, and audit paths should be
settled before adding virtual experiment or telemetry overlays from the
Raspberry Pi.

## 3. Arrows Added

### LLM candidate guidance

The figure now shows:

```text
State Aggregation -> Local LLM Adapter -> Class 2 Clarification Manager
```

This is a dashed support path. It means the LLM may provide candidate guidance
for clarification, but it does not replace Policy Router or Deterministic
Validator authority.

### Context-integrity deferral record

The figure now shows:

```text
Deterministic Validator -> Context-Integrity Safe Deferral -> Audit Logging
```

This makes the deferral block an explicit validator-side branch rather than an
orphan audit source. It records unresolved or integrity-sensitive deferrals as
audit evidence inside the Mac mini boundary.

## 4. RPi Arrows Intentionally Deferred

This pass does not add:

- RPi virtual experiment input arrows,
- RPi dashboard observation arrows,
- RPi result-store arrows,
- RPi governance-support arrows.

Those should be added only after the Mac mini internal behavior is accepted.

## 5. Validation Performed

Validation completed:

- SVG XML parse passed.
- `git diff --check` passed.

## 6. Next Step

Proceed to:

```text
Step 7. RPi experiment arrow pass
```

Step 7 should add RPi experiment and observation flows only as overlays that
enter Mac mini intake or read from Mac mini telemetry. They must not bypass
Policy Router, Deterministic Validator, caregiver handling, dispatch, ACK, or
audit.

Current follow-up output:

- `figure_revision/07_rpi_experiment_arrow_pass.md`

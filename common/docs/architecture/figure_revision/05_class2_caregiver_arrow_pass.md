# System Structure Figure Class 2 And Caregiver Arrow Pass

## 1. Purpose

This document completes Step 5 of
`common/docs/architecture/08_system_structure_figure_revision_plan.md`.

The SVG now includes the Class 2 and caregiver-mediated manual confirmation
flow:

```text
common/docs/architecture/figures/system_layout.svg
```

## 2. Arrows Added

### Class 2 branch

The figure now shows a Class 2 branch from:

```text
Policy Router -> Class 2 Clarification Manager
```

This path is separate from the Class 1 low-risk operational route.

### Caregiver notification

The figure now routes:

```text
Class 2 Clarification Manager
-> Caregiver Notification / Confirmation
-> Telegram Bot API
-> Caregiver
```

Telegram is shown only as notification transport.

### Caregiver response

The caregiver response now routes:

```text
Caregiver
-> Response / Confirmation Evidence
-> Caregiver Notification / Confirmation
```

The response returns to the Mac mini caregiver backend. It does not go directly
to any actuator or physical node.

### Governed manual dispatch

The figure now shows:

```text
Caregiver Notification / Confirmation
-> Doorlock Interface Node
```

This arrow is labeled as governed manual dispatch after Mac mini checks. It is
not Telegram remote direct control and is not autonomous Class 1 execution.

### Confirmation audit

The figure now routes caregiver confirmation evidence to:

```text
Audit Logging
```

This documents the caregiver decision evidence separately from low-risk
execution ACK evidence.

## 3. Arrows Intentionally Not Added

This pass does not add:

- Raspberry Pi experiment or telemetry arrows,
- STM32 measurement export arrows,
- canonical asset reference arrows.

Those remain separate passes.

## 4. Routing Notes

The new arrows use these lanes:

| Flow | Lane |
| --- | --- |
| Class 2 branch | gap between Mac mini middle and right columns |
| Notification | gap between Mac mini and caregiver / Telegram area |
| Confirmation response | separate lower lane in the caregiver / Telegram area |
| Governed manual dispatch | right outer lane, then lower cross-lane to Doorlock Interface Node |
| Confirmation audit | Mac mini internal gap into Audit Logging |

No Telegram arrow is routed to Doorlock Interface Node.

## 5. Validation Performed

Validation completed:

- SVG XML parse passed.
- `git diff --check` passed.

## 6. Next Step

Proceed to:

```text
Step 6. Mac mini internal behavior arrow pass
```

Step 6 should finalize Mac mini internal support flows, especially LLM
candidate guidance and context-integrity deferral records, before RPi experiment
or telemetry arrows are added.

Current follow-up output:

- `figure_revision/06_macmini_internal_behavior_arrow_pass.md`

# System Structure Figure Operational Arrow Pass

## 1. Purpose

This document completes Step 4 of
`common/docs/architecture/08_system_structure_figure_revision_plan.md`.

The SVG now includes only the primary operational flow arrows:

```text
common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg
```

Caregiver, Raspberry Pi experiment, STM32 measurement, and canonical-reference
arrows are intentionally deferred to later passes.

## 2. Arrows Added

### Field input and context intake

One input/context lane now routes from the physical-node area into:

```text
MQTT / Context Intake
```

This represents bounded field-side input and context entering the Mac mini
operational hub. It does not represent doorlock authorization.

### Mac mini operational routing

Internal Mac mini arrows now show:

```text
MQTT / Context Intake
-> State Aggregation
-> Policy Router
-> Deterministic Validator
-> Low-Risk Dispatcher
```

The path is routed through column gaps so arrows do not cross unrelated blocks.

### Approved low-risk dispatch

One execution lane now routes:

```text
Low-Risk Dispatcher -> Lighting Control Node
```

This is intentionally limited to low-risk dispatch. It does not connect the
dispatcher to Doorlock Interface Node, Warning Output Node, or caregiver blocks.

### ACK and audit evidence

The operational return path now shows:

```text
Lighting Control Node -> ACK Handler -> Audit Logging
```

The ACK lane uses a dashed style to distinguish evidence return from execution.

## 3. Arrows Intentionally Not Added

This pass does not add:

- Class 2 clarification arrows,
- caregiver / Telegram arrows,
- governed manual confirmation arrows,
- Raspberry Pi experiment or telemetry arrows,
- STM32 measurement export arrows,
- canonical asset reference arrows.

These remain separate passes to keep the diagram readable and prevent authority
ambiguity.

## 4. Routing Notes

The new arrows use these lanes:

| Flow | Lane |
| --- | --- |
| Field input/context | gap between Actual Physical Nodes and Mac mini |
| Mac mini internal routing | gaps between Mac mini internal columns |
| Low-risk dispatch | right outer lane, lower cross-lane, then left gap |
| ACK evidence | left gap and lower Mac mini internal lane |

No new arrow is intended to cross a block interior.

## 5. Validation Performed

Validation completed:

- SVG XML parse passed.
- `git diff --check` passed.
- The SVG contains operational arrow markers only for this pass.

## 6. Next Step

Proceed to:

```text
Step 5. Class 2 and caregiver arrow pass
```

Step 5 should add the Class 2 clarification, Telegram notification, caregiver
response, governed manual confirmation, ACK, and audit paths without routing
them as autonomous doorlock authorization.

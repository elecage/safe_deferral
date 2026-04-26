# System Structure Figure Block-Only SVG Update

## 1. Purpose

This document completes Step 3 of
`common/docs/architecture/08_system_structure_figure_revision_plan.md`.

The SVG has been updated as a block-only layout:

```text
common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg
```

Detailed arrows are intentionally omitted in this step. They will be added in
separate arrow passes after the block layout is reviewed.

## 2. What Changed

The figure was converted from the older Mac-mini-only L-shape into a wider
block-oriented layout with these areas:

- User actor
- Actual physical nodes
- Mac mini operational hub
- Caregiver / Telegram path
- Raspberry Pi experiment support
- STM32 timing / measurement support
- Canonical assets / contracts reference band
- Footer boundary note

## 3. Blocks Added Or Clarified

### Actual physical nodes

The figure now keeps physical nodes in one unified area:

- Bounded Button Input Node
- Environmental Context Node
- Doorbell / Visitor Context Node
- Lighting Control Node
- Gas / Smoke / Fire Nodes
- Fall-Detection Node
- Warning Output Node
- Doorlock Interface Node

The physical-node area avoids subgroup captions such as experiment-facing
interfaces so the figure reads as a paper-oriented system structure instead of
an implementation inventory.

Wrapped component names use the same visual name style on both lines. The
figure does not introduce `Device State Reporter` or `Feedback Output Node` as
separate physical-node blocks.

### Mac mini operational hub

The Mac mini area now shows:

- MQTT / Context Intake
- State Aggregation
- Local LLM Adapter
- Policy Router
- Deterministic Validator
- Class 2 Clarification Manager
- Context-Integrity Safe Deferral
- Low-Risk Dispatcher
- Caregiver Notification / Confirmation
- Read-Only Telemetry Adapter
- ACK Handler
- Audit Logging Service

### Caregiver / Telegram path

The figure now includes:

- Telegram Bot API
- Caregiver
- Response / Confirmation Evidence

Telegram is represented as a transport path, not as policy or validator
authority.

### Raspberry Pi experiment support

The RPi area now shows:

- Web Experiment Dashboard
- Experiment Manager
- Scenario Manager
- Virtual Node Manager
- Virtual Behavior / Fault Injection
- MQTT / Interface Status Manager
- Result Store / Analysis
- MQTT / Payload Governance Support

The area is explicitly labeled non-authoritative.
It has been moved upward so STM32 and canonical assets can sit higher in the
overall layout.

### STM32 timing / measurement support

The figure now includes:

- STM32 Timing / Measurement Node
- Capture Channels
- Measurement Export

This area is styled as out-of-band support and not as operational control.

The Actual Physical Nodes area has been shortened after removing unsupported
physical-node blocks. The canonical assets / contracts band has been moved
upward with the same lower edge as the Actual Physical Nodes area.

## 4. Validation Performed

Validation completed:

- SVG XML parse passed.
- `git diff --check` passed.
- Final arrows are absent by design for this step.

Preview rendering was attempted with the local system preview tool, but the
sandbox rejected the preview command before rendering. Visual render inspection
should be performed in the next step before committing final arrow routing.

## 5. Known Temporary Limitations

This Step 3 SVG is not the final figure.

Temporary limitations:

- final operational arrows are not present,
- Class 2 / caregiver arrows are not present,
- RPi observation and experiment-input arrows are not present,
- STM32 measurement export arrows are not present,
- canonical asset reference arrows are not present.

These are intentional so arrow routing can be added without block layout churn.

## 6. Next Step

Proceed to:

```text
Step 4. Operational arrow pass
```

Step 4 should add only the main operational path:

```text
physical / virtual input
-> Mac mini MQTT / Context Intake
-> State Aggregation
-> Policy Router
-> Deterministic Validator
-> Low-Risk Dispatcher
-> Lighting Control Node
-> ACK Handler
-> Audit Logging Service
```

Do not add Class 2, caregiver, RPi, or STM32 arrows in Step 4.

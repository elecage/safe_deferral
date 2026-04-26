# System Structure Figure Layout Draft

## 1. Purpose

This document completes Step 2 of
`common/docs/architecture/08_system_structure_figure_revision_plan.md`.

It defines the proposed block-only layout for the revised system structure
figure before detailed arrows are edited.

The next SVG pass should use this as the layout guide.

## 2. Layout Strategy

Use a wide, block-oriented layout instead of the current Mac-mini-only L-shape.

Recommended canvas:

```text
width: 1800
height: 1300
viewBox: 0 0 1800 1300
```

High-level structure:

```text
top: title and legend
left: user + actual physical nodes
center: Mac mini operational hub
right: caregiver + Telegram path
right middle section: Raspberry Pi experiment support
lower center band: STM32 timing / measurement support
lower wide band: canonical assets / contracts, aligned with physical nodes
```

This layout keeps operational authority visually centered in the Mac mini while
placing RPi and STM32 as support layers, not control authority.

## 3. Proposed Areas

| Area | X | Y | W | H | Purpose |
| --- | ---: | ---: | ---: | ---: | --- |
| Title / subtitle | 40 | 24 | 1720 | 70 | Figure title and concise boundary subtitle |
| User actor | 40 | 115 | 340 | 86 | External user, same width as physical node area |
| Actual physical nodes | 40 | 230 | 340 | 875 | Physical nodes and bounded interfaces |
| Mac mini operational hub | 430 | 115 | 780 | 650 | Central operational authority |
| Caregiver / Telegram path | 1260 | 115 | 470 | 300 | Notification and manual confirmation |
| Raspberry Pi experiment support | 1260 | 455 | 470 | 520 | Non-authoritative experiment apps |
| STM32 timing / measurement | 430 | 840 | 780 | 130 | Out-of-band measurement support |
| Canonical assets / contracts | 430 | 1000 | 1300 | 105 | Repository-governed references; bottom aligned with physical nodes |
| Footer boundary note | 40 | 1245 | 1720 | 36 | Authority reminder |

## 4. Actual Physical Nodes Area

Container:

```text
x=40 y=230 w=340 h=875
```

Blocks:

| Block | X | Y | W | H |
| --- | ---: | ---: | ---: | ---: |
| Bounded Button Input Node | 70 | 315 | 280 | 64 |
| Environmental Context Node | 70 | 405 | 280 | 64 |
| Doorbell / Visitor Context Node | 70 | 495 | 280 | 64 |
| Lighting Control Node | 70 | 585 | 280 | 64 |
| Gas / Smoke / Fire Nodes | 70 | 675 | 280 | 64 |
| Fall-Detection Node | 70 | 765 | 280 | 64 |
| Warning Output Node | 70 | 855 | 280 | 64 |
| Doorlock Interface Node | 70 | 945 | 280 | 64 |

Text rule:

- 2 lines per block maximum.
- Use the same name style on both lines when a component name wraps.
- Put details in the area caption, not in every block.

Use `Doorlock Interface Node` as the block name. The safety boundary is carried
by color, notes, and caregiver/manual-path arrows, not by adding sensitive-path
wording into the block label.

Do not introduce `Device State Reporter` or `Feedback Output Node` as separate
physical-node blocks in this figure. They can remain as runtime/interface
concepts elsewhere, but the figure should only show explicitly intended
physical nodes or representative physical interfaces.

## 5. Mac Mini Operational Hub Area

Container:

```text
x=430 y=115 w=780 h=650
```

Recommended internal columns:

```text
left column: intake, aggregation, LLM adapter
middle column: policy, validator, Class 2
right column: dispatch, caregiver backend, telemetry
bottom row: ACK handler and audit logging
```

Blocks:

| Block | X | Y | W | H |
| --- | ---: | ---: | ---: | ---: |
| MQTT / Context Intake | 465 | 175 | 220 | 78 |
| State Aggregation | 465 | 275 | 220 | 78 |
| Local LLM Adapter | 465 | 375 | 220 | 78 |
| Policy Router | 720 | 175 | 220 | 78 |
| Deterministic Validator | 720 | 275 | 220 | 78 |
| Class 2 Clarification Manager | 720 | 375 | 220 | 92 |
| Context-Integrity Safe Deferral | 720 | 490 | 220 | 78 |
| Low-Risk Dispatcher | 975 | 175 | 200 | 78 |
| Caregiver Notification / Confirmation | 975 | 295 | 200 | 100 |
| Read-Only Telemetry Adapter | 975 | 430 | 200 | 78 |
| ACK Handler | 570 | 610 | 230 | 72 |
| Audit Logging Service | 835 | 610 | 230 | 72 |

Mac mini footer label:

```text
Mac mini operational hub
policy, validation, dispatch, caregiver handling, ACK, audit
```

## 6. Caregiver / Telegram Area

Container:

```text
x=1260 y=115 w=470 h=300
```

Blocks:

| Block | X | Y | W | H |
| --- | ---: | ---: | ---: | ---: |
| Telegram Bot API | 1300 | 180 | 180 | 78 |
| Caregiver | 1510 | 180 | 180 | 78 |
| Caregiver Response / Confirmation | 1400 | 305 | 230 | 78 |

Routing idea:

```text
Mac mini caregiver backend -> Telegram Bot API -> Caregiver
Caregiver -> Telegram Bot API -> Mac mini caregiver backend
```

Use a caregiver lane outside the Mac mini box. Do not draw Telegram as a policy
authority block.

## 7. Raspberry Pi Experiment Support Area

Container:

```text
x=1260 y=455 w=470 h=520
```

Blocks:

| Block | X | Y | W | H |
| --- | ---: | ---: | ---: | ---: |
| Web Experiment Dashboard | 1290 | 535 | 190 | 62 |
| Experiment Manager | 1505 | 535 | 190 | 62 |
| Scenario Manager | 1290 | 620 | 190 | 62 |
| Virtual Node Manager | 1505 | 620 | 190 | 62 |
| Virtual Behavior / Fault Injection | 1290 | 705 | 190 | 74 |
| MQTT / Interface Status Manager | 1505 | 705 | 190 | 74 |
| Result Store / Analysis | 1290 | 805 | 190 | 62 |
| MQTT / Payload Governance Support | 1505 | 805 | 190 | 62 |

RPi footer label:

```text
Raspberry Pi experiment support
non-authoritative simulation, monitoring, governance, and results
```

The area is placed high enough to make the experiment support role visible
without pushing STM32 and canonical assets below the physical-node baseline.

## 8. STM32 Timing / Measurement Area

Container:

```text
x=430 y=840 w=780 h=130
```

Blocks:

| Block | X | Y | W | H |
| --- | ---: | ---: | ---: | ---: |
| STM32 Timing / Measurement Node | 470 | 915 | 240 | 34 |
| Capture Channels | 750 | 915 | 190 | 34 |
| Measurement Export | 980 | 915 | 190 | 34 |

Use a distinct measurement style, such as dashed border or blue-gray color.

Route measurement output toward RPi result store / analysis. Do not route it
into Mac mini policy or validator blocks.

## 9. Canonical Assets / Contracts Area

Container:

```text
x=430 y=1000 w=1300 h=105
```

Suggested block:

```text
Canonical Assets / Contracts
policies, schemas, MQTT registry, payload contracts, scenario contracts
```

Draw as a reference band. Connect with light dashed “loads/validates against”
lines only if the figure remains readable.

The lower edge of this band aligns with the lower edge of `Actual Physical
Nodes` so the left and bottom structure read as one stable frame.

## 10. Arrow Lane Plan

This step does not draw final arrows, but the layout reserves these lanes:

| Lane | Coordinates | Flow |
| --- | --- | --- |
| L1 physical input lane | x 380-430 | Physical nodes -> Mac mini intake |
| L2 operational internal lanes | inside Mac mini, column-to-column | Intake -> aggregation -> policy/validator -> dispatch |
| L3 feedback lane | left of Mac mini bottom edge | Mac mini -> user-facing output path |
| L4 ACK lane | lower left-to-center | Lighting/physical ACK -> ACK Handler -> Audit |
| L5 caregiver lane | x 1210-1260 and y 220-350 | Mac mini caregiver backend <-> Telegram <-> Caregiver |
| L6 RPi observation lane | x 1210-1260 and y 500-800 | Mac mini telemetry/audit summary -> RPi dashboard/apps |
| L7 RPi experiment input lane | x 1210-1260 and y 585-720 | RPi virtual/scenario input -> Mac mini intake |
| L8 measurement lane | y 940-1015 | STM32 -> RPi result store / analysis |
| L9 canonical reference lane | y 1010-1085 | Components load/validate against canonical assets |

Final arrows should be orthogonal and should not cross block interiors.

## 11. Layout Risks

| Risk | Mitigation |
| --- | --- |
| Mac mini internal blocks become too dense | Keep labels short and use 2-line text |
| RPi area becomes a dashboard/control authority visually | Add explicit non-authoritative footer and avoid control arrows to dispatcher |
| Telegram path looks like direct approval authority | Label it as transport and route approval back to Mac mini backend |
| Physical nodes become too many | Keep labels short and avoid subgroup captions |
| Arrow lanes still collide | Add arrow pass in separate steps after block-only render |

## 12. Step 2 Outcome

The next SVG edit should perform a block-only update:

```text
Step 3. Block-only SVG update
```

Step 3 should not attempt final arrow routing. It should first confirm that:

- all required blocks fit,
- text stays inside blocks,
- the Mac mini remains visually central,
- RPi and STM32 appear as support layers,
- the physical-node area does not imply a separate experiment-only authority.

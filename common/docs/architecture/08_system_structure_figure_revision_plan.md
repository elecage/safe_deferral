# System Structure Figure Revision Plan

## 1. Purpose

This document records the step-by-step plan for revising:

```text
common/docs/architecture/figures/system_layout_final_macmini_only_lshape.svg
```

The figure must be updated so it matches the current active architecture,
prompt-set structure, experiment support model, and safety boundaries.

This plan does not itself change the SVG. It defines the revision sequence and
acceptance criteria so the figure can be improved in controlled steps.

## 2. Current Problems To Fix

### 2.1 Architecture mismatch

The current figure does not fully represent the active system structure:

- Raspberry Pi support is too compressed and does not show the current
  experiment app categories.
- STM32 timing/measurement support is not represented.
- Telegram Bot API caregiver notification is not explicit.
- Class 2 Clarification Manager is not visually separated enough from general
  safe deferral handling.
- Mac mini read-only telemetry for RPi experiment tools is not explicit.
- Actual physical nodes and experiment-only physical nodes are not clearly
  distinguished.
- RPi virtual fault injection should be shown as virtual/experiment support, not
  as a physical fault-injection node.

### 2.2 Layout and readability problems

The revised figure must avoid:

- arrows crossing through blocks,
- multiple same-direction arrows overlapping on the same path,
- text overflowing outside block boundaries,
- overly long labels that require readers to infer missing line breaks,
- visual ambiguity where RPi dashboard/governance support appears to have
  operational authority,
- visual ambiguity where doorbell context appears to authorize doorlock control.

## 3. Target Figure Scope

The revised figure should show these major areas:

1. User
2. Actual physical nodes
3. Experiment-only physical nodes
4. Mac mini operational hub
5. Caregiver / Telegram notification path
6. Raspberry Pi experiment support
7. STM32 timing and measurement support
8. Canonical assets / contracts as repository-governed references, if space
   allows

## 4. Required Mac Mini Blocks

The Mac mini operational hub should include:

- MQTT / context intake
- State aggregation
- Local LLM adapter
- Policy Router
- Deterministic Validator
- Class 2 Clarification Manager
- Context-integrity safe deferral handling
- Low-risk dispatcher
- Caregiver notification / confirmation backend
- ACK handler
- Audit logging service
- Read-only telemetry adapter for RPi tools

The Mac mini area must make clear that it owns policy routing, validation,
operational dispatch, caregiver handling, ACK, and audit.

## 5. Required Raspberry Pi Blocks

The Raspberry Pi support area should include:

- Web experiment dashboard
- Experiment manager for batch runs
- Scenario generation and execution manager
- Virtual node manager
- Virtual behavior / fault injection manager
- MQTT / interface status manager
- Result store and analysis manager
- MQTT / payload governance support

The RPi area must be labeled as non-authoritative experiment support.

It may initiate experiments through controlled experiment/orchestration paths,
but it must not appear to override Policy Router, Deterministic Validator,
caregiver approval, audit, or operational dispatch.

## 6. Required Physical Node Separation

Actual physical nodes should include:

- bounded button input node,
- environmental context node,
- doorbell / visitor context node,
- lighting control node,
- feedback output node,
- device state reporter.

Experiment-only physical nodes should include:

- gas sensor experiment node,
- smoke/fire experiment node,
- fall-detection interface node,
- warning output experiment node,
- doorlock-sensitive interface experiment node.

The figure should not include a physical fault-injection node in the active
baseline. Fault injection should be shown under RPi virtual behavior / fault
injection support.

## 7. Required Caregiver And Telegram Path

The caregiver path should show:

- Mac mini caregiver notification / confirmation backend,
- Telegram Bot API as the primary outbound notification channel,
- caregiver response or confirmation,
- governed manual confirmation path for sensitive actuation,
- ACK and audit evidence after any governed manual sensitive path.

The figure must not imply that Telegram itself is policy authority, validator
authority, or autonomous doorlock authorization.

## 8. Required STM32 Timing Path

The STM32 node should be represented as:

- out-of-band timing / measurement node,
- optional experiment support,
- latency capture and measurement export source,
- not part of the operational control path.

Its arrows should connect to RPi experiment result collection or measurement
export, not to Mac mini policy routing or actuator dispatch as authority.

## 9. Arrow Routing Rules

When editing the SVG:

- Use orthogonal or clearly segmented paths.
- Keep arrow lanes outside block interiors.
- Do not route arrows across unrelated blocks.
- Avoid stacking same-direction arrows on top of each other.
- Separate these flows visually:
  - operational input/context flow,
  - LLM candidate guidance flow,
  - policy/validator/dispatch flow,
  - Class 2 clarification and caregiver flow,
  - ACK/audit flow,
  - RPi experiment/monitoring flow,
  - STM32 timing/measurement flow.
- Use color or line style only to clarify boundaries, not to create new
  authority semantics.

## 10. Text And Label Rules

All labels must:

- fit inside their blocks,
- use explicit line breaks,
- avoid long one-line descriptions,
- prefer concise component names over explanatory paragraphs,
- move long safety notes to a figure footer or legend.

No text should cross a block boundary or overlap other text or arrows.

## 11. Step-By-Step Revision Sequence

### Step 1. Component inventory

Create a table of current SVG blocks and compare them with the required blocks
above. Mark each block as keep, rename, split, remove, or add.

Current output:

- `figure_revision/01_component_inventory.md`

### Step 2. Layout draft

Draft the revised layout before editing detailed arrows:

- left: user and actual physical nodes,
- center: Mac mini operational hub,
- right: caregiver and Telegram path,
- lower or side band: RPi experiment support,
- bottom or detached side area: STM32 timing/measurement support.

Current output:

- `figure_revision/02_layout_draft.md`

### Step 3. Block-only SVG update

Edit the SVG to update containers and blocks, but keep arrows minimal or
temporarily removed. Validate text fit first.

### Step 4. Operational arrow pass

Add only the main operational path:

```text
physical/virtual input -> Mac mini intake -> state aggregation -> policy/router
-> validator -> dispatcher -> physical actuator -> ACK/audit
```

### Step 5. Class 2 and caregiver arrow pass

Add Class 2 clarification, Telegram notification, caregiver response, governed
manual confirmation, ACK, and audit paths.

### Step 6. RPi experiment arrow pass

Add RPi virtual node, virtual behavior/fault injection, scenario execution,
dashboard, telemetry observation, result store, and governance-support flows.

### Step 7. STM32 timing arrow pass

Add STM32 timing capture and measurement export flow without connecting it as
operational authority.

### Step 8. Text and legend pass

Shorten labels, add line breaks, and add a concise legend for authority
boundaries.

### Step 9. Render validation

Render the SVG and visually inspect:

- text fit,
- arrow routing,
- no block-crossing arrows,
- no same-direction arrow overlap,
- no missing major architecture block,
- no authority ambiguity.

### Step 10. Documentation update

Update any active document references if the figure filename or interpretation
changes.

## 12. Acceptance Criteria

The revision is complete when:

- the figure matches the active architecture documents,
- RPi appears as non-authoritative experiment support,
- STM32 appears as out-of-band measurement support,
- Telegram appears as caregiver notification/confirmation transport only,
- actual physical nodes and experiment-only physical nodes are distinguishable,
- physical fault injection is not shown as an active required node,
- all text fits inside blocks,
- arrows do not cross unrelated blocks,
- same-direction arrows do not overlap as a single ambiguous lane,
- and the rendered SVG is readable without consulting legacy documents.

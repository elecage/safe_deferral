# 12_prompts_physical_nodes.md

## Purpose

This prompt set covers actual physical nodes and optional physical evaluation
interfaces used by the prototype or paper experiments.

These nodes are bounded interfaces. They provide input, context, emergency
evidence, warning output, low-risk actuation, or governed sensitive-interface
surfaces. They do not create policy authority, validator authority, caregiver
approval authority, or autonomous high-risk actuation authority.

## Common Instructions

Before implementing any physical node:

- read `01_system_architecture.md`,
- read `02_safety_and_authority_boundaries.md`,
- read `03_payload_and_mqtt_contracts.md`,
- keep device behavior bounded,
- keep policy/routing/validation on the Mac mini,
- align MQTT topics and payloads with canonical registry assets,
- document build, flash, configuration, reconnect, and manual verification
  procedures.

## Prompt PN-01. Bounded Button Input Node

Generate firmware and support notes for the bounded physical input node.

Required behavior:

- detect one or more physical button inputs,
- debounce and normalize input events,
- support bounded clarification selection patterns where policy-aligned,
- support emergency input patterns only when grounded in canonical policy,
- publish input events using registry-aligned topics and schema-compatible
  payloads,
- avoid local interpretation into actuator commands.

Forbidden behavior:

- no local policy routing,
- no local actuator command,
- no invented emergency semantics.

## Prompt PN-02. Lighting Control Node

Generate firmware and support notes for the lighting control node.

Required behavior:

- receive only upstream-approved low-risk lighting commands,
- control `living_room_light` and/or `bedroom_light` as configured for the
  current prototype,
- maintain conservative startup and reconnect state,
- report ACK or state confirmation after execution,
- report device health and last command result.

Forbidden behavior:

- no acceptance of raw LLM candidates,
- no local expansion of the low-risk catalog,
- no non-lighting actuation.

## Prompt PN-03. Environmental Context Node

Generate firmware and support notes for the environmental context node.

Required behavior:

- report bounded context such as temperature, illuminance, occupancy-adjacent
  state, or other schema-supported environmental fields,
- include timestamps or freshness metadata where required by the active design,
- handle invalid readings conservatively,
- avoid local policy classification.

Forbidden behavior:

- no autonomous action based on sensed values,
- no unsupported schema fields.

## Prompt PN-04. Doorbell / Visitor Context Node

Generate firmware and support notes for the visitor context node.

Required behavior:

- report visitor-arrival or doorbell state as
  `environmental_context.doorbell_detected`,
- default non-visitor scenarios to `false`,
- publish context only through registry-aligned topics,
- support test procedures for true/false visitor context states.

Forbidden behavior:

- no door unlock authorization,
- no doorlock state insertion into `pure_context_payload.device_states`,
- no local doorlock control.

## Prompt PN-05. Gas / Smoke / Fire Nodes

Generate firmware and support notes for bounded gas, smoke, or fire evidence
nodes when required by the prototype or experiment plan.

Required behavior:

- publish gas, smoke, or fire evidence in schema-compatible form,
- document sensor readiness, warm-up, invalid reading, and reconnect behavior,
- support repeatable Class 0 evaluation steps,
- keep thresholds aligned with canonical policy and experiment definitions.

Forbidden behavior:

- no local emergency routing authority,
- no invented trigger thresholds outside canonical policy,
- no direct actuator or notification command.

## Prompt PN-06. Fall-Detection Node

Generate firmware and support notes for a bounded fall-detection interface.

Required behavior:

- interface with an IMU, bounded fall detector, or external fall signal source,
- publish fall-related evidence according to current policy/schema
  interpretation,
- handle ambiguous signals conservatively,
- support repeatable fall scenario validation.

Forbidden behavior:

- no arbitrary fall payload,
- no local emergency dispatch beyond evidence reporting.

## Prompt PN-07. Warning Output Node

Generate firmware and support notes for accessible output feedback.

Required behavior:

- support TTS, buzzer, light, display, or other bounded feedback outputs as
  appropriate for the prototype,
- present execution result, clarification choices, warning state, or safe
  deferral state,
- keep output messages short and accessible,
- support ACK or health status where useful.

Forbidden behavior:

- no policy decision from output node,
- no direct actuator approval,
- no hidden caregiver confirmation.

## Prompt PN-08. Doorlock Interface Node

Generate firmware and support notes for a governed representative doorlock
interface node.

Required behavior:

- treat the node as a sensitive-actuation target,
- require explicit upstream governed manual-path assumptions,
- support ACK, timeout, mismatch, and denied-path evaluation variants,
- expose status for dashboard and audit review,
- document how autonomous Class 1 execution is blocked.

Forbidden behavior:

- no autonomous Class 1 door unlock,
- no unlock from `doorbell_detected`,
- no direct dashboard command bypass,
- no treating caregiver confirmation as validator approval.

## Device-State Reporting Note

Device-state reporting is a behavior of the relevant physical node, especially
the lighting control node and context nodes. Do not create a standalone
`Device State Reporter` node unless an implementation later needs a dedicated
adapter for a specific hardware constraint.

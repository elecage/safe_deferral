# 12_prompts_physical_nodes.md

## Purpose

This prompt set covers physical nodes required for the actual prototype
baseline.

These nodes are bounded interfaces. They provide input, context, state, output,
or low-risk actuation surfaces. They do not create policy authority, validator
authority, caregiver approval authority, or autonomous high-risk actuation
authority.

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

## Prompt PN-05. Physical Feedback Output Node

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

## Prompt PN-06. Device State Reporter

Generate firmware or support software for device-state reporting.

Required behavior:

- report current lighting state and node health,
- include freshness-relevant metadata where required,
- support missing-state and stale-state experiment detection,
- distinguish unknown, unavailable, stale, and known states.

Forbidden behavior:

- no assumption that missing state equals safe state,
- no local override of validator behavior.


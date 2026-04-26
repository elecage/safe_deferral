# 12_prompts_stm32_time_sync_node.md

## Purpose

This prompt set covers STM32 timing, synchronization, and measurement support.

The STM32 node is an out-of-band experiment node. It supports latency evidence,
time capture, readiness indication, and export for repeated experiments. It is
not part of the operational control path.

## Common Instructions

Before implementing STM32 support:

- read `integration/measurement/stm32_nucleo_h723zg_measurement_node.md`,
- read `integration/measurement/class_wise_latency_profiles.md`,
- read `integration/measurement/experiment_preflight_readiness_design.md`,
- read `common/docs/required_experiments.md`,
- keep all STM32 behavior measurement-only,
- do not let measurement output become policy, validator, actuator, caregiver,
  or audit authority.

## Prompt STM32-01. Measurement Firmware Skeleton

Generate the STM32 Nucleo-H723ZG measurement firmware skeleton.

Required behavior:

- initialize board, clock, GPIO, timer/counter, and export interface,
- provide startup self-check,
- expose measurement readiness state,
- keep default behavior passive until a measurement session starts,
- document build, flash, reset, and serial/export assumptions.

Forbidden behavior:

- no operational MQTT publishing,
- no actuator control,
- no policy decision.

## Prompt STM32-02. Timing Capture Firmware

Generate timing capture firmware for out-of-band latency measurement.

Required behavior:

- capture trigger, routing, dispatch, ACK, and optional feedback edges where
  physically wired or otherwise instrumented,
- record raw timestamps with channel identifiers,
- support repeated runs,
- handle missed edge, duplicate edge, and overflow cases conservatively.

Forbidden behavior:

- no latency threshold claim unless grounded in active experiment docs,
- no modification of operational behavior.

## Prompt STM32-03. Time Sync And Readiness Reporter

Generate time-sync and readiness reporting support.

Required behavior:

- report local measurement clock state,
- report readiness, degraded, blocked, and unknown conditions,
- support preflight checks from the RPi experiment manager,
- distinguish measurement readiness from operational readiness.

Forbidden behavior:

- no claim of perfect synchronization,
- no blocking or approving operational control decisions.

## Prompt STM32-04. Measurement Export Path

Generate the export path for measurement results.

Required behavior:

- export raw capture rows in CSV-friendly or JSON-friendly format,
- include session ID, channel ID, timestamp, event marker, and quality/status
  fields,
- support transfer to RPi result store,
- include parsing and validation notes if a host-side helper is later added.

Forbidden behavior:

- no direct write to operational audit log as authority,
- no hidden data transformation that prevents reproducibility.

## Prompt STM32-05. Measurement Validation Checklist

Generate validation docs or checks for the measurement node.

Required checks:

- board boots,
- firmware version or build ID is visible,
- timer initializes,
- each configured capture channel detects known test edges,
- export path works,
- RPi preflight sees the node,
- no operational control side effects occur.

Expected outputs:

- machine-readable readiness result,
- human-readable validation summary,
- runbook for repeated class-wise latency experiments.


# 12_prompts_experiment_physical_nodes.md

## Purpose

This prompt set covers experiment-only or extension-stage physical nodes.

These nodes help evaluate robustness, emergency handling, sensitive-actuation
boundaries, and paper experiments. They are not automatically part of the
current autonomous Class 1 baseline.

Use virtual nodes and virtual behavior managers for stale, missing-state,
conflict, delayed-message, and scripted fault-injection experiments by default.
Do not introduce a dedicated physical fault-injection node unless a later
experiment explicitly proves that virtual injection cannot provide the required
evidence.

## Common Instructions

Before implementing any experiment physical node:

- read `common/docs/required_experiments.md`,
- read `07_scenarios_and_evaluation.md`,
- declare whether the node is experiment-only, extension-stage, or planned
  future operational support,
- keep node outputs schema-compatible,
- keep policy routing and validation on the Mac mini,
- do not duplicate the baseline user input button node here unless an experiment
  needs an additional dedicated input rig,
- document how the node is used in experiments and how it is isolated from
  unauthorized operational authority.

## Prompt EPN-01. Gas Sensor Experiment Node

Generate firmware and experiment notes for a gas-sensing physical node.

Required behavior:

- publish gas-related sensing evidence in schema-compatible form,
- support calibration/warm-up notes,
- handle invalid readings conservatively,
- provide repeatable experiment steps for gas-related Class 0 evaluation.

Forbidden behavior:

- no local emergency routing authority,
- no invented gas-trigger threshold outside canonical policy.

## Prompt EPN-02. Smoke / Fire Detection Experiment Node

Generate firmware and experiment notes for smoke or fire-related sensing.

Required behavior:

- publish bounded smoke/fire evidence in schema-compatible form,
- document sensor readiness, warm-up, invalid reading, and reconnect behavior,
- support repeatable Class 0 smoke/fire experiment steps.

Forbidden behavior:

- no local replacement of the Policy Router,
- no unsupported payload field.

## Prompt EPN-03. Fall-Detection Interface Experiment Node

Generate firmware and experiment notes for a fall-detection interface.

Required behavior:

- interface with an IMU, bounded fall detector, or external fall signal source,
- publish fall-related evidence according to current policy/schema
  interpretation,
- handle ambiguous signals conservatively,
- support repeatable fall scenario validation.

Forbidden behavior:

- no arbitrary fall payload,
- no local emergency dispatch beyond evidence reporting.

## Prompt EPN-04. Warning Interface Experiment Node

Generate firmware and experiment notes for warning output hardware.

Required behavior:

- support buzzer, warning light, display cue, or similar output,
- receive only bounded warning commands from the appropriate upstream path,
- default to safe inactive state on boot and reconnect,
- report ACK or health state.

Forbidden behavior:

- no local policy decision,
- no unrestricted alarm spam loop,
- no unrelated actuator control.

## Prompt EPN-05. Doorlock-Sensitive Interface Experiment Node

Generate firmware and experiment notes for a representative doorlock-sensitive
interface node.

Required behavior:

- treat the node as a sensitive-actuation evaluation target,
- require explicit upstream governed manual-path assumptions,
- support ACK, timeout, mismatch, and denied-path experiment variants,
- expose status for dashboard and audit review,
- document how autonomous Class 1 execution is blocked.

Forbidden behavior:

- no autonomous Class 1 door unlock,
- no unlock from `doorbell_detected`,
- no direct dashboard command bypass,
- no treating caregiver confirmation as validator approval.

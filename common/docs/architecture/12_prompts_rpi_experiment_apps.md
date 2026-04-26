# 12_prompts_rpi_experiment_apps.md

## Purpose

This prompt set covers Raspberry Pi experiment-side applications.

The Raspberry Pi is the experiment support host. It may manage experiment
batches, result storage, result analysis, virtual nodes, scenario execution,
interface status, monitoring, web dashboards, and non-authoritative MQTT/payload
governance support.

It is not the safety-critical operational authority.

## Common Instructions

Before implementing any RPi app:

- read `common/docs/required_experiments.md`,
- read `common/docs/architecture/07_scenarios_and_evaluation.md`,
- load canonical assets through `common/asset_manifest.json`,
- keep generated work under `rpi/` or `integration/` as appropriate,
- keep RPi tools non-authoritative,
- do not publish operational actuator or doorlock commands,
- do not override Mac mini Policy Router or Deterministic Validator behavior.

## Prompt RPI-01. Experiment Manager For Paper Batch Runs

Generate the experiment manager that runs paper-oriented experiments in batches.

Required behavior:

- select experiment families from repository-managed metadata,
- run repeated trials,
- record run parameters, timestamps, asset checksums, scenario IDs, and host
  readiness state,
- collect result artifacts from scenario execution, audit observation, and
  optional measurement nodes,
- save machine-readable summaries and paper-friendly Markdown summaries,
- support paused, aborted, failed, and completed run states.

Forbidden behavior:

- no policy decision authority,
- no direct actuator dispatch,
- no silent modification of canonical assets.

## Prompt RPI-02. Result Store And Analysis Manager

Generate the RPi result storage and analysis manager.

Required behavior:

- store experiment outputs under `integration/` result-oriented paths or another
  documented result area,
- aggregate repeated-run summaries,
- compute metrics required by `common/docs/required_experiments.md`,
- generate CSV/JSON/Markdown exports,
- preserve enough metadata for reproducibility,
- distinguish operational results from measurement-only results.

Forbidden behavior:

- no alteration of scenario contracts during analysis,
- no treating analysis output as operational authority.

## Prompt RPI-03. Virtual Node Manager

Generate the virtual-node manager for controlled experiment nodes.

Required behavior:

- create, configure, start, stop, and delete virtual nodes,
- support virtual context nodes, virtual device-state reporters, virtual
  emergency event nodes, virtual doorbell/visitor context nodes, and virtual
  actuator observers,
- provide deterministic profiles for repeated experiments,
- publish only registry-aligned experiment traffic,
- keep all virtual node events auditable and reproducible.

Forbidden behavior:

- no production-device authority,
- no direct Policy Router override,
- no autonomous doorlock authorization from virtual visitor context.

## Prompt RPI-04. Virtual Behavior Execution Manager

Generate the manager that controls virtual behavior execution.

Required behavior:

- run scripted virtual behaviors such as normal context, stale state, missing
  state, conflict, emergency evidence, caregiver response variants, and ACK
  variants,
- own fault-injection execution by default, including stale, missing-state,
  delayed, conflicting, degraded, timeout/no-response, and caregiver/ACK branch
  variants,
- support deterministic replay and stress modes,
- record behavior profile, seed if used, start/stop time, and observed topic
  traffic,
- expose progress to dashboard and experiment manager.

Forbidden behavior:

- no invented policy thresholds,
- no hidden random behavior without recorded seed,
- no direct operational actuator control.

## Prompt RPI-05. Scenario Generation And Execution Manager

Generate the scenario manager.

Required behavior:

- load scenario contracts from `integration/scenarios/`,
- optionally generate draft scenarios for review without silently changing active
  scenario contracts,
- execute selected scenarios against Mac mini runtime or controlled mocks,
- support scenario families for Class 0, Class 1, Class 2 transitions, stale,
  missing-state, conflict, and doorlock-sensitive visitor-response evaluation,
- collect expected vs observed outcomes,
- emit JSON and Markdown reports.

Forbidden behavior:

- no scenario-generated expansion of autonomous Class 1 authority,
- no treating expected outcomes as validator approval.

## Prompt RPI-06. MQTT And Interface Status Manager

Generate the MQTT/interface status manager.

Required behavior:

- monitor broker connectivity, topic visibility, publisher/subscriber presence,
  payload family conformance, and interface health,
- load topic definitions from `common/mqtt/topic_registry.json`,
- validate topic use against `common/mqtt/publisher_subscriber_matrix.md` and
  `common/mqtt/topic_payload_contracts.md`,
- report dashboard/governance topics as non-authoritative,
- detect missing, unexpected, stale, or unauthorized topic traffic.

Forbidden behavior:

- no direct publishing of operational control topics,
- no direct registry file editing,
- no interface-status warning that grants authority.

## Prompt RPI-07. Experiment Preflight Readiness Manager

Generate the preflight readiness manager.

Required behavior:

- evaluate READY, DEGRADED, BLOCKED, and UNKNOWN states before a run,
- check Mac mini services, RPi apps, virtual nodes, physical nodes, MQTT,
  canonical assets, result-store writability, and optional measurement nodes,
- produce machine-readable readiness reports,
- expose blocked reasons suitable for dashboard display.

Forbidden behavior:

- no automatic policy relaxation when degraded,
- no running sensitive experiments when required authority checks are missing.

## Prompt RPI-08. Web-Based Experiment Monitoring Dashboard

Generate the RPi-hosted web dashboard.

Recommended form:

- web application served from the Raspberry Pi,
- browser-based UI usable from the Mac mini, laptop, tablet, or the Pi itself,
- optional installable PWA behavior if useful,
- no native desktop/mobile app requirement unless a later usability study
  explicitly needs it.

Required behavior:

- show experiment selection, preflight state, node status, MQTT/interface status,
  scenario progress, run controls, result summaries, and export links,
- show Class 2 clarification state, timeout/no-response state, caregiver
  confirmation state, and ACK state where relevant,
- show Telegram notification delivery state and caregiver response state when
  caregiver escalation experiments are active,
- show doorlock-sensitive evaluation status without exposing direct doorlock
  controls,
- call backend services for all create/update/delete/run/export actions.

Forbidden behavior:

- no direct registry-file editing,
- no direct operational topic publishing,
- no unrestricted actuator console,
- no direct doorlock command button.

## Prompt RPI-09. MQTT/Payload Governance Backend

Generate the MQTT/payload governance backend.

Required behavior:

- browse and validate topic registry entries,
- manage draft topic/payload proposals,
- validate payload examples against schemas,
- validate `safe_deferral/clarification/interaction` as evidence-only,
- export review reports,
- preserve draft/proposed/committed distinctions.

Forbidden behavior:

- no direct policy/schema edits,
- no direct operational subscription mutation,
- no conversion of governance reports into operational authority.

## Prompt RPI-10. MQTT/Payload Governance UI

Generate the governance UI that sits on top of the governance backend.

Required behavior:

- browse topics, payload families, schemas, examples, publisher/subscriber roles,
  authority levels, and validation reports,
- show clarification interaction and doorbell/doorlock boundary warnings,
- show diff/proposed-change previews,
- use backend APIs for validation and export.

Forbidden behavior:

- no direct file writes,
- no direct operational control publish,
- no caregiver approval spoofing,
- no dashboard control authority.

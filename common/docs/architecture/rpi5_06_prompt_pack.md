# Raspberry Pi 5 Antigravity Prompt Pack

## 공통 지시문
```
Before writing any code, first submit an Implementation Plan for review and wait for approval.
After implementation, provide:
1. a concise walkthrough of all changes,
2. the exact files created or modified,
3. test results as evidence,
4. any known limitations or follow-up tasks.

Do not invent schemas, thresholds, topic names, or policy rules.
Always read them from the synchronized Phase 0 artifacts first.

The following files must be present locally on Raspberry Pi 5 before implementation:
- policy_table.json
- context_schema.json
- candidate_action_schema.json
- policy_router_input_schema.json
- validator_output_schema.json
- fault_injection_rules.json

All payload generation, fault generation, and scenario orchestration logic must conform 100% to these files.
```

## Prompt 1. Virtual Sensor Node Generator

```
Implement Python-based virtual MQTT sensor publishers for Raspberry Pi 5.

Requirements:
- Read payload structure from `context_schema.json`.
- Publish periodic normal context data for:
  - temperature
  - illuminance
  - occupancy
  - device states
  - doorbell event
- Each virtual node must support:
  - unique node_id
  - topic namespace
  - configurable publish interval
  - deterministic context profile
- Do not hardcode field names outside the synced schema artifacts.
- Include unit tests for payload schema compliance.
```

## Prompt 2. Emergency Simulator

```
Implement Python-based emergency sensor publishers for Raspberry Pi 5.

Requirements:
- Parse emergency rules from `policy_table.json`.
- Generate Class 0-triggering events for:
  - gas leak
  - smoke/fire
  - possible fall
- For each emergency rule, derive the minimal triggering predicate dynamically.
- If the rule is composite, generate the minimal sensor combination needed to satisfy it.
- Support deterministic scenario replay.
- Include tests that verify generated payloads satisfy the policy-defined trigger conditions.
```

## Prompt 3. Fault Injector Harness

```
Implement a Python fault injector harness for Raspberry Pi 5.

Requirements:
- Do NOT hardcode arbitrary fault values.
- Parse thresholds, freshness bounds, required keys, and admissibility-related fields from:
  - policy_table.json
  - context_schema.json
  - fault_injection_rules.json

Implement the following fault categories separately:

A. Threshold-crossing emergency injection
- Derive the minimal triggering predicate from policy rules.
- If single-threshold based, exceed the threshold explicitly.
- If composite, generate the minimal required combination.

B. Context conflict injection
- Inject conditions such that multiple bounded low-risk action candidates remain simultaneously admissible for the same actuator.
- The fault generator must also label the expected safe outcome:
  - SAFE_DEFERRAL + iCR if clarification is allowed
  - CLASS_2 escalation if required context remains insufficient
- Under no condition should this test imply autonomous actuation.

C. Sensor/State staleness injection
- Inject timestamps that exceed freshness limits defined in policy artifacts.

D. Missing state injection
- Intentionally omit required keys.
- Distinguish:
  1. policy-input omissions
  2. validator/action-schema omissions

Support two modes:
1. deterministic scripted fault cases
2. randomized stress injection

Record all generated fault metadata for reproducibility.
Prompt 4. Scenario Orchestrator
Implement a scenario orchestrator for Raspberry Pi 5.

Requirements:
- Load scenario definition files
- Launch normal context simulation, emergency simulation, and fault injection in controlled sequences
- Support batch runs
- Save machine-readable run summaries
- Record scenario timestamps and metadata
- Make no direct assumptions about policy rules beyond what is explicitly defined in synchronized artifacts
```

## Prompt 5. Artifact Sync Utility

```
Implement a utility that synchronizes Phase 0 artifacts from the Mac mini source to Raspberry Pi 5.

Requirements:
- Fetch/copy:
  - policy_table.json
  - context_schema.json
  - candidate_action_schema.json
  - policy_router_input_schema.json
  - validator_output_schema.json
  - fault_injection_rules.json
- Verify checksum or version after sync
- Keep the local copy read-only for runtime modules
- Expose synced artifact paths to the rest of the system
```

## Prompt 6. Time Sync Check Utility

```
Implement a time synchronization verification utility for Raspberry Pi 5.

Requirements:
- Check synchronization status against the shared LAN time source
- Measure and log clock offset before experiments
- Report whether the measured offset is within the configured target bound
- Do not claim absolute or perfect millisecond synchronization
- Provide machine-readable output for experiment logs
```

## Prompt 7. Verification Script

```
Implement a verification script for Raspberry Pi 5.

Requirements:
- Verify MQTT broker connectivity
- Verify topic namespace configuration
- Verify artifact sync consistency
- Verify time sync offset measurement
- Verify deterministic scenario reproducibility
- Produce a pass/fail summary and exit nonzero on failure
```
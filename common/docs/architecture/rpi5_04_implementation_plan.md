# Raspberry Pi 5 Implementation Plan

## Project Goal

Build the Raspberry Pi 5 simulation and fault-injection node for Track B so that it can:

  1. generate policy-consistent normal context payloads,
  1. generate Class 0 emergency-triggering payloads,
  1. inject deterministic and randomized faults,
  1. replay scenario-based experiments against the Mac mini edge hub,
  1. automatically verify observed safe outcomes through a closed-loop audit subscription path.

## Role in the Overall Architecture

* Raspberry Pi 5 is **not part of the operational control plane**.
* It is an **evaluation-support node** for Track B.
* All simulation/fault traffic must enter the system through the same MQTT input plane used by Track A devices, rather than bypassing Policy Router directly.
* Verification must be **closed-loop**: Pi 5 publishes test/fault payloads and observes the Mac mini’s audit decision stream.

## Non-Goals

* No Home Assistant installation
* No local LLM runtime
* No direct hardware actuation control
* No independent policy decision logic separate from frozen Phase 0 artifacts

## Core Modules

  1. Virtual Sensor Nodes
  1. Virtual Emergency Sensors
  1. Fault Injector Harness
  1. Scenario Orchestrator
  1. Verification Utilities
  1. Artifact Sync Utility
  1. Time Sync Check Utility

## Milestones

### M1. Phase 0 Artifact Sync Ready

* Sync policy/schema assets from Mac mini
* Verify checksum/version
* Make artifacts available to all Pi-side modules

### M2. Base Runtime Ready

* Python venv prepared
* MQTT client library installed
* CLI utilities installed
* time sync configured against Mac mini as the authoritative local source

### M3. Normal Context Simulation Ready

* Implement virtual sensor publishers
* Implement configurable topic namespace
* Implement repeatable node profiles

### M4. Emergency Simulation Ready

* Implement emergency sensor publishers
* Generate threshold-crossing emergency events according to policy_table.json

### M5. Fault Injection Ready

* Implement stale data injection
* Implement missing state injection
* Implement context conflict injection
* Implement deterministic and randomized modes

### M6. Scenario Orchestration Ready

* Implement scenario runner
* Load expected scenario definitions
* Trigger batches of experiments automatically

### M7. Closed-loop Verification Ready

* Subscribe to a verification-safe audit MQTT stream (e.g., read-only subset of audit/log/#)
* Match observed audit events against expected safe outcomes
* Produce automated pass/fail assertions

### M8. Verification Ready

* MQTT connectivity test
* artifact sync verification
* time sync offset measurement
* throughput/publish stability tests
* reproducibility check
* closed-loop verdict verification
# 01_installation_target_classification.md

## Installation Target Classification and Deployment Boundary Reference

This document defines where each major component of the safe deferral system should be installed, how it should be deployed, and which deployment boundary it belongs to.

It serves as a reference document for:
- system setup
- repository organization
- implementation planning
- deployment-boundary interpretation
- vibe-coding prompts and agent guidance

This document is not the canonical source of policy truth.  
The canonical source of policy, schema, terminology, and other frozen reference assets remains the shared versioned assets in the Git repository.

---

## Classification Table

| Status | Category | Component | Installation Target | Deployment Method | Notes |
|---|---|---|---|---|---|
| **Current Canonical** | System Service | Home Assistant | Mac mini | Individual service / container | Smart-home platform layer |
| **Current Canonical** | System Service | Mosquitto MQTT Broker | Mac mini | Individual service / container | Primary operational broker. Raspberry Pi 5 and ESP32 nodes may connect over the trusted local network |
| **Current Canonical** | System Service | Ollama | Mac mini | Individual service / container | Local LLM runtime |
| **Current Canonical** | System Service | Local TTS Engine (meloTTS / Piper) | Mac mini | Individual service / container | Cloud-independent one-way voice guidance for safe deferral feedback |
| **Current Canonical** | Model Asset | Llama 3.1 | Mac mini | Ollama pull | Local model for Class 1 reasoning pipeline |
| **Current Canonical** | Python App | Policy Router | Mac mini | Python virtual environment | Custom implementation |
| **Current Canonical** | Python App | Deterministic Validator | Mac mini | Python virtual environment | Custom implementation |
| **Current Canonical** | Python App | Context-Integrity Safe Deferral Handler | Mac mini | Python virtual environment | Implements the context-integrity-based safe deferral stage |
| **Current Canonical** | Python App | Outbound Notification Interface | Mac mini | Python virtual environment | Telegram or mock fallback integration |
| **Current Canonical** | Python App | Caregiver Confirmation Backend | Mac mini | Python virtual environment | Bounded caregiver confirmation handling |
| **Current Canonical** | Python App | Audit Logging Service / DB Access Layer | Mac mini | Python virtual environment | SQLite-backed audit pipeline |
| **Current Canonical** | Embedded / Physical Node | ESP32 Button Node | ESP32 device | PlatformIO / Arduino firmware | Physical bounded input node for button-based interaction, including emergency triple-hit input |
| **Current Canonical** | Embedded / Physical Node | ESP32 Lighting Control Node | ESP32 device | PlatformIO / Arduino firmware | Physical low-risk actuator interface for current canonical low-risk actions |
| **Current Canonical** | Embedded / Physical Node | ESP32 Temperature / Humidity Sensor Node | ESP32 device | PlatformIO / Arduino firmware | Physical environmental sensing node for threshold-based emergency or context generation when included in canonical deployment |
| **Current Canonical** | Embedded / Physical Node | ESP32 Doorbell / Visitor-Arrival Context Node | ESP32 device | PlatformIO / Arduino firmware | Bounded visitor-response context node that emits `doorbell_detected` as `environmental_context.doorbell_detected`. It does not authorize doorlock control |
| **Optional Experimental** | Embedded / Physical Node | ESP32 Gas Sensor Node | ESP32 device | PlatformIO / Arduino firmware | Physical safety sensing node for gas-trigger experiments or extended deployment |
| **Optional Experimental** | Embedded / Physical Node | ESP32 Fire Detection Sensor Node | ESP32 device | PlatformIO / Arduino firmware | Physical safety sensing node for smoke/fire-trigger experiments or extended deployment |
| **Optional Experimental** | Embedded / Physical Node | ESP32 Fall Detection Interface Node | ESP32 device or connected sensing subsystem | PlatformIO / Arduino firmware | Physical or hybrid event interface for fall-detection experiments or extended deployment |
| **Planned Extension** | Embedded / Physical Node | ESP32 Doorlock / Warning Interface Node | ESP32 device | PlatformIO / Arduino firmware | Physical bounded output interface for warning actuation or caregiver-mediated doorlock-sensitive evaluation. Doorlock must remain outside autonomous Class 1 low-risk execution unless future frozen policy/schema revisions explicitly promote it |
| **Current Canonical** | Development / Experiment Tool | Virtual Sensor Nodes / Multi-node Simulation Runtime | Raspberry Pi 5 | Python virtual environment | Large-scale virtual sensor/state network for repeatable experiments, including virtual `doorbell_detected` context generation when required. Not an operational hub runtime |
| **Current Canonical** | Development / Experiment Tool | Virtual Emergency Sensors | Raspberry Pi 5 | Python virtual environment | Emergency event simulation for Class 0 and related scenario replay. Not a Mac mini core-runtime replacement |
| **Current Canonical** | Development / Experiment Tool | Fault Injector Harness / Closed-loop Audit Driver | Raspberry Pi 5 | Python virtual environment | Injects stale / missing / conflict / timeout faults, supports automated verification, and may be used with scenario orchestration or verification utilities |
| **Current Canonical** | Development / Experiment Tool | Experiment and Monitoring Dashboard | Raspberry Pi 5 | Python web app / local dashboard UI | Hosts the experiment-side dashboard for scenario selection, node readiness monitoring, progress visualization, closed-loop result summaries, and CSV/graph export. Not a Mac mini core-runtime service |
| **Current Canonical** | Experimental Timing Infrastructure | STM32 Timing Node / Dedicated Timing Node | External measurement node | MCU firmware / hardware timing setup | Out-of-band latency measurement infrastructure for class-wise timing experiments |
| **Current Canonical** | External Integration | Telegram Bot | External API | Account / token configuration | Caregiver alerts and limited approval path |
| **Current Canonical** | Frozen Reference Asset | Policy tables / JSON schemas / terminology / canonical docs | Git repository + synchronized deployment targets | File synchronization / read-only deployment copies | Shared canonical source of truth before runtime deployment |
| **Deployment-Local** | Local Configuration | `.env`, service credentials, host-specific YAML, runtime secrets | Deployment target host | Local file / secret provisioning | Host-local configuration. Not a frozen shared reference asset |

---

## Architectural Interpretation

- **Mac mini** is the primary operational hub.
- **ESP32 devices** are embedded physical nodes for bounded input, sensing, or actuator/warning interfacing.
- **Raspberry Pi 5** is the experiment-side node for scalable simulation, fault injection, scenario orchestration, closed-loop verification, and dashboard-based experiment monitoring.
- **STM32 timing nodes or equivalent dedicated measurement nodes** are used as out-of-band experimental timing infrastructure when precise class-wise latency measurement is required.
- **External APIs** are limited to bounded outbound integrations such as Telegram.
- **Frozen assets in the Git repository** are the single source of truth before runtime deployment.
- **Deployment-local configuration** such as secrets and host-specific runtime files must not be treated as canonical frozen architecture assets.
- `doorbell_detected` is a required visitor-response context signal in `environmental_context`; it supports interpretation of visitor-related scenarios but does not authorize autonomous doorlock control.
- Doorbell / visitor-arrival context may be generated by physical ESP32 nodes or virtual Raspberry Pi simulation nodes, but it must be represented as `environmental_context.doorbell_detected`.

---

## Canonical Operational Boundary

### Mac mini
Mac mini is the canonical operational hub of this system.

Its intended operational role includes:
- Home Assistant runtime
- MQTT operational broker
- local LLM runtime
- local TTS runtime
- Policy Router
- Deterministic Validator
- Context-Integrity Safe Deferral Handler
- Caregiver Confirmation Backend
- Outbound Notification Interface
- Audit Logging Service / DB Access Layer

Mac mini may expose operational telemetry, audit summaries, and control-state topics consumed by the Raspberry Pi 5 experiment dashboard, but it does not host the experiment and monitoring dashboard itself.

### ESP32
ESP32 devices are bounded physical nodes.

Their intended role includes:
- bounded physical button input
- environmental sensing
- doorbell / visitor-arrival context sensing represented as `environmental_context.doorbell_detected`
- emergency sensing or event interfacing
- bounded actuator or warning interfacing

ESP32 doorlock or warning interface nodes may exist for representative or caregiver-mediated evaluation, but ESP32 nodes must not locally reinterpret doorlock as autonomous Class 1 low-risk execution authority.

### Raspberry Pi 5
Raspberry Pi 5 is **not** the primary operational hub of this system.

Its intended role is limited to the experiment-side and evaluation-side path, including:
- multi-node virtual sensor/state simulation
- virtual `doorbell_detected` visitor-response context generation when required for visitor-response or doorlock-sensitive experiments
- virtual emergency event generation
- fault injection
- scenario orchestration
- closed-loop automated verification
- experiment and monitoring dashboard hosting for scenario selection, node readiness, progress visualization, result summaries, and evaluation artifact export
- support utilities such as MQTT checks, time synchronization checks, and result summarization when needed

Accordingly, Raspberry Pi 5 should **not** host the core operational runtime services that belong on the Mac mini, such as:
- Home Assistant
- Ollama
- Policy Router
- Deterministic Validator
- Context-Integrity Safe Deferral Handler
- Audit Logging Service as the operational hub-side authority

Raspberry Pi 5 should instead host only experiment-side runtimes and aligned support assets, typically including:
- Python 3 and virtual environment
- simulation-side Python apps
- fault injection and scenario-running utilities
- experiment and monitoring dashboard runtime and dashboard-side dependencies
- required Pi-side dependencies such as MQTT, schema/policy parsing, CLI, and testing libraries
- time synchronization client
- synchronized runtime copies of frozen policy/schema assets as needed

---

## Canonical Emergency Sensing Targets

The canonical emergency trigger set is determined by the shared policy table.  
At the current canonical policy level, the project recognizes the following emergency trigger families:

- **E001**: high temperature threshold crossing
- **E002**: emergency triple-hit bounded input
- **E003**: smoke detected state trigger
- **E004**: gas detected state trigger
- **E005**: fall detected event trigger

Accordingly, architecture-level sensing or event-generation support for the following emergency classes should be considered policy-aligned:

- temperature emergency sensing
- smoke/fire-related emergency sensing
- gas emergency sensing
- fall event detection or interfacing
- bounded emergency button pattern input

`doorbell_detected` is not an emergency trigger in the current policy family. It is a visitor-response context signal and must not be interpreted as Class 0 emergency evidence or doorlock execution authority.

This architecture document does not override the policy table.  
If the canonical policy table changes, the emergency interpretation in this section must be updated accordingly.

---

## Source-of-Truth Principle

The authoritative source of policy, schema, terminology, and other frozen reference assets is the **Git repository**, especially the shared assets under `common/`.

Deployment targets must not invent local policy truth.  
They should consume synchronized runtime copies derived from the shared frozen reference set.

In particular:
- Mac mini runtime copies are derived from shared frozen assets
- Raspberry Pi 5 runtime copies are derived from shared frozen assets
- ESP32 firmware behavior should remain consistent with the same canonical policy/schema assumptions where applicable

Host-local files such as `.env`, credentials, tokens, and machine-specific YAML are **deployment-local configuration**, not canonical frozen architecture assets.

---

## Measurement Boundary Principle

Raspberry Pi 5 is an experiment and evaluation node, but it is **not** the preferred out-of-band timing node for class-wise latency measurement.

When precise class-wise latency measurement is required, the project should use:
- an **STM32 timing node**, or
- another **dedicated external measurement node**

This keeps the operational service plane and the measurement plane separated.

---

## Repository Mapping

This classification aligns with the repository structure below:

- `common/`
  - shared frozen assets such as policies, schemas, docs, terminology, and canonical references
- `mac_mini/`
  - installation, configuration, verification scripts, runtime assets, and future hub-side code
- `rpi/`
  - installation, configuration, verification scripts, experiment/dashboard runtime, and future simulation-side code
- `esp32/`
  - embedded firmware, device-specific code, and physical node implementation assets
- `integration/`
  - end-to-end tests, experimental scenarios, reproducibility assets, and optional measurement support assets

---

## Deployment Interpretation Notes

- “Current Canonical” means the component is part of the present authoritative deployment or validation baseline.
- “Optional Experimental” means the component is compatible with the current architecture but is not required in every canonical deployment.
- “Planned Extension” means the component is architecturally anticipated but not part of the present minimum canonical operational scope.
- “Deployment-Local” means the component is host-specific and must not be treated as frozen shared policy truth.

---

## Canonical Terminology

The canonical term used in this project is:

**context-integrity-based safe deferral stage**

The previous label **iCR-based safe deferral stage** is deprecated.

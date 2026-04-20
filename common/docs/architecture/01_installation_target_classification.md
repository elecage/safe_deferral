# 01_installation_target_classification.md

## Installation Target Classification

This document defines where each major component of the safe deferral system should be installed and how it should be deployed.

It serves as a deployment-reference document for:
- system setup
- repository organization
- implementation planning
- vibe-coding prompts and agent guidance

---

| Category | Component | Installation Target | Deployment Method | Notes |
|---|---|---|---|---|
| System Service | Home Assistant | Mac mini | Individual service / container | Smart-home platform layer |
| System Service | Mosquitto MQTT Broker | Mac mini | Individual service / container | Primary operational broker. Raspberry Pi 5 and ESP32 nodes may connect over the trusted local network |
| System Service | Ollama | Mac mini | Individual service / container | Local LLM runtime |
| System Service | Local TTS Engine (meloTTS / Piper) | Mac mini | Individual service / container | Cloud-independent one-way voice guidance for safe deferral feedback |
| Model Asset | Llama 3.1 | Mac mini | Ollama pull | Local model for Class 1 reasoning pipeline |
| Python App | Policy Router | Mac mini | Python virtual environment | Custom implementation |
| Python App | Deterministic Validator | Mac mini | Python virtual environment | Custom implementation |
| Python App | Context-Integrity Safe Deferral Handler | Mac mini | Python virtual environment | Implements the context-integrity-based safe deferral stage |
| Python App | Outbound Notification Interface | Mac mini | Python virtual environment | Telegram or mock fallback integration |
| Python App | Caregiver Confirmation Backend | Mac mini | Python virtual environment | Bounded caregiver confirmation handling |
| Python App | Audit Logging Service / DB Access Layer | Mac mini | Python virtual environment | SQLite-backed audit pipeline |
| Embedded / Physical Node | ESP32 Button Node | ESP32 device | PlatformIO / Arduino firmware | Physical bounded input node for button-based interaction |
| Embedded / Physical Node | ESP32 Temperature / Humidity Sensor Node | ESP32 device | PlatformIO / Arduino firmware | Physical environmental sensing node when used |
| Embedded / Physical Node | ESP32 Gas Sensor Node | ESP32 device | PlatformIO / Arduino firmware | Physical safety sensing node when used |
| Embedded / Physical Node | ESP32 Fire Detection Sensor Node | ESP32 device | PlatformIO / Arduino firmware | Physical emergency detection node when used |
| Embedded / Physical Node | ESP32 Lighting Control Node | ESP32 device | PlatformIO / Arduino firmware | Physical low-risk actuator interface when used |
| Embedded / Physical Node | ESP32 Doorlock / Warning Interface Node | ESP32 device | PlatformIO / Arduino firmware | Physical bounded output node for doorlock or warning actuation when used |
| Development / Experiment Tool | Virtual Sensor Nodes / Multi-node Simulation Runtime | Raspberry Pi 5 | Python virtual environment | Large-scale virtual sensor/state network for repeatable experiments. Not an operational hub runtime |
| Development / Experiment Tool | Virtual Emergency Sensors | Raspberry Pi 5 | Python virtual environment | Emergency event simulation for Class 0 and related scenario replay. Not a Mac mini core-runtime replacement |
| Development / Experiment Tool | Fault Injector Harness / Closed-loop Audit Driver | Raspberry Pi 5 | Python virtual environment | Injects stale / missing / conflict / timeout faults, supports automated verification, and may be used with scenario orchestration or verification utilities |
| Experimental Timing Infrastructure | STM32 Timing Node / Dedicated Timing Node | External measurement node | MCU firmware / hardware timing setup | Out-of-band latency measurement infrastructure for class-wise timing experiments |
| External Integration | Telegram Bot | External API | Account / token configuration | Caregiver alerts and limited approval path |
| Frozen Reference Assets | Policy tables / JSON schemas / output profiles / `.env` / YAML | Git repository + deployment targets | File deployment | Frozen shared reference assets before implementation |

---

## Architectural Interpretation

- **Mac mini** is the primary operational hub.
- **ESP32 devices** are embedded physical nodes for bounded input, sensing, or actuator/warning interfacing.
- **Raspberry Pi 5** is the experiment, simulation, and fault-injection node for scalable multi-node and closed-loop verification workflows.
- **STM32 timing nodes or equivalent dedicated measurement nodes** may be used as out-of-band experimental timing infrastructure.
- **External APIs** are limited to bounded outbound integrations such as Telegram.
- **Frozen assets in the Git repository** are the single source of truth before runtime deployment.

---

## Raspberry Pi 5 Deployment Boundary

Raspberry Pi 5 is **not** the primary operational hub of this system.

Its intended role is limited to the experiment-side and evaluation-side path, including:
- multi-node virtual sensor/state simulation
- virtual emergency event generation
- fault injection
- scenario orchestration
- closed-loop automated verification
- supporting verification utilities such as MQTT checks, time synchronization checks, and result summarization when needed

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
- required Pi-side dependencies such as MQTT, schema/policy parsing, CLI, and testing libraries
- time synchronization client
- synchronized runtime copies of frozen policy/schema assets as needed

### Source-of-truth principle
The authoritative source of policy, schema, terminology, and other frozen reference assets is the **Git repository**, especially the shared assets under `common/`.

Raspberry Pi 5 must not invent local policy truth.  
It should consume synchronized runtime copies derived from the shared frozen reference set.

### Measurement boundary principle
Raspberry Pi 5 is an experiment and evaluation node, but it is **not** the preferred out-of-band timing node for class-wise latency measurement.

When precise class-wise latency measurement is required, the project may use:
- an **STM32 timing node**, or
- another **dedicated external measurement node**

This keeps the operational service plane and the measurement plane separated.

---

## Repository Mapping

This classification aligns with the repository structure below:

- `common/`
  - shared frozen assets such as policies, schemas, docs, and terminology
- `mac_mini/`
  - installation, configuration, verification scripts, runtime assets, and future hub-side code
- `rpi/`
  - installation, configuration, verification scripts, and future simulation-side code
- `esp32/`
  - embedded firmware, device-specific code, and physical node implementation assets
- `integration/`
  - end-to-end tests, experimental scenarios, reproducibility assets, and optional measurement support assets

---

## Canonical Terminology

The canonical term used in this project is:

**context-integrity-based safe deferral stage**

The previous label **iCR-based safe deferral stage** is deprecated.
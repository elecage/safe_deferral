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
| Development / Experiment Tool | Virtual Sensor Nodes / Multi-node Simulation Runtime | Raspberry Pi 5 | Python virtual environment | Large-scale virtual sensor/state network for repeatable experiments |
| Development / Experiment Tool | Virtual Emergency Sensors | Raspberry Pi 5 | Python virtual environment | Emergency event simulation |
| Development / Experiment Tool | Fault Injector Harness / Closed-loop Audit Driver | Raspberry Pi 5 | Python virtual environment | Injects stale / missing / conflict / timeout faults and supports automated verification |
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
  - end-to-end tests, experimental scenarios, and reproducibility assets

---

## Canonical Terminology

The canonical term used in this project is:

**context-integrity-based safe deferral stage**

The previous label **iCR-based safe deferral stage** is deprecated.
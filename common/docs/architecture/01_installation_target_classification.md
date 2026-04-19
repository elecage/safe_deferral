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
| System Service | Mosquitto MQTT Broker | Mac mini | Individual service / container | Primary operational broker. Raspberry Pi 5 may be used only for development or experiments |
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
| Embedded / Physical Node | ESP32 Sensor Node | ESP32 device | PlatformIO / Arduino firmware | Physical sensor/event publishing node when used |
| Embedded / Physical Node | ESP32 Actuator / Warning Interface Node | ESP32 device | PlatformIO / Arduino firmware | Low-risk actuator or warning-output interface when used |
| Development / Experiment Tool | Virtual Sensor Nodes | Raspberry Pi 5 | Python virtual environment | Large-scale virtual sensor network |
| Development / Experiment Tool | Virtual Emergency Sensors | Raspberry Pi 5 | Python virtual environment | Emergency event simulation |
| Development / Experiment Tool | Fault Injector Harness | Raspberry Pi 5 | Python virtual environment | Injects stale / missing / conflict / timeout faults |
| External Integration | Telegram Bot | External API | Account / token configuration | Caregiver alerts and limited approval path |
| Frozen Reference Assets | Policy tables / JSON schemas / output profiles / `.env` / YAML | Git repository + deployment targets | File deployment | Frozen shared reference assets before implementation |

---

## Architectural Interpretation

- **Mac mini** is the primary operational hub.
- **ESP32 devices** are embedded physical nodes for bounded input, sensing, or actuator/warning interfacing.
- **Raspberry Pi 5** is the experiment and simulation node.
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
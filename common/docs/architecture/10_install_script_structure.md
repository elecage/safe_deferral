# 10_install_script_structure.md

## Install Script Structure

## Goal
Install the required components for the Mac mini and Raspberry Pi 5 in a way that is:

- rerunnable where possible
- stage-verifiable
- device-aware
- aligned with the frozen asset strategy
- suitable for vibe-coding and reproducible bring-up

---

## Core Principles

- Use **bash/zsh shell scripts** on macOS rather than platform-specific batch tooling.
- Keep **installation**, **configuration**, and **verification** separated.
- Install Python-based applications inside **virtual environments**.
- Treat the Mac mini as the **primary operational hub**.
- Treat the Raspberry Pi 5 as the **simulation and evaluation node**.
- Ensure scripts fail fast and emit clear logs.
- Complete **shared frozen assets** before implementation-side installation logic depends on them.

---

## Repository-Aligned Script Structure

```text
safe_deferral/
├── common/
│   ├── policies/
│   ├── schemas/
│   ├── docs/
│   │   └── architecture/
│   └── terminology/
├── mac_mini/
│   ├── scripts/
│   │   ├── install/
│   │   ├── configure/
│   │   └── verify/
│   ├── runtime/
│   └── code/
├── rpi/
│   ├── scripts/
│   │   ├── install/
│   │   ├── configure/
│   │   └── verify/
│   └── code/
└── integration/
    ├── tests/
    └── scenarios/
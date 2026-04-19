# 04_project_directory_structure.md

## Recommended Project Directory Structure

This document defines the recommended repository structure for the safe deferral system.

It reflects:
- the current frozen asset strategy
- device-level separation between Mac mini and Raspberry Pi
- the distinction between shared assets, operational scripts, and integration assets
- the canonical terminology of the project

---

## Repository Root Structure

```text
safe_deferral/
├── README.md
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
│   ├── code/
│   └── docs/
├── rpi/
│   ├── scripts/
│   │   ├── install/
│   │   ├── configure/
│   │   └── verify/
│   ├── code/
│   └── docs/
└── integration/
    ├── tests/
    └── scenarios/
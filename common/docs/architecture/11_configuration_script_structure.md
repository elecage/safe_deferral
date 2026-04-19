# 11_configuration_script_structure.md

## Configuration Script Structure

## Goal
Configure installed services and runtimes so that they are aligned with the current safe deferral architecture in a consistent and reproducible way.

---

## Core Principles

- Keep **configuration** separate from installation and verification.
- Write configuration scripts so they **copy templates or deploy frozen assets and inject only the necessary values**.
- Store sensitive values in `.env` or separate secret files, and never commit live secrets to Git.
- Always follow configuration with verification.
- Treat shared frozen assets in `common/` as the **single source of truth** before runtime deployment.
- Inject configuration into the **actual target runtime path** rather than hardcoding paths inside templates.
- Include a **reload or restart step** when required after configuration changes are applied.
- Allow service restart behavior to branch according to the **deployment mode**.
- Complete the shared frozen asset set before implementation-side configuration depends on it.

---

## Shared Frozen Assets Required Before Configuration

The following assets should be finalized before configuration deployment depends on them:

### Shared policy assets
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_0_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- `common/policies/output_profile_v1_0_0.json`

### Shared schema assets
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_0_0_FROZEN.json`

### Terminology asset
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

These are not just deployment files.  
They are design assets that must be fixed before reliable runtime configuration is possible.

---

## Repository-Aligned Directory Structure

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
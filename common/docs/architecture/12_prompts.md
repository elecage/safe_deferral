# 12_prompts.md

## Vibe-Coding Prompt Set

The following prompts are intended for Google Antigravity or similar agent-first development tools.

They are designed to generate implementation artifacts that conform to:
- the frozen shared assets
- the current repository structure
- the canonical terminology of the project
- the Mac mini / Raspberry Pi role separation

---

## Common Instruction Block (apply to all prompts)

```text
Before writing any code, first submit an Implementation Plan for review and wait for approval.

After implementation, provide:
1. a concise walkthrough of all changes,
2. the exact files created or modified,
3. test results as evidence,
4. any known limitations or follow-up tasks.

Do not invent schemas, thresholds, policy rules, timeout values, or action domains.
Always read them from the provided frozen artifacts first.

The following frozen artifacts must be loaded into the agent knowledge base before implementation:
- common/policies/policy_table_v1_1_2_FROZEN.json
- common/policies/low_risk_actions_v1_0_0_FROZEN.json
- common/policies/fault_injection_rules_v1_4_0_FROZEN.json
- common/policies/output_profile_v1_0_0.json
- common/schemas/context_schema_v1_0_0_FROZEN.json
- common/schemas/candidate_action_schema_v1_0_0_FROZEN.json
- common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json
- common/schemas/validator_output_schema_v1_0_0_FROZEN.json
- common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md

All parsing, validation, and generation logic must conform to those artifacts.
Do not use deprecated terminology such as:
- iCR
- iCR Handler
- iCR mapping

Use the canonical term:
context-integrity-based safe deferral stage
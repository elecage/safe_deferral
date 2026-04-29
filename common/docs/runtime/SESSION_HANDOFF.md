# SESSION_HANDOFF.md

## Purpose

This file is the runtime handoff **index** for the `safe_deferral` project.

The previous long-running master handoff has been preserved as:

- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_MASTER_LEGACY_HANDOFF.md`

Read this index first, then the latest dated addenda relevant to the current task.

If older wording in the legacy master handoff conflicts with newer dated addenda, prefer the newer dated addenda.

---

## Current priority read order

For current implementation status, experiment readiness, hardware validation,
setup documentation, and all prior architecture/policy/schema/MQTT work, read
in this order:

1. `common/docs/runtime/SESSION_HANDOFF_2026-04-29_CODE_REVIEW_FIX_PLAN.md`
2. `common/docs/runtime/SESSION_HANDOFF_2026-04-28_TELEMETRY_NOTIFICATION_BUGFIX_UPDATE.md`
2. `common/docs/runtime/SESSION_HANDOFF_2026-04-28_CODE_REVIEW_BUGFIX_UPDATE.md`
3. `common/docs/runtime/SESSION_HANDOFF_2026-04-28_PHASE1_FIXTURE_BOM_UPDATE.md`
2. `common/docs/runtime/SESSION_HANDOFF_2026-04-28_ENTRYPOINT_AND_RUN_DOC_UPDATE.md`
2. `common/docs/runtime/SESSION_HANDOFF_2026-04-28_IMPLEMENTATION_COMPLETE_UPDATE.md`
3. `common/docs/runtime/SESSION_HANDOFF_2026-04-26_DOCUMENTATION_CONTRACT_CLEANUP_UPDATE.md`
2. `common/docs/runtime/SESSION_HANDOFF_2026-04-26_PAYLOAD_EXAMPLES_AND_SCENARIO_ALIGNMENT_MERGE_UPDATE.md`
3. `common/docs/runtime/SESSION_HANDOFF_2026-04-26_CLASS2_POLICY_SCHEMA_INTERFACE_ALIGNMENT_MERGE_UPDATE.md`
4. `common/docs/runtime/SESSION_HANDOFF_2026-04-26_CLASS2_ARCHITECTURE_DOC_ALIGNMENT_UPDATE.md`
5. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_OV_PHASE2_BACKGROUND_RETRY_STATUS.md`
6. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_OV_PHASE1_SCAFFOLD_UPDATE.md`
7. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_OV_FIGURE_DEVELOPMENT_PLAN.md`
8. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_TOPIC_REGISTRY_ROLE_VERIFIER_CLAUDE_PROMPT_TODO.md`
9. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_TOPIC_REGISTRY_ROLE_METADATA_V1_1_UPDATE.md`
10. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_MQTT_CONTEXT_INPUT_PUBLISHER_ALIGNMENT_UPDATE.md`
11. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_SCENARIO_DATA_FLOW_INTERFACE_ROLE_ALIGNMENT_UPDATE.md`
12. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_SCENARIO_DATA_FLOW_MATRIX_UPDATE.md`
13. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_SCENARIO_DATA_FLOW_MATRIX_PLAN.md`
14. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE9_VERIFICATION_SWEEP_UPDATE.md`
15. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE8_INTEGRATION_TEST_ADAPTER_UPDATE.md`
16. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE7_VERIFIER_UPDATE.md`
17. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE6_TEST_FIXTURE_EXPANSION_UPDATE.md`
18. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE5_SCENARIO_JSON_ALIGNMENT_UPDATE.md`
19. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE4_SCENARIO_DOC_ALIGNMENT_UPDATE.md`
20. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE3_SCHEMA_PAYLOAD_TOPIC_ALIGNMENT_UPDATE.md`
21. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE2_POLICY_BASELINE_ALIGNMENT_UPDATE.md`
22. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE1_ARCHITECTURE_ALIGNMENT_UPDATE.md`
23. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE0_FROZEN_BASELINE_AUDIT.md`
24. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_SCENARIO_POLICY_SCHEMA_VERIFY_UPDATE_PLAN_V2.md`
25. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_CLASS2_CLARIFICATION_TRANSITION_IMPACT_PLAN.md`
26. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_SCENARIO_ALIGNMENT_UPDATE.md`
27. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_SCENARIO_ALIGNMENT_PLAN.md`
28. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_SYSTEM_LAYOUT_FIGURE_REVISION_UPDATE.md`
29. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_ESP32_SCRIPT_ALIGNMENT_UPDATE.md`
30. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_RPI_SCRIPT_ALIGNMENT_UPDATE.md`
31. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_MAC_MINI_INSTALL_CONFIG_VERIFY_ALIGNMENT_UPDATE.md`
32. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_SYSTEM_LAYOUT_FIGURE_REVISION_PLAN.md`
33. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_ESP32_SCRIPT_ALIGNMENT_PLAN.md`
34. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_RPI_SCRIPT_ALIGNMENT_PLAN.md`
35. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_POLICY_SCHEMA_MQTT_PAYLOAD_ALIGNMENT_UPDATE.md`
36. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_MQTT_PAYLOAD_GOVERNANCE_AND_ARCH_DOC_ALIGNMENT_UPDATE.md`
37. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_ARCHITECTURE_DOC_CONSOLIDATION_AND_PAYLOAD_REGISTRY_UPDATE.md`
38. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_DOORBELL_VISITOR_CONTEXT_UPDATE.md`
39. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_DOC_ALIGNMENT_UPDATE.md`
40. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_POLICY_SCHEMA_ALIGNMENT_UPDATE.md`
41. `common/docs/runtime/SESSION_HANDOFF_2026-04-24_DASHBOARD_TEST_APP_AND_ORCHESTRATION_UPDATE.md`
42. `common/docs/runtime/SESSION_HANDOFF_2026-04-24_PROMPT_REFACTOR_AND_EVAL_UPDATE.md`
43. `common/docs/runtime/SESSION_HANDOFF_2026-04-25_MASTER_LEGACY_HANDOFF.md`

Use the legacy handoff as historical context and operational history, not as the final authority when it conflicts with newer addenda.

---

## Addendum update rule

For future major changes:

1. Add a new dated addendum in `common/docs/runtime/`.
2. Update this index with the new addendum near the top of the priority read order.
3. Do not rewrite the legacy handoff unless performing a deliberate consolidation pass.
4. If the new addendum supersedes older wording, state that explicitly in the new addendum.

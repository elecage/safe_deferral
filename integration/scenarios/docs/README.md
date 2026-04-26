# integration/scenarios/docs

This directory contains the split review guide for `integration/scenarios/`.

The former monolithic file:

```text
integration/scenarios/scenario_review_guide.md
```

was split into topic-focused guide files to reduce edit conflicts and make future Class 2 scenario expansion easier.

These files are developer-oriented review guidance. They do not define policy authority, schema authority, MQTT authority, or execution authority.

Current baseline references:

```text
common/policies/policy_table_v1_2_0_FROZEN.json
common/policies/low_risk_actions_v1_1_0_FROZEN.json
common/policies/fault_injection_rules_v1_4_0_FROZEN.json
common/schemas/context_schema_v1_0_0_FROZEN.json
common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json
common/schemas/validator_output_schema_v1_1_0_FROZEN.json
common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
common/mqtt/topic_registry_v1_1_0.json
common/mqtt/topic_payload_contracts_v1_0_0.md
common/payloads/examples/clarification_interaction_two_options_pending.json
```

Historical baselines:

```text
common/policies/policy_table_v1_1_2_FROZEN.json
common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json
common/mqtt/topic_registry_v1_0_0.json
```

## Split guide files

Read in this order:

1. `scenario_review_principles.md`
2. `scenario_review_class0_class1.md`
3. `scenario_review_class2.md`
4. `scenario_review_faults.md`

## Why the guide was split

The old monolithic review guide was long and difficult to update through GitHub contents operations. Splitting it reduces SHA conflicts, makes Class 2 scenario expansion easier, and separates general review rules from class-specific and fault-specific guidance.

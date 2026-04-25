# SESSION_HANDOFF_2026-04-25_PHASE3_SCHEMA_PAYLOAD_TOPIC_ALIGNMENT_UPDATE.md

Date: 2026-04-25
Scope: Phase 3 schema / payload / topic alignment for Class 2 clarification/transition semantics
Status: Phase 3 completed.

## 1. Purpose

This handoff addendum records the completion of Phase 3 from:

```text
common/docs/runtime/SESSION_HANDOFF_2026-04-25_SCENARIO_POLICY_SCHEMA_VERIFY_UPDATE_PLAN_V2.md
```

Phase 3 focused on schema, payload, and topic alignment after:

```text
common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE0_FROZEN_BASELINE_AUDIT.md
common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE1_ARCHITECTURE_ALIGNMENT_UPDATE.md
common/docs/runtime/SESSION_HANDOFF_2026-04-25_PHASE2_POLICY_BASELINE_ALIGNMENT_UPDATE.md
```

---

## 2. Phase 3 decisions

### 2.1 Context schema

Left unchanged:

```text
common/schemas/context_schema_v1_0_0_FROZEN.json
```

Reason:

```text
Class 2 clarification data is an interaction/control payload family, not pure operational context. The current context schema should remain a strict context envelope for trigger_event, environmental_context, and device_states.
```

### 2.2 MQTT topic registry

Left unchanged:

```text
common/mqtt/topic_registry_v1_0_0.json
```

Reason:

```text
Existing deferral, escalation, caregiver confirmation, context input, and audit topics remain sufficient for Phase 3. Dedicated clarification topics are not required yet.
```

Existing topics remain usable for Class 2 flow:

```text
safe_deferral/context/input
safe_deferral/deferral/request
safe_deferral/escalation/class2
safe_deferral/caregiver/confirmation
safe_deferral/audit/log
```

---

## 3. New schema files

### 3.1 Class 2 notification schema v1.1.0

Added:

```text
common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json
```

Purpose:

```text
Extends the Class 2 notification payload schema for Class 2 clarification/transition semantics and supports C206/C207 trigger IDs introduced by policy_table_v1_2_0_FROZEN.json.
```

Key changes from v1.0.0:

```text
- Supports C201-C207 instead of only C201-C205.
- Adds class2_clarification_manager as a source_layer.
- Adds tts and display as possible notification channels.
- Describes Class 2 clarification notification payloads in addition to caregiver escalation.
```

Historical schema preserved:

```text
common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json
```

### 3.2 Clarification interaction schema v1.0.0

Added:

```text
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
```

Purpose:

```text
Defines Class 2 clarification interaction artifacts: bounded candidate choices, presentation channel, user/caregiver selection, timeout/no-response result, transition target, and LLM boundary.
```

Important boundary:

```text
This schema does not define pure context input, validator approval, actuation command, doorlock authorization, or emergency trigger authority.
```

Core fields:

```text
clarification_id
unresolved_reason
candidate_choices
presentation_channel
selection_result
transition_target
timeout_result
llm_boundary
timestamp_ms
```

LLM boundary fields enforce:

```text
candidate_generation_only = true
final_decision_allowed = false
actuation_authority_allowed = false
emergency_trigger_authority_allowed = false
```

---

## 4. Policy reference update

Updated:

```text
common/policies/policy_table_v1_2_0_FROZEN.json
```

Commit:

```text
157db9cadc824d67ec0837e248bce0ff7a7efa96
```

Changes:

```text
- Class 2 notification schema reference updated to common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json.
- Clarification interaction schema reference updated to common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json.
- implementation_notes now reference class_2_notification_payload_schema_v1_1_0_FROZEN.json and clarification_interaction_schema_v1_0_0_FROZEN.json.
```

---

## 5. Scenario manifest schema update

Updated:

```text
integration/scenarios/scenario_manifest_schema.json
```

Commit:

```text
9c0ed24ff6fd9bdf1ba4a57dec0216da819b40c7
```

Changes:

```text
- Explicitly documents Class 2 clarification/transition fields.
- Adds top-level clarification_interaction property.
- Adds top-level transition_outcomes property.
- Allows step-level candidate_choices.
- Adds expected_outcomes fields for class2_role, candidate_generation_allowed, candidate_generation_authorizes_actuation, confirmation_required_before_transition, and allowed_transition_targets.
- Keeps additionalProperties=true to preserve compatibility with existing scenario skeletons.
```

---

## 6. Payload registry update

Updated:

```text
common/docs/architecture/17_payload_contract_and_registry.md
```

Commits:

```text
72fd73571814d389e001b4fe81650e3168c9fa48
6b1a18122c2d62dda253b4026e100aa8875862b3
```

Changes:

```text
- Active routing policy baseline remains policy_table_v1_2_0_FROZEN.json.
- Class 2 clarification interaction is now listed as schema-governed plus policy-governed.
- Class 2 notification payload now references class_2_notification_payload_schema_v1_1_0_FROZEN.json.
- clarification_interaction_schema_v1_0_0_FROZEN.json is listed as current formal schema, not future-only.
- class_2_notification_payload_schema_v1_0_0_FROZEN.json is listed as historical/superseded.
- pure_context_payload explicitly excludes Class 2 candidate choices, user selections, timeout results, and transition outcomes.
- MQTT topic registry remains stable for now.
```

---

## 7. Topic registry decision

No new topic registry version was created in Phase 3.

Current decision:

```text
common/mqtt/topic_registry_v1_0_0.json remains active.
```

Rationale:

```text
The existing topic set can represent Class 2 clarification flow at the current documentation and scenario level. New dedicated topics such as safe_deferral/clarification/prompt, safe_deferral/clarification/selection, and safe_deferral/clarification/result should be introduced only if runtime implementation requires that separation.
```

---

## 8. Consistency checks performed

Rechecked:

```text
common/policies/policy_table_v1_2_0_FROZEN.json
common/docs/architecture/17_payload_contract_and_registry.md
integration/scenarios/scenario_manifest_schema.json
```

A GitHub search for old/new schema strings was also attempted:

```text
class_2_notification_payload_schema_v1_0_0_FROZEN
clarification_interaction_schema_v1_0_0_FROZEN
```

Note:

```text
The GitHub search connector may be index-lagged. A local grep in a fresh clone is still recommended before final freeze.
```

---

## 9. Files intentionally left unchanged

```text
common/schemas/context_schema_v1_0_0_FROZEN.json
common/mqtt/topic_registry_v1_0_0.json
common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json
```

Reason:

```text
- The context schema remains the strict pure context envelope.
- The topic registry is sufficient for current Class 2 flow.
- Class 2 notification schema v1.0.0 is preserved as historical baseline, superseded by v1.1.0 for active policy v1.2.0.
```

---

## 10. Phase 3 conclusion

Phase 3 is complete.

Current active schema/policy interpretation:

```text
Policy baseline: common/policies/policy_table_v1_2_0_FROZEN.json
Class 2 notification schema: common/schemas/class_2_notification_payload_schema_v1_1_0_FROZEN.json
Class 2 clarification interaction schema: common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
Pure context schema: common/schemas/context_schema_v1_0_0_FROZEN.json
MQTT topic registry: common/mqtt/topic_registry_v1_0_0.json
Scenario manifest schema: integration/scenarios/scenario_manifest_schema.json
```

Next recommended phase:

```text
Phase 4: Scenario explanation document alignment
```

Expected Phase 4 work:

```text
- Update integration/scenarios/README.md.
- Update integration/scenarios/scenario_review_guide.md.
- Update integration/scenarios/scenario_manifest_rules.md.
- Ensure these documents reference Class 2 clarification/transition semantics, new active policy v1.2.0, and the new Class 2 schemas.
```

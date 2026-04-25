# SESSION_HANDOFF_2026-04-25_PHASE0_FROZEN_BASELINE_AUDIT.md

Date: 2026-04-25
Scope: Phase 0 active frozen baseline impact audit for Class 2 clarification/transition update
Status: Phase 0 audit completed. No implementation changes beyond this audit note.

## 1. Purpose

This document records the Phase 0 audit for the Class 2 clarification/transition update.

The semantic target is:

```text
Class 2 is not a terminal failure/hold state.
Class 2 is a clarification/transition state where the system presents bounded candidate choices, collects user/caregiver confirmation or deterministic evidence, and transitions to Class 1, Class 0, or Safe Deferral / Caregiver Confirmation.
```

Frozen baseline handling principle:

```text
Do not bypass active frozen source-of-truth files by adding separate documents only.
If an active frozen baseline conflicts with the new Class 2 semantics, update it directly or create a new frozen version and migrate references.
```

---

## 2. Audited files

### 2.1 Active policy baseline

File:

```text
common/policies/policy_table_v1_1_2_FROZEN.json
```

Finding:

- The policy table is active because `integration/scenarios/verify_scenario_policy_schema_alignment.py` directly points to this exact file path.
- The current policy defines `class_2_escalation` as caregiver escalation for unresolved ambiguity, staleness, missing critical context, or actuation failure.
- This partially conflicts with the new Class 2 semantics because the new interpretation treats Class 2 as a clarification/transition state before Class 1/Class 0/Safe Deferral outcomes.

Relevant current behavior:

```text
POLICY_TABLE = ROOT / "common" / "policies" / "policy_table_v1_1_2_FROZEN.json"
```

Decision:

```text
Policy baseline must not be bypassed.
Recommended action: create a new frozen policy version, e.g. policy_table_v1_2_0_FROZEN.json, then update verifier references and architecture/scenario docs to point to the new policy baseline.
```

Reason:

- Directly editing `v1_1_2_FROZEN` would blur version meaning.
- The Class 2 meaning is a semantic update, not a small typo fix.
- New versioning gives a clean baseline transition.

---

### 2.2 Active context schema baseline

File:

```text
common/schemas/context_schema_v1_0_0_FROZEN.json
```

Finding:

- This schema is strict and describes the normalized context envelope with trigger event, environmental context, and device states.
- It requires all environmental fields to conservatively evaluate missing-state faults.
- The Class 2 clarification candidate/selection/transition payload does not naturally belong inside this pure context envelope.

Decision:

```text
Do not modify context_schema_v1_0_0_FROZEN.json for Class 2 clarification.
Recommended action: keep it as the operational context input schema and define a separate clarification interaction schema if schema formalization is needed.
```

Recommended new schema, if Phase 3 formalizes it:

```text
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
```

Reason:

- Context input and clarification interaction are different payload families.
- Keeping context schema stable avoids weakening missing-state detection.
- A separate clarification schema is cleaner than overloading pure context payloads.

---

### 2.3 Active MQTT topic registry

File:

```text
common/mqtt/topic_registry_v1_0_0.json
```

Finding:

Existing topics can initially represent the Class 2 clarification flow without adding new topics:

```text
safe_deferral/deferral/request
safe_deferral/escalation/class2
safe_deferral/caregiver/confirmation
safe_deferral/audit/log
```

Relevant existing topic:

```text
safe_deferral/deferral/request
→ Safe deferral event or bounded clarification request.
```

Decision:

```text
Do not create a new topic registry version in Phase 0.
Recommended action: keep topic_registry_v1_0_0.json stable for now and document Class 2 clarification usage over existing topics in architecture/interface docs.
```

Reason:

- `safe_deferral/deferral/request` already describes bounded clarification.
- `safe_deferral/caregiver/confirmation` can represent caregiver confirmation.
- `safe_deferral/audit/log` can capture traceability.
- Explicit `safe_deferral/clarification/*` topics can remain a future option only if runtime implementation requires separation.

---

### 2.4 Scenario manifest schema

File:

```text
integration/scenarios/scenario_manifest_schema.json
```

Finding:

- The manifest schema currently has `additionalProperties: true` at the top level and in step/expected objects.
- Therefore, the current `class2_insufficient_context_scenario_skeleton.json` additions such as `clarification_interaction`, `candidate_choices`, and `transition_outcomes` are not blocked by the schema.
- However, the schema does not document these fields explicitly.

Decision:

```text
No immediate blocking schema failure is expected.
Recommended action: update scenario_manifest_schema.json in Phase 3/4 to explicitly document Class 2 clarification fields even though additionalProperties currently allows them.
```

Reason:

- Explicit schema properties improve reviewability and static validation.
- Current permissive schema avoids immediate breakage.

---

### 2.5 Scenario manifest verifier

File:

```text
integration/scenarios/verify_scenario_manifest.py
```

Finding:

- The verifier allows the `class2_insufficient_context` category.
- It requires common expected outcome safety fields.
- It currently does not enforce the new Class 2 clarification/transition invariants.

Decision:

```text
Update required in Phase 7.
```

Needed checks:

```text
- Class 2 scenario includes clarification_interaction.
- Candidate generation is bounded.
- confirmation_required_before_transition is true.
- allowed transition targets include CLASS_1, CLASS_0, SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION.
- LLM final decision remains prohibited.
- unsafe autonomous actuation remains prohibited.
```

---

### 2.6 Scenario policy/schema alignment verifier

File:

```text
integration/scenarios/verify_scenario_policy_schema_alignment.py
```

Finding:

- This verifier directly uses `common/policies/policy_table_v1_1_2_FROZEN.json`.
- It scans for E001-E005 emergency IDs.
- It checks unsafe autonomous actuation, doorlock autonomous execution, fixture doorbell context, and expected fixture LLM semantics.
- It does not yet validate Class 2 clarification/transition behavior.

Decision:

```text
Update required in Phase 2/7 after the new policy baseline decision.
```

Recommended action:

```text
- Create policy_table_v1_2_0_FROZEN.json with Class 2 clarification/transition semantics.
- Update verifier constant POLICY_TABLE to the new baseline.
- Add Class 2-specific checks for clarification_interaction, candidate boundary, transition requirements, and no-autonomous-actuation behavior.
```

---

### 2.7 Expected Class 2 fixture

File:

```text
integration/tests/data/expected_routing_class2.json
```

Finding:

- The current fixture expects `CLASS_2` route and routing target.
- It allows `expected_llm_guidance_generation_allowed: "policy_constrained_only"` and prohibits LLM decision invocation.
- It describes the safe outcome as `caregiver_or_high_safety_escalation_path`.
- This is compatible with conservative escalation but incomplete for the new Class 2 clarification/transition model.

Decision:

```text
Update required in Phase 6.
```

Recommended action:

```text
- Reinterpret expected_routing_class2.json as initial Class 2 clarification-state entry, not terminal Class 2 final outcome.
- Add or create new expected fixtures for candidate prompt, Class 2→Class 1, Class 2→Class 0, and timeout/safe-deferral outcomes.
```

---

## 3. Phase 0 decisions

| Area | Phase 0 decision |
|---|---|
| Policy table | Active and semantically conflicting. Create a new frozen policy version rather than bypassing. |
| Context schema | Keep current frozen context schema stable. Use separate clarification schema if needed. |
| MQTT topic registry | Keep current registry stable for now. Existing topics are sufficient for documentation-level Class 2 clarification flow. |
| Scenario manifest schema | Not blocking due to `additionalProperties: true`, but should be explicitly extended later. |
| Manifest verifier | Must be updated to enforce Class 2 clarification invariants. |
| Policy/schema verifier | Must be updated to reference new policy baseline and check Class 2 semantics. |
| Expected Class 2 fixture | Must be updated or split into clarification-state and transition fixtures. |

---

## 4. Recommended next phase

Proceed to Phase 1 and Phase 2 in this order:

```text
Phase 1: Architecture document alignment
Phase 2: Policy baseline alignment
```

However, because the policy baseline is an active source of truth and currently conflicts with the new semantics, Phase 2 should create a new policy version before verifier changes are finalized.

Recommended new file:

```text
common/policies/policy_table_v1_2_0_FROZEN.json
```

Recommended later verifier update:

```text
integration/scenarios/verify_scenario_policy_schema_alignment.py
POLICY_TABLE = ROOT / "common" / "policies" / "policy_table_v1_2_0_FROZEN.json"
```

---

## 5. Open questions carried forward

1. Should the new policy version be `v1_1_3` or `v1_2_0`?
   - Recommendation: `v1_2_0`, because Class 2 semantics changed materially.
2. Should a separate clarification schema be created in Phase 3?
   - Recommendation: yes, if fixtures or payload examples will represent candidate/selection/result payloads.
3. Should new clarification MQTT topics be added?
   - Recommendation: no for now; use existing `safe_deferral/deferral/request`, `safe_deferral/caregiver/confirmation`, and `safe_deferral/audit/log` unless runtime implementation needs more separation.
4. Should `expected_routing_class2.json` be replaced or supplemented?
   - Recommendation: reinterpret it as initial clarification-state routing, and add new transition-specific expected fixtures.

---

## 6. Final Phase 0 conclusion

Phase 0 confirms that the Class 2 semantic change requires more than scenario prose updates.

The policy table is an active frozen baseline and currently represents Class 2 primarily as caregiver escalation. Therefore, the cleanest approach is to introduce a new frozen policy version and migrate verifier/documentation references to that new policy baseline.

The context schema and topic registry can remain stable for now because Class 2 clarification can be represented outside the pure context payload and over existing deferral/escalation/confirmation/audit topics.

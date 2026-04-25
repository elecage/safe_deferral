# SESSION_HANDOFF_2026-04-25_PHASE1_ARCHITECTURE_ALIGNMENT_UPDATE.md

Date: 2026-04-25
Scope: Phase 1 architecture document alignment for Class 2 clarification/transition semantics
Status: Phase 1 architecture alignment completed.

## 1. Purpose

This handoff addendum records the completion of Phase 1 from:

```text
common/docs/runtime/SESSION_HANDOFF_2026-04-25_SCENARIO_POLICY_SCHEMA_VERIFY_UPDATE_PLAN_V2.md
```

Phase 1 focused on architecture-document alignment after the Phase 0 frozen baseline audit.

---

## 2. New architecture document

Added:

```text
common/docs/architecture/19_class2_clarification_architecture_alignment.md
```

Commit:

```text
4f2e484717b622cea9a303c44505889d15f51951
```

Purpose:

```text
Records the architecture interpretation that Class 2 is a clarification/transition state rather than a terminal failure state.
```

---

## 3. Main architecture decision

The architecture now explicitly treats Class 2 as:

```text
Class 2 = clarification / transition state
```

Meaning:

```text
Class 2 is entered when the system cannot safely determine the user's intent from available context, or when a bounded interaction requires confirmation before routing. In Class 2, the system may generate bounded candidate choices, present them to the user or caregiver, collect confirmation or timeout evidence, and then transition to Class 1, Class 0, or Safe Deferral / Caregiver Confirmation.
```

This does not grant additional authority to the LLM or actuator path.

---

## 4. Relationship to existing architecture documents

The new document confirms alignment with:

```text
common/docs/architecture/14_system_components_outline_v2.md
common/docs/architecture/15_interface_matrix.md
common/docs/architecture/16_system_architecture_figure.md
common/docs/architecture/17_payload_contract_and_registry.md
common/docs/architecture/18_scenario_node_component_mapping.md
```

Phase 1 intentionally avoided rewriting those large documents because they already contain compatible concepts:

```text
- safe deferral may lead to bounded clarification;
- local LLM generates guidance but is not authority;
- Mac mini Edge Hub includes safe deferral / clarification management;
- interface matrix already supports follow-up input, deferral request, caregiver confirmation, and audit;
- payload registry already separates pure context from manual approval, ACK, audit, and dashboard state;
- node/component mapping already lists Class 2 Clarification Manager and related nodes/components.
```

The new 19th document makes the Class 2-specific interpretation explicit without destabilizing existing architecture text.

---

## 5. Class 2 Clarification Manager

The following logical module is now explicitly defined:

```text
Class 2 Clarification Manager
```

Recommended placement:

```text
Mac mini Edge Hub
└─ Safe Deferral and Clarification Management
   └─ Class 2 Clarification Manager
```

Responsibilities:

```text
- detect Class 2 clarification requirement;
- request bounded candidate generation from LLM Guidance Layer or Input Context Mapper;
- present candidate choices through TTS, display, or accessible output;
- collect user response through Bounded Input Node, Voice Input, or caregiver confirmation;
- handle no-response or timeout;
- request re-routing after confirmation or deterministic evidence;
- prevent autonomous actuation during unresolved Class 2 state;
- audit every candidate, selection, timeout, transition, and deferral.
```

---

## 6. LLM boundary recorded

Canonical boundary:

```text
The LLM may generate candidates and guidance, but the final transition must be determined by user/caregiver confirmation or deterministic evidence and must pass policy/validator constraints before execution.
```

The LLM may:

```text
- summarize ambiguity;
- generate short candidate choices;
- convert candidates into TTS/display wording;
- explain waiting-for-confirmation state;
- explain why automatic execution is not yet performed.
```

The LLM must not:

```text
- make the final class decision;
- authorize actuator execution;
- trigger Class 0 emergency handling by itself;
- approve sensitive actuation;
- override Policy Router or Deterministic Validator;
- fabricate missing state;
- convert dashboard/governance evidence into operational authority.
```

---

## 7. Transition targets recorded

Class 2 can transition to:

| Target | Condition |
|---|---|
| `CLASS_1` | User/caregiver confirms a bounded low-risk assistance request, and deterministic validation passes |
| `CLASS_0` | Emergency confirmation, triple-hit, or deterministic sensor evidence is present |
| `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION` | No response, ambiguity, insufficient context, or unresolved conflict remains |

---

## 8. Interface interpretation recorded

No new MQTT topics are required in Phase 1.

Existing topic use is sufficient for architecture-level representation:

```text
safe_deferral/deferral/request
safe_deferral/context/input
safe_deferral/escalation/class2
safe_deferral/caregiver/confirmation
safe_deferral/audit/log
```

Important boundary:

```text
Follow-up user input must re-enter through the bounded input/context input plane and must not bypass policy routing.
```

---

## 9. Payload interpretation recorded

Phase 1 keeps these stable:

```text
common/schemas/context_schema_v1_0_0_FROZEN.json
common/mqtt/topic_registry_v1_0_0.json
```

Reason:

```text
Class 2 clarification is an interaction/control payload family, not pure operational context.
```

Possible Phase 3 addition:

```text
common/schemas/clarification_interaction_schema_v1_0_0_FROZEN.json
```

---

## 10. Relationship to fault scenarios

The new architecture document preserves the distinction:

| Case | Meaning |
|---|---|
| Class 2 insufficient context | Intent cannot be determined from available context |
| Conflict fault | Multiple plausible candidates remain simultaneously admissible |
| Missing-state fault | Required device/context state is absent |

Conflict and missing-state faults may enter Class 2-like safe deferral or clarification handling, but their fault cause should remain explicit in scenarios, fixtures, and audit logs.

---

## 11. Phase 1 conclusion

Phase 1 is complete.

No immediate SVG redesign, context-schema update, or MQTT topic update is required by Phase 1.

Next recommended phase:

```text
Phase 2: Policy baseline alignment
```

Phase 2 should create a new frozen policy baseline, currently recommended as:

```text
common/policies/policy_table_v1_2_0_FROZEN.json
```

and then update downstream references in verifiers and docs.

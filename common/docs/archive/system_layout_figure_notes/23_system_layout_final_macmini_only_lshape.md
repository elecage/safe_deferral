# 23_system_layout_final_macmini_only_lshape.md

## 1. Purpose

This document records the current **final Mac mini-only routed layout**.
In this version, the Raspberry Pi layer is intentionally omitted from the operational figure, and the Mac mini host boundary is redrawn as an L-shaped enclosure so that the lower-right caregiver-approval region is explicitly included within the Mac mini boundary.

This figure is intended to serve as a cleaner paper-oriented architecture view focused on the operational closed loop itself.

This document should be read together with:
- `common/docs/architecture/14_system_components_outline_v2.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/archive/system_layout_figure_notes/16_system_block_layout_spacious.md`
- `common/docs/archive/system_layout_figure_notes/18_system_layout_step4_with_llm_reasoning.md`
- `common/docs/archive/system_layout_figure_notes/19_system_layout_step5_policy_branching.md`
- `common/docs/archive/system_layout_figure_notes/20_system_layout_step6_execution_completion.md`
- `common/docs/archive/system_layout_figure_notes/21_system_layout_step7_tts_return_paths.md`
- `common/docs/archive/system_layout_figure_notes/22_system_layout_step8_ack_audit_paths.md`

---

## 2. Current final routed layout

![Final Mac mini-only L-shaped system layout](../../architecture/figures/system_layout_final_macmini_only_lshape.svg)

---

## 3. What is included in this figure

The routed interfaces shown in this figure are:

### User Input Interface
- `User → Bounded Input Node`
- `Bounded Input Node → MQTT Ingestion / State Intake`

### Context / State Interface
- `Context Nodes → MQTT Ingestion / State Intake`
- `MQTT Ingestion / State Intake → Context and Runtime State Aggregation`

### Emergency Interface
- `Emergency Nodes → MQTT Ingestion / State Intake`
- `MQTT Ingestion / State Intake → Policy Routing + Validation`

### LLM Reasoning Interface
- `Context and Runtime State Aggregation → Local LLM Reasoning Layer`
- `Local LLM Reasoning Layer → Policy Routing + Validation`

### Policy / Validation Branching Interface
- `Policy Routing + Validation → Approved Low-Risk Actuation Path`
- `Policy Routing + Validation → Safe Deferral and Clarification Management`
- `Policy Routing + Validation → Caregiver Escalation`

### Execution / Approval Completion Interface
- `Approved Low-Risk Actuation Path → Actuator Interface Nodes`
- `Caregiver Escalation → Caregiver Approval`
- `Caregiver Approval → Actuator Interface Nodes`

### TTS / Clarification Return Interface
- `Approved Low-Risk Actuation Path → TTS Rendering / Voice Output`
- `Safe Deferral and Clarification Management → TTS Rendering / Voice Output`
- `Caregiver Escalation → TTS Rendering / Voice Output`

### ACK / Audit Completion Interface
- `Actuator Interface Nodes → Local ACK + Audit Logging`
- `Caregiver Approval → Local ACK + Audit Logging`
- `Safe Deferral and Clarification Management → Local ACK + Audit Logging`

---

## 4. Interpretation of the host boundary

In this final version, the Raspberry Pi layer is not drawn.
This omission is intentional and does not mean that experiment-support metadata or external validation tooling no longer exist in the broader project.
Rather, those elements are excluded here so the figure can focus on the operational assistive-control loop.

The Mac mini boundary is redrawn as an L-shaped enclosure so that:
- the primary reasoning, policy, TTS, and local audit blocks remain in the main body of the host,
- and the lower-right caregiver-approval region is still explicitly included within the same operational host boundary.

Accordingly, this figure should be interpreted as showing caregiver approval handling as part of the Mac mini-centered control loop.

---

## 5. Interpretation of LLM and TTS behavior

This figure still does **not** depict a direct `Local LLM Reasoning Layer → TTS Rendering / Voice Output` path.
This is intentional.

The local LLM is interpreted as generating not only intent-recovery outputs but also language candidates such as:
- current-status explanations,
- safe-deferral reasons,
- and next-input suggestions.

However, these language outputs are forwarded together with the interpreted intent to `Policy Routing + Validation`.
Therefore, the TTS outputs shown in this figure should be interpreted as **policy-constrained spoken outputs** rather than raw LLM outputs.

---

## 6. Why this figure is useful as a final paper figure

This final version emphasizes that:
- bounded input, context, and emergency signals are processed locally,
- reasoning and deterministic validation remain separated,
- approved execution, safe deferral, and caregiver-mediated execution are structurally distinct,
- user-facing spoken feedback is preserved,
- and acknowledgement plus audit return paths complete the local loop.

Because the external experiment-support layer is omitted, the figure becomes more compact and better aligned with the core operational claim of the paper.

---

## 7. Summary

This figure is best interpreted as the **operational closed-loop architecture** of the system, centered on:
- bounded field-side interaction,
- local reasoning and policy validation,
- safe execution or safe deferral,
- caregiver-mediated approval for sensitive actions,
- policy-constrained spoken feedback,
- and local acknowledgement/audit closure.

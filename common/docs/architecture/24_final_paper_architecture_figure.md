# 24_final_paper_architecture_figure.md

## 1. Purpose

This document records the **final paper-oriented system architecture figure** for the safe-deferral smart-home control system.
This version is intended to be used as the primary architectural figure in the paper.

The figure emphasizes the operational closed loop across:
- bounded user input,
- context and emergency ingestion,
- local LLM-assisted reasoning,
- deterministic policy routing and validation,
- safe low-risk execution,
- safe deferral and clarification,
- caregiver-mediated approval for sensitive actions,
- TTS-based user feedback,
- and local acknowledgement plus audit closure.

At the same time, the right-side Raspberry Pi region is retained to represent the support-side monitoring and experiment layer without overwhelming the core control loop.

---

## 2. Final figure

![Final paper architecture figure](./figures/system_layout_final_macmini_only_lshape.svg)

---

## 3. Structural interpretation

### 3.1 ESP32 Device Layer

The ESP32 layer represents field-side interaction and actuation endpoints, including:
- bounded input,
- context sensing,
- emergency detection,
- and actuator interface nodes.

This layer is responsible for physically proximal interaction and event collection, but not for higher-level reasoning or admissibility decisions.

### 3.2 Mac mini Edge Hub

The Mac mini region represents the operational control core.
Its L-shaped boundary intentionally includes the caregiver-approval region in the same host-level operational enclosure.

Within this host, the figure shows:
- MQTT ingestion and state intake,
- context and runtime aggregation,
- local LLM reasoning,
- policy routing and validation,
- approved low-risk actuation,
- safe deferral and clarification management,
- caregiver escalation,
- caregiver approval handling,
- TTS rendering,
- and local ACK plus audit logging.

This layout reflects the intended interpretation that caregiver approval handling is not external to the control loop, but a governed part of the same operational architecture.

### 3.3 Raspberry Pi 5 support region

The Raspberry Pi region is retained as a support-oriented layer that contains:
- **Monitoring / Experiment Dashboard**,
- **Experiment Support**,
- and **Progress / Result Publication**.

This layer should be interpreted as a support and visibility interface rather than the primary execution authority.
It provides the monitoring, orchestration, experiment-management, and result-visibility functions that surround the closed-loop operational core.

---

## 4. Interpretation of the language and TTS path

The local LLM reasoning layer is interpreted as generating:
- intent-recovery outputs,
- status explanations,
- safe-deferral reasons,
- and next-input suggestions.

However, these outputs are not treated as directly speakable raw responses.
They are forwarded together with interpreted intent to the policy-routing and validation stage.
Accordingly, the TTS outputs shown in the figure should be interpreted as **policy-constrained spoken outputs** rather than direct LLM emissions.

---

## 5. Interpretation of approval and execution routing

The figure intentionally distinguishes three downstream policy-result states:
- approved low-risk actuation,
- safe deferral and clarification,
- and caregiver escalation.

Sensitive execution is therefore not shown as directly emitted from reasoning.
Instead, it passes through escalation and caregiver approval before reaching the actuator path.

The caregiver-approval execution line is intentionally drawn as a routed orthogonal path to preserve visual separation from the approved low-risk execution path while still indicating convergence toward the shared actuator-side interface.

---

## 6. Why this figure is suitable for the paper

This final figure is appropriate for paper use because it simultaneously shows:
- the closed-loop assistive control logic,
- the separation between reasoning and deterministic validation,
- the distinction between low-risk execution and caregiver-mediated execution,
- the existence of safe deferral as a first-class outcome,
- the preservation of user-facing spoken feedback,
- and the presence of a support-side monitoring and experiment layer.

As a result, the figure supports both the operational safety claim and the experimental-system interpretation of the proposed architecture.

---

## 7. Summary

This figure should be treated as the **final paper architecture figure**.
It is the version that best balances:
- operational clarity,
- safety interpretation,
- caregiver-in-the-loop control,
- TTS-assisted accessibility,
- and support-side monitoring / experiment visibility.

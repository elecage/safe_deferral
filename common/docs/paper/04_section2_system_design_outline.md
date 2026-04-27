# 04_section2_system_design_outline.md

## 1. Purpose

This document records the current outline for **Section 2 (System Design)** of the paper.

It is intended to keep future drafting aligned with:

- `common/docs/paper/01_paper_contributions.md`
- `common/docs/paper/02_ICT_Express_submission_notes.md`
- `common/docs/paper/03_title_keywords_and_introduction_outline.md`
- `common/docs/required_experiments.md`
- `common/docs/architecture/02_safety_and_authority_boundaries.md`

This is a drafting-support document, not a canonical policy/schema authority document.

---

## 2. Role of Section 2

Section 2 should explain the **system architecture and control logic** of the proposed approach.

For the current ICT Express target, this section should not become a long implementation log.
Instead, it should make the following points clear:

- the user/input problem setting,
- the architecture of the edge system,
- the role of the local LLM,
- the separation between interpretation and execution authority,
- the safe deferral and caregiver escalation path,
- the closed-loop verification structure,
- and the role of doorlock as a representative sensitive-actuation case.

The section should remain architecture-centered and contribution-centered.

---

## 3. Current Section 2 outline

### 2.1 Problem Setting and Design Goals
Main message:
- The target environment involves users with **constrained alternative input**, where direct input alone may be too limited to express intent clearly.
- The system must therefore address both:
  - intent recovery under sparse or ambiguous input,
  - and safe control of physical actuation.
- The design goals should be stated explicitly, such as:
  - local processing,
  - bounded LLM assistance,
  - deterministic control boundaries,
  - and caregiver-mediated handling of sensitive actions.

Main objective of this subsection:
- define the problem in system-design terms,
- and state the design goals before presenting the architecture.

---

### 2.2 Overall Edge Architecture
Main message:
- Present the overall system architecture spanning:
  - bounded input nodes,
  - contextual state formation,
  - local LLM intent recovery,
  - policy routing and deterministic validation,
  - safe deferral / escalation,
  - approved actuation,
  - ACK verification,
  - and local audit logging.
- Clarify the role of the main system hosts, including:
  - Mac mini as the control-side hub,
  - Raspberry Pi as the scenario execution / replay / fault-injection support host,
  - actual physical nodes as bounded ESP32 or equivalent device-layer interfaces,
  - and STM32 as optional out-of-band timing / measurement support.

Main objective of this subsection:
- provide the full architecture view.

Recommended note:
- A single compact system figure should ideally support this subsection.

Recommended figure:

```text
common/docs/architecture/figures/system_layout.svg
```

Draft caption:

```text
Figure X. Privacy-aware edge smart-home architecture with safe deferral. The
Mac mini acts as the operational hub for context intake, local LLM-assisted
intent recovery, policy routing, deterministic validation, low-risk dispatch,
caregiver notification/confirmation handling, ACK collection, and audit logging.
Actual physical nodes provide bounded input, context, emergency evidence, and
actuation interfaces. The Raspberry Pi hosts non-authoritative experiment,
virtual-node, dashboard, and governance-support tools, while the STM32 timing
support path provides out-of-band measurement evidence.
```

Draft body text:

```text
Fig. X summarizes the proposed edge architecture. The Mac mini is the only
operational hub: it receives bounded physical input and context, aggregates
runtime state, invokes the local LLM only for candidate intent recovery, and
passes executable candidates through policy routing and deterministic
validation. Approved Class 1 lighting actions are dispatched through the
low-risk path and closed with ACK and audit evidence. Ambiguous, insufficient,
or sensitive cases enter the Class 2 clarification and safe-deferral path. When
caregiver involvement is required, Telegram is used only as an outbound
notification and response-collection transport; it is not a remote-control or
direct actuator channel.

The support regions in Fig. X are intentionally non-authoritative. Raspberry Pi
tools run paper experiments, virtual nodes, fault-injection behavior,
scenario execution, monitoring dashboards, result analysis, and MQTT/payload
governance checks without replacing Mac mini policy, validation, dispatch, ACK,
or audit authority. STM32 timing support is similarly out-of-band: it captures
physical timing evidence and exports measurements for analysis, but it does not
participate in operational routing or actuation.
```

---

### 2.3 Local LLM-Assisted Intent Recovery
Main message:
- The local LLM is used as an **intent recovery layer**, not as an unrestricted execution authority.
- Its inputs may include:
  - bounded alternative input,
  - environmental context,
  - device-state context.
- Its outputs should remain bounded to candidate interpretation or candidate action space that is later constrained by policy/schema/validator logic.

Main objective of this subsection:
- explain the role of the LLM precisely,
- while making clear that the LLM is not the final safety authority.

Interpretation note:
- This subsection should reinforce that the LLM improves flexibility under constrained input,
  but remains bounded by external architectural control.

---

### 2.4 Policy-Constrained Execution Boundary
Main message:
- Execution authority is bounded by:
  - policy routing,
  - schema-constrained candidate space,
  - and deterministic validation.
- The architecture must clearly distinguish between:
  - current implementation-facing scope,
  - and current authoritative autonomous low-risk Class 1 scope.
- Under the current interpretation:
  - lighting is within the authoritative low-risk autonomous scope,
  - while doorlock is not to be treated as an ordinary autonomous low-risk action.

Main objective of this subsection:
- explain how the architecture structurally separates interpretation from execution authority.

This is one of the most important subsections in the paper.

---

### 2.5 Safe Deferral and Caregiver Escalation
Main message:
- When ambiguity, insufficient context, or policy restriction prevents safe autonomous execution,
  the system shifts to:
  - safe deferral,
  - or caregiver escalation.
- Sensitive actions should not be forced into autonomous execution when the architecture cannot justify them safely.
- The escalation flow should include:
  - unresolved reason formation,
  - notification payload generation,
  - and manual approval path support.

Main objective of this subsection:
- explain how the system handles uncertainty and sensitive action requests safely.

---

### 2.6 Closed-Loop Execution, ACK, and Local Audit
Main message:
- Approved execution is not the end of the control loop.
- The system should confirm execution through ACK or equivalent state confirmation.
- It should also store relevant records locally, including:
  - interpretation summary,
  - validation result,
  - approval result,
  - and ACK outcome.

Main objective of this subsection:
- explain why the proposed architecture is a closed-loop control and verification structure rather than a one-shot prediction system.

---

### 2.7 Doorlock as a Representative Sensitive-Actuation Case
Main message:
- Doorlock should be treated as a representative sensitive-actuation case rather than a standard low-risk convenience action.
- The point of including doorlock is not to maximize autonomous unlock capability.
- The point is to demonstrate:
  - why intent interpretation and execution authority must be separated,
  - why autonomous unlock should be blocked under the current interpretation,
  - and why caregiver-mediated approval, ACK, and audit are necessary.

Main objective of this subsection:
- give a concrete, high-stakes example that makes the paper’s safety architecture argument visible.

Interpretation note:
- This subsection should stay tightly tied to the paper’s control-boundary argument,
  not drift into product-style feature explanation.

---

## 4. Logic flow of Section 2

The intended logic flow of Section 2 is:

1. define the problem setting and design goals,
2. show the overall edge architecture,
3. explain the LLM’s bounded role,
4. explain the policy-constrained execution boundary,
5. explain safe deferral and caregiver escalation,
6. explain closed-loop verification and audit,
7. use doorlock as the representative sensitive-actuation case.

This order should be preserved unless the overall paper framing changes significantly.

---

## 5. Writing cautions for Section 2

### 5.1 Do not turn Section 2 into an implementation manual
Section 2 should explain architecture and control logic, not every deployment or scripting detail.

### 5.2 Do not overstate the LLM’s authority
The section should make clear that the LLM is an interpretation aid, not the final execution authority.

### 5.3 Keep the execution boundary explicit
The distinction between:
- interpretation,
- validation,
- escalation,
- approval,
- and execution
must remain very clear.

### 5.4 Keep doorlock in its correct role
Doorlock should be discussed as:
- a representative sensitive-actuation case,
- not as a current ordinary autonomous low-risk action.

### 5.5 Prefer one clear architecture figure over too many subfigures
Given the short-paper format, a single well-designed architecture figure is likely better than several fragmented diagrams.

---

## 6. Short summary

The current drafting baseline for Section 2 is:

- **2.1** Problem Setting and Design Goals
- **2.2** Overall Edge Architecture
- **2.3** Local LLM-Assisted Intent Recovery
- **2.4** Policy-Constrained Execution Boundary
- **2.5** Safe Deferral and Caregiver Escalation
- **2.6** Closed-Loop Execution, ACK, and Local Audit
- **2.7** Doorlock as a Representative Sensitive-Actuation Case

This structure is intended to keep Section 2 architecture-centered, safety-centered, and directly aligned with the paper’s main contribution claims.

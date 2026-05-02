# 01_paper_contributions.md

## 1. Purpose

This document summarizes the intended **paper-level contribution claims** of the safe_deferral project.

Its purpose is to help future writing sessions maintain consistency across:

- the paper introduction,
- contribution statements,
- system design description,
- experiment framing,
- and reviewer-facing positioning.

This is not a canonical policy or schema authority document.  
Instead, it is a **paper-positioning document** that interprets the current architecture and experiment design as research contributions.

---

## 2. Core Research Position

The paper is **not** primarily about showing that an LLM can directly control a smart-home device.

The paper is also **not** primarily about maximizing autonomous actuation coverage.

The central research position is:

> In assistive smart-home environments for users with constrained alternative input, an LLM may be useful for recovering user intent from sparse and ambiguous signals, but sensitive physical actuation must not be delegated to the LLM as an unrestricted autonomous authority.

Accordingly, the system is designed so that:

- the LLM is used for **bounded intent interpretation**,
- deterministic policy and validation layers remain authoritative,
- safe deferral is preferred over unsafe autonomous action,
- and sensitive actuation is structurally constrained through escalation, approval, ACK verification, and audit logging.

---

## 3. Why This Is a Meaningful Research Problem

The target user setting is important.

This project addresses users whose direct input may be:

- sparse,
- physically difficult,
- temporally delayed,
- hard to disambiguate,
- or limited to bounded modalities such as button hits or short alternative-input events.

In such settings, there is a real tension between two needs:

1. **Intent recovery and usability**
   - because limited input alone may not be expressive enough,
2. **Safety and actuation control**
   - because incorrect interpretation can produce unsafe physical outcomes.

The research value of this work lies in showing how an LLM can be integrated into this setting **without allowing the model to become the final authority for sensitive actuation**.

---

## 4. Main Contribution Framing

The contributions should be framed around **policy-constrained assistive intelligence**, not around unrestricted autonomy.

### Contribution 1. LLM-assisted intent recovery for constrained alternative input
The system proposes an assistive smart-home interaction framework in which a local LLM interprets user intent from bounded alternative input together with environmental and device context.

The contribution is not merely that an LLM is used, but that it is used specifically to recover likely intent in situations where:

- user input is incomplete,
- context matters,
- and purely rule-based direct mapping would be too brittle or too limited.

This contribution is strongest when framed as:

- **bounded LLM-based intent recovery**,
- rather than free-form autonomous decision making.

### Contribution 2. Policy- and schema-constrained actuation authority separation
The paper proposes an authority-separated architecture in which:

- the LLM interprets,
- the policy router determines class,
- the deterministic validator enforces admissibility,
- and the execution path is bounded by explicit policy/schema constraints.

This is a key contribution because the work does not rely on model confidence alone.  
Instead, it places **system-level deterministic constraints** around model output.

The main claim here is:

> sensitive or policy-restricted physical actions are not controlled by model preference, but by explicit architectural boundaries.

### Contribution 3. Safe deferral and caregiver-mediated handling of sensitive actuation
The paper introduces a structured treatment of unresolved or sensitive decisions through:

- bounded safe deferral,
- caregiver escalation,
- manual approval,
- ACK-based confirmation,
- and local audit logging.

This is especially important in assistive environments because ambiguous user intent cannot always be resolved safely through autonomous action alone.

The contribution should therefore be framed as a **safe human-in-the-loop actuation strategy** for assistive smart homes.

### Contribution 4. A safety-oriented closed-loop validation framework for physical assistive action
The system does not stop at intent estimation or route classification.

It explicitly closes the loop through:

- approval or escalation pathways,
- actuation dispatch boundaries,
- device or physical ACK,
- and local audit traces.

This makes the work stronger than a simple classifier-orchestrator paper, because it addresses the full path from:

- input,
- interpretation,
- routing,
- validation,
- escalation,
- execution,
- to post-actuation verification.

---

## 5. Why Doorlock Is an Important Paper Example

Doorlock is important not because the paper is only about door-unlock functionality, but because it is an effective **representative case of sensitive actuation**.

Doorlock is useful in the paper because it clearly exposes the tension between:

- assistive convenience,
- intent ambiguity,
- safety,
- and residential security.

This makes it a strong example for showing that:

- the LLM may infer user intent,
- but the system must still prevent unrestricted autonomous unlock,
- and must require caregiver-mediated approval under the current interpretation.

Therefore, doorlock should be described as:

- a **representative sensitive actuation case**,
- not merely as an ordinary smart-home device,
- and not merely as a convenience function.

---

## 6. Recommended Paper-Level Contribution Statement

A concise contribution summary can be written as follows.

### Recommended version
This work makes four main contributions.

1. It presents an assistive smart-home framework in which a local LLM recovers likely user intent from constrained alternative input and contextual signals.
2. It introduces an authority-separated safety architecture in which deterministic policy and schema constraints remain authoritative over model output.
3. It proposes a safe handling strategy for ambiguous or sensitive actuation using bounded safe deferral, caregiver escalation, manual approval, and ACK-based closed-loop verification.
4. It demonstrates the relevance of this architecture through sensitive actuation scenarios, including doorlock-related visitor-response situations, where unsafe autonomous actuation must be structurally blocked.

### Slightly more formal version
This paper contributes:

1. a bounded LLM-based intent recovery framework for assistive smart-home interaction under constrained alternative-input conditions;
2. a policy- and schema-constrained authority separation architecture that prevents unrestricted model-driven physical actuation;
3. a caregiver-mediated sensitive-actuation pathway combining safe deferral, manual approval, ACK validation, and local audit logging; and
4. an experimental evaluation framework that examines whether the system preserves safety boundaries while still supporting context-aware assistive interaction.

---

## 7. What the Paper Should NOT Overclaim

To keep the paper credible, the following overclaims should be avoided.

### 7.1 Avoid claiming perfect safety
Do not claim:

- perfect safety,
- complete elimination of risk,
- or infallible correctness of user-intent estimation.

Instead use phrases such as:

- policy-constrained,
- structurally restricted,
- deterministic enforcement,
- bounded authority,
- caregiver-mediated,
- unsafe autonomous actuation blocked.

### 7.2 Avoid claiming that the LLM directly solves sensitive actuation
Do not frame the work as:

- “the LLM opens the door for the user,”
- or “the LLM decides all smart-home actions autonomously.”

That framing weakens the safety argument.

Instead frame it as:

- the LLM helps recover likely intent,
- while the architecture constrains what may actually be executed.

### 7.3 Avoid presenting doorlock as an ordinary low-risk action
Doorlock should not be described as a current ordinary Class 1 low-risk autonomous action.

Under the current architecture interpretation, it should be presented as:

- a sensitive actuation case,
- caregiver-mediated,
- and structurally blocked from unrestricted autonomous execution.

---

## 8. Reviewer-Facing Value Proposition

A reviewer should be able to understand that the novelty is not simply “LLM + smart home.”

The stronger reviewer-facing interpretation is:

- many LLM systems focus on capability,
- this work focuses on **capability under explicit safety boundaries**;
- many assistive systems focus on input convenience,
- this work focuses on **input convenience without surrendering actuation authority**;
- many smart-home systems focus on automation,
- this work focuses on **bounded automation and safe delegation**.

The paper’s strongest value proposition is therefore:

> The system demonstrates how LLM-based intent recovery can be incorporated into an assistive smart-home architecture while preserving deterministic control over safety-critical or sensitive physical actions.

---

## 9. How Experiments Should Support the Contribution Claims

The experiments should not only ask whether the system is accurate or fast.

They should also show whether the architecture preserves its claimed safety boundaries.

### Important evaluation themes
- whether emergency events are routed correctly,
- whether bounded low-risk actions are validated correctly,
- whether ambiguity leads to safe deferral rather than unsafe action,
- whether sensitive actuation is escalated rather than autonomously executed,
- whether caregiver approval is required and correctly handled,
- whether ACK and audit traces are preserved,
- whether these safety controls remain intact under fault-injection conditions.

### Doorlock-specific support value
Doorlock-related experiments are especially useful for supporting the claim that:

- the paper is not merely enabling richer action,
- it is **structuring and limiting action authority**.

Accordingly, the most meaningful doorlock-oriented results are:

- autonomous unlock blocked,
- caregiver escalation correctly triggered,
- approval path correctness,
- ACK and audit completeness.

---

## 10. Recommended One-Sentence Thesis-Level Framing

If a single sentence is needed to capture the paper’s contribution, the following is recommended.

### Recommended one-sentence framing
This paper proposes a policy-constrained assistive smart-home architecture in which a local LLM recovers user intent from constrained alternative input and contextual signals, while deterministic validation and caregiver-mediated escalation structurally restrict sensitive physical actuation.

### Alternative version emphasizing doorlock as the representative case
This paper shows how LLM-based intent recovery can improve interaction for users with constrained alternative input, while preventing unsafe autonomous execution of sensitive smart-home actions through policy-bounded validation and caregiver-mediated control.

---

## 11. Short Summary

The paper’s main value is not that it gives an LLM more power over the home.

Its value is that it shows how an LLM can be used to improve intent interpretation for users with constrained input **without allowing sensitive actuation authority to drift into the model itself**.

Doorlock is therefore important as a representative sensitive-actuation case that makes the paper’s safety argument concrete, reviewable, and experimentally testable.

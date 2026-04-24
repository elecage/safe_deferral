# 02_ICT_Express_submission_notes.md

## 1. Purpose

This document summarizes practical notes for preparing the current paper for **ICT Express**.

Its purpose is to help future writing sessions keep the manuscript aligned with:
- the journal scope,
- the short-paper format,
- the current project architecture,
- and the paper contribution framing already documented in:
  - `common/docs/paper/01_paper_contributions.md`
  - `common/docs/required_experiments.md`

This is a **submission-strategy document**, not a canonical policy/schema authority document.

---

## 2. Why ICT Express is a plausible target

ICT Express is suitable for this project when the paper is framed as an **ICT system paper**, not merely as a welfare or assistive-service paper.

The current work is most compatible with the following journal-facing themes:
- local / on-device / edge AI
- LLM-based intent recovery
- AI and IoT convergence
- privacy-preserving smart-home architecture
- safe actuation control under constrained interaction
- practical system validation under realistic experiment conditions

The paper is a better fit when described as:
- an edge AIoT architecture,
- a policy-constrained assistive interaction system,
- or a smart-home control framework with bounded LLM assistance,

rather than simply as:
- a disability support application,
- or a doorlock application paper.

---

## 3. Core writing strategy for this journal

### 3.1 Present the paper as an ICT contribution first
The paper should first answer:
- what ICT problem is being solved,
- why existing rule-only or unrestricted approaches are insufficient,
- what architecture is proposed,
- and what experimental evidence supports the claim.

The disability-support motivation is important, but in this journal it should support the technical problem definition rather than replace it.

### 3.2 Keep the central claim narrow and sharp
A weak paper story would try to claim too many things at once:
- accessibility,
- smart-home platform engineering,
- LLM evaluation,
- full productization,
- complete safety,
- and many device types.

A stronger ICT Express story is narrower:
- constrained alternative input causes intent ambiguity,
- a local LLM can help recover bounded intent candidates,
- sensitive actuation must not be left to unrestricted model autonomy,
- therefore policy/schema/validator/caregiver escalation are used to structurally constrain execution.

### 3.3 Treat doorlock as a representative sensitive-actuation case
Doorlock should not be positioned as the main consumer feature.

It should be written as:
- a representative sensitive actuation domain,
- a strong example that exposes the boundary between intent interpretation and execution authority,
- and a test case showing why unrestricted autonomous LLM actuation is not acceptable.

This is stronger than simply saying:
- the system can open a door,
- or the system includes a smart lock.

---

## 4. Recommended paper framing

A strong one-sentence framing for ICT Express is:

> This paper proposes a policy-constrained edge smart-home architecture in which a local LLM assists intent recovery under constrained alternative-input conditions, while deterministic validation and caregiver-mediated escalation structurally restrict sensitive physical actuation.

A shorter alternative is:

> We present a local LLM-assisted smart-home control framework that improves intent recovery under constrained input while preventing unrestricted autonomous execution of sensitive actions.

---

## 5. Recommended contribution structure

A practical contribution structure for this journal is:

1. **Bounded LLM-assisted intent recovery** for constrained alternative input.
2. **Authority separation** between model interpretation and physical execution using policy/schema/validator layers.
3. **Safe handling of sensitive actuation** through safe deferral, caregiver escalation, manual approval, ACK verification, and audit logging.
4. **Experiment design and validation** showing both interpretation value and safety-boundary preservation.

The manuscript should not try to list too many smaller sub-contributions.
It is better to have 3–4 contributions that are clearly remembered.

---

## 6. What must be emphasized in writing

### 6.1 Emphasize bounded authority
The current project’s strength is not unrestricted autonomy.
Its strength is:
- bounded interpretation,
- deterministic control boundaries,
- safe fallback,
- and human-mediated handling of sensitive actions.

### 6.2 Emphasize edge / local processing
The paper should clearly mention the value of:
- local inference,
- privacy-preserving operation,
- reduced cloud dependence,
- and edge-side controllability.

### 6.3 Emphasize system-level safety design
The paper should make clear that:
- the LLM does not become the final authority for sensitive actuation,
- model output remains bounded by policy and schema,
- and execution safety is enforced outside the model.

This is likely more persuasive than treating the paper as a pure LLM-quality study.

---

## 7. What should be de-emphasized or avoided

### 7.1 Avoid overclaiming
Do not claim:
- perfect safety,
- complete elimination of risk,
- or infallible intent estimation.

Prefer expressions such as:
- policy-constrained,
- bounded,
- deterministic enforcement,
- structurally restricted,
- caregiver-mediated,
- autonomous unlock blocked.

### 7.2 Avoid making the paper look like a welfare-only case report
If the paper reads primarily as a social-need statement with a light technical layer, it becomes weaker for ICT Express.

The assistive use case should motivate the problem, but the manuscript must still read as a technical contribution.

### 7.3 Avoid presenting doorlock as a current autonomous low-risk action
Under the current architecture interpretation, doorlock should not be described as part of the authoritative autonomous low-risk Class 1 scope.

It should be described as:
- implementation-facing interface support,
- representative sensitive-actuation handling,
- and caregiver-mediated execution path.

---

## 8. Expected manuscript style for ICT Express

The journal is better suited to a **compressed, high-signal manuscript** than to a long narrative paper.

That means the paper should:
- move quickly from problem definition to contribution,
- keep related work focused,
- avoid long architectural history,
- and prioritize key figures/tables over verbose explanation.

The writing style should be:
- concise,
- technically direct,
- and contribution-oriented.

---

## 9. Page-budget implications

ICT Express original papers are short.
Therefore the manuscript should be planned from the start as a compressed paper.

### Practical implication
The paper should avoid spending too much space on:
- long motivation text,
- exhaustive literature review,
- implementation log or deployment details,
- or too many experiment variants.

### Recommended focus for limited space
Priority should be given to:
- one compact system figure,
- one contribution paragraph,
- one experiment setup summary,
- and a small number of high-value results.

A practical paper structure may be:
1. Introduction
2. System Design
3. Experimental Setup
4. Results and Discussion
5. Conclusion

---

## 10. What experiments are most important for this journal submission

Given the page limit, the most important experiments are those that directly support the contribution claims.

### Highest priority
1. **Intent recovery comparison under constrained input**
   - direct mapping vs rule-only vs LLM-assisted
2. **Safe deferral / escalation correctness**
3. **Doorlock-sensitive evaluation**
   - autonomous unlock blocked
   - caregiver escalation correctness
   - approval-path correctness
   - ACK / audit completeness
4. **A compact latency or reproducibility summary** if space allows

### Lower priority for the main paper body
These may be reduced, summarized, or moved out of the main emphasis:
- excessive deployment details,
- too many hardware-specific notes,
- broad scenario enumeration without clear contribution linkage.

---

## 11. Recommended reviewer-facing value proposition

A strong reviewer-facing interpretation is:

- the paper does not simply add an LLM to a smart home,
- it shows how an LLM can be used **under explicit control boundaries**,
- it addresses constrained interaction rather than unrestricted chat control,
- and it treats sensitive actuation as a safety-governed architectural problem.

A useful summary sentence is:

> The main value of the paper is not expanded autonomy, but safe, bounded assistive intelligence under constrained-input conditions.

---

## 12. Formatting and submission reminders

Future writing sessions should check the latest official ICT Express author guide before final submission.

At minimum, remember the following journal-facing constraints:
- original papers are short and double-column formatted,
- manuscripts that do not follow formatting requirements may face desk rejection,
- the abstract should remain concise and self-contained,
- keywords should be compact and in English,
- SI units should be used,
- inclusive language should be maintained,
- and any generative AI use in manuscript preparation must be disclosed according to the publisher’s policy.

Do not rely on memory alone for final submission details.
Always re-check the official guide immediately before submission.

---

## 13. Recommended final interpretation for this project

For ICT Express, the current project should be written as:

- an **edge smart-home control architecture**,
- with **bounded LLM-assisted intent recovery**,
- **policy-constrained execution authority**,
- and **caregiver-mediated handling of sensitive actuation**.

If the manuscript maintains that focus, the project is much more likely to appear technically aligned with the journal.

---

## 14. Short summary

The safest and strongest ICT Express submission strategy is:
- frame the work as an ICT architecture paper,
- keep the central claim narrow,
- use doorlock as a representative sensitive-actuation case,
- emphasize bounded authority rather than expanded autonomy,
- and allocate most of the limited space to the experiments that directly support the contribution claims.

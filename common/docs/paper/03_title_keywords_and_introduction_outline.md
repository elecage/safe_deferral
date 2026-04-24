# 03_title_keywords_and_introduction_outline.md

## 1. Purpose

This document records the currently agreed draft of:

- the paper title,
- the keyword set,
- and the Introduction outline.

It is intended to help future writing sessions keep the manuscript aligned with:

- `common/docs/paper/01_paper_contributions.md`
- `common/docs/paper/02_ICT_Express_submission_notes.md`
- `common/docs/required_experiments.md`

This is a drafting-support document, not a canonical policy/schema document.

---

## 2. Current working title

### Selected title
**Local LLM-Assisted Intent Recovery With Policy-Constrained Sensitive-Actuation Control for Assistive Smart Homes**

### Why this title was selected
This title was chosen because it reflects the current paper framing clearly:

- **Local LLM-Assisted Intent Recovery**
  - keeps the LLM role bounded to intent recovery rather than unrestricted actuation
- **Policy-Constrained Sensitive-Actuation Control**
  - highlights the system’s main safety and control contribution
- **Assistive Smart Homes**
  - keeps the application domain explicit

### Interpretation note
The title should continue to be interpreted as:
- a systems/architecture paper,
- not a general product paper,
- and not a paper claiming unrestricted LLM autonomy.

---

## 3. Current keyword set

### Selected keywords
- Assistive smart home
- Large language model
- Intent recovery
- Edge AI
- Constrained alternative input
- Sensitive actuation
- Caregiver escalation

### Why this keyword set was selected
The set is meant to balance:

- application domain:
  - Assistive smart home
- technical core:
  - Large language model
  - Edge AI
- functional contribution:
  - Intent recovery
- user/input condition:
  - Constrained alternative input
- safety/authority structure:
  - Sensitive actuation
  - Caregiver escalation

### Interpretation note
If future journal formatting or indexing considerations require minor keyword revision, the following semantic balance should still be preserved:
- assistive domain,
- LLM/edge-AI technology,
- constrained-input problem,
- sensitive-actuation safety mechanism.

---

## 4. Current Introduction outline

The Introduction should remain compact and contribution-oriented.
For the current ICT Express target direction, a five-paragraph structure is recommended.

### Paragraph 1. Problem background
Main message:
- smart homes can improve convenience and safety,
- but users with severe physical or speech-related limitations may not be able to use standard voice/touch interfaces independently,
- and bounded alternative input may not be expressive enough to communicate intent clearly.

Main objective of this paragraph:
- establish the practical and technical importance of the problem.

### Paragraph 2. Limitation of existing approaches
Main message:
- direct rule-based mapping can be simple and safe, but becomes brittle under ambiguous or underspecified input,
- while unrestricted LLM-driven actuation is unsafe for sensitive physical actions,
- so the main problem is how to use LLM assistance without giving the model unrestricted execution authority.

Main objective of this paragraph:
- motivate the architectural gap that the paper addresses.

### Paragraph 3. Proposed core idea
Main message:
- the paper proposes an edge architecture in which a local LLM assists intent recovery under constrained alternative input,
- while policy/schema/validator layers remain authoritative for execution,
- and safe deferral, caregiver escalation, manual approval, ACK verification, and local audit logging form the closed-loop safety structure.

Main objective of this paragraph:
- present the proposed system at a high level.

### Paragraph 4. Doorlock as a representative sensitive-actuation case
Main message:
- doorlock-related control is not an ordinary low-risk convenience action,
- it is a representative sensitive-actuation case tied to residential safety and security,
- and it is therefore an appropriate scenario for demonstrating why intent recovery and execution authority must be separated.

Main objective of this paragraph:
- justify why the paper includes doorlock-related evaluation.

### Paragraph 5. Contributions
Main message:
- clearly enumerate the paper’s 3–4 contribution points,
- keeping the list short, memorable, and directly tied to the experiments.

Main objective of this paragraph:
- make the paper’s novelty explicit before moving into the next section.

---

## 5. Introduction logic flow

The current intended Introduction flow is:

1. constrained-input assistive interaction is difficult,
2. rule-only mapping is too brittle,
3. unrestricted LLM actuation is unsafe,
4. a bounded architecture is proposed,
5. doorlock is used as a representative sensitive-actuation case,
6. the contributions are summarized explicitly.

This flow should remain stable unless the paper framing changes significantly.

---

## 6. Writing cautions for the Introduction

### 6.1 Do not let the Introduction become too broad
The Introduction should not expand into a broad smart-home survey or a long social background section.

### 6.2 Move quickly from motivation to architecture
The paper should quickly transition from user/input limitation to the technical problem and the proposed solution.

### 6.3 Avoid overclaiming safety
Avoid language implying perfect safety or total risk elimination.
Prefer bounded, policy-constrained, deterministic, or caregiver-mediated wording.

### 6.4 Keep doorlock in the right role
Doorlock should appear as a representative sensitive-actuation case, not as the entire identity of the paper.

### 6.5 Keep contribution count small
The contribution paragraph should ideally remain within 3–4 items.

---

## 7. Short summary

The current paper drafting baseline is:

- **Title:** Local LLM-Assisted Intent Recovery With Policy-Constrained Sensitive-Actuation Control for Assistive Smart Homes
- **Keywords:** Assistive smart home; Large language model; Intent recovery; Edge AI; Constrained alternative input; Sensitive actuation; Caregiver escalation
- **Introduction shape:** problem background → limits of existing methods → proposed architecture → doorlock-sensitive case → contributions

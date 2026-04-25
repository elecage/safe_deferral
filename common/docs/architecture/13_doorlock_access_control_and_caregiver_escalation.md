# 13_doorlock_access_control_and_caregiver_escalation.md

## 1. Purpose

This document defines the current architectural interpretation for **doorlock-related actuation** in the safe_deferral project.

The purpose of this document is to clarify:

- why doorlock control must be treated differently from lighting or other low-risk assistance actions,
- how the LLM may participate in interpreting limited user input,
- why door unlock must not be treated as an autonomous low-risk Class 1 action in the current baseline,
- how caregiver escalation, bounded confirmation, ACK validation, and audit logging should be combined into a safe closed-loop pathway,
- what policy/schema/prompt/experiment implications follow from this interpretation.

This document is an architecture and safety-interpretation document.  
It does **not by itself** redefine the canonical frozen policy or schema baseline.  
Any canonical change to low-risk actuation scope must still be explicitly reflected in the frozen policy/schema assets.

---

## 2. Background

A major objective of this project is to support users who cannot easily speak or produce rich direct input, by combining:

- constrained alternative input (for example, single-hit or bounded button input),
- environmental and device context,
- visitor-response context such as `doorbell_detected`, which represents a recent doorbell or visitor-arrival signal,
- and LLM-based interpretation of likely user intent.

In such settings, the user may intend actions such as:

- ignore the visitor,
- notify a caregiver,
- request visitor confirmation,
- or unlock the door.

However, unlike lighting assistance, **door unlock** is directly tied to:

- residential security,
- user safety,
- caregiver responsibility,
- and potential irreversible harm if executed incorrectly.

Therefore, doorlock actuation must be treated as a **sensitive actuation domain**, not as an ordinary bounded convenience action.

---

## 3. Core Design Position

## 3.1 Door unlock is not a current autonomous low-risk Class 1 action
Under the current project interpretation, door unlock must **not** be treated as part of the presently authorized autonomous low-risk Class 1 actuation domain.

In other words:

- the system may implement a doorlock node,
- the system may interpret user intent related to a visitor event,
- but the system must **not** allow the local LLM to autonomously open the door as a standard Class 1 low-risk action.

## 3.2 Doorlock is implementation-facing scope, not yet autonomous low-risk policy scope
Doorlock may exist in the implementation-facing scope as:

- a representative actuator interface,
- a bounded embedded node,
- a caregiver-mediated actuation endpoint,
- an experimental validation target.

But that does **not** imply that door unlock is already part of the authoritative autonomous low-risk action catalog.

## 3.3 The LLM may interpret intent, but must not hold final unlock authority
The LLM may assist with:

- interpreting limited user input,
- combining contextual cues,
- proposing likely intent candidates,
- recommending escalation or clarification.

The LLM must not be the final authority for:

- autonomous door unlock approval,
- door unlock execution authorization,
- override of policy-restricted actuation domains.

---

## 4. Why Doorlock Is Different from Lighting

Doorlock differs from lighting in several important ways.

### 4.1 Security sensitivity
A mistaken light toggle is typically inconvenient.  
A mistaken door unlock may expose the user to:

- unauthorized entry,
- personal harm,
- theft,
- or privacy/security compromise.

### 4.2 Irreversibility of consequences
Even a short accidental unlock may create a harm window that cannot be undone by simply relocking later.

### 4.3 Ambiguity of visitor context
A doorbell event does not uniquely imply that the user wants the door opened.

In the current context schema, `doorbell_detected=true` is a visitor-response interpretation signal. It does **not** authorize autonomous doorlock control.

The same event may correspond to many possible user intentions:
- notify me only,
- call my caregiver,
- ask who is there,
- ignore it,
- unlock it.

### 4.4 Elevated risk under limited-input conditions
In the target user population, input may be:
- sparse,
- delayed,
- error-prone,
- fatigue-sensitive,
- or hard to disambiguate.

This makes unrestricted autonomous door unlock especially unsafe.

---

## 5. Current Architectural Interpretation

## 5.1 Doorlock requests may enter the interpretation path
A user may express a visitor-response intention through constrained input, such as:
- a button hit,
- a short bounded utterance,
- or another alternative-input signal.

The system may then collect:
- physical environment context,
- observable device state context,
- `doorbell_detected` as visitor-response context,
- caregiver presence/absence context if available,
- and other bounded assistance-relevant information.

This information may be provided to the LLM for **intent interpretation**.

Current schema boundary:

- `doorbell_detected` is part of `environmental_context`.
- Doorlock state is **not** currently part of `context_schema.device_states`.
- Doorlock state, approval state, and ACK state should be represented through separate experiment annotations, mock approval state, dashboard-side observations, audit artifacts, or a future schema revision.

This boundary means that doorlock can remain an implementation-facing representative interface without being silently inserted into the current pure-context device-state contract.

## 5.2 But door unlock must not enter autonomous Class 1 execution
Even if the LLM infers that the user likely wants the door opened, the current architecture must prevent that interpretation from becoming autonomous unlock execution.

That prevention should be enforced by multiple layers:

- policy restrictions,
- allowed action domain restrictions,
- candidate action schema restrictions,
- deterministic validator checks,
- and dispatcher-level actuation boundary checks.

## 5.3 Door unlock currently belongs to caregiver-mediated control
Under the present interpretation, a door unlock request should be routed into a **caregiver-mediated escalation path**, not directly into autonomous low-risk actuation.

This means the effective execution path is:

- user intent interpretation,
- safety restriction enforcement,
- caregiver handoff,
- manual approval,
- bounded actuator dispatch through a separately governed manual confirmation path,
- ACK verification,
- local audit logging.

---

## 6. Recommended Closed-Loop Handling Pipeline

The following is the recommended closed-loop handling path for a doorlock-related request under the current safety interpretation.

## Step 1. Limited user input and pure context collection
When the user produces a bounded input event, the system collects a context package containing:

- the user’s alternative input signal,
- relevant environmental context,
- observable device state context,
- `doorbell_detected` as relevant visitor-response context,
- and other bounded physical context useful for interpretation.

The LLM-facing input should remain focused on meaningful user-intent context.  
Operational routing metadata, network diagnostics, or unrelated internal system metadata should not be mixed into that interpretation payload unless explicitly required.

Doorlock state is not currently included in `context_schema.device_states`; if an experiment needs doorlock state, approval state, or ACK state, it should keep those values outside the current pure-context `device_states` object unless a future schema revision explicitly adds them.

## Step 2. LLM-based intent interpretation under bounded actuation restrictions
The LLM may interpret the user’s likely intent and generate bounded intent candidates such as:

- notify caregiver,
- request confirmation,
- visitor-related assistance request,
- possible door unlock intent.

However, the LLM must **not** be allowed to produce an autonomous door-unlock action as a valid Class 1 low-risk execution candidate in the current baseline.

Instead, if the interpreted intent implies door unlock, the LLM output should remain within one of the following bounded forms:

- safe deferral,
- policy-restricted escalation suggestion,
- caregiver handoff recommendation,
- or another explicitly non-autonomous restricted outcome.

## Step 3. Deterministic policy/validator enforcement
The deterministic validator must ensure that door unlock does not pass into autonomous actuation if it is outside the authorized low-risk actuation domain.

This should be enforced through multiple boundaries:

- the frozen low-risk catalog,
- candidate action constraints,
- policy-domain restrictions,
- validator admissibility checks,
- dispatcher boundary checks.

In practical terms, the validator should prevent the door unlock request from being forwarded as an automatically executable low-risk action.

## Step 4. Caregiver escalation and manual approval
Once autonomous unlock is blocked, the system should transition into a caregiver-mediated escalation path.

The system may send a bounded outbound notification through a safe outbound-only channel, such as Telegram, containing:

- situation summary,
- visitor event summary including `doorbell_detected` when relevant,
- relevant context summary,
- and a manual confirmation path for caregiver review.

Door unlock may be issued only after caregiver approval through a separately governed manual confirmation path outside the Class 1 validator executable payload.

## Step 5. Closed-loop ACK verification and local audit logging
If caregiver approval results in a doorlock command being issued, the system must verify physical or device-state acknowledgment.

That closed-loop verification should include:

- command dispatch result,
- device ACK or equivalent state confirmation,
- failure/timeout detection,
- final outcome recording.

The following should be logged locally through the single-writer audit path:

- user input interpretation summary,
- `doorbell_detected` or visitor-response context when relevant,
- LLM output classification,
- validator rejection or escalation record,
- caregiver approval outcome,
- device ACK result,
- final actuation or non-actuation result.

---

## 7. What the LLM Is Allowed to Do

Under this design, the LLM may:

- interpret limited user input,
- combine sensor and contextual cues,
- estimate likely user intent,
- produce bounded assistance candidates,
- recommend escalation,
- support safe deferral or bounded clarification.

The LLM must not:

- authorize autonomous door unlock,
- override policy restrictions,
- create new door-unlock action domains not present in canonical safety constraints,
- bypass validator or caregiver approval,
- or directly dispatch sensitive doorlock actuation.

---

## 8. Safe Deferral vs Caregiver Escalation for Doorlock

Doorlock-related situations may involve either:

- **safe deferral**, or
- **caregiver escalation**.

The distinction should be made carefully.

## 8.1 Safe deferral
Safe deferral is appropriate when:
- the user intent is ambiguous,
- clarification is still meaningful,
- and no sensitive actuation is executed automatically.

Example:
- the system believes the user may mean either “call caregiver” or “notify only”.

In such cases, bounded clarification may still be appropriate.

## 8.2 Caregiver escalation
Caregiver escalation is appropriate when:
- the inferred action would involve sensitive actuation,
- ambiguity remains,
- or policy restrictions prohibit autonomous execution.

Door unlock under the current interpretation should generally fall into this category.

---

## 9. Relationship to Current Frozen Assets

This document does **not** itself modify frozen assets.  
However, it has strong implications for how existing assets should be interpreted.

### 9.1 Low-risk action catalog
If door unlock is not present in the frozen low-risk action catalog, then it must not be silently treated as a standard autonomous Class 1 action.

### 9.2 Context schema
`doorbell_detected` is currently the schema-level visitor-response context signal.

Doorlock state is not currently part of `context_schema.device_states`. This does not mean doorlock is out of implementation scope; it means the current pure-context device-state contract does not authorize or carry doorlock state as a normal Class 1 context field.

### 9.3 Candidate action schema
If doorlock action types are absent from the permitted candidate action domain, then autonomous unlock must remain structurally blocked.

### 9.4 Validator output behavior
Validator behavior must remain consistent with the principle that restricted sensitive actions are escalated rather than silently admitted into the execution path.

### 9.5 Required experiments
This interpretation implies that doorlock-related tests should focus on:
- doorbell-context-aware visitor-response interpretation,
- blocked autonomous unlock,
- caregiver handoff,
- manual approval path,
- ACK verification,
- and audit completeness.

---

## 10. Potential Future Policy / Schema Changes

The following items may need future review if doorlock support becomes a formalized system feature.

### 10.1 Policy review
Possible future addition:
- an explicit policy statement that door unlock is a caregiver-mediated sensitive actuation domain.

### 10.2 Schema review
Possible future addition:
- schema support for bounded caregiver-approved doorlock actuation records,
- explicit approval metadata,
- explicit ACK/outcome logging fields,
- optional or required doorlock state representation if it becomes part of a future pure-context contract.

### 10.3 Low-risk catalog review
This document does **not** recommend silently adding door unlock to the autonomous low-risk catalog.

If that question is revisited in the future, it should require:
- explicit risk review,
- explicit policy revision,
- explicit experiment updates,
- and likely additional safety constraints.

---

## 11. Prompt Implications

Prompt files and coding instructions should reflect the following rules:

- do not assume doorlock is part of autonomous low-risk Class 1 execution,
- do not generate direct autonomous unlock logic without caregiver approval,
- treat `doorbell_detected` as visitor-response context, not unlock authorization,
- treat doorlock as a sensitive actuation domain,
- allow representative doorlock-node implementation,
- but preserve the distinction between implementation-facing interface support and authorized autonomous actuation scope.

This is especially relevant to:
- architecture prompts,
- Claude Code prompts,
- firmware-generation prompts,
- and future actuator-dispatch prompts.

---

## 12. Experiment Implications

The following experiment families are recommended.

### 12.1 Unauthorized autonomous unlock blocked
Goal:
- verify that LLM-inferred unlock intent is not autonomously executed.

### 12.2 Doorbell-context-aware interpretation
Goal:
- verify that `doorbell_detected=true` and `doorbell_detected=false` are interpreted differently where appropriate, while neither state authorizes autonomous door unlock.

### 12.3 Caregiver escalation path validation
Goal:
- verify that doorlock-sensitive requests are routed to caregiver approval instead of autonomous dispatch.

### 12.4 Manual approval to ACK closed loop
Goal:
- verify:
  - caregiver approval through a separately governed manual confirmation path,
  - command dispatch outside the Class 1 validator executable payload,
  - physical/device ACK,
  - local audit logging.

### 12.5 Safe deferral for ambiguous visitor-response intent
Goal:
- verify that ambiguous visitor situations can be resolved without unsafe autonomous unlock.

---

## 13. Current Recommendation

The current recommended interpretation is:

- implement doorlock as a representative bounded actuator interface if needed,
- use `doorbell_detected` as visitor-response context,
- allow the LLM to interpret constrained user intent in visitor-response situations,
- do not allow autonomous unlock as a standard Class 1 low-risk action,
- route unlock-related sensitive outcomes through caregiver escalation or a separately governed manual confirmation path,
- require ACK-based closed-loop verification,
- and log all relevant steps locally.

This preserves the research goal of using LLMs to support limited-input users, while preventing unsafe autonomous unlock behavior.

---

## 14. Short Summary

In the current safe_deferral architecture, doorlock opening is treated as a **sensitive actuation domain**, not as an ordinary low-risk assistance action.

`doorbell_detected` may help the system interpret a visitor-related situation, but it does not authorize autonomous door unlock.

The LLM may help interpret what the user wants in a visitor-related situation, but it must not autonomously authorize or execute door unlock. Instead, door unlock must remain structurally blocked from autonomous Class 1 execution and should proceed only through caregiver escalation, a separately governed manual confirmation path, ACK-based closed-loop verification, and local audit logging.

This interpretation allows the project to support alternative-input intent recovery without sacrificing residential security and user safety.

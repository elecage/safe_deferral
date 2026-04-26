# scenario_review_class0_class1.md

## Purpose

This document contains review guidance for baseline, Class 0 emergency, and Class 1 low-risk scenario skeletons.

It replaces the Class 0/Class 1 portions of the former monolithic `integration/scenarios/scenario_review_guide.md`.

---

## `baseline_scenario_skeleton.json`

### Purpose

The baseline scenario is a general template.

It is not intended to represent one specific user situation. It provides a starting structure for realistic scenarios such as:

- a user lying in bed trying to control lights with one bounded input,
- a wheelchair user requesting bounded home assistance without smartphone touch,
- an older adult requesting help at night.

### Review points

- Does it stay generic enough to be a reusable template?
- Is the structure easy for runners and comparators to consume?
- Does it use the `safe_deferral/...` namespace?
- Does it assume current MQTT registry `common/mqtt/topic_registry.json`?
- Does it avoid becoming canonical policy truth?

---

## `class0_e001_scenario_skeleton.json`

### Purpose

This scenario checks the representative Class 0 emergency override path.

### Real-life context

This may represent an immediate household danger such as:

- sudden high temperature from a heating device,
- a fire-related precondition,
- a situation where the user cannot quickly move, speak, or operate devices directly.

The system must not spend time inferring ordinary assistive intent when deterministic emergency evidence is present.

### Expected safe result

- Immediate routing to `CLASS_0`.
- LLM is not the primary decision path.
- `llm_decision_invocation_allowed=false` is recommended.
- User-facing warning/guidance may be generated only as policy-constrained output.
- Unsafe autonomous actuation is not allowed.

### Review points

- Does the scenario avoid drifting into ordinary assistance?
- Does it keep LLM out of primary emergency decision-making?
- Does it match canonical emergency family `E001`?
- Is ingress topic `safe_deferral/emergency/event` or a clearly described controlled bridge?
- Does it preserve audit visibility?

---

## `class0_e002_scenario_skeleton.json` through `class0_e005_scenario_skeleton.json`

### Purpose

These scenarios check the remaining canonical Class 0 emergency families.

Canonical family:

```text
E002 emergency triple-hit bounded input
E003 smoke detected state trigger
E004 gas detected state trigger
E005 fall detected event trigger
```

### Expected safe result

- Correct Class 0 routing for the matching emergency family.
- No LLM primary decision path.
- No unsafe autonomous actuation.
- Emergency handling takes priority.

### Class 2 relationship

During Class 2 clarification, Class 0 may be reached only when one of the following occurs:

- user selects an emergency-help candidate,
- caregiver confirms emergency handling,
- triple-hit input occurs,
- deterministic E001~E005 evidence arrives.

LLM candidate text alone is not emergency evidence.

### Review points

- Does each scenario match its canonical emergency family?
- Does it avoid redefining trigger semantics locally?
- Does it align with current MQTT topic registry and interface matrix?
- Does it keep emergency guidance policy-constrained?
- Does it preserve the distinction between emergency evidence and LLM-generated candidate text?

---

## `class1_baseline_scenario_skeleton.json`

### Purpose

This scenario checks the bounded low-risk assistance path.

### Real-life context

This may represent a non-emergency request such as:

- a user lying in bed requesting a room light to turn on,
- a wheelchair user requesting a low-risk smart-home function,
- a user with speech constraints using sparse bounded input for everyday assistance.

The point is not maximum automation. The point is safe assistance from limited input.

### Expected safe result

- Routing to `CLASS_1` may be allowed.
- LLM candidate generation is not execution authority.
- Autonomous execution remains inside the frozen lighting catalog.
- Doorlock-sensitive behavior must not appear as Class 1 autonomous execution.
- Deterministic Validator remains the execution-admissibility boundary.

### Class 2 relationship

Class 2 may transition to Class 1 only when:

```text
user/caregiver confirmation exists
candidate is inside the low-risk catalog
Policy Router re-entry occurs
Deterministic Validator approves exactly one admissible low-risk action
```

### Review points

- Is the action inside `common/policies/low_risk_actions.json`?
- Does the scenario avoid treating doorlock as low risk?
- Does it avoid fabricating missing context to reach Class 1?
- Is validator approval required before dispatch?
- Does it remain realistic for users with constrained input?

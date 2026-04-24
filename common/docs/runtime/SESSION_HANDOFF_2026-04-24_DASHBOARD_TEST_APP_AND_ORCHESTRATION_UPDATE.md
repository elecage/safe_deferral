# SESSION_HANDOFF_2026-04-24_DASHBOARD_TEST_APP_AND_ORCHESTRATION_UPDATE.md

## Purpose

This addendum records the architectural interpretation that resulted from the discussion about:

- experiment control from the dashboard,
- the role of a developer-facing test app,
- and where doorlock-sensitive experiments should be reflected across Mac mini and Raspberry Pi.

Read together with:
- `common/docs/runtime/SESSION_HANDOFF.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-24_PROMPT_REFACTOR_AND_EVAL_UPDATE.md`

---

## 1. Doorlock-sensitive experiments are not dashboard-only concerns

Doorlock-related experiments must not be interpreted as dashboard-only artifacts.

The current agreed interpretation is:

- doorlock-sensitive experiments should be reflected in the dashboard,
- in the developer/test app layer when such an app is used,
- and in scenario orchestration.

This is because the experiment is not just a visual status card.
It is a multi-stage evaluation flow that includes:

- trigger/input injection,
- contextual state setup,
- policy and validation path observation,
- caregiver escalation,
- manual approval simulation or confirmation,
- ACK observation,
- and audit completeness checks.

---

## 2. Role separation: dashboard vs test app

### Dashboard
The dashboard should be treated as an experiment operations console.

Typical responsibilities:
- experiment selection
- preflight readiness visibility
- required-node connectivity/status visibility
- start/stop control
- progress monitoring
- result summary
- graph/CSV export
- doorlock-sensitive experiment status such as:
  - autonomous unlock blocked
  - caregiver escalation state
  - manual approval state
  - ACK state
  - audit completeness state

### Test app
The test app should be treated as a finer-grained developer/research control surface.

Typical responsibilities:
- raw scenario invocation
- baseline selection
- direct mapping vs rule-only vs LLM-assisted comparison execution
- visitor-response mock event injection
- caregiver approval mock state injection
- ACK success/timeout/mismatch simulation
- raw payload/log/debug visibility

The dashboard and test app therefore do not have to be identical.
They may expose overlapping data, but the dashboard is more operations-oriented while the test app is more experiment/debug-oriented.

---

## 3. Role separation: Mac mini vs Raspberry Pi

### Mac mini
The Mac mini remains the most natural host for:
- dashboard UI or dashboard-facing integration
- test app UI/backend if present
- hub-side status aggregation
- approval/audit/result viewing
- experiment-control entry points

### Raspberry Pi
The Raspberry Pi remains the most natural host for:
- scenario orchestration
- simulation and replay
- fault injection
- virtual node driving
- progress/status publication
- evaluation artifact generation

Therefore, Raspberry Pi does not necessarily need to host a UI for these experiments.
Its primary role is execution/support rather than dashboard hosting.

---

## 4. Scenario orchestration must explicitly include doorlock-sensitive experiments

Doorlock-related evaluation must be reflected in scenario orchestration.

The reason is that the experiment is sequence-based rather than a single isolated event.

At minimum, the orchestrator may need to support:
- visitor-response scenario family selection
- bounded input or doorbell-style trigger injection
- contextual state bundle setup
- expected safe outcome declaration
- caregiver approval state variants:
  - approved
  - denied
  - timeout
  - invalid approval
- ACK outcome variants:
  - success
  - timeout
  - mismatch
- audit/result artifact collection

This means the doorlock-sensitive path is a first-class orchestration concern, not just a UI concern.

---

## 5. Documentation implication

The discussion concluded that the repository should eventually reflect this interpretation in:

- prompt documents
- CLAUDE guidance
- handoff addenda
- and any future dashboard/test-app implementation documents

In practice, the most important architectural message is:

> doorlock-sensitive experiments must be visible in the dashboard, operable in the test-app/developer path when such a path exists, and reproducible through scenario orchestration, with Mac mini centered on UI/control and Raspberry Pi centered on execution/replay/fault-injection support.

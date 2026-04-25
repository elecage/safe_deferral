# SESSION_HANDOFF_2026-04-24_DASHBOARD_TEST_APP_AND_ORCHESTRATION_UPDATE.md

## Purpose

This addendum records the architectural interpretation that resulted from the discussion about:

- experiment control from the dashboard,
- the role of a developer-facing test app,
- and where doorlock-sensitive experiments should be reflected across Mac mini and Raspberry Pi.

This document has been realigned with the later architecture decision that the dashboard is an **Raspberry Pi 5-hosted experiment and monitoring console**, while the Mac mini remains the safety-critical operational edge hub.

Read together with:
- `common/docs/runtime/SESSION_HANDOFF.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-24_PROMPT_REFACTOR_AND_EVAL_UPDATE.md`
- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_POLICY_SCHEMA_ALIGNMENT_UPDATE.md`
- `common/docs/architecture/24_final_paper_architecture_figure.md`
- `common/docs/architecture/01_installation_target_classification.md`

---

## 1. Doorlock-sensitive experiments are not dashboard-only concerns

Doorlock-related experiments must not be interpreted as dashboard-only artifacts.

The current agreed interpretation is:

- doorlock-sensitive experiments should be visible in the Raspberry Pi 5-hosted experiment dashboard,
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

Doorlock-sensitive experiments must not be interpreted as Class 1 autonomous low-risk execution experiments.
They are representative sensitive-actuation experiments and must show that autonomous unlock is blocked unless routed through Class 2 escalation or a separately governed manual confirmation path.

---

## 2. Role separation: dashboard vs test app

### Dashboard
The dashboard should be treated as an **experiment operations and monitoring console hosted on Raspberry Pi 5**.

Typical responsibilities:
- experiment selection
- preflight readiness visibility
- required-node connectivity/status visibility
- start/stop control
- progress monitoring
- result summary
- graph/CSV export
- evaluation artifact export
- doorlock-sensitive experiment status such as:
  - autonomous unlock blocked
  - caregiver escalation state
  - manual approval state
  - ACK state
  - audit completeness state

The dashboard is not the policy authority, validator authority, caregiver approval authority, or primary operational hub.
It may consume operational telemetry, audit summaries, and control-state topics exposed by the Mac mini.

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

If a separate test app is implemented, it should not become an unrestricted policy or actuation bypass.
Sensitive actuation branches must still respect the frozen policy/schema boundary and the governed manual confirmation path.

---

## 3. Role separation: Mac mini vs Raspberry Pi

### Mac mini
The Mac mini remains the safety-critical operational edge hub for:
- MQTT/state intake
- context aggregation
- local LLM reasoning
- policy routing
- deterministic validation
- context-integrity safe deferral handling
- caregiver escalation and approval handling
- ACK and audit logging
- telemetry, audit-summary, and control-state topic exposure for the Raspberry Pi 5 dashboard

The Mac mini should not be treated as the experiment dashboard host in the current architecture interpretation.
Its role is operational safety control, policy-governed execution, escalation handling, and audit closure.

### Raspberry Pi 5
The Raspberry Pi 5 remains the most natural host for:
- Monitoring / Experiment Dashboard
- scenario orchestration
- simulation and replay
- fault injection
- virtual node driving
- progress/status publication
- evaluation artifact generation
- graph/CSV export
- experiment result publication

Therefore, Raspberry Pi 5 **does host the experiment and monitoring dashboard** in the current interpretation.
Its role is support-side visibility, orchestration, fault injection, and experiment-result publication rather than safety-critical operational authority.

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

Scenario orchestration must preserve the following policy/schema boundary:
- Class 1 autonomous execution is restricted to the current low-risk light-control catalog.
- Doorlock control must not be emitted as a `candidate_action_schema` autonomous candidate.
- Doorlock control must not be approved in `validator_output_schema.executable_payload`.
- Doorlock-sensitive requests must route to Class 2 escalation or a separately governed manual confirmation path.
- `manual_confirmation_path` is a review/intervention route and does not by itself authorize execution.

---

## 5. Documentation implication

The repository should reflect this interpretation in:

- prompt documents
- CLAUDE guidance
- handoff addenda
- dashboard implementation documents
- test-app implementation documents
- scenario orchestration documents
- experiment result-comparator logic

The most important architectural message is:

> doorlock-sensitive experiments must be visible in the Raspberry Pi 5-hosted dashboard, operable in the test-app/developer path when such a path exists, and reproducible through scenario orchestration, with Mac mini centered on safety-critical operational control and Raspberry Pi 5 centered on experiment dashboard, orchestration, replay, fault injection, and result publication.

---

## 6. Superseded interpretation

The earlier interpretation that Mac mini was the natural host for the dashboard UI is superseded by the later architecture alignment.

Current interpretation:

- **Mac mini**: operational safety-critical edge hub
- **Raspberry Pi 5**: experiment dashboard, orchestration, simulation/replay, fault injection, and result-publication support region

If future documents mention Mac mini as the dashboard host, that wording should be revised unless it clearly means that Mac mini exposes telemetry or dashboard-facing operational data consumed by the Raspberry Pi 5 dashboard.

# 12_prompts_mac_mini_components.md

## Purpose

This prompt set covers Mac mini operational hub components.

The Mac mini is the safety-critical edge hub. It owns operational intake,
policy routing, deterministic validation, bounded LLM guidance, Class 2
clarification, low-risk dispatch, caregiver escalation, ACK handling, audit
logging, and read-only telemetry for experiment tools.

## Common Instructions

Before implementing any Mac mini component:

- read the active architecture documents from `12_prompts.md`,
- load canonical policy/schema/MQTT/payload assets from `common/`,
- keep generated code under `mac_mini/`,
- do not reintroduce implementation code until the implementation resume gate in
  `05_implementation_plan.md` is satisfied,
- do not hardcode topic strings, action domains, schema paths, or policy
  thresholds where canonical assets provide them,
- do not let deployment-local files redefine canonical truth.

## Prompt MM-01. Operational MQTT And Context Intake

Generate the Mac mini intake component that receives registry-aligned MQTT
traffic and constructs validated policy-router input.

Required behavior:

- consume context input through the current MQTT registry,
- validate payloads against `common/schemas/policy_router_input_schema.json`,
- preserve separation between `pure_context_payload` and routing metadata,
- require `environmental_context.doorbell_detected` where context schema validity
  requires it,
- reject or quarantine malformed payloads without treating them as Class 1
  executable requests,
- emit audit events for accepted, rejected, and quarantined inputs.

Forbidden behavior:

- no direct actuator dispatch,
- no LLM invocation from intake,
- no policy decision based on unchecked payloads,
- no doorlock authorization from `doorbell_detected`.

## Prompt MM-02. Local LLM Adapter

Generate the Mac mini local LLM adapter used only for bounded candidate guidance.

Required behavior:

- accept only approved bounded input context from upstream components,
- produce schema-constrained candidates where LLM use is allowed,
- keep routing metadata, freshness metadata, audit metadata, and network status
  out of the LLM interpretation context unless a future canonical design says
  otherwise,
- return candidate text or candidate actions as guidance only,
- support deterministic mock mode for experiments.

Forbidden behavior:

- no final class decision,
- no validator approval,
- no actuator command,
- no emergency trigger declaration,
- no doorlock authorization.

## Prompt MM-03. Policy Router

Generate the deterministic Policy Router.

Required behavior:

- classify inputs into Class 0, Class 1, or Class 2 according to
  `common/policies/policy_table.json`,
- prioritize deterministic emergency evidence,
- route insufficient, stale, missing, conflicting, or sensitive requests
  conservatively,
- expose whether LLM candidate generation is allowed,
- emit machine-readable route results and audit events.

Forbidden behavior:

- no direct hardware control,
- no downgrade of malformed emergency-like evidence into low-risk execution,
- no invented policy classes or thresholds.

## Prompt MM-04. Deterministic Validator

Generate the deterministic validator for Class 1 bounded assistance.

Required behavior:

- validate candidate actions against
  `common/schemas/candidate_action_schema.json`,
- admit only canonical low-risk lighting actions from
  `common/policies/low_risk_actions.json`,
- resolve to one executable low-risk action or produce safe deferral,
  escalation, or rejection,
- require downstream ACK evidence before final success logging.

Forbidden behavior:

- no direct hardware control,
- no high-risk action approval,
- no multi-candidate arbitrary choice,
- no doorlock approval as Class 1.

## Prompt MM-05. Context-Integrity Safe Deferral Handler

Generate the Mac mini safe deferral handler.

Required behavior:

- handle unresolved or ambiguous low-risk candidates,
- convert bounded candidate choices into accessible clarification instructions,
- support timeout/no-response as non-selection,
- re-enter the Policy Router after user/caregiver confirmation or additional
  deterministic evidence,
- emit audit records for candidate presentation, response, timeout, and final
  safe outcome.

Forbidden behavior:

- no open-ended chat path,
- no inferred intent from silence,
- no direct actuator dispatch.

## Prompt MM-06. Class 2 Clarification Manager

Generate the Class 2 clarification manager.

Required behavior:

- publish and consume Class 2 interaction evidence through
  `safe_deferral/clarification/interaction`,
- validate records with `common/schemas/clarification_interaction_schema.json`,
- manage branches for Class 2 to Class 1, Class 2 to Class 0, and Class 2 to
  Safe Deferral / Caregiver Confirmation,
- ensure every transition re-enters the Policy Router,
- record candidate choices, selection, timeout/no-response, transition target,
  and final safe outcome.

Forbidden behavior:

- no final class transition by itself,
- no validator bypass,
- no emergency trigger authority from candidate text,
- no doorlock authorization.

## Prompt MM-07. Low-Risk Dispatcher And ACK Handler

Generate the low-risk dispatch and ACK handling component.

Required behavior:

- accept only validator-approved Class 1 actions,
- dispatch bounded lighting commands to the appropriate actuator interface,
- wait for ACK or state confirmation,
- classify timeout, mismatch, or actuator failure conservatively,
- emit audit events for dispatch request, ACK, timeout, mismatch, and final
  outcome.

Forbidden behavior:

- no direct acceptance of LLM candidates,
- no dispatch from dashboard/governance tools,
- no doorlock dispatch in the autonomous Class 1 path.

## Prompt MM-08. Caregiver Escalation And Confirmation Backend

Generate caregiver escalation and confirmation support.

Required behavior:

- send Class 0 and Class 2 notifications using
  `common/schemas/class2_notification_payload_schema.json` where applicable,
- use Telegram Bot API as the primary caregiver notification channel for the
  current implementation plan,
- support mock notification mode for offline tests and repeatable experiments,
- keep Telegram bot token, chat ID, webhook/polling mode, and deployment
  secrets in deployment-local configuration rather than tracked canonical docs,
- support Telegram inline-button or bounded callback confirmation where
  appropriate, while preserving caregiver confirmation as a governed manual
  path,
- collect caregiver confirmation, denial, invalid response, and timeout,
- keep caregiver confirmation separate from Class 1 validator approval,
- require audit and ACK evidence for any governed manual sensitive path.

Forbidden behavior:

- no caregiver approval spoofing outside controlled test mode,
- no automatic conversion of caregiver confirmation into Class 1 approval,
- no unrestricted doorlock command path.

## Prompt MM-09. Audit Logging Service

Generate the Mac mini audit logging service.

Required behavior:

- provide a single-writer audit pipeline,
- record routing, validation, deferral, clarification, escalation, caregiver,
  dispatch, ACK, timeout, and failure events,
- expose a verification-safe audit stream or read-only summary for RPi
  experiment tools,
- keep audit evidence immutable enough for experiment review.

Forbidden behavior:

- no dashboard or experiment tool as direct audit authority,
- no multi-writer database pattern,
- no audit event that grants operational authority.

## Prompt MM-10. Read-Only Telemetry Adapter For Experiment Tools

Generate a Mac mini telemetry adapter consumed by Raspberry Pi dashboards and
experiment managers.

Required behavior:

- expose route summaries, service status, audit summaries, ACK summaries, and
  Class 2 transition state as read-only telemetry,
- use MQTT or API contracts aligned with the topic registry,
- preserve privacy by exposing only the minimum experiment-safe information,
- support replay or mock mode for offline experiment validation.

Forbidden behavior:

- no dashboard-originated policy override,
- no direct actuator control,
- no registry, policy, or schema editing through this adapter.

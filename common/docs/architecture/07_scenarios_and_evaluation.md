# Scenarios And Evaluation

## 1. Purpose

This document summarizes how scenario contracts and evaluation material fit into
the active architecture.

## 2. Scenario Files Are Contracts

Files under `integration/scenarios/` are active scenario-contract assets, not
scratch examples.

They must stay aligned with:

- canonical policy asset names,
- canonical schema asset names,
- canonical MQTT registry names,
- Class 2 clarification topic and schema,
- active safety and authority boundaries,
- active payload and MQTT contracts.

## 3. Current Scenario Families

The scenario set covers:

- Class 1 bounded low-risk assistance,
- Class 0 emergency families E001 through E005,
- Class 2 insufficient-context clarification,
- stale-state fault handling,
- conflicting-candidate fault handling,
- missing-state fault handling.

## 4. Experiment Packages

`common/docs/required_experiments.md` is the experiment baseline manifest. The
active architecture must support these required and recommended packages:

- Package A: policy-routing accuracy and safety,
- Package B: class-wise latency,
- Package C: fault-injection robustness,
- Package D: Class 2 notification payload completeness,
- Package E: doorlock-sensitive actuation validation,
- Package F: grace-period cancellation / false-dispatch suppression,
- Package G: MQTT/payload contract and governance-boundary validation.

The minimum paper-facing result set includes policy-routing/safety results,
class-wise latency, fault-injection results, experimental node composition, and
intent recovery comparison.

## 5. Scenario Data-Flow Expectations

Every active scenario should be traceable through:

1. input source,
2. normalized context or emergency evidence,
3. Policy Router route,
4. validator or clarification behavior,
5. output, deferral, escalation, or dispatch behavior,
6. ACK/audit expectations where relevant,
7. final safe outcome.

## 6. RPi Virtual Node Requirements

RPi virtual nodes may provide controlled experimental sources when physical
ESP32 nodes are unavailable or when larger multi-node simulation is needed.

Scenario and experiment definitions should identify:

- physical versus virtual input origin,
- virtual node type,
- simulated `source_node_id`,
- ingress topic,
- payload family and schema/example reference,
- expected route,
- expected safe outcome,
- audit and result artifact expectations.

RPi virtual node payloads must remain aligned with:

- `common/schemas/context_schema.json`,
- `common/schemas/policy_router_input_schema.json`,
- `common/schemas/clarification_interaction_schema.json` when Class 2 is tested,
- `common/mqtt/topic_registry.json`,
- `common/mqtt/topic_payload_contracts.md`,
- `common/policies/fault_injection_rules.json` when fault injection is tested.

Virtual nodes are not production devices and do not create operational authority.

## 7. Experiment Environment And Monitoring

Each experiment should be represented by an experiment registry entry or
equivalent metadata containing:

- `experiment_id`,
- required operational nodes,
- required RPi virtual nodes,
- required services,
- required topics,
- required assets,
- required runtime conditions,
- required measurement nodes,
- expected result artifacts,
- blocked/degraded conditions.

Preflight readiness should report:

- `READY` when all required dependencies are available,
- `DEGRADED` when optional measurement or non-blocking support is missing,
- `BLOCKED` when required nodes, services, assets, topics, or runtime conditions
  are missing,
- `UNKNOWN` when the environment cannot be trusted yet.

Monitoring/dashboard views should show selected experiment, node status, virtual
node status, measurement readiness, required assets, blocking reasons, start/stop
eligibility, and result artifact availability. The dashboard is visibility and
operator support only; it must not become policy, validator, caregiver approval,
actuator, or doorlock authority.

## 8. Measurement And Result Artifacts

Latency experiments should preserve class-wise separation:

- Class 0 emergency path latency,
- Class 1 validated low-risk action or safe-deferral decision latency,
- Class 2 caregiver notification or clarification handoff latency.

Where practical, timing should use out-of-band measurement support such as STM32
time probes. Measurement nodes are evidence collectors, not operational nodes.

Expected result artifacts may include:

- `summary.json`,
- raw audit log,
- raw timestamp CSV,
- latency CSV,
- latency plot,
- run metadata,
- governance report,
- topic/payload drift report,
- payload validation report.

All result rows should be traceable to deterministic profile IDs or canonical
scenario IDs.

## 9. Class 2 Scenario Requirements

Class 2 scenarios should explicitly state:

- whether clarification is expected,
- the use of `safe_deferral/clarification/interaction`,
- the use of `common/schemas/clarification_interaction_schema.json`,
- allowed transition targets,
- timeout/no-response handling,
- whether caregiver escalation or safe deferral is expected,
- why no autonomous execution occurs until validator/manual approval requirements
  are satisfied.

## 10. Fault Scenario Requirements

Fault scenarios should preserve conservative behavior:

- stale data should not be treated as current consent or reliable state,
- conflicting candidates should not be arbitrarily selected,
- missing required state should not be filled by LLM assumption,
- fault injection remains experiment-side support, not operational authority.

Fault injection profiles should be derived from canonical policy/schema/rules and
MQTT references rather than hardcoded manually.

## 11. Evaluation Boundary

Evaluation, dashboard, measurement, result export, and governance artifacts are
evidence and analysis layers.

They must not become:

- policy authority,
- validator authority,
- caregiver approval authority,
- actuator authority,
- doorlock execution authority.

## 12. Python Code Status

Python implementation and verification code has been removed for the current
cleanup phase. It may be reintroduced after the document, scenario, and asset
contract baseline is stable.

## 13. Source Notes

This active summary consolidates the stable material from:

- `common/docs/archive/architecture_legacy/18_scenario_node_component_mapping.md`
- `common/docs/archive/architecture_legacy/20_scenario_data_flow_matrix.md`
- `common/docs/archive/architecture_legacy/scenario_data_flows/20_00_interface_role_alignment.md`
- `integration/scenarios/README.md`
- `integration/scenarios/scenario_manifest_rules.md`
- `integration/scenarios/scenario_review_guide.md`
- `common/docs/required_experiments.md`
- `integration/measurement/experiment_preflight_readiness_design.md`
- `integration/measurement/class_wise_latency_profiles.md`

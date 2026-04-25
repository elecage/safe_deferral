# SESSION_HANDOFF_2026-04-25_TOPIC_REGISTRY_ROLE_VERIFIER_CLAUDE_PROMPT_TODO.md

Date: 2026-04-25
Scope: Deferred implementation prompt/TODO for MQTT topic registry role verifier
Status: TODO recorded. No verifier code was created in this step.

## 1. Purpose

This addendum records a deferred implementation task for a future Claude Code session.

The task is to implement a static verifier for:

```text
common/mqtt/topic_registry_v1_1_0.json
```

The verifier should check machine-readable publisher/subscriber role metadata introduced in:

```text
common/docs/runtime/SESSION_HANDOFF_2026-04-25_TOPIC_REGISTRY_ROLE_METADATA_V1_1_UPDATE.md
```

Decision:

```text
Do not implement the verifier now.
Record a precise Claude Code prompt/TODO instead.
```

---

## 2. Recommended target file

Recommended verifier path:

```text
common/mqtt/verify_topic_registry_roles.py
```

Reason:

```text
The verification target is the MQTT registry under common/mqtt, not scenario skeletons under integration/scenarios.
```

Optional future integration:

```text
integration/scenarios/run_scenario_verification_suite.py
```

Once the verifier exists, the suite runner may optionally call it before or after the scenario verifiers.

---

## 3. Claude Code prompt

Use the following prompt in a future Claude Code session.

```text
You are working in the safe_deferral repository.

Task:
Implement a static verifier for MQTT topic registry publisher/subscriber role metadata.

Create:
common/mqtt/verify_topic_registry_roles.py

Primary input:
common/mqtt/topic_registry_v1_1_0.json

Reference files:
common/mqtt/publisher_subscriber_matrix_v1_0_0.md
common/docs/architecture/scenario_data_flows/20_00_interface_role_alignment.md
common/docs/runtime/SESSION_HANDOFF_2026-04-25_TOPIC_REGISTRY_ROLE_METADATA_V1_1_UPDATE.md

Requirements:
1. Use only the Python standard library.
2. The script must be runnable from repository root with:
   python common/mqtt/verify_topic_registry_roles.py
3. Exit 0 on success and nonzero on failure.
4. Print a concise OK message on success.
5. Print a clear list of errors on failure.
6. Do not modify JSON files automatically.
7. Do not contact the network.

Validation rules:
1. The registry JSON must parse successfully.
2. registry_version must equal "1.1.0".
3. role_classes must be an object and must include these role class keys:
   - field_operational_publisher
   - mac_mini_runtime_publisher
   - mac_mini_controlled_bridge_publisher
   - controlled_experiment_publisher
   - runtime_subscriber
   - actuator_subscriber
   - observer_subscriber
   - dashboard_visibility_subscriber
   - analysis_subscriber
4. topics must be a non-empty array.
5. Every topic entry must include:
   - topic
   - publishers
   - publisher_roles
   - subscribers
   - subscriber_roles
   - payload_family
   - authority_level
   - allowed_in_operational_runtime
   - allowed_in_experiment_runtime
6. publishers and subscribers must be arrays of strings.
7. publisher_roles and subscriber_roles must be objects.
8. Every role key under publisher_roles and subscriber_roles must exist in role_classes.
9. Every publisher listed under publisher_roles must also appear in the topic's publishers array.
10. Every subscriber listed under subscriber_roles must also appear in the topic's subscribers array.
11. Every publisher in publishers should appear in at least one publisher_roles list.
12. Every subscriber in subscribers should appear in at least one subscriber_roles list.
13. Topic names must be unique.
14. Topic names must start with "safe_deferral/".
15. payload_family must be a non-empty string.
16. authority_level must be a non-empty string.
17. allowed_in_operational_runtime and allowed_in_experiment_runtime must be booleans.
18. If a topic has controlled_experiment_publisher but allowed_in_operational_runtime is true, require at least one non-controlled publisher role or an explicit note explaining controlled-mode separation.
19. safe_deferral/actuation/command must only allow dispatcher-like publishers. It must not allow dashboard, governance, test app, or generic simulation publishers as operational command publishers.
20. safe_deferral/actuation/command must include actuator_subscriber in subscriber_roles.
21. safe_deferral/context/input must include field_operational_publisher entries for:
    - esp32.bounded_input_node
    - esp32.context_node
    - esp32.doorbell_visitor_context_node
22. safe_deferral/context/input must preserve controlled-mode publishers separately:
    - mac_mini.context_aggregator_controlled_bridge
    - rpi.simulation_runtime_controlled_mode
23. safe_deferral/emergency/event must not have LLM, dashboard, governance, or generic test UI publishers.
24. safe_deferral/llm/candidate_action must have authority_level indicating model candidate / not authority.
25. safe_deferral/dashboard/observation, safe_deferral/experiment/progress, and safe_deferral/experiment/result must not be allowed as operational control topics.
26. Notes for doorbell/visitor context must not imply emergency authority or doorlock authority.
27. Notes for dashboard/governance/test roles must not imply direct operational control authority.

Implementation guidance:
- Implement helper functions:
  - load_json(path)
  - require(condition, errors, message)
  - flatten_role_values(role_map)
  - validate_topic(topic_entry, role_classes, errors)
  - validate_special_topic_rules(topic_entry, errors)
- Keep error messages repository-relative and actionable.
- Do not over-engineer; this is a static consistency verifier.

After implementing, run:
python common/mqtt/verify_topic_registry_roles.py

If it passes, optionally update:
integration/scenarios/run_scenario_verification_suite.py

to include:
python common/mqtt/verify_topic_registry_roles.py

Then create a runtime handoff addendum describing what was implemented and update common/docs/runtime/SESSION_HANDOFF.md.
```

---

## 4. Deferred validation checklist

When the future verifier is implemented, confirm it checks:

```text
- registry_version == 1.1.0
- role_classes completeness
- topic uniqueness
- required fields per topic
- publisher_roles ⊆ publishers
- subscriber_roles ⊆ subscribers
- every publisher/subscriber is classified by at least one role
- no unknown role keys
- actuation command publisher restriction
- context/input operational-vs-controlled publisher split
- emergency/event publisher restriction
- dashboard/experiment topics are visibility/experiment artifacts only
- doorbell/visitor context does not imply emergency or doorlock authority
```

---

## 5. Current status

No code was added in this step.

The current authoritative role metadata file remains:

```text
common/mqtt/topic_registry_v1_1_0.json
```

The current human-readable matrix remains:

```text
common/mqtt/publisher_subscriber_matrix_v1_0_0.md
```

The current scenario interface-role companion remains:

```text
common/docs/architecture/scenario_data_flows/20_00_interface_role_alignment.md
```

---

## 6. Recommended next step

Recommended next step:

```text
Proceed with document-level review or continue scenario data-flow refinement.
```

Do not implement `verify_topic_registry_roles.py` until a future coding pass is intentionally started.

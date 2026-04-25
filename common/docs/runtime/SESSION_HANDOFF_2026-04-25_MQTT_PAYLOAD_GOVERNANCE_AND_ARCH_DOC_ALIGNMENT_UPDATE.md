# SESSION_HANDOFF_2026-04-25_MQTT_PAYLOAD_GOVERNANCE_AND_ARCH_DOC_ALIGNMENT_UPDATE.md

## Purpose

This addendum records the latest architecture-document alignment work completed on 2026-04-25.

It covers:

- MQTT topic and payload governance structure,
- `common/mqtt/` and `common/payloads/` scaffolding,
- registry-driven topic/payload management direction,
- dashboard UI versus governance backend separation,
- doorbell / doorlock-sensitive boundary propagation,
- architecture document updates from `04_project_directory_structure.md` through `16_system_architecture_figure.md`,
- prompt updates for future MQTT/payload governance implementation.

If this addendum conflicts with older handoff wording, prefer this addendum for MQTT/payload governance, dashboard governance, interface matrix, and architecture-figure interpretation.

---

## 1. New shared reference directories

Two new shared reference areas were introduced.

### `common/mqtt/`

Purpose:

- MQTT topic namespace management,
- publisher/subscriber matrix management,
- topic-to-payload contract documentation,
- authority-boundary tracking,
- runtime/governance/dashboard implementation guidance.

Created files:

- `common/mqtt/README.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/mqtt/publisher_subscriber_matrix_v1_0_0.md`
- `common/mqtt/topic_payload_contracts_v1_0_0.md`

Interpretation:

- `common/mqtt/` is a communication-contract reference layer.
- It does not override `common/policies/` or `common/schemas/`.
- Topic entries describe communication contracts, not policy authority.
- Dashboard/governance topics must remain non-authoritative.

### `common/payloads/`

Purpose:

- shared payload examples,
- payload templates,
- scenario/test/dashboard reference payloads,
- payload validation support,
- implementation scaffolding.

Created files:

- `common/payloads/README.md`
- `common/payloads/examples/policy_router_input_non_visitor.json`
- `common/payloads/examples/policy_router_input_visitor_doorbell.json`
- `common/payloads/examples/candidate_action_light_on.json`
- `common/payloads/examples/dashboard_observation_doorlock_sensitive.json`
- `common/payloads/templates/scenario_fixture_template.json`

Interpretation:

- `common/payloads/` is an examples/templates reference layer.
- It is not policy truth and does not replace JSON schemas.
- Schema-governed payload sections must validate against the corresponding schema under `common/schemas/`.

---

## 2. Current MQTT topic registry status

`common/mqtt/topic_registry_v1_0_0.json` is currently marked `DRAFT`.

It contains the current first-pass topic families:

1. `safe_deferral/context/input`
2. `safe_deferral/emergency/event`
3. `safe_deferral/llm/candidate_action`
4. `safe_deferral/validator/output`
5. `safe_deferral/deferral/request`
6. `safe_deferral/escalation/class2`
7. `safe_deferral/caregiver/confirmation`
8. `safe_deferral/actuation/command`
9. `safe_deferral/actuation/ack`
10. `safe_deferral/audit/log`
11. `safe_deferral/sim/context`
12. `safe_deferral/fault/injection`
13. `safe_deferral/dashboard/observation`
14. `safe_deferral/experiment/progress`
15. `safe_deferral/experiment/result`

Important next registry work:

- add stable `topic_id` or equivalent topic-key fields before broad app implementation,
- ensure all runtime apps, dashboards, and experiment tools use registry lookup where practical,
- add/validate dashboard/control/preflight/node-health topics only after reviewing relevant documents,
- ensure topic registry, matrix, and interface matrix remain synchronized,
- ensure example payload paths either exist or are explicitly marked as planned/future examples.

---

## 3. MQTT/payload governance dashboard decision

A future topic/payload management GUI was defined as useful and appropriate, with a strict backend/UI separation.

### Required separation

```text
Governance Dashboard UI
        ↓
MQTT / Payload Governance Backend Service
        ↓
Topic Registry Loader / Payload Validator / Role Manager
        ↓
Draft Registry Change / Validation Report
        ↓
Review / Commit Workflow
```

### Dashboard UI responsibilities

- display topic registry,
- show topic details,
- provide create/edit/delete draft forms,
- display publisher/subscriber role assignments,
- display payload family / schema / example links,
- display validation results,
- display doorbell/doorlock boundary warnings,
- display proposed change reports.

### Governance backend responsibilities

- handle topic create/update/delete draft operations,
- manage publisher role assignment,
- manage subscriber role assignment,
- manage payload family linkage,
- manage schema/example path linkage,
- run validation,
- export proposed change reports,
- maintain draft/proposed/committed distinction.

### Non-negotiable prohibitions

Neither UI nor backend may:

- become policy authority,
- become schema authority,
- override the Policy Router,
- override the Deterministic Validator,
- spoof caregiver approval,
- dispatch actuator commands,
- dispatch doorlock commands,
- treat dashboard observation as policy truth,
- silently rewrite frozen policy/schema files.

---

## 4. Doorbell and doorlock boundaries reinforced

The following interpretation remains active and was propagated across documents.

### Doorbell

- `doorbell_detected` belongs in `environmental_context.doorbell_detected`.
- It is required in valid schema-governed context payload examples.
- Non-visitor scenarios should normally set it to `false`.
- Visitor-response scenarios may set it to `true`.
- It is not emergency evidence.
- It does not authorize autonomous doorlock control.

### Doorlock

- Doorlock is implementation-facing and experiment-facing, but not current autonomous Class 1 low-risk execution.
- Do not add `door_unlock` to current Class 1 candidate action semantics.
- Do not add `front_door_lock` as a current autonomous Class 1 target.
- Do not insert doorlock state into current `pure_context_payload.device_states`.
- Doorlock-sensitive outcomes must route to Class 2 escalation or a separately governed manual confirmation path.
- Doorlock-sensitive execution requires caregiver approval, ACK verification, and audit logging.
- Creating or editing a doorlock-related MQTT topic does not create doorlock execution authority.

---

## 5. Architecture documents updated in this pass

### `04_project_directory_structure.md`

Updated to include:

- `common/mqtt/`,
- `common/payloads/`,
- role separation among policies, schemas, MQTT contracts, payload examples,
- RPi dashboard/simulation/result support,
- ESP32 doorbell / visitor-arrival context node,
- MQTT/payload governance dashboard non-authority boundary.

### `05_automation_strategy.md`

Updated to include:

- `common/mqtt/`, `common/payloads/`,
- `make mqtt-check`, `make payload-check`, `make topic-contract-check`,
- `make registry-check`, `make governance-check`, `make governance-dashboard-check`,
- topic/payload hardcoding prohibition,
- RPi dashboard/governance non-authority,
- `doorbell_detected` emergency exception.

### `06_implementation_plan.md`

Updated to include:

- MQTT Topic Registry Loader / Contract Checker,
- Payload Validation Helper,
- RPi Experiment and Monitoring Dashboard,
- MQTT / Payload Governance Inspector or Dashboard,
- Doorbell / Visitor-Arrival Context Node Firmware,
- MQTT / payload acceptance criteria,
- dashboard non-authority boundary,
- doorbell / doorlock-sensitive scenario correctness.

### `07_task_breakdown.md`

Updated to include:

- `common/mqtt/`, `common/payloads/`,
- topic registry and payload examples/templates tasks,
- Policy Router registry/payload assumptions,
- Validator rejection of doorlock as current Class 1 executable,
- RPi dashboard/governance inspector tasks,
- ESP32 doorbell context node tasks,
- MQTT connectivity plus contract consistency checks.

### `08_additional_required_work.md`

Updated to include:

- MQTT/payload reference completeness,
- port/env variables for dashboard/governance/result export,
- module acceptance criteria for registry loader and payload helper,
- test data for doorbell/doorlock-sensitive cases,
- MQTT connectivity/contract/isolation requirements,
- audit traceability for doorbell and doorlock-sensitive outcomes,
- MQTT / Payload Governance Dashboard Requirements section.

### `09_recommended_next_steps.md`

Updated to include:

- `common/mqtt/`, `common/payloads/`,
- active architecture references `16_system_architecture_figure.md` and `17_payload_contract_and_registry.md`,
- hub-side registry loader / payload validation helper,
- ESP32 doorbell node,
- RPi dashboard/governance inspector,
- new section: `Establish MQTT / Payload Governance Before Broad App Implementation`.

### `10_install_script_structure.md`

Updated to include:

- `common/mqtt/`, `common/payloads/` in repository structure,
- install dependency support for registry loading and payload validation,
- RPi dashboard/governance/result-export install role,
- ESP32 doorbell node target,
- install rules prohibiting topic/payload hardcoding and governance authority escalation.

### `11_configuration_script_structure.md`

Updated to include:

- registry/payload path environment variables,
- optional Mac mini `55_deploy_mqtt_payload_references.sh`,
- optional RPi `60_configure_dashboard_runtime_rpi.sh`,
- optional RPi `70_configure_mqtt_payload_governance_rpi.sh`,
- optional RPi `80_configure_result_export_rpi.sh`,
- Mosquitto topic namespace / ACL alignment with registry,
- RPi sync of MQTT/payload references,
- ESP32 doorbell context assumptions.

### Prompt documents

`12_prompts.md` was updated as an index to include:

- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`

New file added:

- `common/docs/architecture/12_prompts_mqtt_payload_governance.md`

It contains prompts for:

- Topic Registry Loader / Contract Checker,
- MQTT / Payload Governance Backend Service,
- MQTT / Payload Governance Dashboard UI,
- Payload Example Manager and Validator,
- Publisher / Subscriber Role Registry Support.

### `13_doorlock_access_control_and_caregiver_escalation.md`

Updated to clarify:

- MQTT/payload governance does not create doorlock authority,
- doorlock-related topics remain communication contracts,
- governance dashboard visibility does not imply authority,
- registry entries do not create autonomous Class 1 door unlock paths,
- governance boundary validation should be part of experiments.

### `14_system_components_outline_v2.md`

Updated to include:

- MQTT / Payload Governance Backend,
- Governance Dashboard UI,
- Mac mini Topic Registry Loader / Contract Checker,
- Mac mini Payload Validation Helper,
- RPi Topic / Payload Contract Validation,
- RPi Payload Example Manager,
- RPi Publisher / Subscriber Role Manager,
- MQTT/payload governance flow,
- optional paper-figure inset for governance components.

### `15_interface_matrix.md`

Significantly updated and now MQTT-aware.

Key changes:

- added `MQTT Topic / Interface` column,
- added `Payload Family` column,
- reflected all 15 current draft topics from `topic_registry_v1_0_0.json`,
- added MQTT Topic Contract Coverage table,
- added Governance Support interfaces GV-1 through GV-7,
- added prohibited interfaces for governance/dashboard/doorbell/doorlock risks,
- added condensed MQTT/governance interface groups.

### `16_system_architecture_figure.md`

Updated without changing the SVG image.

Key changes:

- clarified that the current SVG is the active Mac-mini-centered operational figure,
- documented that RPi support-layer MQTT connections and governance flows are not yet fully drawn,
- added `Figure elements not yet fully drawn` section,
- added Mac mini registry loader / payload validation helper,
- added RPi governance backend/UI/payload manager/role manager descriptions,
- linked to `15_interface_matrix.md` and `common/mqtt/` references,
- updated caption and interpretation notes.

Important: the figure file itself was not modified. Future figure revision should visually add RPi support-layer MQTT connections and governance flows.

---

## 6. Important commit references from this pass

Notable commits made during this work include:

- `12c813d0628bd1464026b26171bb94999fb8cc12` — project directory structure MQTT/payload directories
- `26172f44a3272c414f956e397742eb383cf5ca00` — automation strategy MQTT/payload governance
- `77ea78a65429af1a04edf94ee69d6fa154ba63b9` — implementation plan MQTT/payload governance
- `5c3f77c8390d5509de0a9aff8edc5bf286259894` — task breakdown MQTT/payload governance
- `127eb76b298ae1d21c012d210f01e3781ae1f474` — additional required work MQTT/payload governance
- `9a9ae9d47db266cd059d5db2540d1957f5f324ff` — recommended next steps MQTT/payload governance
- `655f482de93e094183be219a90850ba75c8d014b` — install script structure MQTT/payload governance
- `7fb3bd102b6dd3e73602810af5e7ad19a2ff8034` — configuration script structure MQTT/payload governance
- `e42fab4f11eff5efecb416d2d3c5d2258df54bf7` — new MQTT/payload governance prompt set
- `4c3e90795e55abeb4596d08b077f76cc3a13e7c3` — prompt index update
- `0f309e8d4cd6e797354f3c9c7f70c9dc60ad0ec2` — doorlock governance boundary update
- `a1cb3ac3949d7942f3b5713fd232ef8158e59335` — system components governance update
- `4c119ed43f2ae1e78ad5aa0ab8a9e34ff941fbb4` — MQTT-aware interface matrix
- `031ff191e6f1d50b6d475894cb908b3818ce1dfe` — system architecture figure explanation update

---

## 7. Current highest-priority next work

### A. Finish document sweep

Continue reviewing remaining active architecture / paper / experiment docs for consistency with:

- `common/mqtt/topic_registry_v1_0_0.json`,
- `common/docs/architecture/15_interface_matrix.md`,
- `common/docs/architecture/16_system_architecture_figure.md`,
- `common/docs/architecture/17_payload_contract_and_registry.md`,
- `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`.

### B. Do not freeze topic registry yet

The current topic registry is still DRAFT.

Before freezing:

1. finish reviewing remaining docs,
2. collect all implied topics,
3. add stable `topic_id` fields,
4. check schema/example paths,
5. align publisher/subscriber role names,
6. decide which dashboard/control/preflight/node-health topics are needed,
7. update `publisher_subscriber_matrix_v1_0_0.md` and `topic_payload_contracts_v1_0_0.md` together.

### C. Future figure revision

The current SVG does not yet fully show:

- Raspberry Pi support-layer MQTT connections,
- dashboard observation topic flows,
- experiment progress/result topic flows,
- MQTT/payload governance backend,
- governance dashboard UI,
- publisher/subscriber role manager,
- payload example manager,
- topic registry CRUD/review workflow.

The explanatory documents now reflect these, but the figure should be updated later.

### D. Future implementation direction

When apps are implemented:

- do not hardcode MQTT topic strings where registry lookup is practical,
- load topics/schema/example references from registry/configuration,
- keep dashboard UI separate from governance backend,
- keep registry edits as draft/proposed changes until reviewed,
- prevent governance tooling from directly publishing operational control topics.

---

## 8. Current non-negotiable reminders

1. Mac mini remains the operational hub.
2. RPi remains dashboard/simulation/orchestration/fault/result/governance support only.
3. ESP32 remains bounded physical node layer.
4. `common/policies/` and `common/schemas/` remain authority.
5. `common/mqtt/` and `common/payloads/` are reference layers.
6. `doorbell_detected` is required visitor-response context, not emergency or unlock authorization.
7. Doorlock is not current autonomous Class 1 execution.
8. Doorlock state must not be placed inside current `pure_context_payload.device_states`.
9. Dashboard observation is visibility only, not policy truth.
10. Audit is evidence/traceability, not policy truth.
11. Governance dashboard UI cannot directly write registry files or publish control topics.
12. Governance backend cannot silently modify policies/schemas or dispatch actuator/doorlock commands.
13. Topic/payload registry edits cannot create doorlock execution authority.
14. Current architecture figure text is ahead of the SVG for RPi/governance flows; future figure revision is required.

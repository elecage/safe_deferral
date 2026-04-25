# SESSION_HANDOFF_2026-04-25_ARCHITECTURE_DOC_CONSOLIDATION_AND_PAYLOAD_REGISTRY_UPDATE.md

## Purpose

This handoff records the architecture-document consolidation, system-layout archive cleanup, and payload-registry renumbering work completed after the doorbell/visitor-response context alignment.

The main goals of this pass were:

1. reduce architecture-figure document fragmentation,
2. preserve historical layout-step notes without keeping them in the active architecture sequence,
3. establish a single current system architecture figure interpretation document,
4. introduce a payload contract / registry document,
5. renumber the payload registry naturally after the new architecture figure document,
6. update known references from the old payload-registry path to the new one.

---

## 1. New active architecture documents

### 1.1 Consolidated system architecture figure document

New current document:

- `common/docs/architecture/16_system_architecture_figure.md`

Commit:

- `5dfe062632da83b40765b3ff933ce35fa0439955`

Purpose:

- Consolidates architecture-figure interpretation that had previously been spread across the 16~24 figure-layout notes.
- Acts as the current active reference for the final paper-oriented architecture figure.
- Includes Mac mini / Raspberry Pi 5 / ESP32 / optional measurement-node role separation.
- Includes operational closed-loop interpretation.
- Includes LLM vs deterministic policy/validator authority boundary.
- Includes safe deferral, caregiver-mediated sensitive path, ACK/audit closure.
- Includes `doorbell_detected` visitor-response context interpretation.
- Includes doorlock-sensitive boundary.
- Includes payload-boundary interpretation.
- Includes suggested paper figure captions.

Current interpretation:

- ESP32 nodes provide bounded physical interaction and sensing.
- Mac mini is the safety-critical operational edge hub.
- Local LLM assists intent interpretation but does not authorize execution.
- Deterministic policy and validation control admissibility.
- Safe deferral and caregiver escalation prevent unsafe autonomous action.
- Doorbell context supports visitor-response interpretation but does not authorize doorlock control.
- Doorlock-sensitive execution remains caregiver-mediated or manually governed.
- Raspberry Pi 5 provides experiment/dashboard/simulation/fault-injection support without becoming authority.
- ACK and audit closure complete the safety argument.

### 1.2 Payload contract and registry document

New current document:

- `common/docs/architecture/17_payload_contract_and_registry.md`

Original draft file:

- `common/docs/architecture/25_payload_contract_and_registry.md`

Initial draft commit:

- `49d9a492f694a42ff42d1804e638491076804b9e`

Renumber/delete old-path commit:

- `1d3bb9cc8c105ce31294e8be60dad5e9fdc67aa9`

Purpose:

- Defines payload taxonomy, ownership boundary, schema coverage, and implementation guidance.
- Prevents drift between policies, schemas, runtime payloads, scenario fixtures, dashboard/test-app payloads, audit artifacts, and paper experiment descriptions.

Payload authority levels introduced:

1. Schema-governed payloads
2. Policy/rules-governed payloads
3. Experiment/runtime artifact payloads

Key payload families covered:

- Policy Router input payload
- routing metadata
- pure context payload
- trigger event
- environmental context
- device states
- LLM candidate action
- validator output
- Class 2 notification payload
- manual confirmation payload/state
- actuation ACK payload/state
- audit event payload
- fault injection payload/profile
- scenario fixture payload
- dashboard observation payload
- experiment annotation payload
- result export payload

Important rules captured:

1. `routing_metadata` is not LLM context.
2. `pure_context_payload` must conform to `context_schema_v1_0_0_FROZEN.json`.
3. `environmental_context.doorbell_detected` is required.
4. `doorbell_detected` is visitor-response context, not doorlock authorization.
5. `doorbell_detected` is not a current emergency trigger.
6. Doorlock state is not currently part of `device_states`.
7. Manual approval state is not `pure_context_payload`.
8. ACK state is not `pure_context_payload`.
9. Dashboard observation state is not policy truth.
10. Scenario fixture metadata is not policy truth.
11. Class 1 executable payload must stay within the frozen low-risk catalog and validator schema.
12. Sensitive actuation must route through Class 2 escalation or separately governed manual confirmation with ACK and audit.
13. Future authoritative payload expansion requires coordinated schema/policy/doc/handoff updates.

---

## 2. Archived system-layout figure notes

A new archive directory was created:

- `common/docs/archive/system_layout_figure_notes/`

The following historical layout-step documents were moved out of active `common/docs/architecture/` and archived there.

### 2.1 Archived architecture figure notes

Archived files:

- `common/docs/archive/system_layout_figure_notes/16_system_block_layout_spacious.md`
- `common/docs/archive/system_layout_figure_notes/17_system_layout_step2_user_input_plus_context.md`
- `common/docs/archive/system_layout_figure_notes/18_system_layout_step4_with_llm_reasoning.md`
- `common/docs/archive/system_layout_figure_notes/19_system_layout_step5_policy_branching.md`
- `common/docs/archive/system_layout_figure_notes/20_system_layout_step6_execution_completion.md`
- `common/docs/archive/system_layout_figure_notes/21_system_layout_step7_tts_return_paths.md`
- `common/docs/archive/system_layout_figure_notes/22_system_layout_step8_ack_audit_paths.md`
- `common/docs/archive/system_layout_figure_notes/23_system_layout_final_macmini_only_lshape.md`
- `common/docs/archive/system_layout_figure_notes/24_final_paper_architecture_figure.md`

Original active files removed from `common/docs/architecture/`:

- `common/docs/architecture/16_system_block_layout_spacious.md`
- `common/docs/architecture/17_system_layout_step2_user_input_plus_context.md`
- `common/docs/architecture/18_system_layout_step4_with_llm_reasoning.md`
- `common/docs/architecture/19_system_layout_step5_policy_branching.md`
- `common/docs/architecture/20_system_layout_step6_execution_completion.md`
- `common/docs/architecture/21_system_layout_step7_tts_return_paths.md`
- `common/docs/architecture/22_system_layout_step8_ack_audit_paths.md`
- `common/docs/architecture/23_system_layout_final_macmini_only_lshape.md`
- `common/docs/architecture/24_final_paper_architecture_figure.md`

Representative archive/delete commits:

- Archive 16: `7e49a83db2839d40c3fe1b35ae5bb4f0531be3e0`
- Archive 18: `fb25a3e081b903ec2c03a43daac0c86a39af66bd`
- Archive 21: `ab7a8c5a6035ee658d6d5ad6c5d32d2c569c29c1`
- Archive paper contribution note: `8ffb364babde54e6ab44d07be2050b6c8926c1c0`
- Delete old 16: `cd624a0edc3f165cf3147b0fd522e2b991e81b39`
- Delete old 17: `67dec130627cddffb06da1111e1ae5aa73396ce7`
- Delete old 18: `76598b67a59eba5bac95c4edaa2c3bc6055d77b6`
- Delete old 19: `2a7b4be97de649a6e1d20d237b63ca50cffe047a`
- Delete old 20: `84b70a7ab48fe0859e270c8d0b66bf77ba28b4c3`
- Delete old 21: `0a25df3f96fb14bd786c9cf675fd373f89b7a16a`
- Delete old 24: `94d5c9572e454f42f3bc083f30417d2987c96f3e`
- Archive 23: `a23d20001642fbe4e1a9e5c365ecd100afa48c14`
- Delete old 23: `9475f2259cf075725ea8e03052057f43e1519abb`

Note:

- The tool response for deletion of old 22 was omitted during the session, but a retry confirmed `common/docs/architecture/22_system_layout_step8_ack_audit_paths.md` returned `Not Found`, so the active-path deletion succeeded.
- The archive copy for 22 was also created under `common/docs/archive/system_layout_figure_notes/22_system_layout_step8_ack_audit_paths.md`.

### 2.2 Archived paper contribution note

The following file was also moved into the same archive folder during this cleanup pass:

- from: `common/docs/paper/01_paper_contributions.md`
- to: `common/docs/archive/system_layout_figure_notes/01_paper_contributions.md`

Delete old active paper note commit:

- `434c4904f4be66be3e0dac218cd69a6f9c352325`

Important implication:

- Older references to `common/docs/paper/01_paper_contributions.md` may now be stale.
- If paper contribution positioning is still needed as an active document, either restore a new current paper contribution file or create a forwarding/index document under `common/docs/paper/`.
- Do not assume the archived copy is the current authoritative paper-positioning file without an explicit decision.

---

## 3. Reference updates completed

### 3.1 Payload registry path update

Old path:

- `common/docs/architecture/25_payload_contract_and_registry.md`

New path:

- `common/docs/architecture/17_payload_contract_and_registry.md`

Updated known references:

1. `common/docs/architecture/16_system_architecture_figure.md`
   - commit: `1725d15676e6018fca8663efd9020c918810c71b`
2. `common/docs/archive/system_layout_figure_notes/24_final_paper_architecture_figure.md`
   - commit: `98cdac4e37105573009b0d991694b12369fd8bdc`

GitHub search did not return additional `25_payload_contract_and_registry` references, but search reliability in this session was inconsistent. Future local grep is recommended.

Recommended local check:

```bash
grep -R "25_payload_contract_and_registry" -n .
grep -R "24_final_paper_architecture_figure" -n common docs README.md CLAUDE.md || true
grep -R "01_paper_contributions" -n .
```

---

## 4. Active architecture sequence after cleanup

The active architecture sequence should now treat these as current key references:

- `common/docs/architecture/01_installation_target_classification.md`
- `common/docs/architecture/02_mac_mini_build_sequence.md`
- `common/docs/architecture/03_deployment_structure.md`
- `common/docs/architecture/04_project_directory_structure.md`
- `common/docs/architecture/05_automation_strategy.md`
- `common/docs/architecture/06_implementation_plan.md`
- `common/docs/architecture/07_task_breakdown.md`
- `common/docs/architecture/08_additional_required_work.md`
- `common/docs/architecture/09_recommended_next_steps.md`
- `common/docs/architecture/10_install_script_structure.md`
- `common/docs/architecture/11_configuration_script_structure.md`
- `common/docs/architecture/12_prompts.md`
- `common/docs/architecture/12_prompts_core_system.md`
- `common/docs/architecture/12_prompts_nodes_and_evaluation.md`
- `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`
- `common/docs/architecture/14_system_components_outline_v2.md`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`

Historical layout-step notes now live under:

- `common/docs/archive/system_layout_figure_notes/`

---

## 5. Important consistency risks introduced by this cleanup

The cleanup intentionally moved files, so some existing docs may still point to old paths.

Known likely stale references:

- `common/docs/architecture/24_final_paper_architecture_figure.md`
- `common/docs/architecture/25_payload_contract_and_registry.md`
- `common/docs/paper/01_paper_contributions.md`
- old active layout-step notes from 16~23

Files likely requiring follow-up reference updates:

- `README.md`
- `CLAUDE.md`
- `common/docs/runtime/SESSION_HANDOFF.md`
- older session handoff addenda
- `common/docs/required_experiments.md`
- `common/docs/architecture/12_prompts*.md`
- integration/scenario docs
- rpi/mac_mini/esp32 README files

Recommended approach:

1. Do not rewrite all historical handoff addenda.
2. Update active guidance files first:
   - `README.md`
   - `CLAUDE.md`
   - `common/docs/runtime/SESSION_HANDOFF.md`
   - `common/docs/required_experiments.md`
3. Then continue architecture-doc review from `03_deployment_structure.md` onward using `17_payload_contract_and_registry.md` as the payload boundary reference.

---

## 6. Current non-negotiable interpretation retained

The cleanup did not change the system interpretation.

The current interpretation remains:

1. Mac mini = safety-critical operational edge hub.
2. Raspberry Pi 5 = experiment/dashboard/orchestration/simulation/fault-injection/result-artifact support host.
3. ESP32 = bounded physical node layer.
4. Optional STM32 or equivalent node = out-of-band measurement only.
5. Class 1 autonomous low-risk execution remains limited to frozen light-control catalog.
6. `environmental_context.doorbell_detected` is required.
7. `doorbell_detected` is visitor-response context, not doorlock authorization.
8. `doorbell_detected` is not a current emergency trigger.
9. Doorlock state is not part of current `context_schema.device_states`.
10. Doorlock-sensitive action must route through Class 2 escalation or a separately governed manual confirmation path with approval, ACK, and audit.
11. Dashboard observation, scenario fixture metadata, experiment annotation, manual approval state, and ACK state are not policy truth.

---

## 7. Recommended next steps

### 7.1 Immediate sanity checks

Run local grep or reliable repository search for stale paths:

```bash
grep -R "24_final_paper_architecture_figure" -n .
grep -R "25_payload_contract_and_registry" -n .
grep -R "common/docs/paper/01_paper_contributions.md" -n .
grep -R "16_system_block_layout_spacious\|17_system_layout_step2\|18_system_layout_step4\|19_system_layout_step5\|20_system_layout_step6\|21_system_layout_step7\|22_system_layout_step8\|23_system_layout_final" -n common README.md CLAUDE.md
```

### 7.2 Update active references

Update active docs to point to:

- `common/docs/architecture/16_system_architecture_figure.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/docs/archive/system_layout_figure_notes/01_paper_contributions.md` only if the archived contribution note remains the intended reference

If paper contribution guidance should remain active, create a new active document such as:

- `common/docs/paper/01_paper_contributions.md`

as an index/forwarder or rewritten current paper-positioning document.

### 7.3 Continue payload-boundary review

Continue document review using:

- `common/docs/architecture/17_payload_contract_and_registry.md`

Next review targets:

1. `common/docs/architecture/03_deployment_structure.md`
2. `common/docs/architecture/04_project_directory_structure.md`
3. `common/docs/architecture/05_automation_strategy.md`
4. `common/docs/architecture/06_implementation_plan.md`
5. `common/docs/architecture/07_task_breakdown.md`
6. `common/docs/architecture/08_additional_required_work.md`
7. `common/docs/architecture/10_install_script_structure.md`
8. `common/docs/architecture/11_configuration_script_structure.md`
9. `common/docs/architecture/12_prompts*.md`
10. `common/docs/required_experiments.md`

---

## 8. Summary

This pass created the new active architecture figure document and payload registry sequence:

- `16_system_architecture_figure.md`
- `17_payload_contract_and_registry.md`

It moved historical layout-step and figure-note documents to:

- `common/docs/archive/system_layout_figure_notes/`

It removed the old active 16~24 layout-step clutter from the architecture directory.

The next important task is to update all active references so that future agents read the new active 16/17 documents rather than old archived or deleted paths.

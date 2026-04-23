# SESSION_HANDOFF.md

## 1. Project Identity

- **Project name:** safe_deferral
- **Primary objective:**  
  Build a policy-first, safety-oriented edge smart-home prototype for assistive/safe interaction, where deterministic routing and validation remain authoritative and the LLM is restricted to bounded low-risk assistance only.
- **Current baseline decision:**  
  Continue with **Llama 3.1** as the primary local LLM baseline for the project.
- **Gemma status:**  
  Gemma 4 is recognized as a possible future comparison candidate, but **it is not the current primary model**. Any migration should happen only after explicit A/B evaluation.
- **Current canonical project term:**  
  **context-integrity-based safe deferral stage**

---

## 2. Canonical Frozen Baseline

These assets are treated as the current authoritative frozen baseline unless explicitly superseded and reviewed.

### Policies
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`

### Optional / version-sensitive companion policy asset
- `common/policies/output_profile_v1_1_0.json`

### Schemas
- `common/schemas/context_schema_v1_0_0_FROZEN.json`
- `common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
- `common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
- `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

### Terminology
- `common/terminology/TERM_FREEZE_CONTEXT_INTEGRITY_SAFE_DEFERRAL_STAGE.md`

---

## 3. Canonical Architectural Interpretation

### Role separation
- `mac_mini/` = operational hub
- `rpi/` = simulation / fault injection / closed-loop evaluation
- `esp32/` = bounded physical node layer
- `integration/measurement/` = optional out-of-band timing / latency evaluation support

### LLM boundary
- The LLM is **not** the autonomous execution authority.
- The LLM is only used in the **Class 1 bounded low-risk assistance path**.
- Deterministic routing and deterministic validation remain authoritative.
- When ambiguity remains unresolved, the system must prefer:
  - **SAFE_DEFERRAL**, or
  - **CLASS_2 escalation**
  rather than unsafe autonomous actuation.

### Deployment-local boundary
- `.env`, secrets, host paths, runtime copies, synchronized copies, and machine-local configuration are **deployment-local**.
- They must **not** redefine canonical frozen policy or schema truth.

### Authority hierarchy
- `policy_table_v1_1_2_FROZEN.json` = routing and safety interpretation authority
- `low_risk_actions_v1_1_0_FROZEN.json` = authoritative low-risk action catalog
- `class_2_notification_payload_schema_v1_0_0_FROZEN.json` = authoritative Class 2 payload contract
- `output_profile_v1_1_0.json` = companion output guidance asset, not canonical policy/schema authority

### Scope distinction that must be preserved
- **implementation-facing device scope** and
- **authoritative autonomous low-risk actuation scope**

must not be conflated.

Current interpretation:
- current implementation-facing scope includes lighting paths and a doorlock representative interface path
- current authoritative autonomous Class 1 low-risk scope remains the frozen low-risk catalog unless that catalog is explicitly updated

---

## 4. Canonical Emergency Family

The current canonical emergency trigger family is defined in `policy_table_v1_1_2_FROZEN.json`.

- `E001` = high temperature threshold crossing
- `E002` = emergency triple-hit bounded input
- `E003` = smoke detected state trigger
- `E004` = gas detected state trigger
- `E005` = fall detected event trigger

All of the following must remain aligned with this trigger family:
- policy routing
- virtual emergency simulation
- fault injection
- closed-loop verification
- physical sensing path interpretation
- test scenario expectations
- required experiments mapping

---

## 5. Current System Decisions

### LLM runtime choice
- **Primary LLM:** Llama 3.1
- **Reason for current choice:**  
  Lower migration risk, better continuity with current architecture, and sufficient capability for bounded Class 1 assistance in the current prototype phase.

### Gemma decision
- Gemma 4 was discussed and considered.
- Current decision: **do not switch now**.
- Recommended future approach: evaluate Gemma 4 only through explicit A/B benchmarking rather than immediate replacement.

### Safety decision model
- Policy Router decides route class.
- Deterministic Validator decides bounded admissibility.
- Context-integrity-based safe deferral stage handles bounded clarification.
- Audit logging remains single-writer.
- Caregiver escalation remains bounded and schema-aligned.

### Current scope decision that must remain explicit
- doorlock is part of the **current implementation-facing scope**
- doorlock is **not automatically equivalent** to the current authoritative autonomous Class 1 low-risk action catalog
- any future document/code that treats doorlock as authoritative autonomous low-risk actuation must first be reconciled with the frozen low-risk catalog and related experiment docs

---

## 6. Recent Important Repository Cleanup

The following obsolete / legacy assets were intentionally removed and should **not** be reintroduced casually.

### Deleted legacy policy assets
- `common/policies/LOW_RISK_ACTIONS_FREEZE_MANIFEST.md`
- `common/policies/low_risk_actions_v1_0_0_FROZEN.json`
- `common/policies/policy_table_v1_2_0_FROZEN.json`
- `common/policies/output_profile_v1_0_0.json`

### Deleted legacy / manifest schema assets
- `common/schemas/CONTEXT_SCHEMA_FREEZE_MANIFEST.md`
- `common/schemas/VALIDATOR_OUTPUT_SCHEMA_FREEZE_MANIFEST.md`
- `common/schemas/validator_output_schema_v1_0_0_FROZEN.json`

### Why they were removed
- To reduce ambiguity and drift
- To keep only the current canonical baseline plus the current optional companion output profile
- To prevent future prompts, scripts, or docs from referencing superseded versions

---

## 7. Architecture and Core Documents Already Aligned

The following docs were reviewed and updated to match the current canonical baseline and project interpretation.

### Architecture docs
- `common/docs/architecture/04_project_directory_structure.md`
- `common/docs/architecture/05_automation_strategy.md`
- `common/docs/architecture/06_implementation_plan.md`
- `common/docs/architecture/07_task_breakdown.md`
- `common/docs/architecture/08_additional_required_work.md`
- `common/docs/architecture/09_recommended_next_steps.md`
- `common/docs/architecture/10_install_script_structure.md`
- `common/docs/architecture/11_configuration_script_structure.md`
- `common/docs/architecture/12_prompts.md`

### Experiment / runtime / layer docs
- `common/docs/required_experiments.md`
- `common/docs/runtime/SESSION_HANDOFF.md`
- `mac_mini/docs/README.md`
- `rpi/docs/README.md`
- `esp32/docs/README.md`
- `integration/README.md`
- `integration/requirements.md`
- `integration/scenarios/scenario_manifest_rules.md`
- `integration/scenarios/scenario_review_guide.md`
- `integration/measurement/class_wise_latency_profiles.md`

### Alignment themes already applied
- canonical baseline version cleanup
- optional / version-sensitive companion asset handling for output profiles
- deployment-local separation
- `E001`~`E005` alignment
- current / optional / planned scope distinction for ESP32-related targets
- canonical consistency check expectations
- prompt anti-drift updates
- deterministic fault profile mapping alignment in `required_experiments.md`
- Mac mini / RPi / ESP32 install-configure-verify flow documentation
- integration scenario layer grounding in actual accessibility / daily-life use context from the root README
- explicit distinction between current implementation-facing scope and authoritative autonomous low-risk scope

---

## 8. Recent Structured Update Bundles Completed

### Bundle 1 completed
- terminology cleanup from legacy `icr` naming toward canonical safe-deferral terminology
- Class 2 payload contract cleanup
- policy table / notification schema / output profile alignment

### Bundle 2 completed
- `fault_injection_rules_v1_4_0_FROZEN.json` updated with `E002` deterministic emergency profile
- conflict profile operationalized and reproducibility notes added
- randomized stress profile labeling clarified
- `common/docs/required_experiments.md` updated to match deterministic emergency profile numbering and `E001`~`E005` mapping

### Bundle 3 completed
- `low_risk_actions_v1_1_0_FROZEN.json` strengthened as authoritative low-risk catalog
- `policy_table_v1_1_2_FROZEN.json` clarified as routing/safety interpretation layer with summarized Class 1 taxonomy
- `output_profile_v1_1_0.json` clarified as companion asset with bounded output guidance notes

### Mac mini runtime alignment completed
- `install/`, `configure/`, `templates/`, and `verify/` scripts were reviewed and largely aligned with the current canonical baseline
- Compose workspace was standardized around `~/smarthome_workspace/docker`
- Runtime asset deployment was updated to use current canonical filenames and paths
- Verify scripts were updated to reflect the current runtime asset set, current core Docker services, and current SQLite schema expectations
- `mac_mini/docs/README.md` was expanded into a step-by-step Korean operational guide with runnable commands for install, configure, and verify phases

### Raspberry Pi runtime/documentation alignment completed
- `rpi/scripts/install/`, `configure/`, and `verify/` were reviewed and aligned around the current canonical asset set and evaluation-only boundary
- `requirements-rpi.txt` was created and tied to the RPi experiment-side Python environment
- `rpi/docs/README.md` was expanded into a Korean step-by-step guide covering install, configure, verify, runtime role boundary, and success criteria

### ESP32 cross-platform bring-up scaffolding completed
- cross-platform install scaffolding was created for macOS / Linux / Windows under `esp32/scripts/install/`
- configure scaffolding was created for POSIX and Windows under `esp32/scripts/configure/`
- verify scaffolding was created for POSIX and Windows under `esp32/scripts/verify/`
- `esp32/docs/README.md` was expanded to explain actual execution order and sample-build success as the current completion criterion
- `common/docs/architecture/12_prompts.md` was expanded with Prompt 19~26 for minimal template and node-specific firmware generation

### Integration layer scaffolding completed
- `integration/` now exists as an explicit cross-device validation layer with root README and requirements docs
- `integration/tests/`, `integration/tests/data/`, `integration/scenarios/`, and `integration/measurement/` now contain starter README/docs/assets
- integration fixture samples, expected outcome fixtures, scenario skeletons, runner skeleton, comparator skeleton, scenario manifest rules, scenario review guide, and class-wise latency profile docs were added
- scenario layer was aligned with `required_experiments.md`, current implemented scope, and canonical emergency family `E001`~`E005`

---

## 9. Current Mac mini Runtime Interpretation

### Workspace layout
The current Mac mini scripts assume the following runtime layout:
- workspace root: `~/smarthome_workspace`
- compose root: `~/smarthome_workspace/docker`
- app runtime assets:
  - `~/smarthome_workspace/docker/volumes/app/config/policies`
  - `~/smarthome_workspace/docker/volumes/app/config/schemas`
- database:
  - `~/smarthome_workspace/db/audit_log.db`
- Python/runtime env:
  - `~/smarthome_workspace/.env`

### Current Mac mini install flow
- `mac_mini/scripts/install/00_preflight.sh`
- `mac_mini/scripts/install/10_install_homebrew_deps.sh`
- `mac_mini/scripts/install/20_install_docker_runtime_mac.sh`
- `mac_mini/scripts/install/21_prepare_compose_stack_mac.sh`
- `mac_mini/scripts/install/30_setup_python_venv_mac.sh`

### Current Mac mini configure flow
- `mac_mini/scripts/configure/70_write_env_files.sh`
- `mac_mini/scripts/configure/50_deploy_policy_files.sh`
- `mac_mini/scripts/configure/40_configure_sqlite.sh`
- `mac_mini/scripts/configure/20_configure_mosquitto.sh`
- `mac_mini/scripts/configure/10_configure_home_assistant.sh`
- `mac_mini/scripts/configure/30_configure_ollama.sh`
- `mac_mini/scripts/configure/60_configure_notifications.sh`

### Current Mac mini verify flow
- `mac_mini/scripts/verify/10_verify_docker_services.sh`
- `mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh`
- `mac_mini/scripts/verify/30_verify_ollama_inference.sh`
- `mac_mini/scripts/verify/40_verify_sqlite.sh`
- `mac_mini/scripts/verify/50_verify_env_and_assets.sh`
- `mac_mini/scripts/verify/60_verify_notifications.sh`
- `mac_mini/scripts/verify/80_verify_services.sh`

### Current Mac mini status
- install/configure/template/verify scaffolding is now much closer to the canonical baseline
- `mac_mini/code/` is still largely unimplemented and remains the major next implementation area
- `edge_controller_app` is represented in compose/runtime structure, but the actual code path still needs implementation

---

## 10. Non-Negotiable Rules for Future Sessions

Any future assistant continuing this project should follow these rules.

1. **Do not invent policy semantics.**  
   Thresholds, routes, triggers, payload requirements, and constraints must come from frozen assets.

2. **Do not let deployment-local files override canonical truth.**  
   `.env`, runtime copies, and synced copies are operational aids, not policy authority.

3. **Do not blur device roles.**  
   Raspberry Pi must not become the Mac mini operational hub.  
   Timing/measurement support must not become part of the operational control plane.

4. **Do not reintroduce deleted legacy assets casually.**  
   If a deleted file is ever restored, it must be justified explicitly and reviewed for drift risk.

5. **Do not expand LLM authority.**  
   The LLM remains bounded to Class 1 assistance and must not become direct autonomous control logic.

6. **Prefer safe deferral over unsafe autonomous actuation.**

7. **Preserve cross-document consistency.**  
   Before changing one architecture file, check whether the same concept appears in the other aligned docs.

8. **Preserve authority hierarchy.**  
   Do not let policy table summaries, output profiles, or docs override the authoritative low-risk catalog or canonical notification schema.

9. **Preserve runtime path consistency.**  
   New install/configure/verify changes should not reintroduce older path layouts when a newer layer has already been standardized.

10. **Preserve current implemented scope vs extended scope distinction.**  
    In particular, do not quietly expand autonomous low-risk actuation beyond the current authoritative frozen low-risk catalog without updating the canonical baseline and required experiments docs.

11. **Do not let implementation-facing doorlock scope silently become authoritative autonomous low-risk policy scope.**

12. **Do not let integration scenario assets become policy truth.**  
    Scenarios, fixtures, runner outputs, and review guides are evaluation assets only.

---

## 11. Known Risks / Drift Risks

### A. Legacy file name reintroduction
Old names such as:
- `policy_table_v1_2_0_FROZEN.json`
- `low_risk_actions_v1_0_0_FROZEN.json`
- `output_profile_v1_0_0.json`
- `validator_output_schema_v1_0_0_FROZEN.json`

may accidentally reappear in prompts, scripts, or docs if a future session relies on stale context.

### B. Terminology drift
Deprecated labels such as:
- `iCR`
- `iCR Handler`
- `iCR mapping`

should not be used in new architecture-facing or implementation-facing outputs, except where legacy/transitional asset references must be acknowledged.

### C. Scope drift in ESP32 references
ESP32 targets must continue to respect:
- **current implementation-facing** = button, lighting, representative sensing, doorlock representative interface path
- **optional experimental** = gas, fire, fall
- **planned extension** = warning interface and other future expansion paths

### D. Notification payload drift
Class 2 outbound escalation must stay aligned with:
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

### E. Consistency verification drift
Future work must preserve:
- policy/schema/rules consistency checking
- trigger-family alignment for `E001`~`E005`
- deterministic fault profile mapping consistency in `required_experiments.md`
- runtime asset verification alignment with current canonical filenames
- distinction between implementation-facing doorlock scope and authoritative low-risk catalog scope

### F. Mac mini compose/runtime drift
The Mac mini scripts were recently aligned, but future changes could still reintroduce mismatch across:
- compose template service names
- env variable naming
- runtime asset mount paths
- verify step expectations

### G. Integration scenario drift
Scenario fixtures and review guides were intentionally grounded in actual accessibility use context from the root README.  
Future edits must keep that connection, while still preserving the rule that scenarios do not redefine canonical policy truth.

### H. ESP32 bring-up vs firmware confusion
The ESP32 cross-platform install/configure/verify layer now exists.  
Future sessions should not confuse this with completed real node firmware implementation.

---

## 12. Recommended Next Actions

These are the recommended next steps after this handoff point.

1. Begin implementation-facing work against the stabilized baseline.
2. Verify that no scripts, prompts, or code still reference deleted legacy policy/schema assets.
3. Keep Llama 3.1 as the primary baseline during implementation and early evaluation.
4. Start defining and implementing the actual `mac_mini/code/` services, especially the policy router, deterministic validator, safe deferral handler, audit logger, and notification backend.
5. Add dedicated payload fixtures for `E002`~`E005` instead of reusing placeholder emergency fixtures in the integration scenario layer.
6. Connect the integration runner and expected outcome comparator through an adapter, then extend toward MQTT publish / audit observe execution.
7. When ESP32 node firmware generation begins, use the prompt set in `common/docs/architecture/12_prompts.md` and keep it aligned with the current bring-up scaffold.
8. If doorlock-related autonomous behavior is to become authoritative Class 1 low-risk scope, update the frozen low-risk catalog and the linked experiment docs before implementing it as such.

---

## 13. Recommended Checks Before Any Future Edit

Before editing code or documents, the next session should verify:

- the current canonical policy file still exists:
  - `common/policies/policy_table_v1_1_2_FROZEN.json`
- the current authoritative low-risk action catalog still exists:
  - `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- the current fault rules still exist:
  - `common/policies/fault_injection_rules_v1_4_0_FROZEN.json`
- the current notification payload schema still exists:
  - `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- the current validator output schema still exists:
  - `common/schemas/validator_output_schema_v1_1_0_FROZEN.json`
- the current Mac mini README still exists:
  - `mac_mini/docs/README.md`
- the current RPi README still exists:
  - `rpi/docs/README.md`
- the current ESP32 README still exists:
  - `esp32/docs/README.md`
- the current integration root README still exists:
  - `integration/README.md`
- the current scenario manifest / review docs still exist:
  - `integration/scenarios/scenario_manifest_rules.md`
  - `integration/scenarios/scenario_review_guide.md`
- no deleted legacy assets were accidentally reintroduced
- prompts, required experiments, and architecture docs still point to the same baseline versions
- current implemented scope wording in `required_experiments.md` is still reflected consistently in integration fixtures and scenario expectations
- no doc silently treats doorlock implementation scope as equivalent to authoritative autonomous low-risk policy scope unless the frozen baseline was updated to match

---

## 14. If a New Session Continues This Project

The next assistant should do the following first:

1. Read this handoff file completely.
2. Treat the listed canonical frozen assets as the source of truth.
3. Confirm current repo state before proposing edits.
4. Avoid reintroducing deleted legacy files or version names.
5. Preserve document-to-document consistency across architecture docs, required experiments docs, device-layer READMEs, and integration docs.
6. Keep Llama 3.1 as the active local model baseline unless the user explicitly asks for a model evaluation change.
7. If modifying prompts, scripts, scenarios, or implementation plans, ensure they still align with:
   - `policy_table_v1_1_2_FROZEN.json`
   - `low_risk_actions_v1_1_0_FROZEN.json`
   - `fault_injection_rules_v1_4_0_FROZEN.json`
   - `validator_output_schema_v1_1_0_FROZEN.json`
   - `class_2_notification_payload_schema_v1_0_0_FROZEN.json`
   - `common/docs/required_experiments.md`
   - `mac_mini/docs/README.md`
   - `rpi/docs/README.md`
   - `esp32/docs/README.md`
   - `integration/README.md`

---

## 15. Commit / Traceability Snapshot

### Important earlier commits mentioned in conversation
- `419bb1a473ac989dbc0c1289d4ac146a03a9da31`  
  added `common/docs/runtime/SESSION_HANDOFF.md`
- `c554f18e8502691c442b964dcf6b14b122a2421b`  
  prompt-set alignment work on `12_prompts.md`
- `351d07dd137943e46c962afcc108bb9e6e82ec45`  
  `11_configuration_script_structure.md` alignment
- `7b3db5080528a16b5b92f527a1238a63874e5014`  
  `10_install_script_structure.md` alignment
- `4238a5492d0d07785f7210804bc81222b8097457`  
  `09_recommended_next_steps.md` alignment
- `fce67f66f4cb8aaa634e40b19fe780ca68c51db2`  
  `08_additional_required_work.md` alignment
- `c2d71777ff48c39762baea1964db0eaddee628eb`  
  `07_task_breakdown.md` alignment
- `3f623a6974dc89806efd7350d4218165c3c1bd55`  
  `06_implementation_plan.md` alignment
- `54562603781de6fa6c3ae6b31acf5bcc9885fdee`  
  `05_automation_strategy.md` alignment
- `dbfbd2c4ed1e2d87c58088276876b504c979b2b7`  
  `04_project_directory_structure.md` alignment

### Recent cleanup and structured alignment commits
- `eba196877ad74416c9960063959f981d55f5ea78`  
  removed obsolete schema manifests and legacy validator schema
- `ded8ac5befad8a401231c32c3b5e6d0234b4c302`  
  Bundle 1: terminology cleanup and Class 2 payload contract alignment
- `97c01c80ba7d3cd121b8e0e21d399c5814eed479`  
  Bundle 2: `E002` deterministic profile and conflict profile refinement
- `1f20642950b85d6a4e2a85da1e7a51f4b650bd42`  
  aligned `common/docs/required_experiments.md` with updated deterministic fault profiles
- `88a07880491cc32cc61e35d190ffa2dfe7bdfcf3`  
  Bundle 3: authority hierarchy and companion asset clarification across policy files
- `2bd22eb02e108347465a2ca19479d565a6e99fd8`  
  expanded `mac_mini/docs/README.md` into a Korean step-by-step runtime guide

### Recent device-layer and architecture alignment commits
- `c46aad8f1c60c13f5ae42973700b3fddf98085ea`  
  Windows ESP32 configure/verify support and `esp32/docs/README.md` execution order expansion
- `525cd76cb0759bdd509d972289303fb80d8988c4`  
  expanded `12_prompts.md` with dedicated ESP32 firmware generation prompts
- `3f8fd0811095510a054463838fcf0104f7b002d4`  
  expanded `rpi/docs/README.md`
- `d7ae83a74c9e6bc5b13b6f301277113560f4a729`  
  aligned `10_install_script_structure.md` and `11_configuration_script_structure.md` with current ESP32 scaffolding
- `073d0d92f559f666f86fe19041da21ba4f77a104`  
  aligned `04_project_directory_structure.md`
- `0668e44a963ded7c947651df27aa2eae1363f8ca`  
  aligned `05_automation_strategy.md`
- `242f2e0d1b9783d803c18c7acaaed402675021f1`  
  aligned `06_implementation_plan.md` and `07_task_breakdown.md`
- `647e24e9606659c785e2c02c3eded392a7cd4be1`  
  aligned `08_additional_required_work.md`
- `25e17ad4cbdbd51436ee30f7cf8e61a3e20e6b19`  
  aligned `09_recommended_next_steps.md`

### Recent integration-layer commits
- `f5b322ff7fc832a717654203a44f640f1f11781d`  
  created `integration/README.md` and `integration/requirements.md`
- `e31f8f59e95746cf7841c1e3d47a49c762c818e6`  
  created integration sub-layer READMEs
- `2e5567eb9af2ac983554fe24e2c74a0e957d10a4`  
  completed initial integration layer documentation structure
- `9dea981b025ecfc6e10453f221bebfded34f283f`  
  added baseline scenario skeleton and initial fixture set
- `02d07ebb92f2fa060c77a3081ec6492511dc3008`  
  added `integration_test_runner_skeleton.py`
- `39abcd8e7b2b65f89a1aaaeecae21c96ef1a15db`  
  added `class_wise_latency_profiles.md` and updated `integration/README.md`
- `3eeea2ae049e4c97c195b4b1ab568e6914619548`  
  added class-oriented and fault-oriented scenario skeletons
- `b0a8b197e92542a1dbb0f9dbed6f1e1d457f6937` / `5fb49d8f34a3dc572cf3b656ee50fcd7d63a5d2f`  
  added and corrected `scenario_manifest_rules.md`
- `2557e1c81fd8ab168b916f7ec8a0faf21d570e9a`  
  added `expected_outcome_comparator.py`
- `44ed4bd446b8f4b5434862435e98bd2e2225aade`  
  added `scenario_review_guide.md`
- `0b5f914e923b31fda605567f51cb4299ab66205c`  
  grounded review guide in real-life accessibility context from root README
- `43fef1833366a9bc2e05b2034f298bc7162b3852` / `58e09969f9006bbb4dede47280d34366272bab26` / `09c66bbf65102c468575916a10c8d7bff3109850` / `25ad98eab97890b74bf261c98f9b67cc15bbbac5`  
  aligned integration scenarios/fixtures with `required_experiments.md`, current implemented scope, and full canonical emergency family coverage
- `d072de32a66aecb520381f976988bb966d580b67`  
  developer-oriented terminology cleanup in `scenario_review_guide.md`

---

## 16. Short Operational Summary

If a future session needs a very short summary:

- Use **Llama 3.1**, not Gemma 4, as the current project baseline.
- Canonical policies are:
  - `policy_table_v1_1_2_FROZEN.json`
  - `low_risk_actions_v1_1_0_FROZEN.json`
  - `fault_injection_rules_v1_4_0_FROZEN.json`
- Canonical schemas include:
  - `validator_output_schema_v1_1_0_FROZEN.json`
  - `class_2_notification_payload_schema_v1_0_0_FROZEN.json`
- Canonical emergency family is `E001`~`E005`.
- `required_experiments.md` is already aligned with the updated deterministic emergency profile numbering.
- Current implementation-facing scope includes lighting paths and a doorlock representative interface path.
- Current authoritative autonomous Class 1 low-risk scope still follows the frozen low-risk catalog unless that catalog is explicitly updated.
- Mac mini install/configure/verify scaffolding and README are now substantially aligned with the current baseline.
- RPi README and experiment-side scaffold are aligned around evaluation-only role separation.
- ESP32 cross-platform bring-up scaffold now exists, but real node firmware is still largely unimplemented.
- `integration/` now contains scenario, fixture, runner, comparator, and measurement starter assets.
- Integration scenarios are grounded in actual accessibility use context, but remain evaluation assets rather than policy truth.
- `mac_mini/code/` is still the major remaining implementation area.
- Legacy policy/schema assets and manifest files were intentionally deleted.
- Do not let deployment-local config override frozen truth.
- Keep Mac mini / RPi / ESP32 / measurement role separation.
- Prefer safe deferral over unsafe autonomous actuation.

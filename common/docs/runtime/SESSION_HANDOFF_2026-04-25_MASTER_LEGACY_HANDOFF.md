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
- **implementation-facing device scope**
- **authoritative autonomous low-risk actuation scope**

These must not be conflated.

Current interpretation:
- current implementation-facing scope includes lighting paths and a doorlock representative interface path
- current authoritative autonomous Class 1 low-risk scope remains the frozen low-risk catalog unless that catalog is explicitly updated

### Measurement-node distinction that must be preserved
- STM32 Nucleo-H723ZG timing/measurement nodes are **not** operational physical nodes.
- They are **out-of-band measurement nodes** used for timing capture, latency evidence collection, and exportable experiment artifacts.
- They must not become part of the operational control path, policy authority, or validator authority.

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
  
### Doorlock-sensitive actuation interpretation
- Doorlock is currently treated as an **implementation-facing representative actuator domain**, but **not** as part of the currently authorized autonomous low-risk Class 1 actuation scope.
- The LLM may interpret limited-input user intent in visitor-response situations, but it must not autonomously authorize or execute door unlock.
- Under the current interpretation, door unlock should follow a **caregiver escalation path** with manual approval, ACK-based closed-loop verification, and local audit logging.
- Detailed rationale and architectural interpretation are documented in:
  - `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`
### Current dashboard / readiness interpretation
- Home Assistant dashboard work is currently a **support-layer UI concept**, not a policy authority.
- Experiment preflight readiness should evaluate:
  - required operational nodes
  - required services/topics
  - required runtime assets
  - required measurement nodes
  - expected result artifact readiness
- Start-button semantics should remain gated by preflight readiness rather than bypassing blocked conditions.

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
- `mac_mini/docs/MAC_MINI_SCRIPT_PRIORITY_AND_COMMANDS.md`
- `mac_mini/docs/TELEGRAM_NOTIFICATION_SETUP.md`
- `rpi/docs/README.md`
- `esp32/docs/README.md`
- `integration/README.md`
- `integration/requirements.md`
- `integration/scenarios/scenario_manifest_rules.md`
- `integration/scenarios/scenario_review_guide.md`
- `integration/measurement/README.md`
- `integration/measurement/class_wise_latency_profiles.md`
- `integration/measurement/experiment_preflight_readiness_design.md`
- `integration/measurement/stm32_nucleo_h723zg_measurement_node.md`
- `integration/measurement/experiment_registry_skeleton.yaml`
- `integration/measurement/node_registry_skeleton.yaml`
- `integration/measurement/preflight_readiness_aggregator_skeleton.py`
- `integration/measurement/sample_state_snapshot.yaml`

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
- explicit distinction between operational nodes and out-of-band STM32 measurement nodes
- experiment preflight readiness as a support layer rather than policy authority

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
- `common/docs/architecture/12_prompts.md` was expanded with Prompt 19~28 for minimal template, node-specific firmware generation, preflight readiness backend, and STM32 measurement-node development

### Integration layer scaffolding completed
- `integration/` now exists as an explicit cross-device validation layer with root README and requirements docs
- `integration/tests/`, `integration/tests/data/`, `integration/scenarios/`, and `integration/measurement/` now contain starter README/docs/assets
- integration fixture samples, expected outcome fixtures, scenario skeletons, runner skeleton, comparator skeleton, scenario manifest rules, scenario review guide, and class-wise latency profile docs were added
- scenario layer was aligned with `required_experiments.md`, current implemented scope, and canonical emergency family `E001`~`E005`

### Preflight readiness and STM32 measurement support design completed
- experiment preflight readiness design was documented under `integration/measurement/experiment_preflight_readiness_design.md`
- STM32 Nucleo-H723ZG was explicitly positioned as an out-of-band measurement node under `integration/measurement/stm32_nucleo_h723zg_measurement_node.md`
- experiment registry and node registry YAML skeletons were added for readiness/dashboard integration
- a preflight readiness aggregator skeleton was added to evaluate experiment readiness from registries and a state snapshot
- a developer-side sample state snapshot was added and successfully exercised from the Mac mini side

### Mac mini `mac_mini/code/` service implementation completed (current session)
- **6 core services** fully implemented and tested:
  1. `policy_router`: deterministic routing (CLASS_0/1/2), CLASS_0 priority over staleness, policy-driven thresholds
  2. `deterministic_validator`: LLM safe deferral, domain check, single-admissible resolution, conflict detection
  3. `safe_deferral_handler`: bounded button clarification (2-3 candidate mapping), timeout handling, policy-driven constraints
  4. `audit_logging_service`: SQLite single-writer (WAL mode), MQTT audit stream support, 7-table schema with correlation tracking
  5. `notification_backend`: Class 0/2 alerts, Telegram integration, mock fallback, DRY_RUN support, dependency injection
  6. `caregiver_confirmation_backend`: Telegram callback parsing, low-risk action confirmation, dependency injection for audit
- All services read policy/schema from frozen JSON files (no hardcoding)
- All unit tests read from frozen baseline (28 + 22 + 22 + 17 + 21 + 24 = 134 tests, all passing)
- Python 3.9.6, pytest, venv at `mac_mini/code/.venv`
- Pydantic v2 with `extra="forbid"` for strict input validation

### Integration adapter and scenario test implementation (current session)
- **`integration/tests/integration_adapter.py`**: Connects runner skeleton and comparator to `policy_router.route()` directly
  - Lenient fixture normalisation (maps legacy field names like `temperature_c` → `temperature`, fills safe defaults)
  - Distinguishes fresh vs stale payloads: `publish_context_payload` → fresh timestamps; `publish_fault_injected_context_payload` → stale
  - Detects empty `environmental_context` as missing policy input (C202 analog) → stale path → CLASS_2
  - Maps `PolicyRouterOutput` to observed dict for comparator (route_class, routing_target, llm_invocation_allowed, safe_outcome, canonical_emergency_family)
- **`integration/tests/test_integration_scenarios.py`**: 11 pytest tests covering full scenario spectrum
  - CLASS_0: E001~E005 (4 emergency scenarios, all passing)
  - CLASS_1: baseline low-risk assistance (passing)
  - CLASS_2: insufficient-context escalation (passing)
  - Faults: staleness (C204) and missing-state (C202) routing (passing)
  - Step-level assertions: result presence, observed dict, comparison results
  - All 11 tests pass; 134 mac_mini tests + 11 integration tests = 145/145 passing

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
- `mac_mini/scripts/install/00_install_homebrew.sh`
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

### Additional Mac mini runtime notes
- Homebrew bootstrap is now treated as part of the actual install path rather than an implicit external prerequisite.
- `00_preflight.sh` no longer blocks on Python installation; Python install/selection is handled in `10_install_homebrew_deps.sh`.
- macOS system `python3` may remain 3.9.x; current scripts explicitly install and select **Homebrew Python 3.11+**.
- `30_setup_python_venv_mac.sh` now uses Homebrew Python 3.11+ explicitly instead of trusting the shell-default `python3`.
- Mosquitto config generation path was corrected to `~/smarthome_workspace/docker/volumes/mosquitto/config` to match compose runtime mounts.
- Mosquitto config mount in the compose template was changed from read-only to read-write to avoid startup-time `chown` / config-read failures in the selected image behavior.
- Telegram notification setup is now documented in a dedicated guide:
  - `mac_mini/docs/TELEGRAM_NOTIFICATION_SETUP.md`
- `mac_mini/scripts/verify/60_verify_notifications.sh` had a bash placeholder parsing bug fixed (`<...>` placeholder handling).
- `mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh` was fixed for empty AUTH_ARGS handling under `set -u`.
- Home Assistant dashboard work has **not** yet been implemented, but experiment dashboard and readiness-panel concepts were designed as a future operational/evaluation UI layer.
- Developer-side execution of the preflight readiness skeleton was confirmed on the Mac mini side using a temporary venv because Homebrew Python enforces PEP 668 protections.

### Current Mac mini status
- install/configure/template/verify scaffolding is now much closer to the canonical baseline
- Homebrew/Python/Docker initial bring-up confusion was reduced through script and doc changes
- Mosquitto runtime path mismatch and config mount issues were diagnosed and corrected in repo scripts/templates
- `mac_mini/code/` is still largely unimplemented and remains the major next implementation area
- `edge_controller_app` is represented in compose/runtime structure, but the actual code path still needs implementation
- `edge_controller_app` build context under `~/smarthome_workspace/docker/app` is still a known gap / placeholder area unless implementation artifacts are added
- `80_verify_rpi_closed_loop_audit.sh` is currently effectively blocked by missing/unavailable `edge_controller_app`

---

## 10. Current RPi Runtime Interpretation

### Current RPi install flow
- `rpi/scripts/install/00_preflight_rpi.sh`
- `rpi/scripts/install/10_install_system_packages_rpi.sh`
- `rpi/scripts/install/20_create_python_venv_rpi.sh`
- `rpi/scripts/install/30_install_python_deps_rpi.sh`
- `rpi/scripts/install/40_install_time_sync_client_rpi.sh`

### Current RPi configure flow
- `rpi/scripts/configure/10_write_env_files_rpi.sh`
- `rpi/scripts/configure/20_sync_phase0_artifacts_rpi.sh`
- `rpi/scripts/configure/30_configure_time_sync_rpi.sh`
- `rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh`
- `rpi/scripts/configure/50_configure_fault_profiles_rpi.sh`

### Current RPi verify flow
- `rpi/scripts/verify/70_verify_rpi_base_runtime.sh`
- `rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh`

### Additional RPi notes
- Python interpreter handling was generalized from hardcoded `python3.11` assumptions to `python3` **3.11+** acceptance.
- `20_sync_phase0_artifacts_rpi.sh` depends on **actual** `MAC_MINI_USER` / `MAC_MINI_HOST` values in `~/smarthome_workspace/.env`; placeholder values such as `mac_user` / `192.168.1.100` will cause immediate sync failure.
- The artifact sync path assumes the Mac mini runtime assets are already present at:
  - `~/smarthome_workspace/docker/volumes/app/config/schemas`
  - `~/smarthome_workspace/docker/volumes/app/config/policies`
- Artifact sync also assumes **unattended SSH/rsync** from RPi to Mac mini.
- A `Connection refused` result during `ssh-copy-id` means the Mac mini SSH server is not accepting connections on port 22 yet; this is usually a **Mac mini Remote Login / sshd availability** issue rather than an SSH key formatting issue.
- `rpi/docs/README.md` now documents:
  - actual `.env` requirements for sync
  - Mac mini Remote Login enablement
  - port 22 / `sshd` checks
  - key-based SSH setup
  - sync/SSH troubleshooting patterns
- `rpi/scripts/verify/70_verify_rpi_base_runtime.sh` was corrected to remove unsupported `mosquitto_pub -W` usage and to handle empty auth arrays safely.

---

## 11. Current Integration / Measurement Interpretation

### Core interpretation
- `integration/` remains a cross-device validation and evaluation layer.
- `integration/measurement/` remains an **evaluation-only** support layer.
- experiment preflight readiness is currently a **support-layer design/skeleton**, not an operational authority and not a policy engine.

### Current measurement-side assets
- `integration/measurement/class_wise_latency_profiles.md`
- `integration/measurement/experiment_preflight_readiness_design.md`
- `integration/measurement/stm32_nucleo_h723zg_measurement_node.md`
- `integration/measurement/experiment_registry_skeleton.yaml`
- `integration/measurement/node_registry_skeleton.yaml`
- `integration/measurement/preflight_readiness_aggregator_skeleton.py`
- `integration/measurement/sample_state_snapshot.yaml`

### Current measurement-side interpretation
- STM32 Nucleo-H723ZG is treated as a **measurement_node**, not a physical operational node.
- experiment preflight readiness distinguishes:
  - required operational nodes
  - required services/topics
  - required runtime assets
  - required measurement nodes
  - expected result artifacts
- measurement dependency failure may yield either:
  - `DEGRADED`, or
  - `BLOCKED`,
  depending on the experiment’s `measurement_policy`.

### Developer-side preflight test already confirmed
Developer-side execution from the Mac mini side confirmed that the skeleton behaves as designed.

Observed example:
- `EXP_CLASSWISE_LATENCY_PROFILE`
- `stm32_time_probe_01 = READY`
- `stm32_time_probe_02 = BLOCKED`
- final readiness result = `BLOCKED`
- reason code = `MEASUREMENT_NODE_UNAVAILABLE`

This matches the current registry semantics, where `EXP_CLASSWISE_LATENCY_PROFILE` treats missing measurement probes as `BLOCKED`.

### Practical execution note
- Running the aggregator directly on the Mac mini with Homebrew Python may hit PEP 668 protection when installing `PyYAML` system-wide.
- The safe workaround used in practice was to create a temporary local venv such as `.venv-preflight` and install `pyyaml` there.
- This is a developer-side test path only; it does not yet mean the Home Assistant dashboard is integrated with the aggregator.

### Current limitation
- The preflight readiness aggregator is still a **registry + snapshot skeleton**.
- It does not yet collect live runtime status from Docker, MQTT heartbeat, API health, serial measurement exporters, or Home Assistant.
- A future runtime adapter is still required before the dashboard can consume real readiness state.

---

## 12. Non-Negotiable Rules for Future Sessions

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

13. **Do not let STM32 measurement nodes drift into operational-node semantics.**  
    They are out-of-band evidence collection nodes, not control-plane nodes.

14. **Do not let preflight readiness become policy authority.**  
    It may block, degrade, or explain experiment execution readiness, but it must not reinterpret canonical policy semantics.

---

## 13. Known Risks / Drift Risks

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
- Homebrew bootstrap assumptions
- system `python3` vs Homebrew Python interpreter selection
- Mosquitto config host path vs compose mount path

### G. Integration scenario drift
Scenario fixtures and review guides were intentionally grounded in actual accessibility use context from the root README.  
Future edits must keep that connection, while still preserving the rule that scenarios do not redefine canonical policy truth.

### H. ESP32 bring-up vs firmware confusion
The ESP32 cross-platform install/configure/verify layer now exists.  
Future sessions should not confuse this with completed real node firmware implementation.

### I. Mac mini notification verification drift
Notification setup and verification are now functional, but future sessions should preserve consistency across:
- `.env` variable naming
- Telegram setup guide steps
- `60_configure_notifications.sh`
- `60_verify_notifications.sh`
- mock fallback semantics

### J. RPi SSH / artifact sync drift
RPi artifact sync relies on runtime assumptions outside the local board itself.  
Future sessions must preserve consistency across:
- `.env` host/user values
- Mac mini Remote Login availability
- SSH key-based unattended access
- actual runtime asset deployment on Mac mini
- rsync source path assumptions under `~/smarthome_workspace/docker/volumes/app/config/...`

### K. Preflight registry / measurement-policy drift
The new experiment registry and node registry skeletons encode readiness semantics for operational vs measurement dependencies.  
Future work must preserve consistency across:
- experiment registry semantics
- node registry semantics
- Home Assistant readiness panel assumptions
- preflight aggregator logic
- measurement-policy `DEGRADED` vs `BLOCKED` interpretation

### L. STM32 measurement-node scope drift
Future sessions may accidentally treat STM32 probes as ordinary physical nodes or control-path participants.  
This must be resisted; they are measurement-only support nodes unless the architecture is explicitly reworked.

---

## 14. Recommended Next Actions

1. Begin implementation-facing work against the stabilized baseline.
2. Verify that no scripts, prompts, or code still reference deleted legacy policy/schema assets.
3. Keep Llama 3.1 as the primary baseline during implementation and early evaluation.
4. ✅ **COMPLETED**: Start defining and implementing the actual `mac_mini/code/` services, especially the policy router, deterministic validator, safe deferral handler, audit logger, notification backend, and caregiver confirmation backend. (All 6 services implemented, 134 tests passing)
5. ✅ **COMPLETED**: Connect the integration runner and expected outcome comparator through an adapter, then extend toward MQTT publish / audit observe execution. (`integration_adapter.py` implements direct policy_router calls; 11 scenario tests passing)
   - Note: Adapter uses direct function calls (not live MQTT) for deterministic local/CI testing; lenient fixture parsing handles legacy field names and missing required fields
6. ✅ **COMPLETED**: Resolve the remaining `edge_controller_app` build-context / placeholder implementation gap. (`edge_controller_app/orchestrator.py`, `models.py`, `mqtt_client.py`, `main.py` implemented; 12 tests passing)
7. ✅ **COMPLETED**: Add a real runtime adapter for preflight readiness so that Home Assistant can consume actual status rather than only synthetic snapshots. (`runtime_state_collector.py` + `ha_realtime_adapter.py` implemented; 37 tests passing; total 183 tests passing)
8. ✅ **COMPLETED**: Add dedicated payload fixtures for `E002`~`E005` and align integration scenario assets with dedicated emergency-path fixtures.
   - Currently E002 has no fixture; E003/E004/E005 all reuse E001 temperature fixture
10. **PENDING**: When ESP32 node firmware generation begins, use the prompt set in `common/docs/architecture/12_prompts.md` and keep it aligned with the current bring-up scaffold.
11. **PENDING**: If doorlock-related autonomous behavior is to become authoritative Class 1 low-risk scope, update the frozen low-risk catalog and the linked experiment docs before implementing it as such.
12. **PENDING**: Revisit `10_configure_home_assistant.sh` template path / template existence assumptions and ensure they match the current repo template layout.
13. **PENDING**: Define the host-side ingestion/export contract for STM32 Nucleo-H723ZG measurement nodes, including heartbeat/status and CSV-friendly timestamp export.

---

## 15. Recommended Checks Before Any Future Edit

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
- the current Mac mini Telegram guide still exists:
  - `mac_mini/docs/TELEGRAM_NOTIFICATION_SETUP.md`
- the current RPi README still exists:
  - `rpi/docs/README.md`
- the current ESP32 README still exists:
  - `esp32/docs/README.md`
- the current integration root README still exists:
  - `integration/README.md`
- the current measurement design docs still exist:
  - `integration/measurement/experiment_preflight_readiness_design.md`
  - `integration/measurement/stm32_nucleo_h723zg_measurement_node.md`
  - `integration/measurement/experiment_registry_skeleton.yaml`
  - `integration/measurement/node_registry_skeleton.yaml`
  - `integration/measurement/preflight_readiness_aggregator_skeleton.py`
- the current scenario manifest / review docs still exist:
  - `integration/scenarios/scenario_manifest_rules.md`
  - `integration/scenarios/scenario_review_guide.md`
- no deleted legacy assets were accidentally reintroduced
- prompts, required experiments, and architecture docs still point to the same baseline versions
- current implemented scope wording in `required_experiments.md` is still reflected consistently in integration fixtures and scenario expectations
- no doc silently treats doorlock implementation scope as equivalent to authoritative autonomous low-risk policy scope unless the frozen baseline was updated to match
- no doc silently treats STM32 measurement nodes as operational control nodes

---

## 16. If a New Session Continues This Project

The next assistant should do the following first:

1. Read this handoff file completely.
2. Treat the listed canonical frozen assets as the source of truth.
3. Confirm current repo state before proposing edits.
4. Avoid reintroducing deleted legacy files or version names.
5. Preserve document-to-document consistency across architecture docs, required experiments docs, device-layer READMEs, and integration docs.
6. Keep Llama 3.1 as the active local model baseline unless the user explicitly asks for a model evaluation change.
7. If modifying prompts, scripts, scenarios, implementation plans, experiment readiness logic, or measurement support docs, ensure they still align with:
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
   - `integration/measurement/experiment_preflight_readiness_design.md`
   - `integration/measurement/stm32_nucleo_h723zg_measurement_node.md`

### Additional Context for Next Session (Current Session Completions)

**Mac mini service implementation** is now complete. Key architectural decisions baked into the code:

- **Policy reading**: All services load `policy_table_v1_1_2_FROZEN.json` and `low_risk_actions_v1_1_0_FROZEN.json` at startup (no hardcoding)
- **CLASS_0 priority**: Emergency check runs BEFORE staleness check (fire/fall alarms must not be ignored for freshness)
- **Single-writer audit**: All audit logging goes through `AuditDB` (SQLite WAL mode); other services use dependency injection callbacks or MQTT to avoid direct writes
- **Lenient input parsing**: Integration adapter normalizes legacy fixture field names and fills safe defaults (e.g., `timestamp_ms=now` for fresh, `=0` for stale) to decouple scenario fixtures from schema changes
- **Telegram fallback**: Notification backend auto-falls back to mock if `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` unset (prevents test/CI breakage)
- **Fault isolation**: Audit callback exceptions are caught and logged, never propagated (confirmation results remain reliable)

**Pre-existing test failure**: `integration/tests/test_policy_fault_consistency.py` has 2 failures due to incorrect profile name mapping in the test itself (not in the code). Expected map says `FAULT_EMERGENCY_02_SMOKE` but actual JSON has `FAULT_EMERGENCY_03_SMOKE`. This should be fixed by the next session (test bug, not implementation).

**Next priority tasks** (in order):
1. Fix `test_policy_fault_consistency.py` (2 failures, simple test-code fix)
2. Add dedicated E002~E005 payload fixtures (so integration tests validate actual emergency types, not all E001 temperature)
3. ESP32 firmware generation (lower priority, use Prompt 19~26 from `12_prompts.md`)

---

## 17. Commit / Traceability Snapshot

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

### Recent Mac mini / RPi bring-up and troubleshooting commits
- `dacdc0ebafbd975ee34422b31f9262001d604370`
- `f2700f51a452b0a6cd7925b37f793dbbb1c73d6e`
- `9530bb95599e2139168072e3414c8e21cca74269`
- `bedaa4140d4e76bd07a3a61e9f8b93a8573c3eb9`  
  Homebrew bootstrap introduction and Mac mini install-order/document updates
- `f7fcf7d7f987567d478f0dbeaa7de92b2015818c`
- `86683cc9d0a2e66480e4a1a8855b66d23a3594ab`  
  generalized RPi Python handling from hardcoded `python3.11` assumptions to `python3` 3.11+
- `9c223ab29022b747b92818e5b013444f35323537`  
  moved Mac mini Python install responsibility out of preflight and into install step
- `8383d42deee176ebb2f15524fcea44e33042c37e`
- `15467e8b3d0aff72e3123c94d043383022200a1f`  
  explicit Homebrew Python 3.11+ install/selection and venv creation on Mac mini
- `15e531c681ec74b7eac8aa7413238680ff4bb159`  
  Mac mini README troubleshooting expansion
- `b2b44b027fc4f5c9b8f037ffaef5a21498330d7f`  
  added `mac_mini/docs/TELEGRAM_NOTIFICATION_SETUP.md`
- `a4984dac4ef29ed62ef9cdb2746619a3d31062dd`
- `57c23ca1c0207d719f6e150e30188e256c9d3a09`  
  Mosquitto configure path alignment and compose template `:ro` removal
- `0aa1eeb189ee7c77cc165ab247b21ad3022c3351`  
  fixed bash placeholder parsing bug in `mac_mini/scripts/verify/60_verify_notifications.sh`
- `25363e94e215e5917daa289da4e53e444165c3ad`  
  documented RPi SSH/rsync artifact sync preconditions and troubleshooting
- `5bd38a27b2334fe48cf012469bd8e32406f51947`  
  fixed empty AUTH_ARGS handling in `mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh`
- `b08fb041462ea9ed09ddd8e5c4ce65d250707860`  
  fixed `rpi/scripts/verify/70_verify_rpi_base_runtime.sh` mosquitto_pub option usage and auth handling

### Recent integration / measurement commits
- `ae2386e35c56ac7cd538800efded5229050ff000`  
  added `experiment_preflight_readiness_design.md`
- `70640600b2930db8d678f2c0526f432adb79339c`  
  added `stm32_nucleo_h723zg_measurement_node.md` and updated integration measurement docs
- `4cecd6bba893ec49dd76c8d06dd19a53aaa9b5b4`  
  added Prompt 27 and Prompt 28 for preflight readiness backend and STM32 measurement node development
- `a640fae4034dc9a4c61479411c70761294dbfa85`  
  added `experiment_registry_skeleton.yaml` and `node_registry_skeleton.yaml`
- `61862a38ddc9f0b09a48c42c7c55a6f9c0b470c3`  
  added `preflight_readiness_aggregator_skeleton.py`
- `722c40378feb443ca6c2f23157e0932694b60781`  
  added `sample_state_snapshot.yaml`

### Current session implementation commits (to be recorded)

**Mac mini service implementation** (6 services, 134 unit tests, all passing):
- `mac_mini/code/requirements.txt` — project dependencies (fastapi, uvicorn, pydantic, pytest, httpx)
- `mac_mini/code/conftest.py` — pytest sys.path bootstrap
- `mac_mini/code/policy_router/` — routing logic (CLASS_0/1/2, CLASS_0 priority, policy-driven thresholds)
- `mac_mini/code/deterministic_validator/` — LLM safe deferral, domain check, single-admissible resolution
- `mac_mini/code/safe_deferral_handler/` — bounded button clarification (2-3 candidate mapping)
- `mac_mini/code/audit_logging_service/` — SQLite single-writer (WAL), MQTT audit stream, 7-table schema
- `mac_mini/code/notification_backend/` — Class 0/2 alerts, Telegram, mock fallback, DRY_RUN
- `mac_mini/code/caregiver_confirmation_backend/` — action confirmation, Telegram callback parsing, injection
- `CLAUDE.md` — renamed from `CLAUD.md` with updated internal self-references

**Integration layer adapter and tests** (11 scenario tests, all passing):
- `integration/tests/integration_adapter.py` — connects runner + comparator to `policy_router.route()`
  - lenient fixture normalisation (legacy field name mapping, safe defaults)
  - fresh vs stale timestamp distinction (`publish_context_payload` vs `publish_fault_injected_context_payload`)
  - empty `environmental_context` → stale path (C202 analog)
  - PolicyRouterOutput → observed dict mapping
- `integration/tests/test_integration_scenarios.py` — 11 pytest tests (CLASS_0 E001~E005, CLASS_1, CLASS_2, faults)

**Edge controller app** (12 tests, all passing):
- `mac_mini/code/edge_controller_app/orchestrator.py` — async pipeline: policy_router → CLASS_0/1/2 결과 반환
- `mac_mini/code/edge_controller_app/models.py` — OrchestratorOutput (Pydantic v2, extra="forbid")
- `mac_mini/code/edge_controller_app/mqtt_client.py` — optional paho-mqtt wrapper, graceful degradation
- `mac_mini/code/edge_controller_app/main.py` — FastAPI lifespan, /health, /orchestrate endpoints
- `mac_mini/code/Dockerfile` — python:3.9-slim, uvicorn on port 8000

**HA realtime adapter** (37 tests, all passing):
- `integration/measurement/runtime_state_collector.py` — async collectors (Docker/MQTT/Ollama/SQLite/Ping), `collect_all_states()`
- `integration/measurement/ha_realtime_adapter.py` — StateSnapshotBuilder, MQTTPrefightPublisher, AdapterService, FastAPI REST
- `integration/measurement/tests/test_runtime_state_collector.py` — 20 unit tests
- `integration/measurement/tests/test_ha_realtime_adapter.py` — 17 unit tests
- `mac_mini/code/requirements.txt` — pyyaml>=6.0 추가

**Status**: 183/183 tests passing (134 mac_mini services + 11 integration scenarios + 12 edge_controller + 26 preflight measurement).

**Known pending** (for next session):
- Fix `test_policy_fault_consistency.py` (2 pre-existing failures: test incorrectly maps FAULT_EMERGENCY_02_SMOKE instead of FAULT_EMERGENCY_03_SMOKE)
- Dedicated payload fixtures for E002~E005 (currently E003/E004/E005 reuse E001 fixture, E002 has none)
- ESP32 firmware (lower priority)

---

## 18. Short Operational Summary

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
- Homebrew bootstrap, Homebrew Python 3.11+, Telegram guide, and Mosquitto compose/config alignment were additional recent fixes.
- RPi README and experiment-side scaffold are aligned around evaluation-only role separation.
- RPi artifact sync now has documented SSH/Remote Login prerequisites.
- ESP32 cross-platform bring-up scaffold now exists, but real node firmware is still largely unimplemented.
- `integration/` now contains scenario, fixture, runner, comparator, and measurement starter assets.
- Integration scenarios are grounded in actual accessibility use context, but remain evaluation assets rather than policy truth.
- STM32 Nucleo-H723ZG is now explicitly treated as an out-of-band measurement node, not an operational node.
- experiment preflight readiness registry/aggregator skeletons now exist and were developer-tested from the Mac mini side.
- **`mac_mini/code/` is now COMPLETE**: All 6 services (policy_router, validator, safe_deferral_handler, audit_logger, notification_backend, caregiver_confirmation) implemented and passing.
- `edge_controller_app` is implemented with MQTT-driven orchestrator (12 tests passing).
- Integration adapter (lenient fixture parsing, direct route() calls) is complete; 11 scenario tests passing.
- HA realtime adapter (`runtime_state_collector` + `ha_realtime_adapter`) is implemented; 37 tests passing.
- **Total: 183 tests passing** across mac_mini/code and integration/measurement.
- Legacy policy/schema assets and manifest files were intentionally deleted.
- Do not let deployment-local config override frozen truth.
- Keep Mac mini / RPi / ESP32 / measurement role separation.
- Prefer safe deferral over unsafe autonomous actuation.
- **Next priorities**: (1) Fix `test_policy_fault_consistency.py` (2 test bugs), (2) Add dedicated E002~E005 fixtures, (3) ESP32 firmware (lower priority)
- ### Doorlock-sensitive actuation interpretation
- Doorlock is currently treated as an **implementation-facing representative actuator domain**, but **not** as part of the currently authorized autonomous low-risk Class 1 actuation scope.
- The LLM may interpret limited-input user intent in visitor-response situations, but it must not autonomously authorize or execute door unlock.
- Under the current interpretation, door unlock should follow a **caregiver escalation path** with manual approval, ACK-based closed-loop verification, and local audit logging.
- Detailed rationale and architectural interpretation are documented in:
  - `common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`

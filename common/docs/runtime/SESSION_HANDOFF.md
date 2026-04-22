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

## 7. Architecture Documents Already Aligned

The following architecture docs were reviewed and updated to match the current canonical baseline and project interpretation.

- `common/docs/architecture/04_project_directory_structure.md`
- `common/docs/architecture/05_automation_strategy.md`
- `common/docs/architecture/06_implementation_plan.md`
- `common/docs/architecture/07_task_breakdown.md`
- `common/docs/architecture/08_additional_required_work.md`
- `common/docs/architecture/09_recommended_next_steps.md`
- `common/docs/architecture/10_install_script_structure.md`
- `common/docs/architecture/11_configuration_script_structure.md`
- `common/docs/architecture/12_prompts.md`
- `common/docs/required_experiments.md`

### Alignment themes already applied
- canonical baseline version cleanup
- optional / version-sensitive companion asset handling for output profiles
- deployment-local separation
- `E001`~`E005` alignment
- current / optional / planned scope distinction for ESP32-related targets
- canonical consistency check expectations
- prompt anti-drift updates
- deterministic fault profile mapping alignment in `required_experiments.md`

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

---

## 9. Non-Negotiable Rules for Future Sessions

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

---

## 10. Known Risks / Drift Risks

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
- **current canonical** = button, lighting, representative sensing
- **optional experimental** = gas, fire, fall
- **planned extension** = doorlock or warning interface

### D. Notification payload drift
Class 2 outbound escalation must stay aligned with:
- `common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`

### E. Consistency verification drift
Future work must preserve:
- policy/schema/rules consistency checking
- trigger-family alignment for `E001`~`E005`
- deterministic fault profile mapping consistency in `required_experiments.md`

---

## 11. Recommended Next Actions

These are the recommended next steps after this handoff point.

1. Begin implementation-facing work against the stabilized baseline.
2. Verify that no scripts, prompts, or code still reference deleted legacy policy/schema assets.
3. Optionally add a lightweight index/readme under `common/policies/` and/or `common/schemas/` listing the current canonical asset set.
4. Keep Llama 3.1 as the primary baseline during implementation and early evaluation.
5. If model comparison becomes necessary later, create an explicit A/B evaluation plan rather than switching directly to Gemma 4.

---

## 12. Recommended Checks Before Any Future Edit

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
- no deleted legacy assets were accidentally reintroduced
- prompts, required experiments, and architecture docs still point to the same baseline versions

---

## 13. If a New Session Continues This Project

The next assistant should do the following first:

1. Read this handoff file completely.
2. Treat the listed canonical frozen assets as the source of truth.
3. Confirm current repo state before proposing edits.
4. Avoid reintroducing deleted legacy files or version names.
5. Preserve document-to-document consistency across architecture docs and required experiments docs.
6. Keep Llama 3.1 as the active local model baseline unless the user explicitly asks for a model evaluation change.
7. If modifying prompts, scripts, or implementation plans, ensure they still align with:
   - `policy_table_v1_1_2_FROZEN.json`
   - `low_risk_actions_v1_1_0_FROZEN.json`
   - `fault_injection_rules_v1_4_0_FROZEN.json`
   - `validator_output_schema_v1_1_0_FROZEN.json`
   - `class_2_notification_payload_schema_v1_0_0_FROZEN.json`
   - `common/docs/required_experiments.md`

---

## 14. Commit / Traceability Snapshot

### Important recent commits mentioned in conversation
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

### Earlier policy cleanup commits
- `189d164abc510b2e8e64f2d8d78ba0e2216193a4`  
  removed `policy_table_v1_2_0_FROZEN.json`
- `b2be040fe0af6b41b8f8820330e25aef61827c39`  
  removed `low_risk_actions_v1_0_0_FROZEN.json`
- `15aad72d19b18a19491f6f73f480f6ea27777dd9`  
  removed `LOW_RISK_ACTIONS_FREEZE_MANIFEST.md`
- `bd2f78ae10e43b3d63e921735878c7258801d410`  
  removed `output_profile_v1_0_0.json`

---

## 15. Short Operational Summary

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
- Legacy policy/schema assets and manifest files were intentionally deleted.
- Do not let deployment-local config override frozen truth.
- Keep Mac mini / RPi / ESP32 / measurement role separation.
- Prefer safe deferral over unsafe autonomous actuation.

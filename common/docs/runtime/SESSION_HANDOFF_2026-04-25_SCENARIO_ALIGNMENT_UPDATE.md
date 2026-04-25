# SESSION_HANDOFF_2026-04-25_SCENARIO_ALIGNMENT_UPDATE.md

Date: 2026-04-25
Scope: `integration/scenarios/`, scenario skeleton JSON files, scenario fixtures, and scenario verification utilities
Status: Scenario alignment Phase S1 through S5 completed

## 1. Purpose

This addendum records the completed scenario-alignment work for the `safe_deferral` project.

It supersedes the planning status in:

- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_SCENARIO_ALIGNMENT_PLAN.md`

The planning document remains useful as process history, but this update document should be treated as the current status reference for scenario documentation, scenario skeleton JSON files, fixture alignment, and scenario verification utilities.

## 2. Primary references

Read these together for scenario interpretation:

- `integration/scenarios/README.md`
- `integration/scenarios/scenario_review_guide.md`
- `integration/scenarios/scenario_manifest_rules.md`
- `integration/scenarios/scenario_manifest_schema.json`
- `integration/scenarios/verify_scenario_manifest.py`
- `integration/scenarios/verify_scenario_topic_alignment.py`
- `integration/scenarios/verify_scenario_fixture_refs.py`
- `integration/scenarios/verify_scenario_policy_schema_alignment.py`
- `common/docs/architecture/15_interface_matrix.md`
- `common/docs/architecture/17_payload_contract_and_registry.md`
- `common/mqtt/topic_registry_v1_0_0.json`
- `common/policies/policy_table_v1_1_2_FROZEN.json`
- `common/policies/low_risk_actions_v1_1_0_FROZEN.json`
- `common/schemas/context_schema_v1_0_0_FROZEN.json`

## 3. Completed phase summary

### Phase S1 — Scenario documentation alignment

Completed.

Updated:

- `integration/scenarios/README.md`
- `integration/scenarios/scenario_review_guide.md`
- `integration/scenarios/scenario_manifest_rules.md`

Key changes:

- Clarified that scenario files are integration/evaluation assets, not canonical policy/schema truth.
- Added `safe_deferral/...` MQTT namespace guidance.
- Marked legacy `smarthome/...` topics as disallowed for aligned/new scenario skeletons.
- Added Class 0 emergency topic interpretation.
- Added Class 1 frozen low-risk lighting catalog boundary.
- Added doorlock-sensitive non-Class-1 boundary.
- Added `environmental_context.doorbell_detected` required-field and non-authority rule.
- Added LLM decision invocation vs policy-constrained guidance generation distinction.
- Added E002~E005 to scenario manifest coverage.
- Added future verifier guidance.

Completed commits:

- `22395c83c53979db271d44f91933aa095cb82183` — `docs(scenarios): align README with current contracts`
- `dd1d454f3083540a79c24387852d38523466deb3` — `docs(scenarios): align review guide with safety boundaries`
- `a03f74ef4f54b1f3ecf48ec5d9b36aede3f2878d` — `docs(scenarios): align manifest rules with current contracts`

### Phase S2 — Scenario skeleton JSON topic and boundary alignment

Completed.

Updated scenario skeletons:

- `integration/scenarios/baseline_scenario_skeleton.json`
- `integration/scenarios/class0_e001_scenario_skeleton.json`
- `integration/scenarios/class0_e002_scenario_skeleton.json`
- `integration/scenarios/class0_e003_scenario_skeleton.json`
- `integration/scenarios/class0_e004_scenario_skeleton.json`
- `integration/scenarios/class0_e005_scenario_skeleton.json`
- `integration/scenarios/class1_baseline_scenario_skeleton.json`
- `integration/scenarios/class2_insufficient_context_scenario_skeleton.json`
- `integration/scenarios/stale_fault_scenario_skeleton.json`
- `integration/scenarios/conflict_fault_scenario_skeleton.json`
- `integration/scenarios/missing_state_scenario_skeleton.json`

Key changes:

- Replaced legacy `smarthome/context/raw` and `smarthome/audit/validator_output` topics.
- Ordinary context/input scenarios now use `safe_deferral/context/input`.
- Class 0 emergency scenarios now use `safe_deferral/emergency/event`.
- Class 0 scenarios declare `normalized_policy_input_topic` and `bridge_mode` to document controlled normalized-input bridge interpretation.
- Audit observation now uses `safe_deferral/audit/log`.
- Added `requires_mqtt_registry_alignment` and `requires_policy_schema_alignment`.
- Added `llm_decision_invocation_allowed` and `llm_guidance_generation_allowed`.
- Added `doorlock_autonomous_execution_allowed: false`.
- Added Class 1 `allowed_action_catalog_ref` to the frozen low-risk lighting catalog.

Completed commits:

- `5db548c5f98ba85c65576c2f356eb2dc9284de16` — `docs(scenarios): align baseline scenario skeleton`
- `7f17f94ef6cb421828814c45f274549d542863d2` — `docs(scenarios): align class0 E001 scenario skeleton`
- `91beec5c33d380a5dca741b9e40a4549fa93960a` — `docs(scenarios): align class0 E002 scenario skeleton`
- `34297592b539fb6fa1b12da8ba6b29878c89ee8c` — `docs(scenarios): align class0 E003 scenario skeleton`
- `cdc4ae23819133d6524a12cf8826e1499619e999` — `docs(scenarios): align class0 E004 scenario skeleton`
- `8c98f41db053ce07ca04979f8ea4721a1559befd` — `docs(scenarios): align class0 E005 scenario skeleton`
- `c27bfa778feb1da5b67d655d609302f6026904f0` — `docs(scenarios): align class1 scenario skeleton`
- `d12659f83212f6dcd318bf65e06dacceb6cca54c` — `docs(scenarios): align class2 scenario skeleton`
- `67415d92ab73bccf82f10a515b73d12dfbf7a98f` — `docs(scenarios): align stale fault scenario skeleton`
- `fe7c678e4e9451dbeb2102fd0acf8587ee69b326` — `docs(scenarios): align conflict fault scenario skeleton`
- `5630d43c6c82c63f82320b793be2226aef0fa700` — `docs(scenarios): align missing-state scenario skeleton`

### Phase S3 — Fixture inventory and fixture reference validation

Completed.

Input fixtures updated:

- `integration/tests/data/sample_policy_router_input_class1.json`
- `integration/tests/data/sample_policy_router_input_class2_insufficient_context.json`
- `integration/tests/data/sample_policy_router_input_class0_e001.json`
- `integration/tests/data/sample_policy_router_input_class0_e002_button_triple_hit.json`
- `integration/tests/data/sample_policy_router_input_class0_e003_smoke.json`
- `integration/tests/data/sample_policy_router_input_class0_e004_gas.json`
- `integration/tests/data/sample_policy_router_input_class0_e005_fall.json`

Expected fixtures updated:

- `integration/tests/data/expected_routing_class1.json`
- `integration/tests/data/expected_routing_class2.json`
- `integration/tests/data/expected_routing_class0_e001.json`
- `integration/tests/data/expected_routing_class0_e002_button_triple_hit.json`
- `integration/tests/data/expected_routing_class0_e003_smoke.json`
- `integration/tests/data/expected_routing_class0_e004_gas.json`
- `integration/tests/data/expected_routing_class0_e005_fall.json`

Key changes:

- Added `environmental_context.doorbell_detected=false` to schema-governed non-visitor/emergency fixtures.
- Preserved Class 2 sparse fixture while keeping the current required doorbell field.
- Added expected split LLM fields: `expected_llm_decision_invocation_allowed`, `expected_llm_guidance_generation_allowed`.
- Added expected unsafe-actuation and doorlock-autonomous-execution boundary fields.
- Added Class 1 expected low-risk catalog reference.

Completed commits:

- `49cb929f400fa157506c3550f0471a1140508548` — `testdata: add doorbell context to class1 fixture`
- `5028793bd945227703d5d0f998c9abeef4f4d876` — `testdata: add doorbell context to class2 fixture`
- `75e6f132e7f7bbcf2328a0d539e9fab0e9081adb` — `testdata: add doorbell context to class0 E001 fixture`
- `2f1e3cf1add5c98abf4baf4cea067fe5943902ee` — `testdata: add doorbell context to class0 E002 fixture`
- `c912ada87d7b4b27ea465e2b80cf2e64f2ff5d3f` — `testdata: add doorbell context to class0 E003 fixture`
- `5a7b1f2b06e0c4138d0a6836dbb46ecd2bb795ec` — `testdata: add doorbell context to class0 E004 fixture`
- `173b86432e87be554f2cab8a3ae3853933bc73b9` — `testdata: add doorbell context to class0 E005 fixture`
- `2c1527da4f4db8be7d2f3ec6e05656890c045b7f` — `testdata: align class1 expected routing fixture`
- `89514311bb676a63e888cd3128ae3134f7dcc098` — `testdata: align class2 expected routing fixture`
- `5ae714b3fbd1ab50e7d58127200568b5c963c5f0` — `testdata: align class0 E001 expected routing fixture`
- `35243e7ffbe8010cf92db632420eb5d51f9e7c00` — `testdata: align class0 E002 expected routing fixture`
- `242c61722f27c3dd366747fe08dfdc964d4b5e76` — `testdata: align class0 E003 expected routing fixture`
- `041de325b802ab9d606372a485c3d0bdfb1a3144` — `testdata: align class0 E004 expected routing fixture`
- `8fd38bbd74b79b1441d2e6f1644e0ad0ddafc500` — `testdata: align class0 E005 expected routing fixture`

### Phase S4 — Scenario verification utilities

Completed.

Added:

- `integration/scenarios/scenario_manifest_schema.json`
- `integration/scenarios/verify_scenario_manifest.py`
- `integration/scenarios/verify_scenario_topic_alignment.py`
- `integration/scenarios/verify_scenario_fixture_refs.py`
- `integration/scenarios/verify_scenario_policy_schema_alignment.py`

Run from repository root:

```bash
python3 integration/scenarios/verify_scenario_manifest.py
python3 integration/scenarios/verify_scenario_topic_alignment.py
python3 integration/scenarios/verify_scenario_fixture_refs.py
python3 integration/scenarios/verify_scenario_policy_schema_alignment.py
```

The verifiers use only the Python standard library.

Completed commits:

- `6eb4d29ea07bf894f34ef54392525143b83b274b` — `test(scenarios): add scenario manifest schema`
- `6c9c5fc3a603536b24872c168cf659df71077c65` — `test(scenarios): add scenario manifest verifier`
- `af69fddb42de3ff06b2d501f13db95c300a97787` — `test(scenarios): add scenario topic alignment verifier`
- `17a18f2453f104d8d1df837d792662d0952052b4` — `test(scenarios): add scenario fixture reference verifier`
- `6b679097ba0e5b781e0b55a0838f5981145868aa` — `test(scenarios): add scenario policy schema alignment verifier`
- `1a91fb6b519fb34bdcc7f770a753170781191533` — `test(scenarios): harden manifest verifier category handling`

### Phase S5 — Add or split fault-specific fixtures

Completed.

Added fault-specific fixtures:

- `integration/tests/data/sample_policy_router_input_fault_stale.json`
- `integration/tests/data/sample_policy_router_input_fault_conflict_multiple_candidates.json`
- `integration/tests/data/sample_policy_router_input_fault_missing_device_state.json`
- `integration/tests/data/sample_policy_router_input_fault_missing_doorbell_detected.json`

Updated fault skeleton references:

- `integration/scenarios/stale_fault_scenario_skeleton.json`
- `integration/scenarios/conflict_fault_scenario_skeleton.json`
- `integration/scenarios/missing_state_scenario_skeleton.json`

Key changes:

- Stale scenario now references `sample_policy_router_input_fault_stale.json`.
- Conflict scenario now references `sample_policy_router_input_fault_conflict_multiple_candidates.json`.
- Missing-state scenario now references `sample_policy_router_input_fault_missing_device_state.json`.
- A separate negative fixture intentionally omits `doorbell_detected`: `sample_policy_router_input_fault_missing_doorbell_detected.json`.
- The negative fixture is not referenced by the baseline missing-state scenario and should be used only by explicit negative schema-boundary tests.

Completed commits:

- `58909dc7a99595dec41614d14206106eb2d5cbc5` — `testdata: add stale fault scenario fixture`
- `5cd06708aad0246a705132e29bd65c3a1d153632` — `testdata: add conflict fault scenario fixture`
- `3769167da5366ec837b2bbe5985714dbf91437d7` — `testdata: add missing device-state fault fixture`
- `23b01b9ef398d1186f313e6bac62edc895f5ad40` — `testdata: add missing doorbell negative fixture`
- `0062ebc8477a2c088d7cdf5da14055b96bffa3db` — `docs(scenarios): use stale fault fixture`
- `787887dc1b59bd5f213acae0c3d8d1bc5c537863` — `docs(scenarios): use conflict fault fixture`
- `cc63e97865ab961835c2a0fe40331fb7b049dd9a` — `docs(scenarios): use missing device-state fault fixture`

## 4. Current scenario asset interpretation

```text
Scenario docs = evaluation contract and review guidance
Scenario skeleton JSON = deterministic/replayable integration scenario definitions
Scenario fixtures = input/expected test data for scenario runner/comparator/verifier
Scenario verifiers = static consistency checks against topic registry, fixture refs, and policy/schema boundaries
```

Current aligned scenario constraints:

```text
ordinary context/input scenario ingress = safe_deferral/context/input
Class 0 emergency ingress = safe_deferral/emergency/event
audit observation = safe_deferral/audit/log
Class 0 emergency = E001~E005, no LLM primary decision path
Class 1 autonomous execution = frozen low-risk lighting catalog only
fault scenarios = conservative safe outcomes only
all active referenced context fixtures include environmental_context.doorbell_detected
doorbell_detected is visitor-response context, not emergency evidence or unlock authorization
doorlock autonomous execution is false across aligned scenarios
```

## 5. Current known caveats

1. The static verifiers were added but were not executed inside this chat environment as a real repository checkout. Run them from a local clone or CI.
2. `sample_policy_router_input_fault_missing_doorbell_detected.json` is an intentional negative fixture and is not referenced by the baseline missing-state scenario.
3. The negative fixture will fail the policy/schema verifier if a future scenario references it without negative-test handling.
4. `candidate_conflict_annotation` in the conflict fixture is evaluation metadata only, not policy truth.
5. `routing_metadata.fault_injection` is evaluation metadata only and must not become operational authority.
6. Existing integration adapter / pytest code may need review if it assumed older `smarthome/...` topics or generic fault fixture names.
7. Verifiers check scenario asset consistency; they do not replace full runtime/closed-loop tests.

## 6. Recommended next work

1. Run the four scenario verifiers from a clean repository checkout.
2. Update any test runner / integration adapter that still expects the old generic fault fixtures.
3. Add explicit negative-test handling for `sample_policy_router_input_fault_missing_doorbell_detected.json`.
4. Optionally add a single wrapper script such as `integration/scenarios/run_all_scenario_verifiers.py`.
5. Optionally wire these verifier scripts into CI or a higher-level `scripts/verify` entry point.
6. Review `integration/tests/test_integration_scenarios.py` and `integration/tests/integration_adapter.py` against the updated fixture names and expected outcome fields.

## 7. Current status statement

Scenario alignment S1~S5 is complete. The current scenario documentation, scenario skeletons, active referenced fixtures, and verifier scripts are now aligned with the current `safe_deferral/...` MQTT namespace, Class 0 E001~E005 emergency family, Class 1 frozen lighting-only low-risk boundary, `doorbell_detected` required-field boundary, and doorlock-sensitive non-autonomous execution boundary.

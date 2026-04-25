# SESSION_HANDOFF_2026-04-25_RPI_SCRIPT_ALIGNMENT_UPDATE.md

Date: 2026-04-25
Scope: Raspberry Pi install/configure/verify scripts
Status: Phase 1 through Phase 8 implemented on `main`

## 1. Purpose

This addendum records the completed Raspberry Pi script alignment work.

The Raspberry Pi side is now aligned as a simulation, verification, dashboard/observation, replay, fault-injection, evaluation, and non-authoritative governance-support node. It is not an operational authority node.

Mac mini remains the safety-critical operational edge hub for policy routing, deterministic validation, caregiver approval, actuator dispatch, audit authority, and runtime authority copies of policy/schema/MQTT/payload assets.

## 2. Completed commits

The following staged commits were applied to `main`:

1. `988248fe0d51f02e0a46525d391368c61457db14` — `fix(rpi): add shell syntax verification script`
2. `8e98b7e44c5ae3872b1fe1d477b121f0d5d2b0b5` — `config(rpi): align env topics and authority flags`
3. `f3590eea72beecde89b1e847aa940f18d4c4c471` — `config(rpi): sync mqtt and payload reference assets`
4. `50cb5d3f798ff37585e595eb79525f31116d646b` — `verify(rpi): strengthen base runtime boundary checks`
5. `1a4f05615a71d981f6171446c544dbd8b8024fb8` — `verify(rpi): add mqtt payload alignment checks`
6. `c98d594b9331a052271bc20bf3170bc4ee71a3e0` — `verify(rpi): harden closed loop audit boundaries`
7. `dca36768d3499825c3edb6255ce01631a2b7a9be` — `config(rpi): align fault profiles with safe deferral semantics`
8. `0f5360a793e7b3c0b577d25cdcf1ed0ff5384283` — `install(rpi): separate required and optional python dependency checks`

The original planning document remains available at:

- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_RPI_SCRIPT_ALIGNMENT_PLAN.md`

## 3. Updated Raspberry Pi verification flow

After pulling the latest `main`, the recommended end-to-end RPi sequence is:

```bash
cd /path/to/safe_deferral

git pull

# Phase 1: static shell syntax verification
bash rpi/scripts/verify/00_verify_rpi_script_syntax.sh

# Install
bash rpi/scripts/install/00_preflight_rpi.sh
bash rpi/scripts/install/10_install_system_packages_rpi.sh
bash rpi/scripts/install/20_create_python_venv_rpi.sh
bash rpi/scripts/install/30_install_python_deps_rpi.sh
bash rpi/scripts/install/40_install_time_sync_client_rpi.sh

# Configure
bash rpi/scripts/configure/10_write_env_files_rpi.sh
# IMPORTANT: edit ~/smarthome_workspace/.env before continuing.
# Required manual checks:
# - MAC_MINI_HOST
# - MAC_MINI_USER
# - MQTT_HOST
# - MQTT_USER
# - MQTT_PASS
# - TOPIC_NAMESPACE=safe_deferral
# - no stale smarthome/* topic values remain
# - ALLOW_RPI_ACTUATION=false
# - ALLOW_RPI_POLICY_AUTHORITY=false
# - ALLOW_RPI_DOORLOCK_CONTROL=false

bash rpi/scripts/configure/20_sync_phase0_artifacts_rpi.sh
bash rpi/scripts/configure/30_configure_time_sync_rpi.sh
bash rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh
bash rpi/scripts/configure/50_configure_fault_profiles_rpi.sh

# Verify
bash rpi/scripts/verify/70_verify_rpi_base_runtime.sh
bash rpi/scripts/verify/75_verify_rpi_mqtt_payload_alignment.sh
bash rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh
```

## 4. Updated script responsibilities

### `rpi/scripts/verify/00_verify_rpi_script_syntax.sh`

New script.

Responsibilities:

- Find all RPi shell scripts under `rpi/scripts`.
- Verify Bash shebang.
- Detect CRLF line endings.
- Detect malformed `cat <` heredoc patterns.
- Run `bash -n` on every script.

This is the first verification command to run after `git pull`.

### `rpi/scripts/configure/10_write_env_files_rpi.sh`

Updated.

Responsibilities:

- Generate or append RPi `.env` values while preserving existing user settings.
- Set RPi role to `simulation_verification_node`.
- Use `safe_deferral/...` topic namespace defaults.
- Add `MQTT_REGISTRY_SYNC_PATH` and `PAYLOAD_EXAMPLES_SYNC_PATH`.
- Add explicit authority-boundary flags:
  - `ALLOW_RPI_ACTUATION=false`
  - `ALLOW_RPI_POLICY_AUTHORITY=false`
  - `ALLOW_RPI_DOORLOCK_CONTROL=false`

Important behavior:

- Existing `.env` keys are preserved.
- If an old `.env` already contains `smarthome/*` values, the user must manually edit them before running verification.

### `rpi/scripts/configure/20_sync_phase0_artifacts_rpi.sh`

Updated.

Responsibilities:

- Sync authority mirrors from Mac mini:
  - `policies`
  - `schemas`
- Sync reference/governance assets from Mac mini:
  - `mqtt`
  - `payloads`
- Verify required policy/schema/MQTT files exist.
- Verify JSON syntax for policy, schema, and topic registry files when `jq` is available.

Mac mini default source paths:

```text
~/smarthome_workspace/docker/volumes/app/config/policies
~/smarthome_workspace/docker/volumes/app/config/schemas
~/smarthome_workspace/docker/volumes/app/config/mqtt
~/smarthome_workspace/docker/volumes/app/config/payloads
```

RPi default mirror paths:

```text
~/smarthome_workspace/config/policies
~/smarthome_workspace/config/schemas
~/smarthome_workspace/config/mqtt
~/smarthome_workspace/config/payloads
```

Interpretation:

- RPi copies are for simulation and verification only.
- RPi copies do not grant policy, validator, caregiver approval, audit, actuator, or doorlock execution authority.

### `rpi/scripts/verify/70_verify_rpi_base_runtime.sh`

Updated.

Responsibilities:

- Verify required CLI tools.
- Verify RPi authority flags are all `false`.
- Check Mac mini network reachability.
- Test MQTT publish using a non-authoritative observation topic.
- Verify policy/schema authority mirrors.
- Verify MQTT/payload reference assets.
- Verify `context_schema_v1_0_0_FROZEN.json` contains `doorbell_detected`.
- Check local `.env` for legacy `smarthome/*` core topic drift.
- Warn or fail on doorlock-related payload misuse.
- Measure time sync offset and network RTT.

### `rpi/scripts/verify/75_verify_rpi_mqtt_payload_alignment.sh`

New script.

Responsibilities:

- Verify `topic_registry_v1_0_0.json`.
- Verify `publisher_subscriber_matrix_v1_0_0.md`.
- Verify `topic_payload_contracts_v1_0_0.md`.
- Verify context schema JSON.
- Verify `.env` topic keys use `safe_deferral/*`.
- Fail on `smarthome/*` topic drift in `.env` or MQTT registry artifacts.
- Verify `doorbell_detected` exists in context schema.
- Validate JSON payload examples.
- Warn if examples do not cover `doorbell_detected`.
- Fail if doorlock state fields appear under `pure_context_payload.device_states`.
- Warn on sensitive doorlock terms outside explicitly prohibited state paths.

This script separates MQTT/payload contract drift checking from basic runtime verification.

### `rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh`

Updated.

Responsibilities:

- Verify RPi authority flags remain false before closed-loop testing.
- Use `safe_deferral/audit/log` as default audit topic.
- Use `safe_deferral/fault/injection` as default injection topic.
- Reject non-`safe_deferral/*` audit or injection topics.
- Inject a fault payload containing:
  - `routing_metadata.audit_correlation_id`
  - `pure_context_payload.trigger_event`
  - `pure_context_payload.environmental_context.doorbell_detected=false`
  - `pure_context_payload.device_states={}`
- Reject doorlock state fields under `device_states`.
- Parse multiple possible audit result fields.
- Fail on missing audit trace.
- Fail on any globally prohibited autonomous/sensitive actuation outcome.
- Pass only expected profile outcomes or recognized safe non-dispatch outcomes.

Global prohibited outcomes:

```text
door_unlock
doorlock_dispatch
autonomous_door_unlock
approved_low_risk_door_unlock
unsafe_actuation
```

Recognized safe non-dispatch outcomes:

```text
safe_deferral
defer_to_caregiver
manual_confirmation_required
validator_reject
blocked
no_dispatch
```

### `rpi/scripts/configure/50_configure_fault_profiles_rpi.sh`

Updated.

Responsibilities:

- Verify RPi authority flags remain false.
- Verify frozen fault-injection rules and context schema JSON.
- Verify frozen dynamic references.
- Verify `doorbell_detected` exists in context schema.
- Generate local safe-deferral verification overlay:
  - `~/smarthome_workspace/config/fault_profiles/rpi_safe_deferral_fault_profiles.json`
- Generate runner config:
  - `~/smarthome_workspace/config/runner/fault_runner.json`

Important semantics:

- Fault profiles are verification cases only.
- `doorbell_detected=true` may support visitor-response interpretation.
- `doorbell_detected=true` does not authorize door unlock.
- Door unlock or doorlock dispatch outcomes remain prohibited.

### `rpi/scripts/install/30_install_python_deps_rpi.sh`

Updated.

Responsibilities:

- Install `requirements-rpi.txt` into `~/smarthome_workspace/.venv-rpi`.
- Verify required simulation/verification dependencies:
  - `paho-mqtt`
  - `pytest`
  - `PyYAML`
  - `jsonschema`
- Verify optional dependencies only when corresponding feature flags are enabled:
  - `fastapi` when `ENABLE_RPI_DASHBOARD_BACKEND=true`
  - `uvicorn` when `ENABLE_RPI_DASHBOARD_BACKEND=true`
  - `pandas` when `ENABLE_RPI_RESULT_EXPORT=true`

Default feature flag behavior:

```env
ENABLE_RPI_DASHBOARD_BACKEND=false
ENABLE_RPI_RESULT_EXPORT=false
```

## 5. Manual `.env` migration note

Because `10_write_env_files_rpi.sh` preserves existing keys, old RPi deployments may retain stale values.

Before running verification, check:

```bash
grep -nE 'smarthome/|TOPIC_NAMESPACE|VERIFICATION_AUDIT_TOPIC|FAULT_INJECTION_TOPIC|ALLOW_RPI_' ~/smarthome_workspace/.env
```

Required values include:

```env
TOPIC_NAMESPACE=safe_deferral
SIM_CONTEXT_TOPIC=safe_deferral/sim/context
FAULT_INJECTION_TOPIC=safe_deferral/fault/injection
VERIFICATION_AUDIT_TOPIC=safe_deferral/audit/log
VALIDATOR_OUTPUT_TOPIC=safe_deferral/validator/output
EXPERIMENT_PROGRESS_TOPIC=safe_deferral/experiment/progress
EXPERIMENT_RESULT_TOPIC=safe_deferral/experiment/result
DASHBOARD_OBSERVATION_TOPIC=safe_deferral/dashboard/observation
ALLOW_RPI_ACTUATION=false
ALLOW_RPI_POLICY_AUTHORITY=false
ALLOW_RPI_DOORLOCK_CONTROL=false
```

If stale `smarthome/*` values remain, edit them manually before running `70`, `75`, or `80` verify scripts.

## 6. Safety boundaries preserved

The RPi update does not change the following project-wide boundaries:

1. RPi is not the operational hub.
2. RPi is not a policy authority.
3. RPi is not a validator authority.
4. RPi is not an actuator dispatcher.
5. RPi is not a doorlock-control authority.
6. MQTT/payload registry files are reference/governance assets only.
7. Doorlock is not Class 1 autonomous low-risk execution.
8. `doorbell_detected` is context only, not unlock authorization.
9. Doorlock state must not be inserted into current `pure_context_payload.device_states`.
10. Missing audit trace during closed-loop verification is non-pass/fatal.

## 7. Known validation status

The changes were committed through the GitHub API. They have not yet been executed on a physical Raspberry Pi in this session.

Required physical/runtime validation:

```bash
git pull
bash rpi/scripts/verify/00_verify_rpi_script_syntax.sh
bash rpi/scripts/install/00_preflight_rpi.sh
bash rpi/scripts/install/10_install_system_packages_rpi.sh
bash rpi/scripts/install/20_create_python_venv_rpi.sh
bash rpi/scripts/install/30_install_python_deps_rpi.sh
bash rpi/scripts/install/40_install_time_sync_client_rpi.sh
bash rpi/scripts/configure/10_write_env_files_rpi.sh
# edit ~/smarthome_workspace/.env
bash rpi/scripts/configure/20_sync_phase0_artifacts_rpi.sh
bash rpi/scripts/configure/30_configure_time_sync_rpi.sh
bash rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh
bash rpi/scripts/configure/50_configure_fault_profiles_rpi.sh
bash rpi/scripts/verify/70_verify_rpi_base_runtime.sh
bash rpi/scripts/verify/75_verify_rpi_mqtt_payload_alignment.sh
bash rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh
```

Any failure in these scripts should be treated as a real integration issue until confirmed otherwise.

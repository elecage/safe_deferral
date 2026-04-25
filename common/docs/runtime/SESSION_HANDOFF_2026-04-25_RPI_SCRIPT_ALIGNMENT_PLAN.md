# RPi Script Alignment Plan

Date: 2026-04-25
Scope: `rpi/scripts/install`, `rpi/scripts/configure`, `rpi/scripts/verify`
Status: Planning baseline before implementation

## 1. Purpose

This document freezes the planned update sequence for Raspberry Pi scripts before implementation.

The Raspberry Pi side must remain a simulation, verification, dashboard, replay, fault-injection, evaluation, and non-authoritative governance-support node. It must not become an operational authority node.

Mac mini remains the safety-critical edge hub for policy routing, deterministic validation, caregiver approval, actuator dispatch, and audit authority.

## 2. Alignment principles

1. Raspberry Pi must not have policy authority.
2. Raspberry Pi must not have actuation authority.
3. Raspberry Pi must not have doorlock-control authority.
4. MQTT registry and payload examples are reference/governance assets only.
5. Policy and schema files synchronized to Raspberry Pi are read-only mirrors for verification.
6. `doorbell_detected` is a visitor-response context signal, not door-unlock authorization.
7. Doorlock state fields must not be added under `pure_context_payload.device_states`.
8. Any autonomous door-unlock or sensitive actuation outcome must fail verification.

## 3. Phase 1 — Shell script syntax recovery

Targets:

- `rpi/scripts/install/*.sh`
- `rpi/scripts/configure/*.sh`
- `rpi/scripts/verify/*.sh`

Planned changes:

- Normalize each script to valid Bash format.
- Keep the shebang on the first line.
- Keep `set -euo pipefail` on its own line.
- Convert descriptive Korean or English prose into comments.
- Fix malformed heredocs.
- Remove CRLF if present.
- Ensure executable permissions.

Validation:

```bash
find rpi/scripts -type f -name "*.sh" -exec chmod +x {} \;

for f in rpi/scripts/install/*.sh rpi/scripts/configure/*.sh rpi/scripts/verify/*.sh; do
  echo "==> bash -n $f"
  bash -n "$f" || exit 1
done

grep -RIn 'cat < ' rpi/scripts || true
```

Completion criterion:

- All RPi shell scripts pass `bash -n`.
- No malformed `cat <` heredoc pattern remains.

## 4. Phase 2 — RPi environment and topic namespace alignment

Primary target:

- `rpi/scripts/configure/10_write_env_files_rpi.sh`

Planned environment defaults:

```env
WORKSPACE_DIR=${HOME}/smarthome_workspace
RPI_ROLE=simulation_verification_node

MAC_MINI_HOST=mac-mini.local
MAC_MINI_USER=${USER}

MQTT_HOST=${MAC_MINI_HOST}
MQTT_PORT=1883
MQTT_USER=simulator_node
MQTT_PASS=CHANGE_ME

POLICY_SYNC_PATH=${HOME}/smarthome_workspace/config/policies
SCHEMA_SYNC_PATH=${HOME}/smarthome_workspace/config/schemas
MQTT_REGISTRY_SYNC_PATH=${HOME}/smarthome_workspace/config/mqtt
PAYLOAD_EXAMPLES_SYNC_PATH=${HOME}/smarthome_workspace/config/payloads

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

TIME_SYNC_MAX_OFFSET_MS=50
```

Completion criterion:

- RPi `.env` uses the `safe_deferral/...` topic namespace.
- RPi authority-boundary flags are present and set to `false`.

## 5. Phase 3 — Reference asset synchronization expansion

Primary target:

- `rpi/scripts/configure/20_sync_phase0_artifacts_rpi.sh`

Planned synchronization targets:

- `policies`: read-only authority mirror
- `schemas`: read-only authority mirror
- `mqtt`: reference copy
- `payloads`: reference copy

Planned variables:

```bash
MQTT_REGISTRY_SYNC_PATH="${MQTT_REGISTRY_SYNC_PATH:-${WORKSPACE_DIR}/config/mqtt}"
PAYLOAD_EXAMPLES_SYNC_PATH="${PAYLOAD_EXAMPLES_SYNC_PATH:-${WORKSPACE_DIR}/config/payloads}"

REMOTE_POLICY_DIR="${REMOTE_POLICY_DIR:-~/smarthome_workspace/docker/volumes/app/config/policies}"
REMOTE_SCHEMA_DIR="${REMOTE_SCHEMA_DIR:-~/smarthome_workspace/docker/volumes/app/config/schemas}"
REMOTE_MQTT_DIR="${REMOTE_MQTT_DIR:-~/smarthome_workspace/docker/volumes/app/config/mqtt}"
REMOTE_PAYLOADS_DIR="${REMOTE_PAYLOADS_DIR:-~/smarthome_workspace/docker/volumes/app/config/payloads}"
```

Completion criterion:

- Raspberry Pi can mirror policies, schemas, MQTT registry, and payload examples from Mac mini runtime paths.
- The mirrored files are used for validation only.

## 6. Phase 4 — Base runtime verification strengthening

Primary target:

- `rpi/scripts/verify/70_verify_rpi_base_runtime.sh`

Planned additions:

- Verify authority-boundary environment flags.
- Verify MQTT registry directory and required files.
- Verify payload examples directory.
- Verify `topic_registry_v1_0_0.json` parses as JSON.
- Verify `context_schema_v1_0_0_FROZEN.json` contains `doorbell_detected`.
- Warn on doorlock-related terms in payload examples.
- Fail on doorlock state under `pure_context_payload.device_states` when directly detectable.

Completion criterion:

- `70_verify_rpi_base_runtime.sh` verifies both runtime readiness and RPi authority boundaries.

## 7. Phase 5 — MQTT/payload alignment verification

New target:

- `rpi/scripts/verify/75_verify_rpi_mqtt_payload_alignment.sh`

Planned checks:

- `topic_registry_v1_0_0.json` exists.
- `publisher_subscriber_matrix_v1_0_0.md` exists.
- `topic_payload_contracts_v1_0_0.md` exists.
- Payload examples exist and parse where applicable.
- RPi scripts/config avoid legacy `smarthome/...` hardcoding.
- RPi scripts/config use `safe_deferral/...` topic namespace.
- `doorbell_detected` is represented in context schema or payload examples.
- Doorlock state fields are not present under `pure_context_payload.device_states`.

Completion criterion:

- A dedicated verification step detects topic and payload drift before closed-loop audit tests.

## 8. Phase 6 — Closed-loop audit verification update

Primary target:

- `rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh`

Planned topic defaults:

```bash
AUDIT_TOPIC="${VERIFICATION_AUDIT_TOPIC:-safe_deferral/audit/log}"
INJECT_TOPIC="${FAULT_INJECTION_TOPIC:-safe_deferral/fault/injection}"
```

Planned fault payload requirements:

- Include `routing_metadata.audit_correlation_id`.
- Include `pure_context_payload.environmental_context.doorbell_detected=false` for non-visitor fault tests.
- Keep `pure_context_payload.device_states={}` unless a schema-governed non-sensitive device-state test is explicitly required.
- Reject doorlock state fields in `device_states`.

Prohibited outcomes:

- `door_unlock`
- `doorlock_dispatch`
- `autonomous_door_unlock`
- `approved_low_risk_door_unlock`
- `unsafe_actuation`

Acceptable safe outcomes, subject to actual Mac mini audit naming:

- `safe_deferral`
- `defer_to_caregiver`
- `manual_confirmation_required`
- `validator_reject`
- `blocked`
- `no_dispatch`

Completion criterion:

- Closed-loop audit fails if any autonomous door-unlock or sensitive actuation outcome appears.
- Missing audit trace is treated as non-pass rather than success.

## 9. Phase 7 — Fault profile alignment

Primary target:

- `rpi/scripts/configure/50_configure_fault_profiles_rpi.sh`

Planned fault-profile semantics:

- Fault profiles are robustness tests, not execution-authority tests.
- Doorbell-positive visitor cases test caregiver escalation or manual confirmation, not unlocking.
- Door-unlock outcomes are prohibited unless explicitly represented as a blocked or escalated sensitive-action case.

Representative profiles:

```json
{
  "profiles": [
    {
      "name": "missing_sensor_context",
      "expected_outcome": "safe_deferral"
    },
    {
      "name": "malformed_context_payload",
      "expected_outcome": "validator_reject"
    },
    {
      "name": "mqtt_delay_or_drop",
      "expected_outcome": "safe_deferral"
    },
    {
      "name": "visitor_response_without_unlock_authority",
      "context": {
        "environmental_context": {
          "doorbell_detected": true
        }
      },
      "expected_outcome": "defer_to_caregiver"
    }
  ],
  "prohibited_outcomes": [
    "door_unlock",
    "doorlock_dispatch",
    "autonomous_door_unlock",
    "unsafe_actuation"
  ]
}
```

Completion criterion:

- Fault profiles verify safe deferral, validator rejection, caregiver escalation, and no-dispatch behavior.

## 10. Phase 8 — Python dependency verification

Primary target:

- `rpi/scripts/install/30_install_python_deps_rpi.sh`

Required dependencies:

- `paho-mqtt`
- `jsonschema`
- `PyYAML`
- `pytest`

Optional dependencies:

- `fastapi`
- `uvicorn`
- `pandas`

Completion criterion:

- Required simulation/fault/audit dependencies are fatal if missing.
- Dashboard and result-export dependencies are fatal only when their corresponding features are enabled.

## 11. Final expected RPi execution order

```bash
cd /path/to/safe_deferral

for f in rpi/scripts/install/*.sh rpi/scripts/configure/*.sh rpi/scripts/verify/*.sh; do
  echo "==> bash -n $f"
  bash -n "$f" || exit 1
done

bash rpi/scripts/install/00_preflight_rpi.sh
bash rpi/scripts/install/10_install_system_packages_rpi.sh
bash rpi/scripts/install/20_create_python_venv_rpi.sh
bash rpi/scripts/install/30_install_python_deps_rpi.sh
bash rpi/scripts/install/40_install_time_sync_client_rpi.sh

bash rpi/scripts/configure/10_write_env_files_rpi.sh
# Edit ~/smarthome_workspace/.env for the actual Mac mini host/user/credentials.

bash rpi/scripts/configure/20_sync_phase0_artifacts_rpi.sh
bash rpi/scripts/configure/30_configure_time_sync_rpi.sh
bash rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh
bash rpi/scripts/configure/50_configure_fault_profiles_rpi.sh

bash rpi/scripts/verify/70_verify_rpi_base_runtime.sh
bash rpi/scripts/verify/75_verify_rpi_mqtt_payload_alignment.sh
bash rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh
```

## 12. Suggested implementation commits

1. `fix(rpi): normalize shell script syntax`
2. `config(rpi): align env topics and authority flags`
3. `config(rpi): sync mqtt and payload reference assets`
4. `verify(rpi): add mqtt payload alignment checks`
5. `verify(rpi): harden closed loop audit boundaries`
6. `config(rpi): align fault profiles with safe deferral semantics`

## 13. Final completion checklist

- [ ] All RPi shell scripts pass `bash -n`.
- [ ] Malformed heredocs are fixed.
- [ ] `.env` uses the `safe_deferral/...` topic namespace.
- [ ] RPi authority flags are explicitly false.
- [ ] Policy/schema/MQTT/payload assets sync from Mac mini runtime paths.
- [ ] Base runtime verification checks authority boundaries.
- [ ] MQTT/payload alignment verification exists.
- [ ] Closed-loop audit verification rejects autonomous door-unlock and unsafe actuation outcomes.
- [ ] Fault payloads include `doorbell_detected` where required.
- [ ] Doorlock state is not placed in `pure_context_payload.device_states`.

## 14. Frozen decision

This plan freezes the intended RPi update strategy before implementation. The next work item is implementation of Phase 1, followed by staged commits for environment/topic alignment, asset synchronization, and verification hardening.

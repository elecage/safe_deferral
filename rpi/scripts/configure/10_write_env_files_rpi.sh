#!/usr/bin/env bash
# ==============================================================================
# Script: 10_write_env_files_rpi.sh
# Purpose: Generate or append .env configuration for Raspberry Pi 5 simulation node
# ==============================================================================
set -euo pipefail

echo "==> [10_write_env_files_rpi] Configuring environment variables for Raspberry Pi 5..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

echo "  [INFO] Ensuring workspace directory exists at ${WORKSPACE_DIR}..."
mkdir -p "${WORKSPACE_DIR}"

if [ ! -f "${ENV_FILE}" ]; then
    echo "  [INFO] ${ENV_FILE} not found. Creating a new one..."
    cat <<EOF > "${ENV_FILE}"
# ====================================================
# Raspberry Pi 5 Simulation/Verification Node Environment Variables
# ====================================================
EOF
else
    echo "  [INFO] ${ENV_FILE} already exists. Appending missing keys to preserve user settings..."
fi

append_env_var() {
    local key="$1"
    local value="$2"
    local comment="${3:-}"

    if ! grep -q "^${key}=" "${ENV_FILE}"; then
        if [ -n "${comment}" ]; then
            echo "" >> "${ENV_FILE}"
            echo "# ${comment}" >> "${ENV_FILE}"
        fi
        echo "${key}=${value}" >> "${ENV_FILE}"
        echo "  [OK] Appended missing key: ${key}"
    else
        echo "  [INFO] Preserving existing key: ${key}"
    fi
}

append_env_var "WORKSPACE_DIR" "${WORKSPACE_DIR}" "Local Raspberry Pi workspace"
append_env_var "RPI_ROLE" "simulation_verification_node" "Raspberry Pi role boundary"

append_env_var "MAC_MINI_HOST" "mac-mini.local" "Mac mini Edge Hub Information (Authoritative Source)"
append_env_var "MAC_MINI_USER" "${USER}" "Mac mini SSH Sync Settings"

append_env_var "MQTT_HOST" "\$MAC_MINI_HOST" "MQTT Broker Settings"
append_env_var "MQTT_PORT" "1883"
append_env_var "MQTT_USER" "simulator_node" "Optional MQTT Authentication Settings"
append_env_var "MQTT_PASS" "CHANGE_ME"

append_env_var "POLICY_SYNC_PATH" "${WORKSPACE_DIR}/config/policies" "RPi local read-only mirror path for policy artifacts"
append_env_var "SCHEMA_SYNC_PATH" "${WORKSPACE_DIR}/config/schemas" "RPi local read-only mirror path for schema artifacts"
append_env_var "MQTT_REGISTRY_SYNC_PATH" "${WORKSPACE_DIR}/config/mqtt" "RPi local reference mirror path for MQTT registry artifacts"
append_env_var "PAYLOAD_EXAMPLES_SYNC_PATH" "${WORKSPACE_DIR}/config/payloads" "RPi local reference mirror path for payload examples"

append_env_var "TOPIC_NAMESPACE" "safe_deferral" "MQTT topic namespace and communication contracts"
append_env_var "SIM_CONTEXT_TOPIC" "safe_deferral/sim/context"
append_env_var "FAULT_INJECTION_TOPIC" "safe_deferral/fault/injection"
append_env_var "VERIFICATION_AUDIT_TOPIC" "safe_deferral/audit/log"
append_env_var "VALIDATOR_OUTPUT_TOPIC" "safe_deferral/validator/output"
append_env_var "EXPERIMENT_PROGRESS_TOPIC" "safe_deferral/experiment/progress"
append_env_var "EXPERIMENT_RESULT_TOPIC" "safe_deferral/experiment/result"
append_env_var "DASHBOARD_OBSERVATION_TOPIC" "safe_deferral/dashboard/observation"

append_env_var "ALLOW_RPI_ACTUATION" "false" "Raspberry Pi authority boundary flags"
append_env_var "ALLOW_RPI_POLICY_AUTHORITY" "false"
append_env_var "ALLOW_RPI_DOORLOCK_CONTROL" "false"

append_env_var "NODE_COUNT" "30" "Simulation parameters"
append_env_var "PUBLISH_INTERVAL_MS" "1000"

append_env_var "SCENARIO_PROFILE" "NON_EMERGENCY_RANDOM" "Fault injection and time sync settings"
append_env_var "FAULT_PROFILE" "FAULT_STALENESS_01"
append_env_var "TIME_SYNC_HOST" "\$MAC_MINI_HOST"
append_env_var "TIME_SYNC_MAX_OFFSET_MS" "50"
append_env_var "TIME_SYNC_TARGET_BOUND_MS" "15"

PLACEHOLDER_WARNINGS=0

if grep -Eq '^(MAC_MINI_HOST|MQTT_HOST)=192\.168\.1\.100$' "${ENV_FILE}"; then
    echo "  [WARNING] Placeholder IP 192.168.1.100 remains in ${ENV_FILE}."
    PLACEHOLDER_WARNINGS=1
fi

if grep -q '^MAC_MINI_USER=mac_user$' "${ENV_FILE}"; then
    echo "  [WARNING] Placeholder MAC_MINI_USER=mac_user remains in ${ENV_FILE}."
    PLACEHOLDER_WARNINGS=1
fi

if grep -q '^MQTT_PASS=CHANGE_ME$' "${ENV_FILE}"; then
    echo "  [WARNING] MQTT_PASS is still CHANGE_ME. Clear it for anonymous MQTT or set the real password."
    PLACEHOLDER_WARNINGS=1
fi

if grep -q 'smarthome/' "${ENV_FILE}"; then
    echo "  [WARNING] Legacy smarthome/* topic values remain in ${ENV_FILE}."
    PLACEHOLDER_WARNINGS=1
fi

echo "  [WARNING] ACTION REQUIRED: Please verify MAC_MINI_HOST, MAC_MINI_USER, MQTT_HOST, and MQTT_PASS manually in ${ENV_FILE}."
if [ "${PLACEHOLDER_WARNINGS}" -ne 0 ]; then
    echo "  [WARNING] Placeholder or legacy values must be fixed before sync/verification."
else
    echo "  [OK] No obvious placeholder or legacy topic values detected."
fi
echo "==> [PASS] RPi 5 environment variables configuration completed."

#!/usr/bin/env bash
# ==============================================================================
# Script: 30_verify_ollama_inference.sh
# Purpose: Verify local Ollama inference API functionality for the current Mac mini baseline
# ==============================================================================
set -euo pipefail

echo "==> [30_verify_ollama_inference] Testing Ollama inference API..."

if ! command -v curl >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1; then
    echo "  [FATAL] 'curl' or 'jq' command is not available."
    echo "          Please ensure both are installed via the Mac mini install step or Homebrew."
    exit 1
fi
echo "  [OK] 'curl' and 'jq' tools verified."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

if [ -f "${ENV_FILE}" ]; then
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    echo "  [OK] Environment variables loaded from ${ENV_FILE}."
else
    echo "  [FATAL] ${ENV_FILE} not found. Cannot load Ollama configuration."
    exit 1
fi

TARGET_OLLAMA="${OLLAMA_HOST:-http://127.0.0.1:11434}"
TARGET_MODEL="${OLLAMA_MODEL:-llama3.1}"

echo "  [INFO] Target Ollama API: ${TARGET_OLLAMA}"
echo "  [INFO] Target Model: ${TARGET_MODEL}"
echo "  [INFO] Sending test prompt to Ollama (this may take a few seconds if the model is loading)..."

if ! RESPONSE=$(curl -fsS --connect-timeout 5 --max-time 60 -X POST "${TARGET_OLLAMA}/api/generate" -d "{
  \"model\": \"${TARGET_MODEL}\",
  \"prompt\": \"Please reply with exactly the word READY.\",
  \"stream\": false
}"); then
    echo "  [FATAL] Failed to connect to Ollama API or request timed out."
    echo "          Diagnostic hints:"
    echo "          - Is the Ollama container running? (Check with 'docker compose ps')"
    echo "          - Has the model '${TARGET_MODEL}' been pulled successfully?"
    exit 1
fi

ANSWER=$(echo "${RESPONSE}" | jq -r '.response // empty' | xargs)

if [ "${ANSWER}" = "READY" ] || [ "${ANSWER}" = "READY." ] || [ "${ANSWER}" = "READY!" ]; then
    echo "  [OK] Ollama ${TARGET_MODEL} inference is functioning correctly."
    echo "       (Model Output: '${ANSWER}')"
    echo "==> [PASS] Local LLM inference test successful."
else
    echo "  [FATAL] Ollama inference returned an unexpected response."
    echo "          Expected 'READY', but got: '${ANSWER}'"
    echo "          Full JSON payload: ${RESPONSE}"
    exit 1
fi

#!/usr/bin/env bash
# ==============================================================================
# Script: 30_verify_ollama_inference.sh
# Purpose: Verify Local LLM (Ollama) Inference API functionality (Phase 5)
# ==============================================================================
set -euo pipefail

echo "==> [30_verify_ollama_inference] Testing Ollama Inference API..."

# 1. 필수 명령어 존재 여부 확인 (Fail-fast)
if ! command -v curl >/dev/null 2>&1 || ! command -v jq >/dev/null 2>&1; then
    echo "  [FATAL] 'curl' or 'jq' command is not available."
    echo "          Please ensure both are installed to test and parse the REST API."
    exit 1
fi
echo "  [OK] 'curl' and 'jq' tools verified."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"

# 2. 환경변수 파일 검증 및 로드
if [ -f "${ENV_FILE}" ]; then
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

# 3. LLM 추론 요청 (curl 연결 타임아웃 5초, 최대 응답 대기 60초 제한)
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

# 4. jq를 사용하여 실제 생성된 응답 텍스트만 추출 및 공백/개행 제거
ANSWER=$(echo "${RESPONSE}" | jq -r '.response // empty' | xargs)

# 5. 응답 결과 검증 (LLM 특유의 구두점 생성 예외 처리 포함)
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

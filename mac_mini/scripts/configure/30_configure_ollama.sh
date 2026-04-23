#!/usr/bin/env bash
# ==============================================================================
# Script: 30_configure_ollama.sh
# Purpose: Configure Dockerized Ollama, pull Llama 3.1 model, and verify inference
# ==============================================================================
set -euo pipefail

echo "==> [30_configure_ollama] Configuring Dockerized Ollama and pulling Llama 3.1..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
COMPOSE_DIR="${WORKSPACE_DIR}/docker"
OLLAMA_HOST="http://127.0.0.1:11434"

# 1. Docker workspace 존재 여부 확인
if [ ! -d "${COMPOSE_DIR}" ]; then
    echo "  [FATAL] Docker workspace not found at ${COMPOSE_DIR}."
    echo "          Please complete the install step first."
    exit 1
fi
echo "  [OK] Docker workspace found."

cd "${COMPOSE_DIR}"

# 2. Docker Compose 파일 존재 여부 확인
if [ -f "docker-compose.yml" ] || [ -f "docker-compose.yaml" ] || [ -f "compose.yml" ] || [ -f "compose.yaml" ]; then
    echo "  [OK] Docker Compose stack file found."
else
    echo "  [FATAL] Docker Compose stack file not found in ${COMPOSE_DIR}."
    exit 1
fi

# 3. Ollama 서비스 정의 여부 확인
if docker compose config --services 2>/dev/null | grep -qx "ollama"; then
    echo "  [OK] 'ollama' service is defined in Docker Compose."
else
    echo "  [FATAL] 'ollama' service is not defined in the Docker Compose stack."
    exit 1
fi

# 4. Ollama 서비스 기동 보장
echo "  [INFO] Ensuring Ollama service is running..."
docker compose up -d ollama > /dev/null
echo "  [OK] Ollama service is up."

# 5. Ollama API 기동 상태 확인
echo "  [INFO] Checking if Ollama API is reachable..."
if ! curl -s -f -o /dev/null "${OLLAMA_HOST}/api/tags"; then
    echo "  [FATAL] Ollama API is not reachable at ${OLLAMA_HOST}."
    echo "          Please check Docker logs: docker compose logs ollama"
    exit 1
fi
echo "  [OK] Ollama API is reachable."

# 6. Llama 3.1 모델 설치/갱신 (컨테이너 내부에서 수행)
if docker compose exec -T ollama ollama list 2>/dev/null | grep -q "llama3.1"; then
    echo "  [INFO] llama3.1 model is already present. Verifying for updates..."
else
    echo "  [INFO] Pulling llama3.1 model. This may take a while depending on network speed..."
fi

docker compose exec -T ollama ollama pull llama3.1 > /dev/null
echo "  [OK] llama3.1 model is ready inside the Ollama container."

# 7. 추론 테스트 (API 기반)
echo "  [INFO] Testing Llama 3.1 inference via HTTP API..."
TEST_RESPONSE=$(
  curl -s -X POST "${OLLAMA_HOST}/api/generate"     -H "Content-Type: application/json"     -d '{
      "model": "llama3.1",
      "prompt": "Please reply with exactly the word READY.",
      "stream": false
    }'
)

if echo "${TEST_RESPONSE}" | grep -q "READY"; then
    echo "  [OK] Llama 3.1 responded successfully."
else
    echo "  [WARNING] Unexpected inference response from llama3.1."
    echo "            Response payload: ${TEST_RESPONSE}"
fi

# 8. 설치된 버전/상태 출력
echo "  [INFO] Installed Ollama Runtime Status:"
docker compose exec -T ollama ollama --version | awk '{print "    - "$0}'
docker compose exec -T ollama ollama list | awk 'NR==1 || /llama3.1/ {print "    - "$0}'

echo "==> [PASS] Dockerized Ollama configuration and model verification completed."

#!/usr/bin/env bash
# ==============================================================================
# Script: 21_prepare_compose_stack_mac.sh
# Purpose: Mac mini 엣지 허브의 Docker Compose 스택 실행을 위한 환경 및 볼륨 준비
# ==============================================================================

set -euo pipefail

echo "=========================================================================="
echo "[Phase 3] Mac mini: Preparing Docker Compose Stack (Idempotent Setup)"
echo "=========================================================================="

# 1. 환경 변수 및 기본 경로 설정
PROJECT_ROOT=$(pwd)
COMPOSE_DIR="${PROJECT_ROOT}/compose"
TEMPLATE_FILE="${PROJECT_ROOT}/templates/docker-compose.template.yml"
TARGET_COMPOSE_FILE="${COMPOSE_DIR}/docker-compose.yml"

# 2. 필수 볼륨 디렉터리 생성 (멱등성 보장)
echo "[INFO] Creating Docker volume directories..."
VOLUMES=(
  "volumes/homeassistant/config"
  "volumes/mosquitto/config"
  "volumes/mosquitto/data"
  "volumes/mosquitto/log"
  "volumes/ollama/data"
  "volumes/sqlite/db"
)

for vol in "${VOLUMES[@]}"; do
  mkdir -p "${COMPOSE_DIR}/${vol}"
  echo "  -> Created: ${COMPOSE_DIR}/${vol}"
done

# 3. 디렉터리 권한 설정 (단일 작성자 및 보안 격리 원칙)
echo "[INFO] Setting up strict permissions for volumes..."
# Mosquitto (일반적으로 UID/GID 1883 사용)
sudo chown -R 1883:1883 "${COMPOSE_DIR}/volumes/mosquitto"
# SQLite DB 단일 작성자(Single-writer) 권한 강제 (외부 개입 차단)
chmod 700 "${COMPOSE_DIR}/volumes/sqlite/db"

# 4. Compose 템플릿 복사 및 배포 준비
echo "[INFO] Deploying docker-compose.yml from template..."
if [ -f "${TEMPLATE_FILE}" ]; then
  cp "${TEMPLATE_FILE}" "${TARGET_COMPOSE_FILE}"
  echo "  -> Successfully copied docker-compose.yml"
else
  echo "[ERROR] Template file not found at: ${TEMPLATE_FILE}"
  exit 1
fi

echo "=========================================================================="
echo "[SUCCESS] Docker Compose stack preparation completed on Mac mini."
echo "          Next step: run 30_setup_python_venv_mac.sh or deploy .env files."
echo "=========================================================================="
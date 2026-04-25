#!/usr/bin/env bash
# ==============================================================================
# Script: 20_configure_mosquitto.sh
# Purpose: Configure Mosquitto MQTT Broker and apply Trust Boundary rules (Phase 4)
# ==============================================================================
set -euo pipefail

echo "==> [20_configure_mosquitto] Configuring Mosquitto MQTT Broker..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
MOSQ_CONFIG_DIR="${WORKSPACE_DIR}/docker/volumes/mosquitto/config"
TARGET_FILE="${MOSQ_CONFIG_DIR}/mosquitto.conf"

echo "  [INFO] Ensuring target configuration directory exists at ${MOSQ_CONFIG_DIR}..."
mkdir -p "${MOSQ_CONFIG_DIR}"

# 1. 덮어쓰기 방지: 파일이 이미 존재하면 생성 생략 (사용자 커스텀/보안 설정 보존)
if [ ! -f "${TARGET_FILE}" ]; then
    echo "  [INFO] Generating default mosquitto.conf with LAN-only Trust Boundary..."

    # [SECURITY DEFAULT EXPLANATION]
    # listener 1883 0.0.0.0은 로컬 네트워크(LAN) 상에 있는 Raspberry Pi 5 시뮬레이션 노드가
    # Mac mini 브로커에 접속할 수 있도록 허용하기 위한 필수 설정입니다.
    # WARNING: 이 설정은 LAN-only Trust Boundary를 형성하므로, 인터넷 기원(WAN)의
    # 인바운드 트래픽은 반드시 하드웨어 라우터 방화벽이나 macOS 방화벽으로 차단되어야 합니다.
    # NOTE: allow_anonymous true is for controlled LAN lab setup only.
    # Production or shared-network deployments should replace this with password_file
    # and explicit ACL rules aligned with common/mqtt publisher/subscriber contracts.
    cat <<EOF > "${TARGET_FILE}"
listener 1883 0.0.0.0
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
EOF
    echo "  [OK] mosquitto.conf deployed successfully."
else
    echo "  [INFO] mosquitto.conf already exists. Skipping overwrite to preserve user settings."
fi

# 1-1. 가독성과 운영 일관성을 위해 파일 접근 권한을 명시한다.
chmod 644 "${TARGET_FILE}"
echo "  [INFO] Ensured mosquitto.conf has readable file permissions (644)."

# 2. Deployment mode-dependent restart (Compose 파일 및 서비스 정밀 확인)
echo "  [INFO] Applying changes by restarting Mosquitto container..."
if [ -d "${WORKSPACE_DIR}/docker" ]; then
    cd "${WORKSPACE_DIR}/docker"

    # 2-1. Docker Compose 공식 지원 파일명 4종 포괄적 확인
    if [ -f "docker-compose.yml" ] || [ -f "docker-compose.yaml" ] || [ -f "compose.yml" ] || [ -f "compose.yaml" ]; then
        # 2-2. 서비스가 compose 파일에 정의 및 생성되어 있는지 정밀 일치 검사 (-qx)
        if docker compose ps -a --services 2>/dev/null | grep -qx "mosquitto"; then
            docker compose restart mosquitto > /dev/null 2>&1
            echo "  [OK] Mosquitto container restarted successfully."
        else
            echo "  [WARNING] 'mosquitto' service is not found or not created yet. Configuration will apply on first start."
        fi
    else
        echo "  [WARNING] docker-compose stack file not found in ${WORKSPACE_DIR}/docker. Skipping restart."
    fi
else
    echo "  [WARNING] Docker workspace not found at ${WORKSPACE_DIR}/docker. Skipping restart."
fi

echo "==> [PASS] Mosquitto configuration applied."

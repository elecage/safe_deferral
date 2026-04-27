#!/usr/bin/env bash
# ==============================================================================
# Script: 30_configure_time_sync_rpi.sh
# Purpose: Configure Chrony for LAN-only time sync with Mac mini
# ==============================================================================
set -euo pipefail

echo "==> [30_configure_time_sync_rpi] Configuring Chrony for LAN-only Time Sync..."

WORKSPACE_DIR="${HOME}/smarthome_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"
LOG_DIR="${WORKSPACE_DIR}/logs"
SYNC_LOG="${LOG_DIR}/time_sync.log"

mkdir -p "${LOG_DIR}"

# 1. 환경변수 파일 검증 및 로드
if [ -f "${ENV_FILE}" ]; then
    source "${ENV_FILE}"
else
    echo "  [FATAL] ${ENV_FILE} not found."
    echo "          Please run 10_write_env_files_rpi.sh first."
    exit 1
fi

if [ -z "${MAC_MINI_HOST:-}" ]; then
    echo "  [FATAL] MAC_MINI_HOST is missing in ${ENV_FILE}."
    exit 1
fi

if [ "${MAC_MINI_HOST}" = "192.168.1.100" ]; then
    echo "  [FATAL] MAC_MINI_HOST still uses the placeholder IP 192.168.1.100."
    echo "          Set the real Mac mini LAN hostname or IP in ${ENV_FILE}."
    exit 1
fi

# 2. Chrony 명령어 존재 여부 확인 (Fail-fast)
if ! command -v chronyc >/dev/null 2>&1; then
    echo "  [FATAL] 'chronyc' command is not available."
    echo "          Please ensure chrony is installed on the system."
    exit 1
fi

CHRONY_CONF="/etc/chrony/chrony.conf"

echo "  [INFO] Configuring this experiment RPi to sync strictly with Mac mini (${MAC_MINI_HOST})."
echo "  [WARNING] This will replace ${CHRONY_CONF} after creating a timestamped backup."

# 3. 덮어쓰기 방지를 위해 타임스탬프를 포함한 누적 백업 파일 생성
if [ -f "${CHRONY_CONF}" ]; then
    BACKUP_FILE="${CHRONY_CONF}.$(date +%Y%m%d_%H%M%S).bak"
    sudo cp "${CHRONY_CONF}" "${BACKUP_FILE}"
    echo "  [OK] Original chrony configuration safely backed up to ${BACKUP_FILE}"
fi

TEMP_CHRONY_CONF="$(mktemp)"
cat > "${TEMP_CHRONY_CONF}" <<EOF
server ${MAC_MINI_HOST} iburst minpoll 2 maxpoll 4
makestep 1 3
rtcsync
logdir /var/log/chrony
EOF
sudo install -m 0644 "${TEMP_CHRONY_CONF}" "${CHRONY_CONF}"
rm -f "${TEMP_CHRONY_CONF}"

echo "  [INFO] Restarting chrony service and waiting for stabilization..."
sudo systemctl restart chrony

# 5. 수치 기반 Time Sync Offset 자동 검증 루프 및 로그 기록
MAX_RETRIES=5
SYNC_SUCCESS=false
TARGET_BOUND_MS="${TIME_SYNC_TARGET_BOUND_MS:-15}"

for i in $(seq 1 ${MAX_RETRIES}); do
    sleep 3
    # chronyc -c tracking: 4번째 필드는 System time offset, 5번째 필드는 RMS offset
    TRACKING_DATA=$(chronyc -c tracking 2>/dev/null || echo "N/A")

    if [[ "${TRACKING_DATA}" == "N/A" || -z "${TRACKING_DATA}" ]]; then
        echo "  [WARNING] [Attempt $i] Could not retrieve tracking data from chrony."
        continue
    fi

    OFFSET_SEC=$(echo "${TRACKING_DATA}" | awk -F',' '{print $4}')
    RMS_OFFSET_SEC=$(echo "${TRACKING_DATA}" | awk -F',' '{print $5}')

    if [[ -z "${OFFSET_SEC}" ]]; then
         echo "  [WARNING] [Attempt $i] Offset field is empty."
         continue
    fi

    # 절댓값을 밀리초(ms)로 변환
    OFFSET_MS=$(awk -v offset="${OFFSET_SEC}" 'BEGIN { printf "%.3f", (offset < 0 ? -offset : offset) * 1000 }')
    RMS_OFFSET_MS=$(awk -v rms="${RMS_OFFSET_SEC}" 'BEGIN { printf "%.3f", (rms < 0 ? -rms : rms) * 1000 }')

    # [수정 반영] 용어를 Jitter에서 RMS offset으로 정확히 정정
    echo "  [INFO] [Attempt $i] Current Time Sync Offset: ${OFFSET_MS} ms (RMS offset: ${RMS_OFFSET_MS} ms)"

    # target bound 이내인지 수치 비교 (안전한 변수 사용)
    if awk -v off="${OFFSET_MS}" -v bound="${TARGET_BOUND_MS}" 'BEGIN { exit (off <= bound) ? 0 : 1 }'; then
        echo "  [OK] Time sync offset is within the target bound of ${TARGET_BOUND_MS} ms."

        # [수정 반영] 로그 기록 키값을 RMS_Offset으로 변경
        echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] SYNC_SUCCESS: Offset=${OFFSET_MS}ms, RMS_Offset=${RMS_OFFSET_MS}ms, Bound=${TARGET_BOUND_MS}ms, Source=${MAC_MINI_HOST}" >> "${SYNC_LOG}"

        SYNC_SUCCESS=true
        break
    fi
done

if [ "${SYNC_SUCCESS}" = false ]; then
    echo "  [FATAL] Time sync offset could not meet the target bound of ${TARGET_BOUND_MS} ms within the time limit."
    echo "          Please check network latency to Mac mini or chrony configuration."

    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] SYNC_FAILED: Last_Offset=${OFFSET_MS:-N/A}ms, Bound=${TARGET_BOUND_MS}ms" >> "${SYNC_LOG}"
    exit 1
fi

echo "==> [PASS] Time synchronization configured and verified successfully against Mac mini."

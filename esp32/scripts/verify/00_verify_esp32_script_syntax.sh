#!/usr/bin/env bash
# ==============================================================================
# Script: 00_verify_esp32_script_syntax.sh
# Purpose: Verify Bash syntax and basic formatting invariants for ESP32 scripts
# ==============================================================================
set -euo pipefail

echo "==> [00_verify_esp32_script_syntax] Verifying ESP32 Bash script syntax..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ESP32_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SCRIPTS_ROOT="${ESP32_ROOT}/scripts"

if [ ! -d "${SCRIPTS_ROOT}" ]; then
    echo "  [FATAL] ESP32 scripts directory not found: ${SCRIPTS_ROOT}"
    exit 1
fi

mapfile -t SCRIPT_FILES < <(find "${SCRIPTS_ROOT}" -type f -name "*.sh" | sort)

if [ "${#SCRIPT_FILES[@]}" -eq 0 ]; then
    echo "  [FATAL] No ESP32 Bash scripts found under ${SCRIPTS_ROOT}."
    exit 1
fi

FAILURES=0

for script in "${SCRIPT_FILES[@]}"; do
    rel_path="${script#${ESP32_ROOT}/}"
    echo "  [INFO] Checking ${rel_path}..."

    first_line="$(head -n 1 "${script}")"
    if [ "${first_line}" != "#!/usr/bin/env bash" ]; then
        echo "    [FATAL] Missing or invalid Bash shebang: ${rel_path}"
        FAILURES=1
    fi

    if grep -Iq . "${script}" && grep -q $'\r' "${script}"; then
        echo "    [FATAL] CRLF line endings detected: ${rel_path}"
        FAILURES=1
    fi

    malformed_heredoc_log="/tmp/esp32_malformed_heredoc_$$.txt"
    if grep -nE '^cat < [^<]' "${script}" > "${malformed_heredoc_log}"; then
        echo "    [FATAL] Possible malformed heredoc pattern found: ${rel_path}"
        sed 's/^/      /' "${malformed_heredoc_log}"
        FAILURES=1
    fi
    rm -f "${malformed_heredoc_log}"

    if ! bash -n "${script}"; then
        echo "    [FATAL] Bash syntax check failed: ${rel_path}"
        FAILURES=1
    else
        echo "    [OK] Syntax valid."
    fi
done

if [ "${FAILURES}" -ne 0 ]; then
    echo "==> [FAIL] One or more ESP32 Bash scripts failed syntax/format checks."
    exit 1
fi

echo "==> [PASS] All ESP32 Bash scripts passed syntax and formatting checks."

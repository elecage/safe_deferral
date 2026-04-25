#!/usr/bin/env bash
# ==============================================================================
# Script: 00_verify_rpi_script_syntax.sh
# Purpose: Verify Bash syntax and basic formatting invariants for RPi scripts
# ==============================================================================
set -euo pipefail

echo "==> [00_verify_rpi_script_syntax] Verifying RPi shell script syntax..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RPI_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SCRIPTS_ROOT="${RPI_ROOT}/scripts"

if [ ! -d "${SCRIPTS_ROOT}" ]; then
    echo "  [FATAL] RPi scripts directory not found: ${SCRIPTS_ROOT}"
    exit 1
fi

mapfile -t SCRIPT_FILES < <(find "${SCRIPTS_ROOT}" -type f -name "*.sh" | sort)

if [ "${#SCRIPT_FILES[@]}" -eq 0 ]; then
    echo "  [FATAL] No RPi shell scripts found under ${SCRIPTS_ROOT}."
    exit 1
fi

FAILURES=0

for script in "${SCRIPT_FILES[@]}"; do
    rel_path="${script#${RPI_ROOT}/}"
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

    if grep -nE '^cat < [^<]' "${script}" >/tmp/rpi_malformed_heredoc_$$.txt; then
        echo "    [FATAL] Possible malformed heredoc pattern found: ${rel_path}"
        sed 's/^/      /' /tmp/rpi_malformed_heredoc_$$.txt
        FAILURES=1
    fi
    rm -f /tmp/rpi_malformed_heredoc_$$.txt

    if ! bash -n "${script}"; then
        echo "    [FATAL] Bash syntax check failed: ${rel_path}"
        FAILURES=1
    else
        echo "    [OK] Syntax valid."
    fi
done

if [ "${FAILURES}" -ne 0 ]; then
    echo "==> [FAIL] One or more RPi shell scripts failed syntax/format checks."
    exit 1
fi

echo "==> [PASS] All RPi shell scripts passed syntax and formatting checks."

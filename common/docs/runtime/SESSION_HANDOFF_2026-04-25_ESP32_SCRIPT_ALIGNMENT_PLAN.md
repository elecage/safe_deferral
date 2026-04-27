# SESSION_HANDOFF_2026-04-25_ESP32_SCRIPT_ALIGNMENT_PLAN.md

Date: 2026-04-25
Scope: `esp32/scripts/install`, `esp32/scripts/configure`, `esp32/scripts/verify`
Status: Planning baseline before implementation

## 1. Purpose

This document freezes the planned update sequence for ESP32 development-environment scripts before implementation.

The ESP32 side must remain a bounded physical-node layer. ESP32 scripts may install ESP-IDF, configure local build workspaces, prepare sample projects, and verify build readiness. They must not introduce policy authority, validator authority, caregiver-approval authority, LLM inference authority, or autonomous doorlock authorization.

Mac mini remains the safety-critical operational edge hub. Raspberry Pi remains the simulation/verification/governance-support host. ESP32 remains a bounded physical node.

## 2. Current reviewed script set

The current reviewed ESP32 script set includes:

### install/linux

- `esp32/scripts/install/linux/00_preflight_esp32_linux.sh`
- `esp32/scripts/install/linux/10_install_prereqs_esp32_linux.sh`
- `esp32/scripts/install/linux/20_install_esp_idf_esp32_linux.sh`

### install/mac

- `esp32/scripts/install/mac/00_preflight_esp32_mac.sh`
- `esp32/scripts/install/mac/10_install_prereqs_esp32_mac.sh`
- `esp32/scripts/install/mac/20_install_esp_idf_esp32_mac.sh`

### install/windows

- `esp32/scripts/install/windows/00_preflight_esp32_windows.ps1`
- `esp32/scripts/install/windows/10_install_prereqs_esp32_windows.ps1`
- `esp32/scripts/install/windows/20_install_esp_idf_esp32_windows.ps1`

### configure

- `esp32/scripts/configure/10_write_env_files_esp32.sh`
- `esp32/scripts/configure/10_write_env_files_esp32_windows.ps1`
- `esp32/scripts/configure/20_prepare_idf_workspace_esp32.sh`
- `esp32/scripts/configure/20_prepare_idf_workspace_esp32_windows.ps1`
- `esp32/scripts/configure/30_prepare_sample_project_esp32.sh`
- `esp32/scripts/configure/30_prepare_sample_project_esp32_windows.ps1`
- `esp32/scripts/configure/40_prepare_managed_components_esp32.sh`
- `esp32/scripts/configure/40_prepare_managed_components_esp32_windows.ps1`
- `esp32/scripts/configure/README.md`

### verify

- `esp32/scripts/verify/00_verify_esp32_script_syntax.sh`
- `esp32/scripts/verify/00_verify_esp32_powershell_syntax.ps1`
- `esp32/scripts/verify/10_verify_idf_cli_esp32.sh`
- `esp32/scripts/verify/10_verify_idf_cli_esp32_windows.ps1`
- `esp32/scripts/verify/20_verify_toolchain_target_esp32.sh`
- `esp32/scripts/verify/20_verify_toolchain_target_esp32_windows.ps1`
- `esp32/scripts/verify/30_verify_component_resolution_esp32.sh`
- `esp32/scripts/verify/30_verify_component_resolution_esp32_windows.ps1`
- `esp32/scripts/verify/40_verify_sample_build_esp32.sh`
- `esp32/scripts/verify/40_verify_sample_build_esp32_windows.ps1`
- `esp32/scripts/verify/README.md`

### top-level

- `esp32/scripts/README.md`

## 3. Non-negotiable ESP32 interpretation

1. ESP32 is a bounded physical node layer.
2. ESP32 is not a policy router.
3. ESP32 is not a deterministic validator.
4. ESP32 is not a caregiver-approval authority.
5. ESP32 is not an LLM inference node.
6. ESP32 is not an autonomous doorlock authorization node.
7. ESP32 firmware and environment scripts must not silently create direct doorlock authority.
8. ESP32 may eventually receive bounded commands from the authorized operational pipeline, but it must not decide policy or safety class on its own.

## 4. Recommended current execution order

The reviewed scripts imply the following practical execution order.

### macOS

```bash
cd /path/to/safe_deferral

bash esp32/scripts/install/mac/00_preflight_esp32_mac.sh
bash esp32/scripts/install/mac/10_install_prereqs_esp32_mac.sh
bash esp32/scripts/install/mac/20_install_esp_idf_esp32_mac.sh

bash esp32/scripts/configure/10_write_env_files_esp32.sh
# edit ~/esp32_workspace/.env

bash esp32/scripts/configure/20_prepare_idf_workspace_esp32.sh
bash esp32/scripts/configure/30_prepare_sample_project_esp32.sh
bash esp32/scripts/configure/40_prepare_managed_components_esp32.sh

bash esp32/scripts/verify/10_verify_idf_cli_esp32.sh
bash esp32/scripts/verify/20_verify_toolchain_target_esp32.sh
bash esp32/scripts/verify/30_verify_component_resolution_esp32.sh
bash esp32/scripts/verify/40_verify_sample_build_esp32.sh
```

### Linux

```bash
cd /path/to/safe_deferral

bash esp32/scripts/install/linux/00_preflight_esp32_linux.sh
bash esp32/scripts/install/linux/10_install_prereqs_esp32_linux.sh
bash esp32/scripts/install/linux/20_install_esp_idf_esp32_linux.sh

bash esp32/scripts/configure/10_write_env_files_esp32.sh
# edit ~/esp32_workspace/.env

bash esp32/scripts/configure/20_prepare_idf_workspace_esp32.sh
bash esp32/scripts/configure/30_prepare_sample_project_esp32.sh
bash esp32/scripts/configure/40_prepare_managed_components_esp32.sh

bash esp32/scripts/verify/10_verify_idf_cli_esp32.sh
bash esp32/scripts/verify/20_verify_toolchain_target_esp32.sh
bash esp32/scripts/verify/30_verify_component_resolution_esp32.sh
bash esp32/scripts/verify/40_verify_sample_build_esp32.sh
```

### Windows PowerShell

```powershell
cd C:\path\to\safe_deferral

.\esp32\scripts\install\windows\00_preflight_esp32_windows.ps1
.\esp32\scripts\install\windows\10_install_prereqs_esp32_windows.ps1
.\esp32\scripts\install\windows\20_install_esp_idf_esp32_windows.ps1

.\esp32\scripts\configure\10_write_env_files_esp32_windows.ps1
# edit $HOME\esp32_workspace\.env.ps1

.\esp32\scripts\configure\20_prepare_idf_workspace_esp32_windows.ps1
.\esp32\scripts\configure\30_prepare_sample_project_esp32_windows.ps1
.\esp32\scripts\configure\40_prepare_managed_components_esp32_windows.ps1

.\esp32\scripts\verify\10_verify_idf_cli_esp32_windows.ps1
.\esp32\scripts\verify\20_verify_toolchain_target_esp32_windows.ps1
.\esp32\scripts\verify\30_verify_component_resolution_esp32_windows.ps1
.\esp32\scripts\verify\40_verify_sample_build_esp32_windows.ps1
```

Important: configure execution places sample project preparation before managed-component placeholder preparation, because `30_prepare_sample_project_esp32.*` deletes and re-copies the sample project directory.

## 5. Phase E1 — ESP32 README refresh

Targets:

- `esp32/scripts/README.md`
- `esp32/scripts/configure/README.md`
- `esp32/scripts/verify/README.md`

Planned changes:

- Replace outdated scaffold wording.
- List current install/configure/verify scripts.
- Document macOS, Linux, and Windows flows.
- Explicitly document the current configure order:
  - `20_prepare_idf_workspace`
  - `30_prepare_sample_project`
  - `40_prepare_managed_components`
- Explain POSIX `.env` versus Windows `.env.ps1`.
- State that ESP32 is a bounded physical node and must not become an authority node.

Completion criterion:

- README files match the current implemented script set and safe-deferral role boundary.

## 6. Phase E2 — ESP32 script syntax verification

Targets:

- New: `esp32/scripts/verify/00_verify_esp32_script_syntax.sh`
- New: `esp32/scripts/verify/00_verify_esp32_powershell_syntax.ps1`

Planned Bash checks:

- Find all ESP32 `.sh` files under `esp32/scripts`.
- Verify Bash shebang.
- Detect CRLF line endings.
- Detect malformed `cat <` heredoc patterns.
- Run `bash -n` on every Bash script.

Planned PowerShell checks:

- Find all ESP32 `.ps1` files under `esp32/scripts`.
- Parse each file using PowerShell parser APIs.
- Fail on syntax errors.

Completion criterion:

- ESP32 Bash and PowerShell scripts have reproducible static syntax verification.

## 7. Phase E3 — ESP-IDF install scripts read environment files

Targets:

- `esp32/scripts/install/linux/20_install_esp_idf_esp32_linux.sh`
- `esp32/scripts/install/mac/20_install_esp_idf_esp32_mac.sh`
- `esp32/scripts/install/windows/20_install_esp_idf_esp32_windows.ps1`

Problem:

- POSIX configure writes `~/esp32_workspace/.env`.
- Windows configure writes `~/esp32_workspace/.env.ps1`.
- Current ESP-IDF install scripts mostly read process environment variables, not these generated files.

Planned POSIX addition:

```bash
WORKSPACE_DIR="${HOME}/esp32_workspace"
ENV_FILE="${WORKSPACE_DIR}/.env"
if [ -f "${ENV_FILE}" ]; then
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
fi
```

Planned Windows addition:

```powershell
$EnvFile = Join-Path $HOME 'esp32_workspace\.env.ps1'
if (Test-Path $EnvFile) {
    . $EnvFile
}
```

Completion criterion:

- `ESP_ROOT`, `IDF_PATH`, `IDF_TOOLS_PATH`, and `ESP_IDF_GIT_REF` can be set through the generated env files before ESP-IDF installation.

## 8. Phase E4 — ESP32 bounded-node authority flags

Targets:

- `esp32/scripts/configure/10_write_env_files_esp32.sh`
- `esp32/scripts/configure/10_write_env_files_esp32_windows.ps1`

Planned POSIX env additions:

```env
ESP32_NODE_ROLE=bounded_physical_node
ALLOW_ESP32_POLICY_AUTHORITY=false
ALLOW_ESP32_VALIDATOR_AUTHORITY=false
ALLOW_ESP32_LLM_INFERENCE=false
ALLOW_ESP32_CAREGIVER_APPROVAL_AUTHORITY=false
ALLOW_ESP32_DIRECT_DOORLOCK_AUTHORITY=false
```

Planned Windows `.env.ps1` additions:

```powershell
$ESP32_NODE_ROLE = 'bounded_physical_node'
$ALLOW_ESP32_POLICY_AUTHORITY = 'false'
$ALLOW_ESP32_VALIDATOR_AUTHORITY = 'false'
$ALLOW_ESP32_LLM_INFERENCE = 'false'
$ALLOW_ESP32_CAREGIVER_APPROVAL_AUTHORITY = 'false'
$ALLOW_ESP32_DIRECT_DOORLOCK_AUTHORITY = 'false'
```

Completion criterion:

- ESP32 environment files explicitly preserve the bounded-node, non-authoritative role boundary.

## 9. Phase E5 — Managed-component/sample-project ordering cleanup

Targets:

- README files.
- Configure script filenames:
  - `30_prepare_sample_project_esp32.*`
  - `40_prepare_managed_components_esp32.*`

Problem:

- `30_prepare_sample_project_esp32.*` deletes and re-copies the sample project directory.
- `40_prepare_managed_components_esp32.*` creates `idf_component.yml` under the sample project.
- Therefore, sample-project preparation must run before managed-component placeholder preparation.

Planned fix:

- Keep execution order as `20 -> 30 -> 40`.
- Keep filenames aligned with that order so docs and scripts do not need an exception note.

Completion criterion:

- The documented configure flow no longer deletes outputs created by the previous step.

## 10. Phase E6 — Linux serial permission check

Target:

- `esp32/scripts/install/linux/10_install_prereqs_esp32_linux.sh`

Planned addition:

- Check whether the current user belongs to a likely serial-port access group, such as:
  - `dialout`
  - `uucp`
  - `tty`
  - `plugdev`
- If not, print a warning and suggested command, for example:

```bash
sudo usermod -aG dialout "$USER"
# Then log out and back in.
```

Completion criterion:

- Linux users get early visibility into serial flash/monitor permission issues.

## 11. Phase E7 — Sample build artifact verification generalization

Targets:

- `esp32/scripts/verify/40_verify_sample_build_esp32.sh`
- `esp32/scripts/verify/40_verify_sample_build_esp32_windows.ps1`

Problem:

- Current verification expects:
  - `build/hello_world.bin`
  - `build/hello_world.elf`
- This is valid for the current ESP-IDF hello_world sample but too rigid for future `minimal_node` or bounded-node firmware.

Planned changes:

- Add `EXPECTED_APP_NAME` or `ESP32_EXPECTED_APP_NAME` environment variable.
- Default to `hello_world`.
- Verify:
  - `build/${EXPECTED_APP_NAME}.bin`
  - `build/${EXPECTED_APP_NAME}.elf`

Completion criterion:

- Current hello_world build remains supported.
- Future firmware sample names can be verified without editing the script.

## 12. Suggested staged commits

1. `docs(esp32): refresh script README files`
2. `verify(esp32): add script syntax checks`
3. `install(esp32): load env files during ESP-IDF install`
4. `config(esp32): add bounded node authority flags`
5. `docs(esp32): document sample and component ordering`
6. `install(esp32): warn on Linux serial permissions`
7. `verify(esp32): generalize sample build artifact checks`

## 13. Final completion checklist

- [ ] ESP32 README files reflect current implementation.
- [ ] POSIX Bash scripts pass static syntax verification.
- [ ] PowerShell scripts pass static syntax verification.
- [ ] ESP-IDF install scripts can load generated env files.
- [ ] ESP32 env files include bounded-node authority flags.
- [ ] Configure execution order avoids deleting managed-component placeholder output.
- [ ] Linux users are warned about serial permission group membership.
- [ ] Sample build verifier supports configurable expected app name.
- [ ] ESP32 scripts do not create policy, validator, caregiver approval, LLM inference, or doorlock authorization authority.

## 14. Frozen decision

This plan freezes the intended ESP32 script-alignment strategy before implementation. The next work item should begin with Phase E1, followed by E2 through E7 in staged commits.

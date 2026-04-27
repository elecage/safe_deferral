# SESSION_HANDOFF_2026-04-25_ESP32_SCRIPT_ALIGNMENT_UPDATE.md

Date: 2026-04-25
Scope: `esp32/scripts/install`, `esp32/scripts/configure`, `esp32/scripts/verify`
Status: Phase E1 through Phase E7 implemented on `main`

## 1. Purpose

This addendum records the completed ESP32 script-alignment work.

The ESP32 layer is now documented and partially guarded as a bounded physical-node development environment. The scripts standardize ESP-IDF installation, workspace preparation, sample project preparation, and build verification across Linux, macOS, and Windows.

This update does not grant ESP32 any policy, validator, caregiver approval, LLM inference, or autonomous doorlock authority.

## 2. Non-negotiable ESP32 interpretation

1. ESP32 is a bounded physical node layer.
2. ESP32 is not a policy router.
3. ESP32 is not a deterministic validator.
4. ESP32 is not a caregiver-approval authority.
5. ESP32 is not an LLM inference node.
6. ESP32 is not an autonomous doorlock authorization node.
7. ESP32 environment scripts must not silently create direct actuator or doorlock authority.
8. Future ESP32 firmware may execute bounded physical commands only when those commands are produced by the authorized operational pipeline.

Mac mini remains the safety-critical operational edge hub. Raspberry Pi remains the simulation, verification, and non-authoritative governance-support host.

## 3. Completed commits

The following staged commits were applied to `main` for ESP32 script alignment:

### Planning and index

1. `3764b398715bf2a7fc36acc141558bbbc28ed02a` — `docs: add ESP32 script alignment plan`
2. `06323dd7239be7f61e3515c7983e18ad4cf55f08` — `docs: index ESP32 script alignment plan`

### Phase E1 — README refresh

3. `d5041f7db5edbdd354e78eb68378b2cb137dfddb` — `docs(esp32): refresh script README files`
4. `5edc33c3d2f1bf2c11ab952fc7a1cd2036acae28` — `docs(esp32): refresh configure README`
5. `8e91d16bfe2b161f6d5f1df19228abde9bba193c` — `docs(esp32): refresh verify README`

### Phase E2 — Static syntax verification

6. `ec54aceeee395f3b80f1bb84d7854b48bdcdeb66` — `verify(esp32): add bash script syntax checks`
7. `3bd769e3e84976a9cde075127b983c4e93febdcc` — `verify(esp32): add powershell script syntax checks`

### Phase E3 — ESP-IDF install scripts load env files

8. `f8f6326e5c50ff6e6578abdf26ef78c8d6210126` — `install(esp32): load env file during Linux IDF install`
9. `35ae293d643f85f6f61c79ffaa44c69d1a1de60f` — `install(esp32): load env file during macOS IDF install`
10. `b20d17a8c8306cc16b8f3640b92a33d1e966e763` — `install(esp32): load env file during Windows IDF install`

### Phase E4 — Bounded-node authority flags

11. `bd8a238ae6ef0ee3abd3a01698e25ac7069379d2` — `config(esp32): add bounded node authority flags`
12. `cddd2ae2993b0e2df3ed95af51a879a5da19021d` — `config(esp32): add Windows bounded node authority flags`

### Phase E5 — Sample/component ordering guard

13. `7706db645a818784b0ac5f899d1472147e3b5c7a` — `config(esp32): enforce sample before component prep`
14. `0d867fefe0c6f53cb26eb8a127f236abb6550b27` — `config(esp32): enforce Windows sample before component prep`

### Phase E6 — Linux serial permissions

15. `82112edb43eb1c7a0fcbc73e66d14bf6a63e73e5` — `install(esp32): warn on Linux serial permissions`

### Phase E7 — Sample build artifact generalization

16. `d0aa61ec0906acc17e96133681c983461b64927f` — `verify(esp32): generalize sample build artifact checks`
17. `d7548d86630f5968bbe1dc3142bc52075bcd0553` — `verify(esp32): generalize Windows sample build artifact checks`

The original planning document remains available at:

- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_ESP32_SCRIPT_ALIGNMENT_PLAN.md`

## 4. Updated script responsibilities

### `esp32/scripts/README.md`

Updated to reflect the current implemented script set and to document the ESP32 bounded physical-node role.

Key points:

- install/configure/verify scripts now exist for Linux, macOS, and Windows.
- completion requires `40_verify_sample_build_esp32.*` to pass.
- ESP32 remains non-authoritative.

### `esp32/scripts/configure/README.md`

Updated to reflect the implemented configure scripts and the required execution order:

```text
10_write_env_files
20_prepare_idf_workspace
30_prepare_sample_project
40_prepare_managed_components
```

This order is required because `30_prepare_sample_project_esp32.*` removes and re-copies the sample project directory, while `40_prepare_managed_components_esp32.*` writes `idf_component.yml` under that project.

### `esp32/scripts/verify/README.md`

Updated to define the verify stages:

1. `10_verify_idf_cli_esp32.*`
2. `20_verify_toolchain_target_esp32.*`
3. `30_verify_component_resolution_esp32.*`
4. `40_verify_sample_build_esp32.*`

The final success criterion is a successful sample build.

### `esp32/scripts/verify/00_verify_esp32_script_syntax.sh`

New Bash syntax verifier.

Checks:

- all `.sh` files under `esp32/scripts`,
- Bash shebang,
- CRLF line endings,
- malformed `cat <` heredoc patterns,
- `bash -n` syntax.

### `esp32/scripts/verify/00_verify_esp32_powershell_syntax.ps1`

New PowerShell syntax verifier.

Checks:

- all `.ps1` files under `esp32/scripts`,
- parser-based PowerShell syntax errors,
- line/column reporting for parse failures.

### `esp32/scripts/install/linux/20_install_esp_idf_esp32_linux.sh`

Updated to load:

```text
~/esp32_workspace/.env
```

before resolving:

- `ESP_ROOT`
- `IDF_PATH`
- `IDF_TOOLS_PATH`
- `ESP_IDF_GIT_REF`

If `.env` does not exist, built-in defaults are used.

### `esp32/scripts/install/mac/20_install_esp_idf_esp32_mac.sh`

Same behavior as the Linux ESP-IDF installer, but for macOS.

### `esp32/scripts/install/windows/20_install_esp_idf_esp32_windows.ps1`

Updated to load:

```text
$HOME\esp32_workspace\.env.ps1
```

before resolving:

- `$ESP_ROOT`
- `$IDF_PATH`
- `$IDF_TOOLS_PATH`
- `$ESP_IDF_GIT_REF`

Resolution order:

```text
.env.ps1 variable > process environment variable > built-in default
```

### `esp32/scripts/configure/10_write_env_files_esp32.sh`

Updated to append bounded-node authority flags:

```env
ESP32_NODE_ROLE=bounded_physical_node
ALLOW_ESP32_POLICY_AUTHORITY=false
ALLOW_ESP32_VALIDATOR_AUTHORITY=false
ALLOW_ESP32_LLM_INFERENCE=false
ALLOW_ESP32_CAREGIVER_APPROVAL_AUTHORITY=false
ALLOW_ESP32_DIRECT_DOORLOCK_AUTHORITY=false
```

Existing keys are preserved and not overwritten.

### `esp32/scripts/configure/10_write_env_files_esp32_windows.ps1`

Updated to append Windows `.env.ps1` equivalents:

```powershell
$ESP32_NODE_ROLE = 'bounded_physical_node'
$ALLOW_ESP32_POLICY_AUTHORITY = 'false'
$ALLOW_ESP32_VALIDATOR_AUTHORITY = 'false'
$ALLOW_ESP32_LLM_INFERENCE = 'false'
$ALLOW_ESP32_CAREGIVER_APPROVAL_AUTHORITY = 'false'
$ALLOW_ESP32_DIRECT_DOORLOCK_AUTHORITY = 'false'
```

Existing keys are preserved and not overwritten.

### `esp32/scripts/configure/40_prepare_managed_components_esp32.sh`

Updated to fail if the sample project has not already been prepared.

It now requires:

- sample project directory exists,
- `CMakeLists.txt` exists,
- `main/` directory exists.

It no longer silently creates an empty sample project directory.

### `esp32/scripts/configure/40_prepare_managed_components_esp32_windows.ps1`

Windows equivalent of the same ordering guard.

### `esp32/scripts/install/linux/10_install_prereqs_esp32_linux.sh`

Updated to warn if the current user may not have serial-port access for ESP32 flash/monitor.

Checks membership in likely serial groups:

- `dialout`
- `uucp`
- `tty`
- `plugdev`

Suggested commands:

```bash
sudo usermod -aG dialout "$USER"   # apt/dnf-family default suggestion
sudo usermod -aG uucp "$USER"      # pacman-family default suggestion
```

The user must log out and back in after group changes.

### `esp32/scripts/verify/40_verify_sample_build_esp32.sh`

Updated to use configurable expected artifact names.

Resolution order:

```text
ESP32_EXPECTED_APP_NAME > EXPECTED_APP_NAME > hello_world
```

Expected files:

```text
build/${EXPECTED_APP_NAME}.bin
build/${EXPECTED_APP_NAME}.elf
```

### `esp32/scripts/verify/40_verify_sample_build_esp32_windows.ps1`

Windows equivalent of configurable expected artifact checks.

## 5. Current recommended execution flow

### Linux

```bash
cd /path/to/safe_deferral

git pull

bash esp32/scripts/verify/00_verify_esp32_script_syntax.sh

bash esp32/scripts/install/linux/00_preflight_esp32_linux.sh
bash esp32/scripts/install/linux/10_install_prereqs_esp32_linux.sh
bash esp32/scripts/configure/10_write_env_files_esp32.sh
# edit ~/esp32_workspace/.env if needed, especially ESP_IDF_GIT_REF, IDF_PATH, ESPPORT
bash esp32/scripts/install/linux/20_install_esp_idf_esp32_linux.sh

bash esp32/scripts/configure/20_prepare_idf_workspace_esp32.sh
bash esp32/scripts/configure/30_prepare_sample_project_esp32.sh
bash esp32/scripts/configure/40_prepare_managed_components_esp32.sh

bash esp32/scripts/verify/10_verify_idf_cli_esp32.sh
bash esp32/scripts/verify/20_verify_toolchain_target_esp32.sh
bash esp32/scripts/verify/30_verify_component_resolution_esp32.sh
bash esp32/scripts/verify/40_verify_sample_build_esp32.sh
```

### macOS

```bash
cd /path/to/safe_deferral

git pull

bash esp32/scripts/verify/00_verify_esp32_script_syntax.sh

bash esp32/scripts/install/mac/00_preflight_esp32_mac.sh
bash esp32/scripts/install/mac/10_install_prereqs_esp32_mac.sh
bash esp32/scripts/configure/10_write_env_files_esp32.sh
# edit ~/esp32_workspace/.env if needed, especially ESP_IDF_GIT_REF, IDF_PATH, ESPPORT
bash esp32/scripts/install/mac/20_install_esp_idf_esp32_mac.sh

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

git pull

.\esp32\scripts\verify\00_verify_esp32_powershell_syntax.ps1

.\esp32\scripts\install\windows\00_preflight_esp32_windows.ps1
.\esp32\scripts\install\windows\10_install_prereqs_esp32_windows.ps1
.\esp32\scripts\configure\10_write_env_files_esp32_windows.ps1
# edit $HOME\esp32_workspace\.env.ps1 if needed, especially ESP_IDF_GIT_REF, IDF_PATH, ESPPORT
.\esp32\scripts\install\windows\20_install_esp_idf_esp32_windows.ps1

.\esp32\scripts\configure\20_prepare_idf_workspace_esp32_windows.ps1
.\esp32\scripts\configure\30_prepare_sample_project_esp32_windows.ps1
.\esp32\scripts\configure\40_prepare_managed_components_esp32_windows.ps1

.\esp32\scripts\verify\10_verify_idf_cli_esp32_windows.ps1
.\esp32\scripts\verify\20_verify_toolchain_target_esp32_windows.ps1
.\esp32\scripts\verify\30_verify_component_resolution_esp32_windows.ps1
.\esp32\scripts\verify\40_verify_sample_build_esp32_windows.ps1
```

## 6. Manual environment migration note

The env-generation scripts preserve existing keys.

If `~/esp32_workspace/.env` or `$HOME\esp32_workspace\.env.ps1` already exists, newly added keys may be appended, but stale or intentionally overridden values are not replaced.

Check bounded-node flags after running env generation.

### POSIX

```bash
grep -nE 'ESP32_NODE_ROLE|ALLOW_ESP32_' ~/esp32_workspace/.env
```

Required values:

```env
ESP32_NODE_ROLE=bounded_physical_node
ALLOW_ESP32_POLICY_AUTHORITY=false
ALLOW_ESP32_VALIDATOR_AUTHORITY=false
ALLOW_ESP32_LLM_INFERENCE=false
ALLOW_ESP32_CAREGIVER_APPROVAL_AUTHORITY=false
ALLOW_ESP32_DIRECT_DOORLOCK_AUTHORITY=false
```

### Windows PowerShell

```powershell
Select-String -Path $HOME\esp32_workspace\.env.ps1 -Pattern 'ESP32_NODE_ROLE|ALLOW_ESP32_'
```

Required values:

```powershell
$ESP32_NODE_ROLE = 'bounded_physical_node'
$ALLOW_ESP32_POLICY_AUTHORITY = 'false'
$ALLOW_ESP32_VALIDATOR_AUTHORITY = 'false'
$ALLOW_ESP32_LLM_INFERENCE = 'false'
$ALLOW_ESP32_CAREGIVER_APPROVAL_AUTHORITY = 'false'
$ALLOW_ESP32_DIRECT_DOORLOCK_AUTHORITY = 'false'
```

## 7. Known validation status

The changes were committed through the GitHub API. They have not yet been executed on physical Linux/macOS/Windows ESP32 development hosts in this session.

Required runtime validation:

- run the syntax verifier on Linux/macOS,
- run the PowerShell syntax verifier on Windows,
- run the full install/configure/verify flow on at least one POSIX host,
- optionally run the Windows flow on a Windows ESP-IDF host,
- confirm sample build artifacts are generated.

Any failure in these scripts should be treated as a real integration issue until confirmed otherwise.

## 8. Next likely work items

1. Execute the ESP32 flow on the target development host.
2. Pin `ESP_IDF_GIT_REF` to a project-approved version if reproducibility is required.
3. Add future firmware-contract verification when bounded-node firmware exists.
4. Add serial port detection/flash/monitor verification only after a physical ESP32 board is available.
5. If firmware evolves beyond `hello_world`, set `ESP32_EXPECTED_APP_NAME` accordingly.

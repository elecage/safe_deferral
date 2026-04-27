# esp32/scripts

This directory contains ESP32 development-environment scripts for installation, configuration, and verification.

The current goal is to standardize the ESP-IDF development environment before implementing production firmware.

## Role boundary

ESP32 is a **bounded physical node layer** in the `safe_deferral` project.

ESP32 scripts and firmware must not create or imply any of the following authority:

- policy routing authority,
- deterministic validator authority,
- caregiver-approval authority,
- LLM inference authority,
- autonomous doorlock authorization,
- unrestricted actuator-dispatch authority.

Mac mini remains the safety-critical operational edge hub. Raspberry Pi remains the simulation, verification, and non-authoritative governance-support host. ESP32 remains a bounded physical node.

## Directory structure

```text
esp32/scripts/
  install/
    linux/
    mac/
    windows/
  configure/
  verify/
```

## Current implementation status

### install

Linux:

- `install/linux/00_preflight_esp32_linux.sh`
- `install/linux/10_install_prereqs_esp32_linux.sh`
- `install/linux/20_install_esp_idf_esp32_linux.sh`

macOS:

- `install/mac/00_preflight_esp32_mac.sh`
- `install/mac/10_install_prereqs_esp32_mac.sh`
- `install/mac/20_install_esp_idf_esp32_mac.sh`

Windows PowerShell:

- `install/windows/00_preflight_esp32_windows.ps1`
- `install/windows/10_install_prereqs_esp32_windows.ps1`
- `install/windows/20_install_esp_idf_esp32_windows.ps1`

### configure

POSIX shell for macOS/Linux:

- `configure/10_write_env_files_esp32.sh`
- `configure/20_prepare_idf_workspace_esp32.sh`
- `configure/30_prepare_sample_project_esp32.sh`
- `configure/40_prepare_managed_components_esp32.sh`

Windows PowerShell:

- `configure/10_write_env_files_esp32_windows.ps1`
- `configure/20_prepare_idf_workspace_esp32_windows.ps1`
- `configure/30_prepare_sample_project_esp32_windows.ps1`
- `configure/40_prepare_managed_components_esp32_windows.ps1`

### verify

POSIX shell for macOS/Linux:

- `verify/00_verify_esp32_script_syntax.sh`
- `verify/10_verify_idf_cli_esp32.sh`
- `verify/20_verify_toolchain_target_esp32.sh`
- `verify/30_verify_component_resolution_esp32.sh`
- `verify/40_verify_sample_build_esp32.sh`

Windows PowerShell:

- `verify/00_verify_esp32_powershell_syntax.ps1`
- `verify/10_verify_idf_cli_esp32_windows.ps1`
- `verify/20_verify_toolchain_target_esp32_windows.ps1`
- `verify/30_verify_component_resolution_esp32_windows.ps1`
- `verify/40_verify_sample_build_esp32_windows.ps1`

## Recommended execution order

### Linux

```bash
cd /path/to/safe_deferral

bash esp32/scripts/install/linux/00_preflight_esp32_linux.sh
bash esp32/scripts/install/linux/10_install_prereqs_esp32_linux.sh
bash esp32/scripts/install/linux/20_install_esp_idf_esp32_linux.sh

bash esp32/scripts/configure/10_write_env_files_esp32.sh
# Edit ~/esp32_workspace/.env if needed.

bash esp32/scripts/configure/20_prepare_idf_workspace_esp32.sh
bash esp32/scripts/configure/30_prepare_sample_project_esp32.sh
bash esp32/scripts/configure/40_prepare_managed_components_esp32.sh

bash esp32/scripts/verify/00_verify_esp32_script_syntax.sh
bash esp32/scripts/verify/10_verify_idf_cli_esp32.sh
bash esp32/scripts/verify/20_verify_toolchain_target_esp32.sh
bash esp32/scripts/verify/30_verify_component_resolution_esp32.sh
bash esp32/scripts/verify/40_verify_sample_build_esp32.sh
```

### macOS

```bash
cd /path/to/safe_deferral

bash esp32/scripts/install/mac/00_preflight_esp32_mac.sh
bash esp32/scripts/install/mac/10_install_prereqs_esp32_mac.sh
bash esp32/scripts/install/mac/20_install_esp_idf_esp32_mac.sh

bash esp32/scripts/configure/10_write_env_files_esp32.sh
# Edit ~/esp32_workspace/.env if needed.

bash esp32/scripts/configure/20_prepare_idf_workspace_esp32.sh
bash esp32/scripts/configure/30_prepare_sample_project_esp32.sh
bash esp32/scripts/configure/40_prepare_managed_components_esp32.sh

bash esp32/scripts/verify/00_verify_esp32_script_syntax.sh
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
# Edit $HOME\esp32_workspace\.env.ps1 if needed.

.\esp32\scripts\configure\20_prepare_idf_workspace_esp32_windows.ps1
.\esp32\scripts\configure\30_prepare_sample_project_esp32_windows.ps1
.\esp32\scripts\configure\40_prepare_managed_components_esp32_windows.ps1

.\esp32\scripts\verify\00_verify_esp32_powershell_syntax.ps1
.\esp32\scripts\verify\10_verify_idf_cli_esp32_windows.ps1
.\esp32\scripts\verify\20_verify_toolchain_target_esp32_windows.ps1
.\esp32\scripts\verify\30_verify_component_resolution_esp32_windows.ps1
.\esp32\scripts\verify\40_verify_sample_build_esp32_windows.ps1
```

## Completion criterion

The ESP32 development environment is considered ready only after the sample ESP-IDF project builds successfully through:

```text
verify/40_verify_sample_build_esp32.*
```

For the current alignment plan, see:

- `common/docs/runtime/SESSION_HANDOFF_2026-04-25_ESP32_SCRIPT_ALIGNMENT_PLAN.md`

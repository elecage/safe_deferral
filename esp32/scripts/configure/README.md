# esp32/scripts/configure

This directory contains ESP32 development-environment configuration scripts.

The scripts prepare local environment variables, workspace directories, sample ESP-IDF projects, and managed-component placeholders. They do not configure policy authority, validator authority, caregiver approval, LLM inference, or doorlock authorization.

## Role boundary

ESP32 remains a bounded physical node layer. Configuration scripts may prepare build-time and workspace settings, but they must not create operational decision authority.

## POSIX scripts for macOS/Linux

- `10_write_env_files_esp32.sh`
- `20_prepare_idf_workspace_esp32.sh`
- `30_prepare_managed_components_esp32.sh`
- `40_prepare_sample_project_esp32.sh`

The POSIX environment file is:

```text
~/esp32_workspace/.env
```

## Windows PowerShell scripts

- `10_write_env_files_esp32_windows.ps1`
- `20_prepare_idf_workspace_esp32_windows.ps1`
- `30_prepare_managed_components_esp32_windows.ps1`
- `40_prepare_sample_project_esp32_windows.ps1`

The Windows environment file is:

```text
$HOME\esp32_workspace\.env.ps1
```

## Recommended configure order

Use this order on macOS/Linux:

```bash
bash esp32/scripts/configure/10_write_env_files_esp32.sh
# Edit ~/esp32_workspace/.env if needed.
bash esp32/scripts/configure/20_prepare_idf_workspace_esp32.sh
bash esp32/scripts/configure/40_prepare_sample_project_esp32.sh
bash esp32/scripts/configure/30_prepare_managed_components_esp32.sh
```

Use this order on Windows PowerShell:

```powershell
.\esp32\scripts\configure\10_write_env_files_esp32_windows.ps1
# Edit $HOME\esp32_workspace\.env.ps1 if needed.
.\esp32\scripts\configure\20_prepare_idf_workspace_esp32_windows.ps1
.\esp32\scripts\configure\40_prepare_sample_project_esp32_windows.ps1
.\esp32\scripts\configure\30_prepare_managed_components_esp32_windows.ps1
```

## Why `40` runs before `30`

The current `40_prepare_sample_project_esp32.*` scripts remove and re-copy the sample project directory from the ESP-IDF `hello_world` example.

The current `30_prepare_managed_components_esp32.*` scripts create an `idf_component.yml` placeholder under the sample project directory.

Therefore, running `30` before `40` can delete the placeholder created by `30`. Until the scripts are renumbered or refactored, use:

```text
20_prepare_idf_workspace -> 40_prepare_sample_project -> 30_prepare_managed_components
```

## Current output paths

Default POSIX paths:

```text
~/esp32_workspace/.env
~/esp32_workspace/samples/hello_idf
~/esp32_workspace/logs
~/esp32_workspace/artifacts
~/esp32_workspace/managed_components_cache
```

Default Windows paths:

```text
$HOME\esp32_workspace\.env.ps1
$HOME\esp32_workspace\samples\hello_idf
$HOME\esp32_workspace\logs
$HOME\esp32_workspace\artifacts
$HOME\esp32_workspace\managed_components_cache
```

## Completion criterion

Configuration is complete when:

1. the environment file exists,
2. the workspace directories exist,
3. the ESP-IDF `hello_world` sample is copied into the configured sample directory,
4. the managed-component placeholder exists after sample-project preparation.

Build readiness is verified separately in `esp32/scripts/verify/`.

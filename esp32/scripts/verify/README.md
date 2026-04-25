# esp32/scripts/verify

This directory contains ESP32 development-environment verification scripts.

The final success criterion is not simply installing ESP-IDF. The ESP32 development environment is considered ready only when a sample ESP-IDF project can be configured, resolved, and built successfully.

## Role boundary

Verification scripts validate toolchain and build readiness only. They must not create or imply policy authority, validator authority, caregiver-approval authority, LLM inference authority, or autonomous doorlock authorization.

## POSIX scripts for macOS/Linux

- `10_verify_idf_cli_esp32.sh`
- `20_verify_toolchain_target_esp32.sh`
- `30_verify_component_resolution_esp32.sh`
- `40_verify_sample_build_esp32.sh`

The POSIX environment file is:

```text
~/esp32_workspace/.env
```

## Windows PowerShell scripts

- `10_verify_idf_cli_esp32_windows.ps1`
- `20_verify_toolchain_target_esp32_windows.ps1`
- `30_verify_component_resolution_esp32_windows.ps1`
- `40_verify_sample_build_esp32_windows.ps1`

The Windows environment file is:

```text
$HOME\esp32_workspace\.env.ps1
```

## Recommended verification order

macOS/Linux:

```bash
bash esp32/scripts/verify/10_verify_idf_cli_esp32.sh
bash esp32/scripts/verify/20_verify_toolchain_target_esp32.sh
bash esp32/scripts/verify/30_verify_component_resolution_esp32.sh
bash esp32/scripts/verify/40_verify_sample_build_esp32.sh
```

Windows PowerShell:

```powershell
.\esp32\scripts\verify\10_verify_idf_cli_esp32_windows.ps1
.\esp32\scripts\verify\20_verify_toolchain_target_esp32_windows.ps1
.\esp32\scripts\verify\30_verify_component_resolution_esp32_windows.ps1
.\esp32\scripts\verify\40_verify_sample_build_esp32_windows.ps1
```

## Verification stages

### 10 — ESP-IDF CLI verification

Checks that the ESP-IDF environment can be loaded and that required tools are available:

- `idf.py`
- Python
- CMake
- Ninja
- esptool

### 20 — target toolchain verification

Runs:

```text
idf.py set-target <IDF_TARGET>
```

against the configured sample project.

### 30 — component resolution verification

Runs:

```text
idf.py reconfigure
```

and verifies that CMake configuration artifacts are generated.

### 40 — sample build verification

Runs a clean build for the configured sample project and checks for generated binary and ELF artifacts.

Current default expected artifact names are tied to the ESP-IDF `hello_world` sample:

```text
build/hello_world.bin
build/hello_world.elf
```

A future alignment phase will generalize this with a configurable expected application name.

## Completion criterion

The ESP32 development environment is ready when:

```text
40_verify_sample_build_esp32.* passes
```

A passing build only proves local ESP-IDF build readiness. It does not imply that ESP32 firmware has been granted any safety-critical authority in the `safe_deferral` system.

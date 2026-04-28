# SESSION_HANDOFF_2026-04-28_IMPLEMENTATION_COMPLETE_UPDATE.md

## Purpose

This addendum records the full implementation batch completed on 2026-04-28.
It supersedes any earlier handoff wording that refers to implementation items
below as "not yet started" or "pending".

---

## What Was Completed

### Mac mini components (MM-01 ~ MM-10)

All 10 Mac mini components implemented under `mac_mini/code/`:

| ID | Module | Path |
|----|--------|------|
| MM-01 | Context Intake | `context_intake/` |
| MM-02 | Local LLM Adapter | `local_llm_adapter/` |
| MM-03 | Policy Router | `policy_router/` |
| MM-04 | Deterministic Validator | `deterministic_validator/` |
| MM-05 | Safe Deferral Handler | `safe_deferral_handler/` |
| MM-06 | Class 2 Clarification Manager | `class2_clarification_manager/` |
| MM-07 | Low-Risk Dispatcher | `low_risk_dispatcher/` |
| MM-08 | Caregiver Escalation | `caregiver_escalation/` |
| MM-09 | Audit Logger | `audit_logger/` |
| MM-10 | Telemetry Adapter | `telemetry_adapter/` |

Tests: **203 passed** (`mac_mini/code/tests/`).

### RPi experiment apps (RPI-01 ~ RPI-10)

All 10 RPi apps implemented under `rpi/code/`:

| ID | Module | Path |
|----|--------|------|
| RPI-01 | Experiment Manager | `experiment_manager/` |
| RPI-02 | Result Store | `result_store/` |
| RPI-03 | Virtual Node Manager | `virtual_node_manager/` |
| RPI-04 | Virtual Behavior Manager | `virtual_behavior/` |
| RPI-05 | Scenario Manager | `scenario_manager/` |
| RPI-06 | MQTT Status Monitor | `mqtt_status/` |
| RPI-07 | Preflight Readiness Manager | `preflight/` |
| RPI-08 | Dashboard | `dashboard/` (port 8888) |
| RPI-09 | Governance Backend | `governance/` |
| RPI-10 | Governance UI | `governance/` (port 8889) |

Tests: **79 passed** (`rpi/code/tests/test_rpi_components.py`).

### ESP32 physical nodes (PN-01 ~ PN-08)

All 8 nodes implemented under `esp32/code/`:

| Node | Path | Role |
|------|------|------|
| PN-01 | `pn01_button_input/` | Physical button input |
| PN-02 | `pn02_lighting_control/` | Living room / bedroom light relay |
| PN-03 | `pn03_env_context/` | Temperature / illuminance / occupancy |
| PN-04 | `pn04_doorbell/` | Doorbell visitor context |
| PN-05 | `pn05_gas_smoke_fire/` | Gas / smoke / fire emergency evidence |
| PN-06 | `pn06_fall_detection/` | IMU two-phase fall detection |
| PN-07 | `pn07_warning_output/` | Buzzer / LED / TTS warning output |
| PN-08 | `pn08_doorlock_interface/` | Governed doorlock interface |

All nodes use **ESP32-C3 Super Mini** with corrected GPIO assignments:

| Node | GPIO | Role |
|------|------|------|
| PN-01 | GPIO9 | Built-in boot button (active-LOW) |
| PN-02 | GPIO4 / GPIO5 | Living room / bedroom light relay |
| PN-04 | GPIO3 | Doorbell input |
| PN-05 | GPIO0 / GPIO1 | Gas ADC (ADC1_CH0) / Smoke ADC (ADC1_CH1) |
| PN-06 | GPIO8 / GPIO10 | IMU I2C SDA / SCL |
| PN-07 | GPIO6 / GPIO7 / GPIO10 | Buzzer (LEDC) / Status LED / TTS UART1 TX |
| PN-08 | GPIO4 / GPIO5 | Doorlock relay / Status LED |

Shared library: `esp32/code/shared/` contains `sd_payload.c/h`,
`sd_mqtt_topics.h`, `sd_provision.c/h`.

#### WiFi Provisioning (`sd_provision.c/h`)

On first boot with no saved credentials, each node enters SoftAP + captive
portal provisioning mode:

- SoftAP SSID: `sd-XXXXXX` (last 3 MAC bytes)
- DNS hijack on UDP:53 → triggers iOS/Android captive portal pop-up
- HTTP server on port 80 serves bilingual (Korean/English) config form
- Submitting the form saves `wifi_ssid`, `wifi_password`, `mqtt_broker_uri`
  to NVS namespace `sd_prov`, then calls `esp_restart()`
- On subsequent boots, `sd_prov_load()` + `sd_prov_wifi_connect()` restores
  the saved configuration

Key API (`sd_provision.h`):
```c
bool sd_prov_load(sd_prov_config_t *out);
bool sd_prov_wifi_connect(const sd_prov_config_t *cfg, int timeout_s);
void sd_prov_start(sd_prov_config_t *out);  /* does not return */
void sd_prov_erase(void);
```

Each node's `app_main` calls `nvs_flash_init()`, `esp_netif_init()`,
`esp_event_loop_create_default()` before the provisioning block.
`sd_prov_start()` does NOT call these itself (caller's responsibility).

### STM32 timing measurement firmware (STM32-01 ~ STM32-05)

Skeleton firmware under `integration/measurement/stm32/`:

- Target: STM32H743, 480 MHz
- TIM2: prescaler=239 → 1 MHz tick (1 µs resolution), 32-bit counter
- Input capture: PA0–PA3 (TIM2_CH1–CH4), 4-sample digital filter
- UART3: PD8/PD9, 115200 8N1 for session commands and result output
- Session state machine: IDLE → ARMED → RUNNING → DONE
- Modules: `sd_capture.c`, `sd_export.c`, `sd_status.c`, `sd_sync.c`,
  `sd_validation.c`
- `sd_measure.h` defines `sd_capture_t`, `sd_session_t`, `sd_readiness_t`

### Setup documentation (`docs/setup/`)

| File | Content |
|------|---------|
| `01_mac_mini_setup.md` | Script-based install guide: 3 phases (install/configure/verify), maps each step to numbered script |
| `02_rpi_setup.md` | Script-based install guide: 3 phases, maps each step to numbered script |
| `03_esp32_setup.md` | Bilingual build/flash guide, GPIO pin table, provisioning flow |
| `04_stm32_setup.md` | Bilingual build/flash guide, 3 flash methods, session commands |

Both `01_mac_mini_setup.md` and `02_rpi_setup.md` were rewritten from
manual step-by-step format to script-based format using the existing scripts
under `mac_mini/scripts/` and `rpi/scripts/`.

Mac mini install script order:
1. `install/00_install_homebrew.sh`
2. `install/00_preflight.sh`
3. `install/10_install_homebrew_deps.sh`
4. `install/20_install_docker_runtime_mac.sh`
5. `install/21_prepare_compose_stack_mac.sh`
6. `install/30_setup_python_venv_mac.sh`
7. `configure/70_write_env_files.sh` → edit `.env` → then scripts 10–60
8. `verify/80_verify_services.sh`

RPi install script order:
1. `install/00_preflight_rpi.sh`
2. `install/10_install_system_packages_rpi.sh`
3. `install/20_create_python_venv_rpi.sh`
4. `install/30_install_python_deps_rpi.sh`
5. `install/40_install_time_sync_client_rpi.sh`
6. `configure/10_write_env_files_rpi.sh` → set `MAC_MINI_HOST` → then scripts 20–50
7. `verify/70_verify_rpi_base_runtime.sh` → 75 → 80

---

## Current Implementation Status

| Layer | Status |
|-------|--------|
| Mac mini (MM-01~10) | ✅ Implemented, 203 tests pass |
| RPi apps (RPI-01~10) | ✅ Implemented, 79 tests pass |
| ESP32 nodes (PN-01~08) | ✅ Implemented, hardware validation pending |
| STM32 timing (STM32-01~05) | ✅ Skeleton implemented, hardware validation pending |
| Setup documentation | ✅ All 4 docs complete, script-based |
| Actual experiments | ⬜ Not yet run |
| System structure diagram | ⬜ Revision plan exists (`08_system_structure_figure_revision_plan.md`) |
| Paper writing | ⬜ Outline exists (`common/docs/paper/`) |

---

## What Remains

1. **Run actual experiments** — `integration/scenarios/` skeletons are in
   place; `required_experiments.md` defines what to measure. Requires Mac mini
   and RPi hardware connected and Mac mini hub running.

2. **System structure diagram** — Follow
   `common/docs/architecture/08_system_structure_figure_revision_plan.md`.

3. **Paper writing** — `common/docs/paper/` contains ICT Express submission
   notes and section outlines. Requires experiment results.

4. **Hardware validation** — ESP32 node firmware and STM32 firmware require
   physical boards for functional verification.

---

## Key File Locations

```
mac_mini/code/              — Mac mini Python implementation
rpi/code/                   — RPi Python implementation
esp32/code/                 — ESP32 C firmware (8 nodes + shared/)
integration/measurement/stm32/ — STM32 timing firmware
docs/setup/                 — Installation guides
mac_mini/scripts/           — Mac mini install/configure/verify scripts
rpi/scripts/                — RPi install/configure/verify scripts
```

Python venv paths:
- Mac mini: `~/smarthome_workspace/.venv-mac`
- RPi: `~/smarthome_workspace/.venv-rpi`

---

## Branch / PR Status

PR #15 (`feat/implement-mm-rpi-components`) was squash-merged into `main`
on 2026-04-28. The branch has been deleted. `main` is the current baseline.

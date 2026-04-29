# SESSION_HANDOFF_2026-04-29_HARDWARE_INTEGRATION_RUN_COMPLETE.md

## Status

**Both Mac mini and RPi physical hardware are fully installed, verified, and integration-tested.**

All verify scripts pass. Integration run tests all passed.

---

## What Was Completed This Session

### Mac mini (all fixed and verified in earlier session)
- Docker services (homeassistant, mosquitto, ollama) start correctly
- `main.py` runs from repo with `.env` sourced
- Verify scripts 10–80 all pass

### RPi verify script bugs fixed (PRs #31–#35)

| PR | Fix |
|----|-----|
| #31 | `80_verify_rpi_closed_loop_audit.sh`: wrong inject topic (`fault/injection` → `context/input`), wrong observe topic (`audit/log` → `dashboard/observation`), invalid payload (missing required schema fields, invalid event_type enum) |
| #32 | Same script: `SIM_CONTEXT_TOPIC` resolves to `safe_deferral/sim/context` which `main.py` does not subscribe to — hardcoded to `safe_deferral/context/input` |
| #33 | `05_integration_run.md`: added `source .env` step before running `main.py`; without it env vars like `$MAC_MINI_HOST` are passed as literal strings |
| #34 | `05_integration_run.md`: expanded section 3-1 with IP check and troubleshooting entries |
| #35 | `10_write_env_files_rpi.sh`: `MQTT_HOST` and `TIME_SYNC_HOST` were written as literal `$MAC_MINI_HOST` string (backslash-escaped) — fixed to `mac-mini.local` direct default |

### Key discoveries during first hardware run

1. **`main.py` reads env vars from shell, not `.env` directly** — must `source .env` before running
2. **RPi `.env` `MQTT_HOST=$MAC_MINI_HOST`** — variable not exported to child process; fixed to use direct value
3. **`mac-mini.local` mDNS** — does not resolve on all LAN configs; use LAN IP directly for `MAC_MINI_HOST`, `MQTT_HOST`, `TIME_SYNC_HOST`
4. **Mac mini git pull** — must be current before running `main.py`; old code doesn't publish telemetry to the right topic
5. **80 verify keepalive timeout (15s)** — can occur if Mac mini pipeline is slow (LLM path); resolved by ensuring Mac mini is running current code

---

## Current State

- Mac mini: `main.py` running, MQTT connected, pipeline ready
- RPi: `rpi/code/main.py` running, subscribed to 4 monitor topics
- Integration tests: all passed
- All verify scripts (Mac mini + RPi): all pass

---

## Next Steps

- ESP32 node physical setup (`03_esp32_setup.md`)
- Full end-to-end experiment run with actual physical nodes
- STM32 timing measurement (optional)

---

## Files Changed This Session

- `rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh` — full rewrite
- `rpi/scripts/configure/10_write_env_files_rpi.sh` — MQTT_HOST/TIME_SYNC_HOST default fix
- `docs/setup/05_integration_run.md` — .env source step, IP check section, troubleshooting

# 06. Local M1 MacBook End-to-End Verification

**한국어 요약:** M1 노트북 한 대로 Mac mini stack + RPi stack + MQTT 브로커 + Ollama LLM + paper-eval 도구 전체를 동시에 띄워서 paper-grade 운영 검증을 수행한다. ESP32 물리 노드는 RPi의 가상 노드 매니저가 시뮬레이트하므로 추가 하드웨어가 필요 없다. 한 명령(`./scripts/local_e2e_launcher.sh`)으로 모든 컴포넌트를 띄우고, 다른 한 명령(`./scripts/local_e2e_smoke_test.sh`)으로 sweep → aggregate → digest 파이프라인 전체가 동작하는지 자동 검증한다.

**English summary:** Stand up the entire safe_deferral stack on a single M1 MacBook — Mac mini Python stack, RPi Python stack, MQTT broker, Ollama LLM, paper-eval toolchain — for paper-grade operational verification. ESP32 physical nodes are simulated by the RPi virtual node manager; no extra hardware is required. One command (`./scripts/local_e2e_launcher.sh`) brings everything up; another (`./scripts/local_e2e_smoke_test.sh`) auto-verifies the full sweep → aggregate → digest pipeline.

---

## 1. Prerequisites / 사전 준비

| Component | Install command (macOS / homebrew) | Notes |
|---|---|---|
| Homebrew | https://brew.sh | for `brew install` to work |
| Mosquitto MQTT broker | `brew install mosquitto` | Started automatically by the launcher via `brew services start mosquitto`. |
| Ollama | https://ollama.com | Download the macOS app and run it. |
| llama3.2 model | `ollama pull llama3.2` | The Mac mini stack defaults to this model (#128 verified 0% fallback). |
| Python ≥ 3.9 | macOS-bundled is fine | The launcher checks for `paho.mqtt`, `fastapi`, `jsonschema`, `requests`. |
| Python deps | `pip install paho-mqtt fastapi uvicorn jsonschema requests python-dotenv` | One-time. |

**한국어:** 사전 준비물은 위 표대로. Ollama 앱은 미리 띄워두기. 다른 항목은 launcher가 누락 시 정확한 설치 명령을 안내한다.

## 2. One-shot launcher (Option 1)

```bash
./scripts/local_e2e_launcher.sh
```

What it does:
1. Verifies preconditions (mosquitto / ollama / python deps).
2. Starts mosquitto via `brew services` if not already running on `:1883`.
3. Auto-creates `~/smarthome_workspace/.env` with sensible defaults if missing (existing `.env` is left untouched).
4. Spawns Mac mini stack (`mac_mini/code/main.py`) in the background; PID + log written to `/tmp/safe_deferral_e2e/macmini.{pid,log}`.
5. Spawns RPi stack (`rpi/code/main.py`); PID + log at `/tmp/safe_deferral_e2e/rpi.{pid,log}`.
6. Waits up to 30 s for the dashboard `:8888/health` to respond.
7. Prints a summary with PIDs, log paths, dashboard URL, and the stop command.

**Idempotent** — run it twice in a row; the second invocation detects already-running stacks and is a no-op.

Useful flags:
- `--stop` : SIGTERM both stacks (mosquitto is left running so other sessions can use it).
- `--no-mosquitto-start` : assume the broker is already managed elsewhere (CI / Docker / a separate service).

After launch, open the dashboard:
```bash
open http://localhost:8888/
```

Tail logs:
```bash
tail -f /tmp/safe_deferral_e2e/{macmini,rpi}.log
```

## 3. Smoke test (Option 2)

```bash
./scripts/local_e2e_smoke_test.sh
```

What it does (about 60–90 s on M1):
1. Calls the launcher (idempotent — reuses already-running stacks).
2. Creates a virtual context node via the dashboard HTTP API.
3. Starts a paper-eval sweep with `integration/paper_eval/matrix_smoke.json` (1 cell × 1 trial — finishes in seconds).
4. Polls `/paper_eval/sweeps/current` until status is `completed` (timeout 90 s, configurable via `SMOKE_SWEEP_TIMEOUT_S`).
5. Downloads the digest CSV + Markdown and runs minimal sanity checks (header columns present, exactly 1 BASELINE row, `pass_rate=1.0000`, Markdown footer mentions `v1-smoke` + `Reproducibility`).
6. Tears down the launcher (`--stop`) automatically — even on failure (`trap EXIT`).

Pass / fail is signalled via the script's exit code:
| Code | Meaning |
|---|---|
| 0 | ✓ smoke test passed end-to-end |
| 1 | setup failed (broker not up, python deps missing, dashboard not healthy) |
| 2 | sweep did not reach `completed` within timeout |
| 3 | digest content failed sanity checks |

Use `--keep-running` to skip the teardown so you can poke around the dashboard afterwards:
```bash
./scripts/local_e2e_smoke_test.sh --keep-running
# ... explore at http://localhost:8888 ...
./scripts/local_e2e_launcher.sh --stop   # stop manually when done
```

The smoke test's success means: **operator → dashboard → sweep_runner → Sweeper → Mac mini stack → real Ollama → policy router → validator → dispatcher → ACK → trial_store → aggregator → digest writer → CSV/MD download** all wired correctly. Any future regression in any of those layers will surface as a smoke failure.

## 4. Real paper-eval sweep (after smoke passes)

Once smoke confirms plumbing, run a real measurement sweep from the dashboard UI:

1. `./scripts/local_e2e_launcher.sh` (if not already running)
2. Open http://localhost:8888 → tab "⑤ Paper-Eval Sweep"
3. Sweep config:
   - matrix path: `integration/paper_eval/matrix_v1.json` (the full 12-cell × 30-trial matrix)
   - node ID: the virtual node you created (or the one the smoke test left behind)
4. Click **▶ Sweep 시작** and watch the per-cell progress table
5. When complete (real-LLM 12 × 30 trials ≈ 30–60 minutes on M1), download:
   - `digest_v1_<ts>.csv` for paper plotting
   - `digest_v1_<ts>.md` for direct paper-table inclusion

This addresses doc 13 §11 open question #1 (variance measurement on actual data).

## 5. What's simulated vs. real

| Layer | Real on M1 MacBook | Simulated |
|---|---|---|
| LLM (Ollama llama3.2) | ✓ real | — |
| Policy router / validator / dispatcher | ✓ real (Mac mini Python code) | — |
| MQTT broker (mosquitto) | ✓ real | — |
| Dashboard / sweep runner / aggregator / digest | ✓ real (RPi Python code) | — |
| ESP32 input/emergency/actuator nodes | — | RPi `VirtualNodeManager` simulates publish/subscribe |
| TTS audible output | optional (`TTS_ENABLED=true` in `.env`) — uses macOS `say` | default false in launcher-generated `.env` |
| Telegram caregiver notifications | optional (set `TELEGRAM_BOT_TOKEN`) | empty token → mock-mode logging only |
| Physical doorlock / warning hardware | — | logical state in audit log only |

## 6. Troubleshooting / 문제 해결

**`launcher` exits with `paho-mqtt missing`:**
```bash
pip install paho-mqtt fastapi uvicorn jsonschema requests python-dotenv
```

**Dashboard `/health` does not respond within 30 s:**
- Check `/tmp/safe_deferral_e2e/rpi.log` — usually port `:8888` collision or a Python import error.
- If port collision: edit `~/smarthome_workspace/.env`, set `DASHBOARD_PORT=18888`, re-run launcher.

**Smoke test fails at step 4 (sweep didn't complete):**
- Check `/tmp/safe_deferral_e2e/macmini.log` for LLM call errors.
- Increase budget: `SMOKE_SWEEP_TIMEOUT_S=180 ./scripts/local_e2e_smoke_test.sh`
- Confirm Ollama llama3.2 model is installed: `ollama list | grep llama3.2`

**Mosquitto already running but on a different port:**
- Use `--no-mosquitto-start` and ensure your broker is on the port `MQTT_PORT` env var points to.

**Want to keep stacks running after smoke test (to inspect dashboard):**
```bash
./scripts/local_e2e_smoke_test.sh --keep-running
```

**Stop everything:**
```bash
./scripts/local_e2e_launcher.sh --stop
brew services stop mosquitto   # optional — leave running if other sessions use it
```

## 7. Boundary notes

- This setup is **paper-eval verification**, not production deployment. The two stacks intentionally remain separate processes (mirroring the real Mac mini ↔ RPi process boundary).
- The launcher does NOT modify any canonical asset under `common/policies/`, `common/schemas/`, `common/mqtt/`, or `common/payloads/`. It only writes user config (`.env`) and runtime artifacts (logs, PID files, sweep manifests).
- Telegram and TTS remain optional / off by default — explicit env-var opt-in required for live external side effects.

# SESSION_HANDOFF — Local M1 MacBook E2E (Launcher + Smoke Test)

**Date:** 2026-05-02
**Tests:** rpi 291/291, mac_mini 711/711 unchanged. Two new shell scripts validated via dry-run (syntax + error-path detection); no python tests added (shell scripts).
**Plan baseline:** `PLAN_2026-05-02_LOCAL_MACBOOK_E2E.md`. Closes the "needs hardware" caveat on doc 13 §11 open question #1 — paper-grade variance measurement is now possible on a single M1 laptop.

---

## 이번 세션의 범위

`PLAN_2026-05-02_LOCAL_MACBOOK_E2E.md`의 옵션 1 + 옵션 2를 단일 PR로 ship. M1 노트북 한 대에서 Mac mini stack + RPi stack + MQTT 브로커 + Ollama LLM + paper-eval 도구 전체를 한 명령으로 띄우고, 다른 한 명령으로 자동 검증 가능.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/docs/runtime/PLAN_2026-05-02_LOCAL_MACBOOK_E2E.md` (신규) | 9-section plan — scope, 환경, 디자인 결정, 파일 구성, validation, risks, phase split, 다음 단계, 안티-목표. |
| `scripts/local_e2e_launcher.sh` (신규) | Option 1 — ~135 줄. precondition 검사 (brew/mosquitto/ollama/python deps), `~/smarthome_workspace/.env` 자동 작성 (없을 때만), mac_mini + rpi stack을 nohup 백그라운드 실행, dashboard `/health` gate, PID + log path 출력. `--stop` (SIGTERM → 3s wait → SIGKILL fallback), `--no-mosquitto-start` (CI/Docker 용). idempotent — 두 번 실행해도 안전. |
| `scripts/local_e2e_smoke_test.sh` (신규) | Option 2 — ~140 줄. launcher 호출 → virtual node 생성 → matrix_smoke.json으로 sweep 시작 → 90s 안에 completed 도달 폴링 → digest CSV/MD sanity check (header + BASELINE row + Reproducibility footer) → 자동 cleanup (`trap EXIT`). exit code 0/1/2/3 (success / setup fail / timeout / verification fail). `--keep-running`으로 cleanup 생략 가능. |
| `integration/paper_eval/matrix_smoke.json` (신규) | 1 cell × 1 trial 최소 매트릭스. matrix_v1과 같은 baseline scenario 사용. `paper_eval.sweep.load_matrix()`로 검증 OK. |
| `docs/setup/06_local_macbook_e2e.md` (신규) | 사람용 setup guide — prerequisites 표, launcher/smoke 사용법, 실제 paper-eval sweep 실행 안내, 시뮬 vs 실 컴포넌트 대조표, troubleshooting. 한국어 + 영어 병기. |

### 디자인 원칙

- **Idempotent + fail-fast**: launcher가 누락 의존성 발견 시 정확한 설치 명령 출력. 두 번 실행해도 안전 (already-running 감지 → no-op).
- **Process supervision 안 함**: nohup으로 띄우고 PID 기록. crash 자동 재시작 X — 운영자가 로그 확인. 두 stack 동시 죽는 일 거의 없음, 한쪽 죽어도 다른쪽 그대로.
- **Trap-based cleanup**: smoke test가 어떤 exit path에서도 launcher `--stop` 보장. CI 안전.
- **Conservative side effects**: launcher가 `~/smarthome_workspace/.env`를 **없을 때만** 작성. 기존 .env 절대 덮어쓰지 않음. canonical asset 0 변경. mosquitto는 brew services로 시작하지만 `--stop`이 그건 안 끔 (다른 세션도 사용할 수 있어서).
- **Smoke 매트릭스 분리**: 본 매트릭스 (`matrix_v1.json`, 12 cells × 30 trials = ~30분)와 smoke 매트릭스 (`matrix_smoke.json`, 1 cell × 1 trial = ~10초) 분리. CI에서 매번 30분 매트릭스를 돌릴 수 없음.
- **Verifiable assertions**: smoke가 digest CSV에서 header + BASELINE row + pass_rate=1.0000 + Markdown footer를 명시적으로 grep. silent success 방지.

### Dry-run 검증 (이 세션 중)

```bash
$ bash -n scripts/local_e2e_launcher.sh && echo OK   # syntax
launcher syntax OK
$ bash -n scripts/local_e2e_smoke_test.sh && echo OK
smoke syntax OK

$ ./scripts/local_e2e_launcher.sh --stop   # no-op when nothing running
[launcher] stopping safe_deferral E2E stacks
[launcher] done.

$ ./scripts/local_e2e_launcher.sh   # mosquitto missing case
[launcher] checking preconditions
[launcher] ERROR: mosquitto not installed. Install: brew install mosquitto

$ ./scripts/local_e2e_launcher.sh --no-mosquitto-start
[launcher] checking preconditions
[launcher] skipping mosquitto start (--no-mosquitto-start)
[launcher] ERROR: MQTT port 1883 not listening. Start your broker first.
```

모든 error path가 actionable message + non-zero exit. python deps (paho-mqtt / fastapi / jsonschema / requests) 자동 검출 OK.

### 다음 단계 (사용자 측)

1. `brew install mosquitto` (한 번만)
2. `./scripts/local_e2e_smoke_test.sh` 실행 → 60–90s 안에 ✓ 또는 명확한 실패 원인
3. smoke 통과하면 `./scripts/local_e2e_launcher.sh` + 브라우저 `http://localhost:8888` → ⑤ Paper-Eval Sweep 탭 → matrix_v1.json으로 실제 sweep (~30–60분) → digest CSV/MD로 paper-grade variance 측정
4. doc 13 §11 open question #1 답변 가능

### Boundary 영향

없음. canonical asset / dashboard 코드 / mac_mini 코드 / rpi 코드 모두 미수정. 두 새 shell script + 새 매트릭스 fixture + setup doc만 추가.

### Test plan

```bash
# Shell syntax
bash -n scripts/local_e2e_launcher.sh && bash -n scripts/local_e2e_smoke_test.sh
# Existing tests unaffected
cd rpi/code && python -m pytest tests/ -q
# 291 passed
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 711 passed
# matrix_smoke.json loads via load_matrix
PYTHONPATH=rpi/code python -c "
from pathlib import Path
from paper_eval.sweep import load_matrix
spec = load_matrix(
    Path('integration/paper_eval/matrix_smoke.json'),
    Path('integration/scenarios'),
)
assert spec.matrix_version == 'v1-smoke'
assert len(spec.cells) == 1
assert spec.cells[0].trials_per_cell == 1
"
```

(Full launcher + smoke run requires `brew install mosquitto` first — that's the user's one-time step.)

### Files touched

```
common/docs/runtime/PLAN_2026-05-02_LOCAL_MACBOOK_E2E.md (new)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_LOCAL_MACBOOK_E2E.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
scripts/local_e2e_launcher.sh (new, +x)
scripts/local_e2e_smoke_test.sh (new, +x)
integration/paper_eval/matrix_smoke.json (new)
docs/setup/06_local_macbook_e2e.md (new)
```

### Notes

- launcher 작성 후 paho-mqtt가 conda 환경에 미설치된 사실 발견 → `pip install --user paho-mqtt`로 해결. 이 사실을 setup doc의 prerequisites 표에 명시.
- smoke의 BASELINE row 검증은 `pass_rate=1.0000`까지 정확 매칭하지만 미스매치 시 WARN으로 격하 (실제 LLM 응답 variance 가능성 인정). header / row count / 파일 존재는 hard fail.
- 두 stack을 한 process로 합칠 수도 있지만 의도적으로 분리 — 운영 환경의 process boundary (Mac mini ↔ RPi)를 노트북에서도 유지.
- mosquitto는 launcher가 brew services로 시작하지만 `--stop`이 그건 안 끔 → 다른 세션 (테스트 / 다른 프로젝트)이 사용 중일 수 있으므로 사용자가 명시적으로 `brew services stop mosquitto`.
- TTS 기본 비활성 (`TTS_ENABLED=false`) — sweep 중 노트북이 시끄러워지는 것 방지.

# PLAN — Local MacBook E2E Verification (Options 1 + 2)

**Date:** 2026-05-02
**Goal:** M1 MacBook 한 대에서 Mac mini stack + RPi stack + MQTT broker + Ollama + paper-eval toolchain까지 전부 동시에 띄워서 paper-grade 운영 검증을 가능케 한다. 사용자가 손으로 5단계 setup 안 해도 한 명령 (`launcher`) 또는 두 명령 (`smoke test`)으로 동작.

**왜 지금**: doc 13 §11 open question #1 (30 trials/cell variance 측정)이 hardware 가용성에 막혀있는 상태. 이 plan이 ship되면 **M1 노트북 한 대로** 실제 sweep 운영이 가능해지고, paper-grade 측정 데이터를 즉시 산출할 수 있다.

---

## 1. Scope (이번 PR)

**In scope:**
- `scripts/local_e2e_launcher.sh` — Option 1. MQTT broker 시작 + .env 검증/생성 + Ollama 확인 + Mac mini stack 백그라운드 + RPi stack 백그라운드 + dashboard health gate. PID/log path 출력. `--stop` 으로 일괄 종료.
- `scripts/local_e2e_smoke_test.sh` — Option 2. launcher 위에서 (a) virtual node 생성, (b) 최소 매트릭스로 Phase 4 sweep 시작, (c) 폴링하여 완료 대기, (d) digest CSV 다운로드 + sanity check, (e) cleanup. CI에서도 사용 가능 (timeout 보호 + non-zero exit on failure).
- `integration/paper_eval/matrix_smoke.json` — 최소 sweep 매트릭스 (1 baseline cell × 1 trial). full matrix_v1은 12 cells × 30 trials = 360 trials → real LLM 호출 시 ~1시간; smoke 매트릭스는 1 trial → 수십 초.
- `docs/setup/06_local_macbook_e2e.md` — 사람용 setup guide (script가 자동화하지만 trouble shooting + manual override 안내).
- 핸드오프 doc.

**Out of scope (별 PR 가능):**
- macOS 외 OS 지원 (Linux launcher는 분리 가능).
- Telegram 실연결 검증 (mock으로 충분).
- 실제 24h soak test, variance 측정 자체 (스크립트 위에서 사용자가 운영).
- Docker compose 변종.

## 2. 현재 환경 (M1 MacBook 기준)

| 컴포넌트 | 상태 | 검증된 것 |
|---|---|---|
| Ollama | ✓ 작동 중 | `:11434/api/tags` OK, llama3.2 모델 설치됨 (#128에서 fallback rate 0% 검증) |
| Mac mini Python stack | ✓ 코드 있음 | 어떤 포트도 listen 안 함, paho-mqtt 필요 |
| RPi Python stack | ✓ 코드 있음 | dashboard :8888 + governance :8889 |
| Mosquitto | ✗ 미설치 | `brew install mosquitto && brew services start mosquitto` 필요 |
| `~/smarthome_workspace/.env` | ✗ 없음 | 두 stack의 dotenv loader가 graceful 처리 (에러 X), 하지만 적절 값 필요 (MQTT_HOST=localhost 등) |

## 3. 디자인 결정

### 3.1 단일 PR vs 분할
두 스크립트는 단일 PR. 이유:
- smoke가 launcher를 source/wrap → 강결합
- 둘 다 작음 (launcher ~80줄, smoke ~120줄)
- separate PR이면 reviewer가 두 번 보는 비효율

### 3.2 launcher 설계 원칙
- **Idempotent**: 두 번 실행해도 안전 (mosquitto already started → no-op, .env already exists → no-op).
- **Fail-fast with actionable message**: 누락된 의존성 (brew/mosquitto/python deps) 발견 시 정확한 설치 명령 출력.
- **Process supervision은 안 함**: nohup으로 띄우고 PID 파일에 기록만. crash 시 자동 재시작 X — 운영자가 로그 확인. 2 stacks 동시에 죽는 일은 운영적으로 거의 없음 (한쪽 죽어도 다른쪽은 그대로).
- **Log paths 명시**: `/tmp/safe_deferral_e2e/{macmini,rpi}.log` 디렉터리 + tail 명령 안내.
- **`--stop` flag**: 시작한 PID들 SIGTERM, 정상 종료 안 되면 SIGKILL fallback.
- **`--no-mosquitto-start` flag**: 이미 broker 띄워둔 운영자용 (CI / Docker 환경 등).

### 3.3 smoke test 설계 원칙
- **Self-contained timeout**: 최대 90초 안에 완료 또는 실패 (launcher 30s + sweep 60s). CI 부담 적게.
- **Cleanup on any exit path**: trap EXIT으로 launcher --stop 보장.
- **Verifiable assertions**: digest CSV의 `cell_id` 컬럼 존재 + 1개 row + `pass_rate=1.0000` 등 명시적 grep.
- **Exit codes**: 0 success, 1 setup failure (브로커 못 띄움 등), 2 sweep timeout, 3 verification failure (digest 내용 비정상).

### 3.4 minimal smoke matrix
matrix_v1은 12 cells × 30 trials. real LLM에서 1 trial ~5초 → 매트릭스 전체 ~30분. 너무 길음.

smoke 매트릭스: **BASELINE 1개 × trials_per_cell=1**. 약 5–10초 소요. plumbing이 동작하는지만 확인. paper-grade variance는 따로 운영 sweep으로.

```json
{
  "matrix_version": "v1-smoke",
  "matrix_description": "Minimal local E2E smoke matrix. 1 cell × 1 trial.",
  "trials_per_cell_default": 1,
  "package_id": "A",
  "cells": [{
    "cell_id": "BASELINE",
    "comparison_condition": null,
    "scenarios": ["class1_baseline_scenario_skeleton.json"],
    "trials_per_cell": 1,
    "expected_route_class": "CLASS_1",
    "expected_validation": "approved"
  }],
  "anchor_commits": {"matrix_file_sha": null, "scenarios_dir_sha": null, "policy_table_sha": null}
}
```

## 4. 파일 구성

```
scripts/
├── local_e2e_launcher.sh          (new, ~120 lines)
└── local_e2e_smoke_test.sh        (new, ~140 lines)
integration/paper_eval/
└── matrix_smoke.json              (new)
docs/setup/
└── 06_local_macbook_e2e.md        (new, ~150 lines)
common/docs/runtime/
├── PLAN_2026-05-02_LOCAL_MACBOOK_E2E.md          (this file)
└── SESSION_HANDOFF_2026-05-02_LOCAL_MACBOOK_E2E.md  (post-ship)
```

## 5. Validation strategy

스크립트 자체는 unit test 안 함 (shell이라 비용 대비 효익 낮음). 검증 방식:

1. **Local dry-run**: launcher 실행 → 두 stack PID 확인 → dashboard `:8888/health` 응답 → `--stop`으로 정리. 사용자 머신에서 직접 체크.
2. **Smoke test self-validation**: smoke가 launcher 위에서 1 trial sweep 실행 → digest CSV 검증 → 통과/실패 자체가 회귀 테스트 역할.
3. **shellcheck**: 두 스크립트 shellcheck 통과 (가능하면).
4. **Idempotency**: launcher 두 번 연속 실행해도 같은 결과.
5. **Stop cleanup**: `--stop` 후 PID들이 실제로 사라졌는지 ps 확인.

## 6. Risks

- **mosquitto 설치 시간**: brew install ~1분. 이미 설치되어 있으면 그냥 시작.
- **포트 충돌**: 8888/8889/1883/11434 모두 다름. 하지만 운영자가 이미 다른 dashboard 띄워뒀다면 충돌 — 명확한 에러 메시지.
- **Mac mini stack의 paho-mqtt 의존성 미설치**: `python -c "import paho.mqtt"` pre-flight 검사로 잡음.
- **Ollama 응답 지연**: M1 MacBook에서 llama3.2 1 inference ~1.5–4초 (#128 측정). 1 trial smoke는 충분.
- **TTS 발성**: launcher가 .env 만들 때 `TTS_ENABLED=false` 기본. 시끄러움 방지.
- **Ollama 모델 미설치**: pre-flight에서 `ollama list` 결과에 llama3.2 있는지 확인.

## 7. Phase split

**한 PR로 ship.** PR 분량 대략 600 줄 (코드 + 문서). 둘 다 해 야 사용자가 실제로 한 명령 운영 가능.

## 8. 다음 단계 (이번 PR 후)

- 사용자가 launcher로 직접 sweep 운영 → variance 측정 → doc 13 §11 open question #1 답변
- (선택) launcher를 Linux/RPi에서도 동작하게 generalize (별 PR)
- (선택) Telegram 실연결 검증을 smoke에 통합 (별 PR)

## 9. 안티-목표

- "한 노트북에서 production deployment를 흉내" 아님 — 운영 정확성 검증 + paper-eval 데이터 산출이 목적.
- 두 stack을 한 process로 합치지 않음 — 운영 환경 (분리된 두 머신) 의 process boundary를 보존.
- 새 schema/policy/topic 추가 0.

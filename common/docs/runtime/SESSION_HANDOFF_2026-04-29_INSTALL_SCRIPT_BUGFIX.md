# SESSION_HANDOFF — 2026-04-29 설치 스크립트 버그픽스

## 1. 이 문서의 목적

Mac mini 및 Raspberry Pi 실물 하드웨어 설치 과정에서 발견된
스크립트 버그 5건과 설치 문서 보완 2건을 기록한다.

관련 커밋: `2e13fd7` ~ `9a86112` (main 직접 커밋)

---

## 2. Mac mini 설치 버그픽스

### BUG-MM-1 — Ollama API 도달 실패 (Race Condition)

**커밋:** `2e13fd7`  
**파일:** `mac_mini/scripts/configure/30_configure_ollama.sh`

`docker compose up -d ollama` 직후 Ollama 프로세스가 포트 바인딩을
완료하기 전에 curl을 실행해 FATAL 종료.

**수정:** 1초 간격 최대 30회 재시도 루프 추가.

---

### BUG-MM-2 — 모델명 불일치 (llama3.1 vs llama3.2)

**커밋:** `2e13fd7`  
**파일:** `mac_mini/code/main.py`

configure 스크립트는 `llama3.1`을 pull하는데 `main.py` 기본값은
`llama3.2`였다. 환경변수 `OLLAMA_MODEL` 미설정 시 모델을 못 찾아 실패.

**수정:** `main.py` 기본값을 `llama3.1`로 정렬.

---

### BUG-MM-3 — homeassistant / mosquitto 미기동

**커밋:** `15f938b`  
**파일:** `mac_mini/scripts/configure/10_configure_home_assistant.sh`  
`mac_mini/scripts/configure/20_configure_mosquitto.sh`

configure 스크립트가 컨테이너가 없을 때 `WARNING`만 출력하고
`docker compose up -d`를 실행하지 않았다. `30_configure_ollama.sh`만
ollama를 기동하고 나머지 두 서비스는 검증 시까지 한 번도 기동되지 않음.

**수정:** 컨테이너 미생성 시 `docker compose up -d <service>` 실행으로 변경.

---

### BUG-MM-4 — 스키마 검증 시 시스템 python3 사용

**커밋:** `d58c95e`  
**파일:** `mac_mini/scripts/verify/50_verify_env_and_assets.sh`

`python3`(시스템 Python)를 직접 호출해 `jsonschema` import 실패.
`jsonschema`는 venv(`~/smarthome_workspace/.venv-mac`)에만 설치됨.

**수정:** venv Python(`~/.venv-mac/bin/python`)으로 교체, venv 존재 여부 사전 확인 추가.

---

### BUG-MM-5 — $ref 스키마 참조 실패 (RefResolver 누락)

**커밋:** `5f46c19`  
**파일:** `mac_mini/scripts/verify/50_verify_env_and_assets.sh`

`policy_router_input_schema.json`이 `$ref: "context_schema.json#"`를
사용하는데 `Draft7Validator`에 `resolver`를 주입하지 않아
`unknown url type: 'context_schema.json'` 에러 발생.

**수정:** `AssetLoader.make_schema_resolver()`와 동일한 방식으로
`RefResolver`를 빌드해 `Draft7Validator`에 주입.

---

## 3. RPi 설치 문서 보완

### DOC-RPI-1 — MQTT_PASS 처리 안내 누락

**커밋:** `f0ce7bb`  
**파일:** `docs/setup/02_rpi_setup.md` 섹션 4-1

`MQTT_PASS=CHANGE_ME` 경고가 항상 출력되지만 문서에 처리 방법이
없었다. Mac mini Mosquitto는 `allow_anonymous true`이므로 빈 값으로
지우면 된다.

**추가 내용:** `MQTT_PASS` 항목을 표에 추가 + `sed` 한 줄 처리 방법 안내.

---

### DOC-RPI-2 — ACTION REQUIRED 경고 및 플레이스홀더 처리 안내 누락

**커밋:** `9a86112`  
**파일:** `docs/setup/02_rpi_setup.md` 섹션 4-1

스크립트 실행 후 항상 출력되는 `ACTION REQUIRED` 경고와
플레이스홀더별 `Placeholder or legacy values` 경고에 대한
안내가 없었다.

**추가 내용:**
- `MAC_MINI_USER` 항목 표에 추가
- ACTION REQUIRED 경고가 정상 동작임을 명시
- 플레이스홀더 경고 4종(IP, mac_user, CHANGE_ME, smarthome/ 토픽)별
  원인과 해결 방법 표 추가

---

## 4. 현재 설치 진행 상태

| 단계 | 상태 |
|------|------|
| Mac mini — install | ✅ 완료 |
| Mac mini — configure | ✅ 완료 |
| Mac mini — verify | 진행 중 (버그픽스 후 재실행 필요) |
| RPi — install | ✅ 완료 |
| RPi — configure | 진행 중 |
| RPi — verify | 미시작 |

---

## 5. 다음 세션 권고 사항

- Mac mini: `git pull` 후 `80_verify_services.sh` 재실행으로 전체 통과 확인
- RPi: `.env` 수정 완료 후 configure 나머지 단계 및 verify 진행
- 설치 완료 후 `docs/setup/05_integration_run.md` 절차에 따라 통합 기동

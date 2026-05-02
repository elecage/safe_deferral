# 통합 실행 절차 / Integration Run Procedure

각 장치를 모두 설치·설정한 상태에서 전체 시스템을 순서대로 기동하고 확인하는 절차입니다.  
This document covers the ordered startup and health-check procedure for the full system, assuming all devices have been installed and configured.

전제 조건 문서:
- Mac mini: `01_mac_mini_setup.md`
- Raspberry Pi: `02_rpi_setup.md`
- ESP32 노드: `03_esp32_setup.md`

---

## 1. 기동 순서 개요 / Startup Order Overview

```
[1] Mac mini — Docker 서비스 (Mosquitto · Ollama · Home Assistant)
[2] Mac mini — Python 허브 앱 (main.py)
[3] Raspberry Pi — Python 실험 앱 (main.py)
[4] ESP32 노드 — 전원 투입 (자동 WiFi 연결 및 MQTT 구독)
```

**한국어**  
Mac mini의 MQTT 브로커(Mosquitto)가 모든 다른 컴포넌트보다 먼저 실행되어야 합니다. RPi와 ESP32 노드는 Mac mini 브로커에 연결하므로 Mac mini가 완전히 기동된 후 연결해야 합니다.

**English**  
The Mac mini's MQTT broker (Mosquitto) must be running before any other component. Both the RPi and ESP32 nodes connect to the Mac mini broker, so the Mac mini must be fully up before they connect.

---

## 2. Mac mini 기동 / Mac mini Startup

### 2-1. Docker 서비스 기동

**한국어**

```bash
cd ~/smarthome_workspace/docker
docker compose up -d
```

세 서비스가 모두 `running` 상태인지 확인합니다:

```bash
docker compose ps
```

예상 출력:
```
NAME                STATUS
edge_mosquitto      running
edge_ollama         running
edge_homeassistant  running
```

문제 발생 시 로그 확인:
```bash
docker compose logs mosquitto
docker compose logs ollama
```

**English**

```bash
cd ~/smarthome_workspace/docker
docker compose up -d
```

Verify all three services show `running`:

```bash
docker compose ps
```

Expected output:
```
NAME                STATUS
edge_mosquitto      running
edge_ollama         running
edge_homeassistant  running
```

On errors, check service logs:
```bash
docker compose logs mosquitto
docker compose logs ollama
```

---

### 2-2. 서비스 상태 검증 (선택)

**한국어**  
빠른 종합 검증이 필요하면 실행합니다:

```bash
cd /path/to/safe_deferral_claude
bash mac_mini/scripts/verify/80_verify_services.sh
```

예상 출력: `[PASS] All aggregated verification steps completed successfully`

**English**  
Optional quick aggregated verification:

```bash
cd /path/to/safe_deferral_claude
bash mac_mini/scripts/verify/80_verify_services.sh
```

Expected: `[PASS] All aggregated verification steps completed successfully`

---

### 2-3. Python 허브 앱 실행

**한국어**

> **중요**: `.env` 를 먼저 source 해야 합니다. 생략하면 `$MAC_MINI_HOST` 등 환경변수가 문자 그대로 출력되며 MQTT 연결에 실패합니다.

```bash
source ~/smarthome_workspace/.env
cd /path/to/safe_deferral_claude
~/smarthome_workspace/.venv-mac/bin/python mac_mini/code/main.py
```

정상 기동 시 로그 출력 예시:

```
[INFO] sd.main — Safe Deferral — Mac mini hub starting …
[INFO] sd.main — MQTT broker: localhost:1883
[INFO] sd.main — Audit DB: /Users/<user>/smarthome_workspace/audit.db
[INFO] sd.main — Telegram: configured          ← TELEGRAM_TOKEN 설정 시
[INFO] sd.main — LLM: llama3.1 @ http://localhost:11434/api/generate
[INFO] sd.main — Initialising pipeline components …
[INFO] sd.main — Pipeline ready.
[INFO] sd.main — MQTT connected to localhost:1883
[INFO] sd.main — Entering main loop …
```

> **주의**: `MQTT connected` 줄이 나오지 않으면 Docker 서비스가 아직 준비되지 않은 것입니다. `docker compose ps`로 Mosquitto가 `running` 상태인지 확인하세요.

**English**

> **Important**: Source `.env` first. Without it, variables like `$MAC_MINI_HOST` are passed as literal strings and the MQTT connection will fail.

```bash
source ~/smarthome_workspace/.env
cd /path/to/safe_deferral_claude
~/smarthome_workspace/.venv-mac/bin/python mac_mini/code/main.py
```

Expected startup log:

```
[INFO] sd.main — Safe Deferral — Mac mini hub starting …
[INFO] sd.main — MQTT broker: localhost:1883
[INFO] sd.main — Audit DB: /Users/<user>/smarthome_workspace/audit.db
[INFO] sd.main — Telegram: configured          ← if TELEGRAM_TOKEN is set
[INFO] sd.main — LLM: llama3.1 @ http://localhost:11434/api/generate
[INFO] sd.main — Initialising pipeline components …
[INFO] sd.main — Pipeline ready.
[INFO] sd.main — MQTT connected to localhost:1883
[INFO] sd.main — Entering main loop …
```

> **Note**: If `MQTT connected` does not appear, Mosquitto is not yet ready. Run `docker compose ps` to verify.

---

## 3. Raspberry Pi 기동 / Raspberry Pi Startup

### 3-1. .env IP 설정 확인 및 Mac mini 연결 확인

**한국어**

먼저 `.env` 의 IP 관련 항목 3개가 모두 같은 Mac mini LAN IP 로 되어 있는지 확인합니다.  
`mac-mini.local` 은 mDNS 가 지원되는 환경에서만 동작하므로, 확실하지 않으면 IP 로 직접 입력합니다.

```bash
grep -E "^(MAC_MINI_HOST|MQTT_HOST|TIME_SYNC_HOST)=" ~/smarthome_workspace/.env
```

세 항목이 모두 같은 IP(또는 동일한 hostname)가 아니면 `.env` 를 직접 수정합니다:

```bash
# 예: Mac mini LAN IP 가 192.168.1.50 인 경우
nano ~/smarthome_workspace/.env
# MAC_MINI_HOST=192.168.1.50
# MQTT_HOST=192.168.1.50
# TIME_SYNC_HOST=192.168.1.50
```

이후 MQTT 연결을 확인합니다:

```bash
source ~/smarthome_workspace/.env
ping -c 3 "${MQTT_HOST}"
mosquitto_pub -h "${MQTT_HOST}" -p 1883 -t "safe_deferral/test" -m "ping"
```

`mosquitto_pub` 이 아무 출력 없이 종료되면 정상입니다.

**English**

First verify that all three IP-related entries in `.env` point to the same Mac mini LAN IP.  
`mac-mini.local` only works when mDNS is available — if unsure, use the IP directly.

```bash
grep -E "^(MAC_MINI_HOST|MQTT_HOST|TIME_SYNC_HOST)=" ~/smarthome_workspace/.env
```

If they differ, update `.env`:

```bash
# Example: Mac mini LAN IP is 192.168.1.50
nano ~/smarthome_workspace/.env
# MAC_MINI_HOST=192.168.1.50
# MQTT_HOST=192.168.1.50
# TIME_SYNC_HOST=192.168.1.50
```

Then verify MQTT connectivity:

```bash
source ~/smarthome_workspace/.env
ping -c 3 "${MQTT_HOST}"
mosquitto_pub -h "${MQTT_HOST}" -p 1883 -t "safe_deferral/test" -m "ping"
```

`mosquitto_pub` exiting with no output means success.

---

### 3-2. Python 실험 앱 실행

**한국어**

> **중요**: `.env` 를 먼저 source 해야 합니다.

```bash
source ~/smarthome_workspace/.env
cd /path/to/safe_deferral_claude
~/smarthome_workspace/.venv-rpi/bin/python rpi/code/main.py
```

정상 기동 시 로그 출력 예시:

```
[INFO] sd.rpi — Safe Deferral — RPi experiment node starting …
[INFO] sd.rpi — MQTT broker: mac-mini.local:1883
[INFO] sd.rpi — dashboard started on port 8888
[INFO] sd.rpi — governance-ui started on port 8889
[INFO] sd.rpi — MQTT connected to mac-mini.local:1883
[INFO] sd.rpi — Subscribed to 4 monitor topics
[INFO] sd.rpi — Dashboard: http://localhost:8888
[INFO] sd.rpi — Governance: http://localhost:8889
[INFO] sd.rpi — Entering main loop …
```

브라우저에서 접근:
- **대시보드**: `http://<RPi_IP>:8888`
- **거버넌스 UI**: `http://<RPi_IP>:8889`

**English**

> **Important**: Source `.env` first.

```bash
source ~/smarthome_workspace/.env
cd /path/to/safe_deferral_claude
~/smarthome_workspace/.venv-rpi/bin/python rpi/code/main.py
```

Expected startup log:

```
[INFO] sd.rpi — Safe Deferral — RPi experiment node starting …
[INFO] sd.rpi — MQTT broker: mac-mini.local:1883
[INFO] sd.rpi — dashboard started on port 8888
[INFO] sd.rpi — governance-ui started on port 8889
[INFO] sd.rpi — MQTT connected to mac-mini.local:1883
[INFO] sd.rpi — Subscribed to 4 monitor topics
[INFO] sd.rpi — Dashboard: http://localhost:8888
[INFO] sd.rpi — Governance: http://localhost:8889
[INFO] sd.rpi — Entering main loop …
```

Browser access:
- **Dashboard**: `http://<RPi_IP>:8888`
- **Governance UI**: `http://<RPi_IP>:8889`

---

## 4. ESP32 노드 연결 / ESP32 Node Connection

### 4-1. 최초 WiFi 프로비저닝 (처음 전원 투입 시)

**한국어**  
저장된 WiFi 자격증명이 없는 노드는 SoftAP 모드로 진입합니다.

1. ESP32에 전원 투입
2. 스마트폰/노트북에서 WiFi 목록 스캔 → `sd-XXXXXX` (MAC 주소 끝 3바이트) SSID 접속
3. 브라우저가 캡티브 포털을 자동으로 표시 (자동으로 뜨지 않으면 `192.168.4.1` 접속)
4. 양식에 입력:
   - WiFi SSID / 비밀번호
   - MQTT Broker URI: `mqtt://mac-mini.local:1883` (또는 `mqtt://<Mac mini IP>:1883`)
5. 제출 → 노드 자동 재시작 및 LAN 연결

이후 전원을 껐다 켜도 저장된 설정으로 자동 연결됩니다.

**English**  
Nodes without saved WiFi credentials enter SoftAP provisioning mode.

1. Power on the ESP32 node
2. Scan WiFi on a smartphone or laptop → connect to `sd-XXXXXX` (last 3 MAC bytes)
3. Browser shows captive portal automatically (if not, navigate to `192.168.4.1`)
4. Fill in the form:
   - WiFi SSID / password
   - MQTT Broker URI: `mqtt://mac-mini.local:1883` (or `mqtt://<Mac mini IP>:1883`)
5. Submit → node restarts and joins the LAN

On subsequent power-cycles, the node reconnects automatically using saved credentials.

---

### 4-2. 노드 연결 확인

**한국어**  
Mac mini 또는 RPi 터미널에서 노드 publish를 확인합니다:

```bash
mosquitto_sub -h localhost -p 1883 -t "safe_deferral/#" -v
```

각 ESP32 노드가 연결되면 해당 토픽으로 메시지가 수신됩니다:

| 노드 | 토픽 |
|------|------|
| PN-01 (버튼) | `safe_deferral/context/input` 발행 |
| PN-03 (환경) | `safe_deferral/context/input` 발행 |
| PN-04 (도어벨) | `safe_deferral/context/input` 발행 |
| PN-05 (가스/연기) | `safe_deferral/emergency/event` 발행 |
| PN-06 (낙상) | `safe_deferral/emergency/event` 발행 |
| PN-07 (경보 출력) | `safe_deferral/deferral/request` + `safe_deferral/clarification/interaction` 구독 (안전 보류 / Class 2 명료화 상태를 사용자에게 알림). 선택적으로 `safe_deferral/actuation/ack`도 구독하여 실행 결과 피드백 |
| PN-08 (도어락) | `safe_deferral/actuation/command` 구독 (validator 승인 + 보호자 manual 경로를 거친 명령만 수신). 실행 후 `safe_deferral/actuation/ack` 발행 |

**English**  
From a Mac mini or RPi terminal, subscribe to observe node traffic:

```bash
mosquitto_sub -h localhost -p 1883 -t "safe_deferral/#" -v
```

Each connected ESP32 node publishes to its respective topic:

| Node | Topic |
|------|-------|
| PN-01 (button) | publishes `safe_deferral/context/input` |
| PN-03 (env) | publishes `safe_deferral/context/input` |
| PN-04 (doorbell) | publishes `safe_deferral/context/input` |
| PN-05 (gas/smoke) | publishes `safe_deferral/emergency/event` |
| PN-06 (fall) | publishes `safe_deferral/emergency/event` |
| PN-07 (warning output) | subscribes `safe_deferral/deferral/request` + `safe_deferral/clarification/interaction` (announces safe-deferral / Class 2 clarification state to the user). Optionally also subscribes `safe_deferral/actuation/ack` for execution-result feedback. |
| PN-08 (doorlock) | subscribes `safe_deferral/actuation/command` (only commands that passed validator approval + caregiver manual path). Publishes `safe_deferral/actuation/ack` after executing. |

---

## 5. 시스템 헬스체크 / System Health Check

### 5-1. Mac mini 파이프라인 테스트

**한국어**  
Mac mini 앱이 실행 중인 상태에서 테스트 컨텍스트 페이로드를 발행합니다:

```bash
mosquitto_pub -h localhost -p 1883 -t safe_deferral/context/input \
  -f integration/tests/data/sample_policy_router_input_sc01_light_on_request.json
```

Mac mini 터미널 로그에서 다음 흐름이 출력되어야 합니다:
```
[INFO] sd.main — Route: CLASS_1 (trigger=None)
[INFO] sd.main — LLM candidate: action=light_on target=living_room_light fallback=False
[INFO] sd.main — Validation: approved (target=actuator_dispatcher)
[INFO] sd.main — Dispatched command_id=<uuid>
```

**English**  
With the Mac mini app running, publish a test context payload:

```bash
mosquitto_pub -h localhost -p 1883 -t safe_deferral/context/input \
  -f integration/tests/data/sample_policy_router_input_sc01_light_on_request.json
```

The Mac mini log should show:
```
[INFO] sd.main — Route: CLASS_1 (trigger=None)
[INFO] sd.main — LLM candidate: action=light_on target=living_room_light fallback=False
[INFO] sd.main — Validation: approved (target=actuator_dispatcher)
[INFO] sd.main — Dispatched command_id=<uuid>
```

---

### 5-2. RPi 대시보드 헬스체크

**한국어**  
RPi 앱이 실행 중인 상태에서 브라우저 또는 curl로 확인합니다:

```bash
# Preflight 상태
curl -s http://localhost:8888/preflight | python3 -m json.tool

# MQTT 상태
curl -s http://localhost:8888/mqtt/status | python3 -m json.tool
```

`overall` 필드가 `ready` 또는 `degraded`이면 정상입니다. `blocked`이면 로그를 확인하세요.

**English**  
With the RPi app running, check via browser or curl:

```bash
# Preflight status
curl -s http://localhost:8888/preflight | python3 -m json.tool

# MQTT status
curl -s http://localhost:8888/mqtt/status | python3 -m json.tool
```

`overall` value of `ready` or `degraded` is normal. `blocked` requires investigation.

---

### 5-3. RPi 폐쇄 루프 감사 검증

**한국어**

```bash
cd /path/to/safe_deferral_claude
bash rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh
```

예상 출력: `[PASS] Closed-loop audit verification completed`

**English**

```bash
cd /path/to/safe_deferral_claude
bash rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh
```

Expected: `[PASS] Closed-loop audit verification completed`

---

## 6. 정지 절차 / Shutdown Procedure

### 6-1. 정지 순서

**한국어**

```
[1] ESP32 노드 전원 차단
[2] RPi Python 앱 종료  (Ctrl+C)
[3] Mac mini Python 앱 종료  (Ctrl+C)
[4] Docker 서비스 정지
```

Docker 정지:
```bash
cd ~/smarthome_workspace/docker
docker compose stop
```

**English**

```
[1] Power off ESP32 nodes
[2] Stop RPi Python app  (Ctrl+C)
[3] Stop Mac mini Python app  (Ctrl+C)
[4] Stop Docker services
```

Stop Docker:
```bash
cd ~/smarthome_workspace/docker
docker compose stop
```

---

## 7. 트러블슈팅 / Troubleshooting

| 증상 / Symptom | 원인 / Cause | 조치 / Action |
|---|---|---|
| Mac mini `MQTT connected` 미출력 | Mosquitto 미기동 | `docker compose ps` 확인, `docker compose up -d` |
| `Could not connect to MQTT broker at $MAC_MINI_HOST` | `.env` 미source — 변수가 문자 그대로 전달됨 | `source ~/smarthome_workspace/.env` 후 재실행 |
| RPi `Could not connect to MQTT broker` / `[Errno -2]` | `MQTT_HOST` 가 hostname 인데 mDNS 미지원, 또는 Mac mini 미기동 | `.env` 의 `MQTT_HOST`, `MAC_MINI_HOST`, `TIME_SYNC_HOST` 를 LAN IP 로 변경 |
| 80번 verify — `No telemetry snapshot found` | Mac mini `main.py` 미실행 또는 git pull 미완료 | Mac mini 에서 `git pull` 후 `.env` source → `main.py` 재실행 |
| RPi 대시보드 포트 접근 불가 | uvicorn 미설치 | `pip install uvicorn fastapi` |
| ESP32 SoftAP가 나타나지 않음 | 이미 WiFi 설정됨 또는 플래시 필요 | `sd_prov_erase()` 호출 또는 펌웨어 재플래시 |
| `TELEGRAM_TOKEN not set` 로그 | 토큰 미설정 | Mac mini `.env`에 `TELEGRAM_TOKEN=<token>` 추가 |
| LLM 응답 없음 / MockLlmClient 사용 | Ollama 미기동 또는 모델 미설치 | `docker compose logs ollama`, `ollama list` 확인 |
| CLASS_0 emergency 발생 | 가스/낙상/화재 센서 트리거 | 실제 비상 상황 확인; 테스트 시 fault injection 사용 |

---

## 8. 포트 요약 / Port Summary

| 서비스 / Service | 호스트 / Host | 포트 / Port |
|---|---|---|
| MQTT 브로커 (Mosquitto) | Mac mini | 1883 |
| Ollama LLM API | Mac mini | 11434 |
| Home Assistant | Mac mini | 8123 |
| 실험 대시보드 | RPi | 8888 |
| 거버넌스 UI | RPi | 8889 |

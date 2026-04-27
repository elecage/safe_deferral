# Raspberry Pi 실험 앱 설치 및 설정 / Raspberry Pi Experiment Apps Setup

---

## 1. 개요 / Overview

**한국어**  
Raspberry Pi 5는 실험 지원 호스트입니다. 모니터링 대시보드, 시나리오 오케스트레이션, 시뮬레이션/리플레이, 결과 저장·내보내기, 비권한 MQTT/페이로드 거버넌스 UI를 실행합니다.

**English**  
The Raspberry Pi 5 is the experiment-side support host. It runs the monitoring dashboard, scenario orchestration, simulation/replay, result export, and non-authoritative MQTT/payload governance UI.

---

## 2. 사전 요구사항 / Prerequisites

**한국어**

| 구성요소 | 버전 | 비고 |
|---|---|---|
| Python | 3.9 이상 | `python3 --version` |
| pip | 최신 권장 | `pip3 install --upgrade pip` |
| OS | Raspberry Pi OS (64-bit) Bullseye 이상 | |

**English**

| Component | Version | Notes |
|---|---|---|
| Python | 3.9+ | `python3 --version` |
| pip | Latest recommended | `pip3 install --upgrade pip` |
| OS | Raspberry Pi OS (64-bit) Bullseye or later | |

---

## 3. Python 패키지 설치 / Python Package Installation

**한국어**

```bash
pip3 install jsonschema fastapi uvicorn pytest
```

패키지 역할:
- `jsonschema` — 페이로드 검증 (거버넌스 백엔드)
- `fastapi` — 대시보드 및 거버넌스 UI HTTP 서버
- `uvicorn` — ASGI 서버 (FastAPI 실행)
- `pytest` — 단위 테스트 실행

**English**

```bash
pip3 install jsonschema fastapi uvicorn pytest
```

Package roles:
- `jsonschema` — Payload validation (governance backend)
- `fastapi` — Dashboard and governance UI HTTP server
- `uvicorn` — ASGI server for FastAPI
- `pytest` — Unit test execution

---

## 4. PYTHONPATH 설정 / PYTHONPATH Configuration

**한국어**  
모든 RPi 앱은 `rpi/code/` 를 Python 경로 루트로 사용합니다. 아래 방법 중 하나를 선택합니다.

**방법 A — 쉘 프로파일에 추가 (영구)**
```bash
echo 'export PYTHONPATH=/path/to/safe_deferral_claude/rpi/code' >> ~/.bashrc
source ~/.bashrc
```

**방법 B — 서버 실행 시 인라인 지정**
```bash
PYTHONPATH=/path/to/safe_deferral_claude/rpi/code uvicorn dashboard.app:create_app ...
```

**English**  
All RPi apps use `rpi/code/` as the Python path root. Choose one of the following methods.

**Method A — Add to shell profile (permanent)**
```bash
echo 'export PYTHONPATH=/path/to/safe_deferral_claude/rpi/code' >> ~/.bashrc
source ~/.bashrc
```

**Method B — Inline when starting the server**
```bash
PYTHONPATH=/path/to/safe_deferral_claude/rpi/code uvicorn dashboard.app:create_app ...
```

---

## 5. 단위 테스트 실행 / Running Unit Tests

**한국어**

```bash
cd /path/to/safe_deferral_claude/rpi/code
python3 -m pytest tests/test_rpi_components.py -v
```

예상 결과: `79 passed`

**English**

```bash
cd /path/to/safe_deferral_claude/rpi/code
python3 -m pytest tests/test_rpi_components.py -v
```

Expected result: `79 passed`

---

## 6. 대시보드 서버 시작 / Starting the Dashboard Server

**한국어**

```bash
cd /path/to/safe_deferral_claude/rpi/code
PYTHONPATH=. python3 -m uvicorn dashboard.app:create_app \
    --factory --host 0.0.0.0 --port 8888
```

브라우저에서 확인:
- Swagger UI: `http://<rpi-ip>:8888/docs`
- Preflight 상태: `http://<rpi-ip>:8888/preflight`
- 실험 런 목록: `http://<rpi-ip>:8888/runs`
- MQTT 상태: `http://<rpi-ip>:8888/mqtt/status`
- 시나리오 목록: `http://<rpi-ip>:8888/scenarios`

**English**

```bash
cd /path/to/safe_deferral_claude/rpi/code
PYTHONPATH=. python3 -m uvicorn dashboard.app:create_app \
    --factory --host 0.0.0.0 --port 8888
```

Verify in browser:
- Swagger UI: `http://<rpi-ip>:8888/docs`
- Preflight status: `http://<rpi-ip>:8888/preflight`
- Experiment run list: `http://<rpi-ip>:8888/runs`
- MQTT status: `http://<rpi-ip>:8888/mqtt/status`
- Scenario list: `http://<rpi-ip>:8888/scenarios`

---

## 7. 거버넌스 UI 서버 시작 / Starting the Governance UI Server

**한국어**

```bash
cd /path/to/safe_deferral_claude/rpi/code
PYTHONPATH=. python3 -m uvicorn governance.ui_app:create_governance_app \
    --factory --host 0.0.0.0 --port 8889
```

브라우저에서 확인:
- Swagger UI: `http://<rpi-ip>:8889/docs`
- 토픽 목록: `http://<rpi-ip>:8889/governance/topics`
- 제안 목록: `http://<rpi-ip>:8889/governance/proposals`
- 검증 보고서: `http://<rpi-ip>:8889/governance/validation-reports`

> **주의**: 거버넌스 UI는 레지스트리 파일을 직접 편집하거나 운영 제어 토픽을 발행하지 않습니다.

**English**

```bash
cd /path/to/safe_deferral_claude/rpi/code
PYTHONPATH=. python3 -m uvicorn governance.ui_app:create_governance_app \
    --factory --host 0.0.0.0 --port 8889
```

Verify in browser:
- Swagger UI: `http://<rpi-ip>:8889/docs`
- Topic list: `http://<rpi-ip>:8889/governance/topics`
- Proposals: `http://<rpi-ip>:8889/governance/proposals`
- Validation reports: `http://<rpi-ip>:8889/governance/validation-reports`

> **Note**: The governance UI does not directly edit registry files or publish operational control topics.

---

## 8. systemd 서비스 등록 (선택) / systemd Service Registration (Optional)

**한국어**  
재부팅 시 자동 시작이 필요하면 아래 서비스 파일을 생성합니다.

`/etc/systemd/system/sd-dashboard.service`:
```ini
[Unit]
Description=safe_deferral Experiment Dashboard
After=network.target

[Service]
User=pi
WorkingDirectory=/path/to/safe_deferral_claude/rpi/code
Environment=PYTHONPATH=/path/to/safe_deferral_claude/rpi/code
ExecStart=/usr/bin/python3 -m uvicorn dashboard.app:create_app \
    --factory --host 0.0.0.0 --port 8888
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable sd-dashboard
sudo systemctl start sd-dashboard
sudo systemctl status sd-dashboard
```

`/etc/systemd/system/sd-governance.service` (동일한 형식으로 포트 8889, `governance.ui_app:create_governance_app` 사용)

**English**  
For auto-start on reboot, create the following service files.

`/etc/systemd/system/sd-dashboard.service`:
```ini
[Unit]
Description=safe_deferral Experiment Dashboard
After=network.target

[Service]
User=pi
WorkingDirectory=/path/to/safe_deferral_claude/rpi/code
Environment=PYTHONPATH=/path/to/safe_deferral_claude/rpi/code
ExecStart=/usr/bin/python3 -m uvicorn dashboard.app:create_app \
    --factory --host 0.0.0.0 --port 8888
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable sd-dashboard
sudo systemctl start sd-dashboard
sudo systemctl status sd-dashboard
```

Create `/etc/systemd/system/sd-governance.service` with the same format using port 8889 and `governance.ui_app:create_governance_app`.

---

## 9. 정식 자산 파일 동기화 / Canonical Asset Sync

**한국어**  
RPi는 `common/` 하위의 정식 자산을 읽기 전용으로 사용합니다. Mac mini에서 변경이 있을 경우 아래 명령으로 동기화합니다.

```bash
# Mac mini → RPi rsync (Mac mini에서 실행)
rsync -av --delete \
    /path/to/safe_deferral_claude/common/ \
    pi@<rpi-ip>:/path/to/safe_deferral_claude/common/
```

**English**  
The RPi uses canonical assets under `common/` as read-only. If changes are made on the Mac mini, sync with:

```bash
# Mac mini → RPi rsync (run from Mac mini)
rsync -av --delete \
    /path/to/safe_deferral_claude/common/ \
    pi@<rpi-ip>:/path/to/safe_deferral_claude/common/
```

---

## 10. 모듈 구조 / Module Structure

**한국어**

```
rpi/code/
├── shared/                  # RpiAssetLoader (읽기 전용)
├── experiment_manager/      # RPI-01: 실험 런 생명주기
├── result_store/            # RPI-02: 결과 저장·내보내기
├── virtual_node_manager/    # RPI-03: 가상 노드 발행 시뮬레이션
├── virtual_behavior/        # RPI-04: 변이 엔진, 결함 주입
├── scenario_manager/        # RPI-05: 시나리오 계약 실행
├── mqtt_status/             # RPI-06: MQTT 인터페이스 상태 모니터
├── preflight/               # RPI-07: 사전 준비 체크
├── dashboard/               # RPI-08: FastAPI 대시보드 (포트 8888)
└── governance/              # RPI-09/10: 거버넌스 백엔드 + UI (포트 8889)
```

**English**

```
rpi/code/
├── shared/                  # RpiAssetLoader (read-only)
├── experiment_manager/      # RPI-01: Experiment run lifecycle
├── result_store/            # RPI-02: Result storage and export
├── virtual_node_manager/    # RPI-03: Virtual node publish simulation
├── virtual_behavior/        # RPI-04: Mutation engine, fault injection
├── scenario_manager/        # RPI-05: Scenario contract execution
├── mqtt_status/             # RPI-06: MQTT interface health monitor
├── preflight/               # RPI-07: Preflight readiness checks
├── dashboard/               # RPI-08: FastAPI dashboard (port 8888)
└── governance/              # RPI-09/10: Governance backend + UI (port 8889)
```

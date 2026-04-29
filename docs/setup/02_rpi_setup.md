# Raspberry Pi 실험 앱 설치 및 설정 / Raspberry Pi Experiment Apps Setup

---

## 1. 개요 / Overview

**한국어**  
Raspberry Pi 5는 실험 지원 호스트입니다. 모니터링 대시보드, 시나리오 오케스트레이션, 시뮬레이션/리플레이, 결과 저장·내보내기, 비권한 MQTT/페이로드 거버넌스 UI를 실행합니다.

설치는 세 단계로 구성되며 모두 `rpi/scripts/` 하위의 스크립트로 처리됩니다:
- **install/** — 시스템 패키지, Python venv, 의존성, 시간 동기화 클라이언트
- **configure/** — 환경 변수, Mac mini asset 동기화, 시간 동기화, 시뮬레이션 런타임, 폴트 프로파일
- **verify/** — 런타임·MQTT·페이로드 정렬·폐쇄 루프 감사 검증

> **전제 조건**: Mac mini 설치(`01_mac_mini_setup.md`)가 완료되고 MQTT 브로커가 실행 중이어야 합니다.

**English**  
The Raspberry Pi 5 is the experiment-side support host. It runs the monitoring dashboard, scenario orchestration, simulation/replay, result export, and non-authoritative MQTT/payload governance UI.

Installation is divided into three phases, all handled by scripts under `rpi/scripts/`:
- **install/** — System packages, Python venv, dependencies, time sync client
- **configure/** — Environment variables, Mac mini asset sync, time sync, simulation runtime, fault profiles
- **verify/** — Runtime, MQTT, payload alignment, and closed-loop audit verification

> **Prerequisite**: Mac mini setup (`01_mac_mini_setup.md`) must be complete and the MQTT broker must be running.

---

## 2. 사전 요구사항 / Prerequisites

**한국어**
- Raspberry Pi OS (64-bit) Bookworm 또는 Bullseye
- Python 3.11 이상
- Mac mini와 동일한 LAN에 연결
- Mac mini의 호스트명 확인 (configure 단계에서 필요 — 아래 참조)

> **Mac mini 주소 확인 방법**  
> macOS는 Bonjour(mDNS)를 통해 `<호스트명>.local`로 자동 노출됩니다.  
> Mac mini 터미널에서 실행:
> ```bash
> scutil --get LocalHostName
> # 예시 출력: mac-mini
> # → RPi에서 mac-mini.local 로 접속 가능
> ```
> RPi에서 `ping mac-mini.local`로 통신 여부를 확인합니다.  
> mDNS가 동작하지 않으면 IP 직접 입력: `ipconfig getifaddr en0`

**English**
- Raspberry Pi OS (64-bit) Bookworm or Bullseye
- Python 3.11 or later
- Connected to the same LAN as the Mac mini
- Mac mini hostname on hand (required in the configure phase — see below)

> **How to find the Mac mini address**  
> macOS advertises itself via Bonjour (mDNS) as `<hostname>.local`.  
> Run on the Mac mini terminal:
> ```bash
> scutil --get LocalHostName
> # Example output: mac-mini
> # → RPi can reach it as mac-mini.local
> ```
> Verify from the RPi with `ping mac-mini.local`.  
> If mDNS does not work, use the IP directly: `ipconfig getifaddr en0`

---

## 3. 설치 (install) / Installation

**한국어**  
RPi에서 저장소 루트로 이동한 뒤 스크립트를 순서대로 실행합니다.

```bash
cd /path/to/safe_deferral_claude
```

### 3-1. 사전 검사

```bash
bash rpi/scripts/install/00_preflight_rpi.sh
```

OS, Python 3.11+, 디스크 공간(최소 5 GB), 네트워크 연결을 확인합니다.  
**결과 확인:** `[PASS] All preflight checks completed successfully`

### 3-2. 시스템 패키지 설치

```bash
bash rpi/scripts/install/10_install_system_packages_rpi.sh
```

APT로 다음을 설치합니다: `python3`, `python3-venv`, `git`, `mosquitto-clients`, `chrony`, `jq`, `rsync`, `curl`  
> `sudo` 권한이 필요합니다. 스크립트가 실행 중 세션을 유지합니다.

**결과 확인:** `[PASS] System packages installed successfully`

### 3-3. Python 가상환경 생성

```bash
bash rpi/scripts/install/20_create_python_venv_rpi.sh
```

`~/smarthome_workspace/.venv-rpi`에 Python 3.11+ 가상환경을 생성하고 pip/setuptools/wheel을 최신으로 업데이트합니다.  
**결과 확인:** `[PASS] Virtual environment ready at ~/smarthome_workspace/.venv-rpi`

### 3-4. Python 의존성 설치

```bash
bash rpi/scripts/install/30_install_python_deps_rpi.sh
```

`requirements-rpi.txt`의 패키지를 설치합니다. 필수 패키지(`paho-mqtt`, `pytest`, `PyYAML`, `jsonschema`)와 선택 패키지(`fastapi`, `uvicorn`, `pandas`)를 검증합니다.  
**결과 확인:** `[PASS] Python dependencies installed and verified successfully`

### 3-5. 시간 동기화 클라이언트 설치

```bash
bash rpi/scripts/install/40_install_time_sync_client_rpi.sh
```

Chrony 서비스를 활성화하고 시작합니다.  
**결과 확인:** `[PASS] Time sync client is active`

---

**English**  
From the repository root on the RPi:

```bash
cd /path/to/safe_deferral_claude
```

### 3-1. Preflight checks

```bash
bash rpi/scripts/install/00_preflight_rpi.sh
```

Checks OS, Python 3.11+, disk space (minimum 5 GB), and network.  
**Success:** `[PASS] All preflight checks completed successfully`

### 3-2. Install system packages

```bash
bash rpi/scripts/install/10_install_system_packages_rpi.sh
```

Installs via APT: `python3`, `python3-venv`, `git`, `mosquitto-clients`, `chrony`, `jq`, `rsync`, `curl`  
> Requires `sudo`. The script keeps the session alive automatically.

**Success:** `[PASS] System packages installed successfully`

### 3-3. Create Python virtual environment

```bash
bash rpi/scripts/install/20_create_python_venv_rpi.sh
```

Creates a Python 3.11+ venv at `~/smarthome_workspace/.venv-rpi` and updates pip/setuptools/wheel.  
**Success:** `[PASS] Virtual environment ready at ~/smarthome_workspace/.venv-rpi`

### 3-4. Install Python dependencies

```bash
bash rpi/scripts/install/30_install_python_deps_rpi.sh
```

Installs packages from `requirements-rpi.txt`. Validates required packages (`paho-mqtt`, `pytest`, `PyYAML`, `jsonschema`) and optional packages (`fastapi`, `uvicorn`, `pandas`).  
**Success:** `[PASS] Python dependencies installed and verified successfully`

### 3-5. Install time sync client

```bash
bash rpi/scripts/install/40_install_time_sync_client_rpi.sh
```

Enables and starts the Chrony service.  
**Success:** `[PASS] Time sync client is active`

---

## 4. 설정 (configure) / Configuration

**한국어**  
configure 단계는 먼저 환경 변수 파일(`.env`)을 작성한 뒤 나머지 스크립트를 실행합니다.

### 4-1. 환경 변수 파일 작성

```bash
bash rpi/scripts/configure/10_write_env_files_rpi.sh
```

`~/smarthome_workspace/.env`를 생성합니다. 스크립트 실행 후 아래 항목을 실제 값으로 편집합니다:

```bash
nano ~/smarthome_workspace/.env
```

확인 및 수정이 필요한 항목:
| 키 | 설명 | 기본값 | 조치 |
|---|---|---|---|
| `MAC_MINI_HOST` | Mac mini 호스트명 또는 IP | `mac-mini.local` | Bonjour 동작 시 기본값 유지, 불가 시 IP로 교체 |
| `MAC_MINI_USER` | Mac mini SSH 사용자명 | 현재 RPi 로그인 사용자 | asset 동기화에 사용하는 Mac mini 계정명으로 수정 |
| `MQTT_HOST` | MQTT 브로커 주소 | `$MAC_MINI_HOST` | MAC_MINI_HOST와 동일하게 자동 참조됨 |
| `MQTT_PORT` | MQTT 포트 | `1883` | 변경 불필요 |
| `MQTT_PASS` | MQTT 비밀번호 | `CHANGE_ME` | 아래 참조 |

스크립트 실행 후 항상 아래 경고가 출력됩니다 — 정상입니다:
```
[WARNING] ACTION REQUIRED: Please verify MAC_MINI_HOST, MAC_MINI_USER, MQTT_HOST, and MQTT_PASS manually in .env
```
이 경고는 자동으로 사라지지 않으므로, `.env`를 직접 열어 값을 확인·수정한 뒤 다음 단계로 진행합니다.

추가로 아래 경고 중 해당하는 항목이 있으면 함께 수정합니다:

```
[WARNING] Placeholder or legacy values must be fixed before sync/verification
```

| 경고 메시지 | 원인 | 해결 방법 |
|---|---|---|
| `Placeholder IP 192.168.1.100 remains` | `MAC_MINI_HOST` 또는 `MQTT_HOST`가 `192.168.1.100` | 실제 호스트명 또는 IP로 교체 |
| `Placeholder MAC_MINI_USER=mac_user remains` | `MAC_MINI_USER`가 `mac_user` | 실제 Mac mini 사용자명으로 교체 |
| `MQTT_PASS is still CHANGE_ME` | `MQTT_PASS=CHANGE_ME` 그대로 | 아래 참조 |
| `Legacy smarthome/* topic values remain` | `.env`에 `smarthome/` 포함된 토픽 | 해당 줄 삭제 또는 `safe_deferral/`로 교체 |

> **MAC_MINI_HOST 확인 방법**  
> macOS Bonjour가 동작하는 환경에서는 기본값(`mac-mini.local`) 그대로 사용 가능합니다.  
> 동일 LAN에서 `ping mac-mini.local`이 응답하면 변경 불필요.  
> mDNS가 동작하지 않는 경우 Mac mini에서 `ipconfig getifaddr en0`으로 IP를 확인하세요.

> **MQTT_PASS 처리**  
> Mac mini의 Mosquitto는 `allow_anonymous true`로 설정되어 있어 비밀번호가 필요 없습니다.  
> `MQTT_PASS=CHANGE_ME` 경고가 표시되면 아래 명령으로 빈 값으로 지워주세요:
> ```bash
> sed -i 's/^MQTT_PASS=CHANGE_ME$/MQTT_PASS=/' ~/smarthome_workspace/.env
> ```
> 비밀번호 인증을 사용하는 환경이라면 실제 비밀번호로 교체하세요.

### 4-2. Mac mini 런타임 asset 동기화

```bash
bash rpi/scripts/configure/20_sync_runtime_assets_rpi.sh
```

Mac mini에서 정책·스키마·MQTT·페이로드 reference asset을 rsync로 동기화합니다.  
스크립트는 `-o BatchMode=yes`(비밀번호 입력 없는 키 전용 모드)로 rsync를 실행하므로,
**사전에 SSH 키 기반 접속이 설정되어 있어야 합니다.**

> **SSH 키 설정 방법**
>
> 1. RPi에 키가 있는지 확인:
>    ```bash
>    ls ~/.ssh/id_*.pub
>    ```
>    파일이 있으면 2번으로 넘어갑니다. 없으면 키를 생성합니다:
>    ```bash
>    ssh-keygen -t ed25519 -C "rpi-sync" -N "" -f ~/.ssh/id_ed25519
>    ```
>    (`ed25519`는 SSH 인증에 사용하는 암호화 알고리즘입니다. 현재 가장 권장되는 방식입니다.)
>
> 2. Mac mini에 공개키 등록 (Mac mini 비밀번호를 한 번 입력):
>    ```bash
>    ssh-copy-id <MAC_MINI_USER>@<MAC_MINI_HOST>
>    # 예: ssh-copy-id elecage@mac-mini.local
>    ```
>
> 3. 키 접속 확인 (비밀번호 없이 OK가 출력되면 성공):
>    ```bash
>    ssh -o BatchMode=yes <MAC_MINI_USER>@<MAC_MINI_HOST> echo OK
>    ```

**결과 확인:** `[PASS] Runtime assets synced`

### 4-3. 시간 동기화 설정

```bash
bash rpi/scripts/configure/30_configure_time_sync_rpi.sh
```

Chrony를 Mac mini를 NTP 소스로 사용하도록 설정합니다.  
**결과 확인:** `[PASS] Chrony configured for LAN-only time sync`

### 4-4. 시뮬레이션 런타임 설정

```bash
bash rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh
```

시뮬레이션 로그, 시나리오, 검증 결과 디렉터리를 생성합니다.  
**결과 확인:** `[PASS] Simulation runtime configured`

### 4-5. 폴트 프로파일 설정

```bash
bash rpi/scripts/configure/50_configure_fault_profiles_rpi.sh
```

safe-deferral 검증용 폴트 프로파일을 구성합니다.  
> RPi 권한 플래그(`ALLOW_RPI_ACTUATION`, `ALLOW_RPI_POLICY_AUTHORITY`, `ALLOW_RPI_DOORLOCK_CONTROL`)가 모두 `false`여야 합니다.

**결과 확인:** `[PASS] Fault profile verification configured`

---

**English**

### 4-1. Write environment variables

```bash
bash rpi/scripts/configure/10_write_env_files_rpi.sh
```

Creates `~/smarthome_workspace/.env`. After running, edit the file with real values:

```bash
nano ~/smarthome_workspace/.env
```

Values to verify and update:
| Key | Description | Default | Action |
|---|---|---|---|
| `MAC_MINI_HOST` | Mac mini hostname or IP | `mac-mini.local` | Keep default if Bonjour works, replace with IP otherwise |
| `MAC_MINI_USER` | Mac mini SSH username | Current RPi login user | Set to the Mac mini account used for asset sync |
| `MQTT_HOST` | MQTT broker address | `$MAC_MINI_HOST` | Automatically references MAC_MINI_HOST |
| `MQTT_PORT` | MQTT port | `1883` | No change needed |
| `MQTT_PASS` | MQTT password | `CHANGE_ME` | See note below |

The script always prints the following warning — this is expected:
```
[WARNING] ACTION REQUIRED: Please verify MAC_MINI_HOST, MAC_MINI_USER, MQTT_HOST, and MQTT_PASS manually in .env
```
This warning does not clear automatically. Open `.env`, verify each value, then proceed to the next step.

If any placeholder is still present, you will also see:
```
[WARNING] Placeholder or legacy values must be fixed before sync/verification
```

| Warning message | Cause | Fix |
|---|---|---|
| `Placeholder IP 192.168.1.100 remains` | `MAC_MINI_HOST` or `MQTT_HOST` is `192.168.1.100` | Replace with real hostname or IP |
| `Placeholder MAC_MINI_USER=mac_user remains` | `MAC_MINI_USER` is `mac_user` | Replace with actual Mac mini username |
| `MQTT_PASS is still CHANGE_ME` | `MQTT_PASS=CHANGE_ME` unchanged | See note below |
| `Legacy smarthome/* topic values remain` | `.env` contains `smarthome/` topics | Delete the line or replace with `safe_deferral/` |

> **MAC_MINI_HOST**  
> If macOS Bonjour is active on the same LAN, the default (`mac-mini.local`) works without change.  
> Verify with `ping mac-mini.local` from the RPi.  
> If mDNS does not resolve, use the IP from `ipconfig getifaddr en0` on the Mac mini.

> **MQTT_PASS handling**  
> The Mac mini Mosquitto broker is configured with `allow_anonymous true`, so no password is required.  
> If you see a `MQTT_PASS=CHANGE_ME` warning, clear it with:
> ```bash
> sed -i 's/^MQTT_PASS=CHANGE_ME$/MQTT_PASS=/' ~/smarthome_workspace/.env
> ```
> If your environment uses password authentication, replace it with the real password instead.

### 4-2. Sync Mac mini runtime assets

```bash
bash rpi/scripts/configure/20_sync_runtime_assets_rpi.sh
```

Rsyncs policy, schema, MQTT, and payload reference assets from the Mac mini.  
The script uses `-o BatchMode=yes` (key-only, no password prompt), so
**SSH key-based access must be configured before running this step.**

> **SSH key setup**
>
> 1. Check if a key already exists on the RPi:
>    ```bash
>    ls ~/.ssh/id_*.pub
>    ```
>    If a file is listed, skip to step 2. Otherwise generate a key:
>    ```bash
>    ssh-keygen -t ed25519 -C "rpi-sync" -N "" -f ~/.ssh/id_ed25519
>    ```
>    (`ed25519` is the encryption algorithm used for SSH authentication — the current recommended option.)
>
> 2. Register the public key on the Mac mini (enter the Mac mini password once):
>    ```bash
>    ssh-copy-id <MAC_MINI_USER>@<MAC_MINI_HOST>
>    # e.g. ssh-copy-id elecage@mac-mini.local
>    ```
>
> 3. Verify key-based access (OK printed without a password prompt means success):
>    ```bash
>    ssh -o BatchMode=yes <MAC_MINI_USER>@<MAC_MINI_HOST> echo OK
>    ```

**Success:** `[PASS] Runtime assets synced`

### 4-3. Configure time sync

```bash
bash rpi/scripts/configure/30_configure_time_sync_rpi.sh
```

Configures Chrony to use the Mac mini as the NTP source.  
**Success:** `[PASS] Chrony configured for LAN-only time sync`

### 4-4. Configure simulation runtime

```bash
bash rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh
```

Creates simulation log, scenario, and verification result directories.  
**Success:** `[PASS] Simulation runtime configured`

### 4-5. Configure fault profiles

```bash
bash rpi/scripts/configure/50_configure_fault_profiles_rpi.sh
```

Configures fault profiles for safe-deferral verification.  
> RPi authority flags (`ALLOW_RPI_ACTUATION`, `ALLOW_RPI_POLICY_AUTHORITY`, `ALLOW_RPI_DOORLOCK_CONTROL`) must all be `false`.

**Success:** `[PASS] Fault profile verification configured`

---

## 5. 검증 (verify) / Verification

**한국어**

```bash
# 스크립트 문법 검사
bash rpi/scripts/verify/00_verify_rpi_script_syntax.sh

# 기본 런타임·권한 경계·asset 동기화·시간 동기화 확인
bash rpi/scripts/verify/70_verify_rpi_base_runtime.sh

# MQTT 토픽 레지스트리 및 페이로드 계약 정렬 확인
bash rpi/scripts/verify/75_verify_rpi_mqtt_payload_alignment.sh

# 폐쇄 루프 폴트 주입 감사 확인
bash rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh
```

모든 단계가 `[PASS]`로 끝나면 RPi 실험 노드가 정상 동작 준비 완료입니다.

**English**

```bash
# Script syntax validation
bash rpi/scripts/verify/00_verify_rpi_script_syntax.sh

# Base runtime, authority boundaries, asset sync, and time sync
bash rpi/scripts/verify/70_verify_rpi_base_runtime.sh

# MQTT topic registry and payload contract alignment
bash rpi/scripts/verify/75_verify_rpi_mqtt_payload_alignment.sh

# Closed-loop fault-injection audit
bash rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh
```

All steps passing `[PASS]` confirms the RPi experiment node is ready.

---

## 6. 단위 테스트 실행 / Running Unit Tests

**한국어**

```bash
source ~/smarthome_workspace/.venv-rpi/bin/activate
cd /path/to/safe_deferral_claude/rpi/code
python -m pytest tests/test_rpi_components.py -v
```

예상 결과: `79 passed`

**English**

```bash
source ~/smarthome_workspace/.venv-rpi/bin/activate
cd /path/to/safe_deferral_claude/rpi/code
python -m pytest tests/test_rpi_components.py -v
```

Expected result: `79 passed`

---

## 7. 대시보드 서버 시작 / Starting the Dashboard Server

**한국어**

```bash
source ~/smarthome_workspace/.venv-rpi/bin/activate
cd /path/to/safe_deferral_claude/rpi/code
PYTHONPATH=. python -m uvicorn dashboard.app:create_app \
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
source ~/smarthome_workspace/.venv-rpi/bin/activate
cd /path/to/safe_deferral_claude/rpi/code
PYTHONPATH=. python -m uvicorn dashboard.app:create_app \
    --factory --host 0.0.0.0 --port 8888
```

Verify in browser:
- Swagger UI: `http://<rpi-ip>:8888/docs`
- Preflight status: `http://<rpi-ip>:8888/preflight`
- Experiment run list: `http://<rpi-ip>:8888/runs`
- MQTT status: `http://<rpi-ip>:8888/mqtt/status`
- Scenario list: `http://<rpi-ip>:8888/scenarios`

---

## 8. 거버넌스 UI 서버 시작 / Starting the Governance UI Server

**한국어**

```bash
source ~/smarthome_workspace/.venv-rpi/bin/activate
cd /path/to/safe_deferral_claude/rpi/code
PYTHONPATH=. python -m uvicorn governance.ui_app:create_governance_app \
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
source ~/smarthome_workspace/.venv-rpi/bin/activate
cd /path/to/safe_deferral_claude/rpi/code
PYTHONPATH=. python -m uvicorn governance.ui_app:create_governance_app \
    --factory --host 0.0.0.0 --port 8889
```

Verify in browser:
- Swagger UI: `http://<rpi-ip>:8889/docs`
- Topic list: `http://<rpi-ip>:8889/governance/topics`
- Proposals: `http://<rpi-ip>:8889/governance/proposals`
- Validation reports: `http://<rpi-ip>:8889/governance/validation-reports`

> **Note**: The governance UI does not directly edit registry files or publish operational control topics.

---

## 9. systemd 서비스 등록 (선택) / systemd Service Registration (Optional)

**한국어**  
재부팅 시 자동 시작이 필요하면 서비스 파일을 생성합니다.

`/etc/systemd/system/sd-dashboard.service`:
```ini
[Unit]
Description=safe_deferral Experiment Dashboard
After=network.target

[Service]
User=pi
WorkingDirectory=/path/to/safe_deferral_claude/rpi/code
Environment=PYTHONPATH=/path/to/safe_deferral_claude/rpi/code
ExecStart=/home/pi/smarthome_workspace/.venv-rpi/bin/python -m uvicorn \
    dashboard.app:create_app --factory --host 0.0.0.0 --port 8888
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

거버넌스 UI는 동일한 형식으로 포트 8889와 `governance.ui_app:create_governance_app`을 사용합니다 (`sd-governance.service`).

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
ExecStart=/home/pi/smarthome_workspace/.venv-rpi/bin/python -m uvicorn \
    dashboard.app:create_app --factory --host 0.0.0.0 --port 8888
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

Create `sd-governance.service` with the same format using port 8889 and `governance.ui_app:create_governance_app`.

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

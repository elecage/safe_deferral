# rpi/docs

이 디렉터리는 Raspberry Pi 5 기반 실험 지원 환경의 설치, 구성, 검증, 실행 절차를 설명한다.

현재 프로젝트에서 `rpi/`는 운영 허브가 아니다. Raspberry Pi는 Mac mini를 대체하지 않으며, 논문용 실험 실행, 가상 노드, fault injection, 모니터링, 결과 수집, MQTT/payload 정합성 검증을 지원하는 비권한 계층이다.

RPi는 다음 권한을 가져서는 안 된다.

- policy authority
- validator authority
- caregiver approval authority
- actuator authority
- doorlock execution authority

---

## 1. 역할

`rpi/`의 현재 역할은 다음과 같다.

- 실험 패키지 A~G 트라이얼 실행 및 결과 기록
- 가상 노드 생성·관리 및 MQTT 페이로드 발행 (실험 소스 전용)
- 물리 노드(ESP32) + 가상 노드 통합 presence 추적
- fault injection profile 기반 이상 페이로드 생성
- MQTT/payload reference alignment 확인
- closed-loop audit 관찰 및 결과 분석
- 실험 preflight readiness 점검

장치별 경계는 다음과 같이 유지한다.

- `mac_mini/`: operational hub
- `rpi/`: experiment support host
- `esp32/`: bounded physical node layer
- `stm32/`: out-of-band timing/measurement support
- `integration/`: scenario, fixture, measurement, result assets

---

## 2. 디렉터리 구조

```text
rpi/
├── code/
│   ├── main.py                         # 진입점 — 모든 서비스 시작
│   ├── observation_store.py            # MQTT 관찰 버퍼
│   ├── dashboard/
│   │   ├── app.py                      # FastAPI 대시보드 앱 (port 8888)
│   │   └── static/index.html           # 브라우저 UI
│   ├── experiment_manager/             # 실험 런 생성/관리
│   ├── experiment_package/             # 패키지 A~G 정의, fault profiles, trial store
│   │   ├── definitions.py              # PackageId, PackageDefinition, PACKAGES
│   │   ├── fault_profiles.py           # FaultProfile, FAULT_PROFILES (9개)
│   │   ├── trial_store.py              # TrialResult, TrialStore, compute_metrics
│   │   └── runner.py                   # PackageRunner — 트라이얼 오케스트레이션
│   ├── governance/                     # MQTT/payload 거버넌스 백엔드
│   ├── governance_ui/                  # 거버넌스 UI (port 8889)
│   ├── mqtt_status/                    # MQTT 브로커 연결 상태 모니터
│   ├── node_presence/
│   │   └── registry.py                 # NodePresenceRegistry — 물리+가상 통합 추적
│   ├── preflight/
│   │   └── readiness.py                # PreflightManager — READY/DEGRADED/BLOCKED
│   ├── result_store/                   # 실험 결과 저장
│   ├── scenario_manager/               # 시나리오 계약 로드·관리
│   ├── shared/
│   │   └── asset_loader.py             # RpiAssetLoader — 공통 asset 접근
│   ├── virtual_node_manager/
│   │   ├── manager.py                  # VirtualNodeManager
│   │   └── models.py                   # VirtualNode, VirtualNodeProfile, ...
│   └── tests/
│       └── test_rpi_components.py      # 유닛 테스트 (79개)
├── docs/
│   ├── README.md                       # 이 파일
│   └── RPI_CLEANUP_PLAN.md
└── scripts/
    ├── install/
    ├── configure/
    └── verify/
```

---

## 3. Runtime Layout

RPi 스크립트는 기본적으로 다음 local workspace를 사용한다.

```text
~/smarthome_workspace/
├── .env
├── .venv-rpi/
├── requirements-rpi-lock.txt
├── config/
│   ├── policies/
│   ├── schemas/
│   ├── mqtt/
│   └── payloads/
├── scenarios/
└── logs/
    ├── simulation/
    └── verification/
```

`config/` 아래의 파일들은 RPi 권한의 원본이 아니다. Mac mini runtime/reference asset을 실험 검증용으로 복사한 local mirror다.

---

## 4. 앱 실행

### 사전 요건

```bash
cd rpi/code
source ~/smarthome_workspace/.venv-rpi/bin/activate
```

### 실험 노드 시작

```bash
python main.py
```

기본 서비스:

| 서비스 | 포트 | 설명 |
|---|---|---|
| 대시보드 UI | 8888 | 실험 모니터링 및 실행 |
| 거버넌스 UI | 8889 | MQTT/payload 거버넌스 탐색 |
| MQTT 모니터 | — | 브로커 연결 추적 |
| 가상 노드 매니저 | — | 가상 센서/액추에이터 관리 |

환경변수 (`.env` 또는 셸에서 설정):

| 변수 | 기본값 | 설명 |
|---|---|---|
| `MQTT_HOST` | `mac-mini.local` | MQTT 브로커 호스트 |
| `MQTT_PORT` | `1883` | MQTT 브로커 포트 |
| `MQTT_USER` | (없음) | MQTT 인증 사용자 |
| `MQTT_PASS` | (없음) | MQTT 인증 비밀번호 |
| `DASHBOARD_PORT` | `8888` | 대시보드 포트 |
| `GOVERNANCE_PORT` | `8889` | 거버넌스 UI 포트 |

### 대시보드 접근

```
http://localhost:8888        # 대시보드
http://localhost:8889        # 거버넌스 UI
http://localhost:8888/docs   # API 문서 (Swagger)
```

### 테스트 실행

```bash
cd rpi/code
python -m pytest tests/ -q
```

---

## 5. Install Sequence

저장소 루트에서 실행한다.

```bash
bash rpi/scripts/install/00_preflight_rpi.sh
bash rpi/scripts/install/10_install_system_packages_rpi.sh
bash rpi/scripts/install/20_create_python_venv_rpi.sh
bash rpi/scripts/install/30_install_python_deps_rpi.sh
bash rpi/scripts/install/40_install_time_sync_client_rpi.sh
```

Install 단계는 다음을 준비한다.

- Raspberry Pi OS/Linux 환경 확인
- Python 3.11+ 확인
- `python3`, `python3-venv`, `git`, `mosquitto-clients`, `chrony`, `jq`, `rsync`, `curl` 설치
- `~/smarthome_workspace/.venv-rpi` 생성
- `requirements-rpi.txt` 기반 Python dependency 설치 (fastapi, uvicorn, paho-mqtt, python-dotenv 포함)
- Chrony time sync client 활성화

---

## 6. Configure Sequence

권장 순서:

```bash
bash rpi/scripts/configure/10_write_env_files_rpi.sh
bash rpi/scripts/configure/20_sync_runtime_assets_rpi.sh
bash rpi/scripts/configure/30_configure_time_sync_rpi.sh
bash rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh
bash rpi/scripts/configure/50_configure_fault_profiles_rpi.sh
```

### `10_write_env_files_rpi.sh`

`~/smarthome_workspace/.env`를 생성하거나 누락된 키를 추가한다.

핵심 변수:

- `MAC_MINI_HOST`, `MAC_MINI_USER`
- `MQTT_HOST`, `MQTT_PORT`, `MQTT_USER`, `MQTT_PASS`
- `DASHBOARD_PORT` (기본 8888), `GOVERNANCE_PORT` (기본 8889)
- `ALLOW_RPI_ACTUATION=false`
- `ALLOW_RPI_POLICY_AUTHORITY=false`
- `ALLOW_RPI_DOORLOCK_CONTROL=false`

### `20_sync_runtime_assets_rpi.sh`

Mac mini의 current runtime/reference asset을 RPi local mirror로 동기화한다.

필수 전제:

- `MAC_MINI_HOST`와 `MAC_MINI_USER`가 실제 값이어야 한다.
- Mac mini의 Remote Login/SSH가 켜져 있어야 한다.
- RPi에서 Mac mini로 key-based SSH 접속이 가능해야 한다.
- Mac mini에서 `mac_mini/scripts/configure/50_deploy_policy_files.sh`가 먼저 실행되어 있어야 한다.

---

## 7. Verify Sequence

권장 순서:

```bash
bash rpi/scripts/verify/00_verify_rpi_script_syntax.sh
bash rpi/scripts/verify/70_verify_rpi_base_runtime.sh
bash rpi/scripts/verify/75_verify_rpi_mqtt_payload_alignment.sh
bash rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh
```

---

## 8. 실험 패키지 A~G 사용 방법

### 대시보드 UI를 통한 실험 실행

1. **① 패키지 선택** — A~G 패키지 카드에서 선택. 폴트 프로파일, 비교 조건, 추천 시나리오 선택.
2. **② 노드 설정** — 가상 노드 생성 및 시작. 물리+가상 노드 통합 현황 확인.
3. **③ 실험 실행** — 패키지 런 생성 → "▶ 트라이얼 1회 실행" 반복 또는 자동 실행. 실시간 결과 테이블 확인.
4. **④ 결과 분석** — 패키지 A/B/C 전용 메트릭 뷰. JSON/CSV/Markdown 내보내기.

### API를 통한 실험 실행

```bash
# 패키지 목록 조회
curl http://localhost:8888/packages

# 패키지 런 생성 (패키지 A, 5회 트라이얼)
curl -X POST http://localhost:8888/package_runs \
  -H "Content-Type: application/json" \
  -d '{"package_id":"A","scenario_ids":["S_CLASS1_BASELINE_01"],"trial_count":5}'

# 트라이얼 1회 실행
curl -X POST http://localhost:8888/package_runs/{run_id}/trial \
  -H "Content-Type: application/json" \
  -d '{"node_id":"<virtual-node-id>","scenario_id":"S_CLASS1_BASELINE_01"}'

# 결과 메트릭 조회
curl http://localhost:8888/package_runs/{run_id}/metrics

# Markdown 내보내기
curl http://localhost:8888/package_runs/{run_id}/export/markdown
```

---

## 9. 노드 Presence 시스템

RPi는 `safe_deferral/node/presence` 토픽을 통해 물리(ESP32) + 가상 노드를 통합 추적한다.

- **물리 노드**: ESP32가 connect 시 explicit online publish, 연결 끊기면 MQTT LWT로 offline 자동 발행
- **가상 노드**: VirtualNodeManager가 `start_node()` → online, `stop_node()/delete_node()` → offline 발행

```bash
# 노드 현황 조회
curl http://localhost:8888/node_presence

# 특정 노드 조회
curl http://localhost:8888/node_presence/{node_id}
```

Presence payload 형식:
```json
{
  "node_id": "rpi.virtual_context_node_abc123",
  "node_type": "context_node",
  "source": "virtual",
  "status": "online",
  "timestamp_ms": 1746000000000
}
```

---

## 10. Preflight 점검

```bash
curl http://localhost:8888/preflight
```

| 체크 | required | 실패 시 |
|---|---|---|
| `canonical_assets_present` | ✅ | BLOCKED |
| `scenarios_present` | ✅ | BLOCKED |
| `physical_nodes_present` | ❌ | DEGRADED (가상 전용 모드) |
| `stm32_present` | ❌ | DEGRADED (소프트웨어 레이턴시) |

DEGRADED는 실험 실행 가능, 결과에 제한 조건 명시 필요.
BLOCKED는 실험 실행 불가.

---

## 11. Common SSH/Sync Issues

### Placeholder 값이 남아 있는 경우

```bash
grep -E 'MAC_MINI_HOST|MAC_MINI_USER|MQTT_HOST|MQTT_PASS' ~/smarthome_workspace/.env
```

### Mac mini SSH가 꺼져 있는 경우

```bash
sudo systemsetup -setremotelogin on
```

### Key-based SSH가 안 되는 경우

```bash
ssh-keygen -t ed25519 -C "rpi-sync"
ssh-copy-id <MAC_MINI_USER>@<MAC_MINI_HOST>
```

### Mac mini runtime/reference asset 경로가 없는 경우

```bash
bash mac_mini/scripts/configure/50_deploy_policy_files.sh
```

---

## 12. 구현 현황

| 컴포넌트 | 상태 | 비고 |
|---|---|---|
| VirtualNodeManager | ✅ 완료 | 가상 노드 생성/시작/정지/삭제, presence 발행 |
| ExperimentManager | ✅ 완료 | 실험 런 생성·관리 |
| ResultStore | ✅ 완료 | 결과 저장 |
| ScenarioManager | ✅ 완료 | 시나리오 계약 로드 |
| PreflightManager | ✅ 완료 | READY/DEGRADED/BLOCKED 점검 |
| MqttStatusMonitor | ✅ 완료 | 브로커 연결 상태 |
| ObservationStore | ✅ 완료 | MQTT 관찰 버퍼 + correlation_id 검색 |
| PackageRunner (A~G) | ✅ 완료 | 트라이얼 오케스트레이션, 9개 fault profile |
| TrialStore | ✅ 완료 | 트라이얼 결과 + 패키지별 메트릭 |
| NodePresenceRegistry | ✅ 완료 | 물리+가상 통합 presence 추적 |
| Dashboard (port 8888) | ✅ 완료 | FastAPI + 브라우저 UI (4섹션) |
| GovernanceBackend/UI (port 8889) | ✅ 완료 | MQTT/payload 거버넌스 |
| STM32 타이밍 노드 | ⬜ 선택 | GPIO 레이턴시 측정, 논문에서 optional |

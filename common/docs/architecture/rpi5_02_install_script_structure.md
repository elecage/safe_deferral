# Raspberry Pi 5 설치 스크립트 구조안

## 목표
Raspberry Pi 5에 시뮬레이션 및 결함 주입 계층을 재실행 가능(idempotent) 하고 검증 가능한 방식으로 설치한다.

## 기본 원칙
* Python 기반 모듈은 전용 가상환경에 설치한다.
* 정책/스키마 파일은 설치 대상이 아니라 Phase 0 설계 자산이며, 설치 후 별도 동기화한다.
* 시간 동기화 클라이언트를 설치하되, 절대적인 ms 보장을 약속하지 않는다.
* 실험 전 실제 clock offset을 측정·기록하는 검증 절차를 반드시 둔다.

##권장 디렉토리 구조

scripts/
├── install/
│   ├── 00_preflight_rpi.sh
│   ├── 10_install_system_packages_rpi.sh
│   ├── 20_create_python_venv_rpi.sh
│   ├── 30_install_python_deps_rpi.sh
│   └── 40_install_time_sync_client_rpi.sh
└── common/
    ├── env.sh
    ├── logging.sh
    └── checks.sh

## 스크립트별 역할

### 00_preflight_rpi.sh

* Raspberry Pi OS 버전 확인
* Python 버전 확인
* 네트워크 연결 확인
* 디스크 여유 공간 확인
* 작업 디렉토리 생성

### 10_install_system_packages_rpi.sh

* apt update && apt upgrade
* python3, python3-venv, git 설치
* mosquitto-clients 설치
* time sync client(예: systemd-timesyncd 또는 chrony) 설치
* 기본 CLI 유틸리티 설치

## 20_create_python_venv_rpi.sh

* `.venv-rpi` 생성
* pip / setuptools / wheel 업그레이드
* 버전 정보 저장

## 30_install_python_deps_rpi.sh

설치 대상 예시:

* paho-mqtt
* pytest
* pytest-asyncio
* PyYAML
* jsonschema
* click 또는 typer
* faker(선택)
* numpy(선택)

## 40_install_time_sync_client_rpi.sh

* 공통 시간원(local router 또는 Mac mini와 동일한 LAN 시간원) 설정
* 시간 동기화 서비스 활성화
* 설치 후 time sync 상태 점검 명령 실행

### 실행 순서 예시
```
bash scripts/install/00_preflight_rpi.sh
bash scripts/install/10_install_system_packages_rpi.sh
bash scripts/install/20_create_python_venv_rpi.sh
bash scripts/install/30_install_python_deps_rpi.sh
bash scripts/install/40_install_time_sync_client_rpi.sh
```

## 설치 후 반드시 검증할 항목

* Python venv 활성화 가능
* MQTT broker까지 네트워크 연결 가능
* 시간 동기화 서비스 상태 확인 가능
* CLI 도구 정상 실행
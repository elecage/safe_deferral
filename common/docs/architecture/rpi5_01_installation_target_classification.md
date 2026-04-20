# Raspberry Pi 5 설치 대상 분류표

## 목적

Raspberry Pi 5는 본 시스템의 **운영 핵심 허브가 아니라**, Track B의 **시뮬레이션 및 결함 주입**(Evaluation-support node) 역할을 수행한다. 따라서 Pi 5에는 Mac mini의 핵심 런타임(Home Assistant, Ollama, Policy Router 등)을 설치하지 않고, **가상 센서망·응급 시뮬레이터·결함 주입기·실험 러너만 설치**한다.

| **구분** | **구성요소** | **설치 위치** | **설치 방식** | **비고** |
|:-:|:-: |:-:|---|---|
|시스템 런타임 | Python 3 / venv | Raspberry Pi 5 | apt + venv | Pi-side Python 실행 환경 |
| Python 앱 | Virtual Sensor Nodes | Raspberry Pi 5 | Python 가상환경 | 정상 문맥(Context) MQTT 발행 |
| Python 앱 | Virtual Emergency Sensors | Raspberry Pi 5 | Python 가상환경 | Class 0용 응급 이벤트 시뮬레이션 |
| Python 앱 | Fault Injector Harness | Raspberry Pi 5 | Python 가상환경 | stale/missing/conflict/delay 주입 |
| Python 앱 | Scenario Orchestrator | Raspberry Pi 5 | Python 가상환경 | 실험 시나리오 자동 실행 |
| Python 앱 | Verification Utilities | Raspberry Pi 5 | Python 가상환경 | MQTT 연결, 시간 동기화, 결과 요약 |
| Python 라이브러리 | paho-mqtt | Raspberry Pi 5 | pip | MQTT publisher/subscriber |
| Python 라이브러리 | pytest / pytest-asyncio | Raspberry Pi 5 | pip | 테스트 러너 |
| Python 라이브러리 | PyYAML / jsonschema | Raspberry Pi 5 | pip | 정책/스키마 파싱 및 검증 |
| Python 라이브러리 | click 또는 typer | Raspberry Pi 5 | pip | CLI 유틸리티 |
| 시스템 서비스 | NTP/시간 동기화 클라이언트 | Raspberry Pi 5 | apt | Mac mini 또는 로컬 시간원과 시계 동기화 |
| 설정 자산 | Phase 0 정책/스키마 파일 | Raspberry Pi 5 로컬 동기화 경로 | Git fetch / rsync / scp | authoritative source는 Mac mini 저장소 |
| 환경설정 | `.env` / `.env.example` | Raspberry Pi 5 |  파일 배포 | MQTT broker, credentials, topic namespace 등 |

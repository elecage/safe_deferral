# 01_installation_target_classification.md

### Installation Target Classification

| 구분 | 구성요소 | 설치 위치 | 설치 방식 | 비고 |
| ------ | ------ | ------ | ------ | ------ |
| 시스템 서비스 | Home Assistant | Mac mini | 개별 서비스/컨테이너 | 스마트홈 플랫폼 계층 |
| 시스템 서비스 | Mosquitto MQTT Broker | Mac mini | 개별 서비스/컨테이너 | 최종 운영 위치. 개발/실험 시 Raspberry Pi 5 대체 가능 |
| 시스템 서비스 | Ollama | Mac mini | 개별 서비스/컨테이너 | Local LLM runtime |
| 시스템 서비스 | Local TTS Engine (meloTTS / Piper) | Mac mini | 개별 서비스/컨테이너 | 클라우드 독립형 단방향 음성 안내용 (iCR 피드백 등) |
| 모델 자산 | Llama 3.1 | Mac mini | Ollama pull | Class 1 전용 모델 |
| Python 앱 | Policy Router | Mac mini | Python 가상환경 | 직접 개발 |
| Python 앱 | Deterministic Validator | Mac mini | Python 가상환경 | 직접 개발 |
| Python 앱 | iCR Handler | Mac mini | Python 가상환경 | 직접 개발 |
| Python 앱 | Outbound Notification Interface | Mac mini | Python 가상환경 | Telegram 또는 Mock Server 연동 |
| Python 앱 | Caregiver Confirmation Backend | Mac mini | Python 가상환경 | bounded confirmation 처리 |
| Python 앱 | Audit Log Service / DB access layer | Mac mini | Python 가상환경 | SQLite 연동 |
| 개발/실험 도구 | Virtual Sensor Nodes | Raspberry Pi 5 | Python 가상환경 | 대규모 가상 센서망 |
| 개발/실험 도구 | Virtual Emergency Sensors | Raspberry Pi 5 | Python 가상환경 | 응급 이벤트 모사 |
| 개발/실험 도구 | Fault Injector Harness | Raspberry Pi 5 | Python 가상환경 | stale/missing/conflict/timeout 주입 |
| 외부 연동 | Telegram Bot | 외부 API | 계정/토큰 설정 | 보호자 알림 및 제한 승인 |
| 설정 자산 | policy tables / JSON schema / output_profile.json / .env / YAML | Mac mini + Git 저장소 | 파일 배포 | 구현 전 필수 고정 문서 |

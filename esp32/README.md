# esp32

ESP32는 `safe_deferral`의 bounded physical node 계층이다.

현재 이 폴더의 우선순위는 실제 펌웨어 구현이 아니라 ESP-IDF 개발환경의 설치, 구성, 검증 절차를 안정화하는 것이다.

## Directory Roles

- `scripts/`: ESP-IDF 개발환경 설치, workspace 구성, 샘플 빌드 검증 스크립트
- `docs/`: ESP32 영역의 역할, 실행 순서, 성공 기준 문서
- `code/`: 향후 실제 bounded node 펌웨어 소스가 들어갈 위치
- `firmware/`: 향후 펌웨어 템플릿, 샘플 프로젝트, 보드별 기본 설정이 들어갈 위치

## Boundary

ESP32는 정책 라우팅, deterministic validation, caregiver approval, LLM inference, doorlock authorization 권한을 갖지 않는다.

ESP32 펌웨어는 향후 Mac mini의 승인된 operational pipeline에서 내려온 bounded command를 수행하는 물리 노드로만 다룬다.

## Current Entry Point

현재 작업은 다음 문서에서 시작한다.

- `esp32/scripts/README.md`
- `esp32/docs/README.md`

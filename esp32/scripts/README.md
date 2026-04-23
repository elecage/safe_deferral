# esp32/scripts

이 디렉터리는 ESP32 개발환경의 **설치(install)**, **구성(configure)**, **검증(verify)** 스크립트를 둔다.

현재 단계에서는 실제 펌웨어 코드보다 먼저, 개발환경 표준화 스크립트를 준비하는 것이 우선이다.

구조 원칙:
- `install/` : OS별 설치 스크립트
- `configure/` : 공통 환경 변수 / workspace 준비
- `verify/` : 실제 빌드 가능한지 검증

현재 반영 상태:
- `install/mac/` 초안 반영
- `install/linux/` 초안 반영
- `install/windows/` 초안 반영
- `configure/`, `verify/` 는 디렉터리 scaffold만 생성

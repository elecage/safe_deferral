# esp32/docs

이 디렉터리는 **ESP32 기반 bounded physical node 개발환경**의 설치, 구성, 검증 구조를 정의하는 문서 모음이다.

현재 `esp32/`는 `code/`, `docs/`, `firmware/` 폴더만 존재하고 실제 펌웨어 구현은 아직 시작되지 않은 상태다.  
따라서 본 문서는 **펌웨어 코딩 이전에 먼저 표준화해야 하는 개발환경 준비 체계**를 정리한다.

---

## 1. ESP32 영역의 역할

프로젝트 전체 구조에서 `esp32/`는 다음 역할을 담당한다.

- bounded physical node 펌웨어 개발
- 물리 입력/출력 인터페이스 제어
- Mac mini / RPi 계층과 연동되는 노드 펌웨어 관리
- 보드 타깃(`esp32`, `esp32c3`, `esp32s3` 등)별 개발환경 검증

여기서 중요한 점은, **ESP32는 지금 단계에서 코드보다 개발환경 표준화가 먼저**라는 것이다.

즉, 다음 세 가지가 먼저 필요하다.

- install: OS별 도구체인/SDK/필수 패키지 설치
- configure: 공통 환경변수, workspace, 샘플 프로젝트 준비
- verify: 실제로 `idf.py`가 동작하고 샘플 빌드가 성공하는지 검증

---

## 2. 권장 개발환경 전략

ESP32 개발환경은 운영체제별 차이가 크므로, 다음 원칙을 따른다.

### 2.1 기본 원칙
- **install은 OS별 분리**한다.
- **configure와 verify는 최대한 공통 구조**를 유지한다.
- 단, Windows는 Shell 차이 때문에 `.ps1` 기반 스크립트를 별도로 둔다.
- 새 사용자/GUI 환경에서는 **EIM(ESP-IDF Installation Manager)** 를 우선 고려한다.
- 자동화/반복 설치/CI 관점에서는 **ESP-IDF CLI 기반 standard setup 흐름**도 함께 지원한다.

### 2.2 실제 적용 원칙
- macOS: Homebrew + ESP-IDF CLI/EIM
- Linux: distro package manager + ESP-IDF CLI/EIM
- Windows: PowerShell + EIM 또는 공식 installer 기반

즉, 문서상 권장 경로는 EIM이지만, 저장소 스크립트는 **자동화 가능성** 때문에 CLI 중심으로 설계하는 것이 바람직하다.

---

## 3. 권장 디렉터리 구조 초안

아래 구조를 `esp32/` 아래에 추가하는 것을 권장한다.

```text
esp32/
├─ code/
│  ├─ components/
│  ├─ main/
│  └─ CMakeLists.txt
├─ docs/
│  ├─ README.md
│  ├─ 01_dev_environment_plan.md
│  ├─ 02_supported_targets.md
│  └─ 03_build_and_flash_workflow.md
├─ firmware/
│  ├─ templates/
│  │  └─ minimal_node/
│  ├─ examples/
│  └─ sdkconfig.defaults
└─ scripts/
   ├─ install/
   │  ├─ mac/
   │  │  ├─ 00_preflight_esp32_mac.sh
   │  │  ├─ 10_install_prereqs_esp32_mac.sh
   │  │  ├─ 20_install_esp_idf_esp32_mac.sh
   │  │  └─ 30_install_extra_tools_esp32_mac.sh
   │  ├─ linux/
   │  │  ├─ 00_preflight_esp32_linux.sh
   │  │  ├─ 10_install_prereqs_esp32_linux.sh
   │  │  ├─ 20_install_esp_idf_esp32_linux.sh
   │  │  └─ 30_install_extra_tools_esp32_linux.sh
   │  └─ windows/
   │     ├─ 00_preflight_esp32_windows.ps1
   │     ├─ 10_install_prereqs_esp32_windows.ps1
   │     ├─ 20_install_esp_idf_esp32_windows.ps1
   │     └─ 30_install_extra_tools_esp32_windows.ps1
   ├─ configure/
   │  ├─ 10_write_env_files_esp32.sh
   │  ├─ 20_prepare_idf_workspace_esp32.sh
   │  ├─ 30_prepare_managed_components_esp32.sh
   │  └─ 40_prepare_sample_project_esp32.sh
   └─ verify/
      ├─ 10_verify_idf_cli_esp32.sh
      ├─ 20_verify_toolchain_target_esp32.sh
      ├─ 30_verify_component_resolution_esp32.sh
      └─ 40_verify_sample_build_esp32.sh
```

---

## 4. 각 디렉터리의 역할 정의

### 4.1 `code/`
실제 ESP32 펌웨어 소스가 위치할 곳이다.

예상 내용:
- `main/` : 애플리케이션 entry point
- `components/` : 재사용 가능한 custom components
- `CMakeLists.txt` : ESP-IDF build entry

현재는 아직 비어 있어도 된다.

### 4.2 `docs/`
개발환경, 지원 타깃, 빌드/플래시 절차, 펌웨어 구조 문서를 둔다.

현재 단계에서는 코드 문서보다도 먼저,
- 개발환경 구축 절차
- 설치 대상 도구
- 지원 보드/칩셋 정의
- 공통 검증 절차
를 문서화하는 것이 중요하다.

### 4.3 `firmware/`
샘플 프로젝트, 템플릿, `sdkconfig.defaults`, 공통 기본 설정을 둔다.

현재 단계에서는 다음 용도로 먼저 쓰는 것이 좋다.
- 최소 샘플 프로젝트 템플릿
- sample build verify용 기준 프로젝트
- 보드 공통 기본 sdkconfig

### 4.4 `scripts/`
OS별 개발환경 설치와 공통 구성/검증을 자동화한다.

이 디렉터리는 지금 ESP32 영역에서 가장 먼저 채워야 하는 부분이다.

---

## 5. install / configure / verify 분리 원칙

### 5.1 install 단계
운영체제별로 다른 prerequisite, package manager, installer 흐름을 처리한다.

예:
- macOS: brew 설치, Python/Git/CMake/Ninja/dfu-util 준비
- Linux: apt/dnf/pacman 등으로 prerequisite 설치
- Windows: PowerShell 기반 prerequisite 점검 및 EIM/installer 준비

### 5.2 configure 단계
운영체제가 달라도 공통으로 맞춰야 할 개발환경 변수와 workspace를 준비한다.

예:
- `ESP_IDF_VERSION`
- `IDF_TARGET`
- `IDF_PATH`
- `IDF_TOOLS_PATH`
- sample project path
- component cache path

### 5.3 verify 단계
설치가 끝났다는 사실보다 더 중요한 것은, **실제로 빌드가 되는지**를 확인하는 것이다.

예:
- `idf.py --version`
- `idf.py set-target esp32`
- component resolution
- sample firmware build 성공 여부

---

## 6. OS별 install 스크립트 역할 정의

---

### 6.1 macOS

#### `00_preflight_esp32_mac.sh`
목적:
- macOS 여부 확인
- Homebrew 존재 여부 확인
- Python 3.11+ 확인
- Git 존재 여부 확인
- 디스크 공간/네트워크 상태 확인

출력 예:
- OS 적합 여부
- brew 설치 여부
- Python 버전
- 설치 진행 가능 여부

#### `10_install_prereqs_esp32_mac.sh`
목적:
- Homebrew 기반 prerequisite 설치

예상 설치 항목:
- `git`
- `cmake`
- `ninja`
- `python`
- `dfu-util`
- 필요 시 `ccache`

#### `20_install_esp_idf_esp32_mac.sh`
목적:
- ESP-IDF 설치
- EIM 또는 standard CLI 설치 경로 중 프로젝트 표준 방식 적용

예상 작업:
- ESP-IDF clone
- `install.sh` 실행
- toolchain 및 Python env 설치

#### `30_install_extra_tools_esp32_mac.sh`
목적:
- 추가 개발 보조 도구 설치

예상 항목:
- serial monitor 관련 보조도구
- optional flashing helpers
- optional VS Code extension 연동 안내

---

### 6.2 Linux

#### `00_preflight_esp32_linux.sh`
목적:
- Linux 여부 확인
- package manager 유형 식별
- Python/Git 존재 여부 확인
- 디스크 공간/네트워크 상태 확인

#### `10_install_prereqs_esp32_linux.sh`
목적:
- distro별 prerequisite 설치

예상 설치 항목:
- `git`
- `wget`
- `flex`
- `bison`
- `gperf`
- `python3`
- `python3-pip`
- `python3-venv`
- `cmake`
- `ninja-build`
- `ccache`
- `dfu-util`
- `libusb` 계열
- `libffi-dev`
- `libssl-dev`

#### `20_install_esp_idf_esp32_linux.sh`
목적:
- ESP-IDF clone
- `install.sh` 실행
- toolchain 설치

#### `30_install_extra_tools_esp32_linux.sh`
목적:
- udev/serial access 보조 설정
- optional monitor tooling
- flashing 편의 도구 준비

---

### 6.3 Windows

#### `00_preflight_esp32_windows.ps1`
목적:
- Windows 여부 확인
- PowerShell 실행 정책 확인
- Python/Git 존재 여부 확인
- 설치 경로에 공백/특수문자 문제가 없는지 확인

#### `10_install_prereqs_esp32_windows.ps1`
목적:
- prerequisite 점검
- 필요 시 Git/Python 설치 유도 또는 winget 기반 설치

#### `20_install_esp_idf_esp32_windows.ps1`
목적:
- EIM 또는 공식 installer 기반 ESP-IDF 설치
- 활성 버전 설정

#### `30_install_extra_tools_esp32_windows.ps1`
목적:
- serial driver/monitor 보조 설정
- optional USB serial tooling 확인

---

## 7. 공통 configure 스크립트 역할 정의

### `10_write_env_files_esp32.sh`
목적:
- 공통 개발환경 변수 파일 생성

예상 변수:
- `ESP_IDF_VERSION`
- `IDF_TARGET`
- `ESP32_WORKSPACE_DIR`
- `ESP32_FIRMWARE_TEMPLATE_DIR`
- `IDF_TOOLS_PATH`
- `ESPPORT` (선택)
- `ESPBAUD` (선택)

주의:
- 사용자 환경별 override를 허용하되, 기본값은 append-only 방식이 바람직하다.

### `20_prepare_idf_workspace_esp32.sh`
목적:
- workspace 디렉터리 생성
- 공통 프로젝트 루트 준비
- sample build용 디렉터리 정리

예상 결과:
- `~/esp32_workspace`
- `build/`
- `artifacts/`
- `logs/`
- `samples/`

### `30_prepare_managed_components_esp32.sh`
목적:
- `idf_component.yml` 기반 managed component resolve 준비
- component cache 구조 준비

이 스크립트는 실제 component dependency가 생기기 전까지는 최소 scaffold 수준으로 둘 수 있다.

### `40_prepare_sample_project_esp32.sh`
목적:
- verify 단계에서 사용할 최소 sample project 생성 또는 복사

예상 기능:
- blink 또는 hello_world 계열 샘플 생성
- `idf.py set-target` 가능한 최소 구조 준비

---

## 8. 공통 verify 스크립트 역할 정의

### `10_verify_idf_cli_esp32.sh`
목적:
- ESP-IDF CLI가 실제로 동작하는지 확인

검증 항목:
- `idf.py --version`
- `python --version`
- `cmake --version`
- `ninja --version`
- `esptool.py version`

### `20_verify_toolchain_target_esp32.sh`
목적:
- target toolchain과 board target 설정이 정상 동작하는지 확인

검증 항목:
- `idf.py set-target esp32`
- 필요 시 `esp32c3`, `esp32s3`까지 확장 가능

### `30_verify_component_resolution_esp32.sh`
목적:
- managed components / CMake dependency resolution 확인

검증 항목:
- `idf.py reconfigure`
- `managed_components/` 생성 여부
- component resolution error 여부

### `40_verify_sample_build_esp32.sh`
목적:
- 가장 중요한 최종 smoke test

검증 항목:
- 샘플 프로젝트 build 성공 여부
- `build/` 산출물 존재 여부
- `.bin`, `.elf`, `.map` 생성 여부

이 스크립트가 통과해야만 “개발환경 구축 성공”으로 보는 것이 바람직하다.

---

## 9. 문서 우선 작성 순서 권장안

ESP32 영역은 아직 코드가 없으므로, 다음 순서로 채우는 것을 권장한다.

### 1단계
- `esp32/docs/README.md` 확장
- `esp32/scripts/` 구조 생성

### 2단계
- macOS / Linux / Windows preflight 스크립트 초안 작성
- 공통 configure 스크립트 초안 작성

### 3단계
- sample project 준비 스크립트 작성
- 공통 verify 스크립트 작성

### 4단계
- `firmware/templates/minimal_node/` 최소 샘플 추가
- 이후 실제 bounded node firmware 구현 시작

---

## 10. 현재 단계에서의 핵심 판단

지금 `esp32/`에서 가장 먼저 필요한 것은 다음이다.

- 실제 펌웨어 코드 구현이 아님
- **개발환경 설치/구성/검증 스크립트 체계 수립**
- OS별 install 분리
- 공통 configure/verify 정리
- sample build를 기준으로 한 최종 검증 흐름 확립

즉, ESP32 영역의 현재 선행 과제는 **코드 작성보다 개발환경 표준화 문서와 스크립트 scaffold 작성**이다.

---

## 11. 후속 작업 권장안

이 문서 다음 단계로 권장되는 작업은 다음과 같다.

1. `esp32/scripts/install/mac/`, `linux/`, `windows/` 디렉터리 생성
2. 각 OS별 `00_preflight`, `10_install_prereqs` 스크립트 초안 작성
3. 공통 `configure/` 스크립트 초안 작성
4. 공통 `verify/` 스크립트 초안 작성
5. `firmware/templates/minimal_node/` 최소 샘플 준비
6. `esp32/docs/README.md`에 실제 실행 순서와 명령 예시 추가

이후에야 ESP32 bounded node 펌웨어 코드를 안정적으로 구현할 수 있다.

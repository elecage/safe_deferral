# esp32/docs

이 디렉터리는 **ESP32 기반 bounded physical node 개발환경**의 설치, 구성, 검증 구조를 정의하는 문서 모음이다.

현재 `esp32/`는 `code/`, `docs/`, `firmware/` 폴더는 존재하지만 실제 bounded node 펌웨어 구현은 아직 시작되지 않은 상태다.  
따라서 지금 단계에서 가장 먼저 필요한 것은 **펌웨어 코드가 아니라 개발환경 표준화**다.

즉, 다음 세 가지가 먼저 필요하다.

- `install`: OS별 도구체인/SDK/필수 패키지 설치
- `configure`: 공통 환경변수, workspace, 샘플 프로젝트 준비
- `verify`: 실제로 `idf.py`가 동작하고 샘플 빌드가 성공하는지 검증

---

## 1. ESP32 영역의 역할

프로젝트 전체 구조에서 `esp32/`는 다음 역할을 담당한다.

- bounded physical node 펌웨어 개발
- 물리 입력/출력 인터페이스 제어
- Mac mini / RPi 계층과 연동되는 노드 펌웨어 관리
- 보드 타깃(`esp32`, `esp32c3`, `esp32s3` 등)별 개발환경 검증

여기서 중요한 점은, **ESP32는 지금 단계에서 코드보다 개발환경 표준화가 먼저**라는 것이다.

---

## 2. 권장 개발환경 전략

ESP32 개발환경은 운영체제별 차이가 크므로, 다음 원칙을 따른다.

### 2.1 기본 원칙
- **install은 OS별 분리**한다.
- **configure와 verify는 최대한 공통 구조**를 유지한다.
- 단, Windows는 shell 차이 때문에 `.ps1` 기반 스크립트를 별도로 둔다.
- 새 사용자/GUI 환경에서는 **EIM(ESP-IDF Installation Manager)** 를 우선 고려한다.
- 자동화/반복 설치/CI 관점에서는 **ESP-IDF CLI 기반 standard setup 흐름**도 함께 지원한다.

### 2.2 실제 적용 원칙
- macOS: Homebrew + ESP-IDF CLI/EIM
- Linux: distro package manager + ESP-IDF CLI/EIM
- Windows: PowerShell + EIM 또는 공식 installer 기반

문서상 권장 경로는 EIM이지만, 저장소 스크립트는 **자동화 가능성** 때문에 CLI 중심으로 설계한다.

---

## 3. 현재 반영된 디렉터리/스크립트 구조

```text
esp32/
├─ code/
├─ docs/
│  └─ README.md
├─ firmware/
└─ scripts/
   ├─ README.md
   ├─ install/
   │  ├─ mac/
   │  │  ├─ 00_preflight_esp32_mac.sh
   │  │  ├─ 10_install_prereqs_esp32_mac.sh
   │  │  └─ 20_install_esp_idf_esp32_mac.sh
   │  ├─ linux/
   │  │  ├─ 00_preflight_esp32_linux.sh
   │  │  ├─ 10_install_prereqs_esp32_linux.sh
   │  │  └─ 20_install_esp_idf_esp32_linux.sh
   │  └─ windows/
   │     ├─ 00_preflight_esp32_windows.ps1
   │     ├─ 10_install_prereqs_esp32_windows.ps1
   │     └─ 20_install_esp_idf_esp32_windows.ps1
   ├─ configure/
   │  ├─ README.md
   │  ├─ 10_write_env_files_esp32.sh
   │  ├─ 20_prepare_idf_workspace_esp32.sh
   │  ├─ 30_prepare_managed_components_esp32.sh
   │  ├─ 40_prepare_sample_project_esp32.sh
   │  ├─ 10_write_env_files_esp32_windows.ps1
   │  ├─ 20_prepare_idf_workspace_esp32_windows.ps1
   │  ├─ 30_prepare_managed_components_esp32_windows.ps1
   │  └─ 40_prepare_sample_project_esp32_windows.ps1
   └─ verify/
      ├─ README.md
      ├─ 10_verify_idf_cli_esp32.sh
      ├─ 20_verify_toolchain_target_esp32.sh
      ├─ 30_verify_component_resolution_esp32.sh
      ├─ 40_verify_sample_build_esp32.sh
      ├─ 10_verify_idf_cli_esp32_windows.ps1
      ├─ 20_verify_toolchain_target_esp32_windows.ps1
      ├─ 30_verify_component_resolution_esp32_windows.ps1
      └─ 40_verify_sample_build_esp32_windows.ps1
```

---

## 4. 각 디렉터리의 역할 정의

### 4.1 `code/`
실제 ESP32 bounded node 펌웨어 소스가 위치할 곳이다.

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
샘플 프로젝트, 템플릿, `sdkconfig.defaults`, 공통 기본 설정을 둘 공간이다.

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
- Windows: PowerShell 기반 prerequisite 점검 및 installer 준비

### 5.2 configure 단계
운영체제가 달라도 공통으로 맞춰야 할 개발환경 변수와 workspace를 준비한다.

예:
- `IDF_TARGET`
- `IDF_PATH`
- `IDF_TOOLS_PATH`
- sample project path
- component cache path
- build log path

### 5.3 verify 단계
설치가 끝났다는 사실보다 더 중요한 것은, **실제로 빌드가 되는지**를 확인하는 것이다.

예:
- `idf.py --version`
- `idf.py set-target esp32`
- component resolution
- sample firmware build 성공 여부

---

## 6. 현재 반영된 스크립트 역할 정의

### 6.1 install

#### macOS
- `00_preflight_esp32_mac.sh`
  - macOS 여부 확인
  - Homebrew, Python, Git, 디스크 공간, 네트워크 상태 확인
- `10_install_prereqs_esp32_mac.sh`
  - Homebrew 기반 prerequisite 설치
- `20_install_esp_idf_esp32_mac.sh`
  - ESP-IDF clone 및 `install.sh` 기반 설치

#### Linux
- `00_preflight_esp32_linux.sh`
  - Linux 여부, package manager, Python, Git, 디스크 공간, 네트워크 확인
- `10_install_prereqs_esp32_linux.sh`
  - distro별 prerequisite 설치
- `20_install_esp_idf_esp32_linux.sh`
  - ESP-IDF clone 및 `install.sh` 기반 설치

#### Windows
- `00_preflight_esp32_windows.ps1`
  - Windows 여부, PowerShell 버전, winget/Git/Python, 디스크 공간, 네트워크 확인
- `10_install_prereqs_esp32_windows.ps1`
  - winget 기반 prerequisite 설치
- `20_install_esp_idf_esp32_windows.ps1`
  - ESP-IDF clone 및 `install.ps1` 기반 설치

### 6.2 configure

#### POSIX(macOS/Linux)
- `10_write_env_files_esp32.sh`
  - 공통 env 파일 생성
- `20_prepare_idf_workspace_esp32.sh`
  - workspace 디렉터리 생성
- `30_prepare_managed_components_esp32.sh`
  - managed component cache 및 placeholder manifest 준비
- `40_prepare_sample_project_esp32.sh`
  - `hello_world` 샘플 프로젝트 복사

#### Windows
- `10_write_env_files_esp32_windows.ps1`
  - Windows용 `.env.ps1` 생성
- `20_prepare_idf_workspace_esp32_windows.ps1`
  - Windows workspace 디렉터리 생성
- `30_prepare_managed_components_esp32_windows.ps1`
  - Windows용 managed component cache 및 placeholder manifest 준비
- `40_prepare_sample_project_esp32_windows.ps1`
  - `hello_world` 샘플 프로젝트 복사

### 6.3 verify

#### POSIX(macOS/Linux)
- `10_verify_idf_cli_esp32.sh`
  - `idf.py`, Python, CMake, Ninja, esptool 동작 확인
- `20_verify_toolchain_target_esp32.sh`
  - `idf.py set-target` 확인
- `30_verify_component_resolution_esp32.sh`
  - `idf.py reconfigure` 및 component resolution 확인
- `40_verify_sample_build_esp32.sh`
  - 샘플 프로젝트 실제 build 확인

#### Windows
- `10_verify_idf_cli_esp32_windows.ps1`
  - `idf.py`, Python, CMake, Ninja, esptool 동작 확인
- `20_verify_toolchain_target_esp32_windows.ps1`
  - `idf.py set-target` 확인
- `30_verify_component_resolution_esp32_windows.ps1`
  - `idf.py reconfigure` 및 component resolution 확인
- `40_verify_sample_build_esp32_windows.ps1`
  - 샘플 프로젝트 실제 build 확인

---

## 7. 실제 실행 순서

### 7.1 macOS / Linux

저장소 루트에서 실행하는 것을 권장한다.

```bash
cd /path/to/safe_deferral
chmod +x esp32/scripts/install/mac/*.sh 2>/dev/null || true
chmod +x esp32/scripts/install/linux/*.sh 2>/dev/null || true
chmod +x esp32/scripts/configure/*.sh 2>/dev/null || true
chmod +x esp32/scripts/verify/*.sh 2>/dev/null || true
```

#### macOS 실행 순서
```bash
bash esp32/scripts/install/mac/00_preflight_esp32_mac.sh
bash esp32/scripts/install/mac/10_install_prereqs_esp32_mac.sh
bash esp32/scripts/install/mac/20_install_esp_idf_esp32_mac.sh

bash esp32/scripts/configure/10_write_env_files_esp32.sh
bash esp32/scripts/configure/20_prepare_idf_workspace_esp32.sh
bash esp32/scripts/configure/30_prepare_managed_components_esp32.sh
bash esp32/scripts/configure/40_prepare_sample_project_esp32.sh

bash esp32/scripts/verify/10_verify_idf_cli_esp32.sh
bash esp32/scripts/verify/20_verify_toolchain_target_esp32.sh
bash esp32/scripts/verify/30_verify_component_resolution_esp32.sh
bash esp32/scripts/verify/40_verify_sample_build_esp32.sh
```

#### Linux 실행 순서
```bash
bash esp32/scripts/install/linux/00_preflight_esp32_linux.sh
bash esp32/scripts/install/linux/10_install_prereqs_esp32_linux.sh
bash esp32/scripts/install/linux/20_install_esp_idf_esp32_linux.sh

bash esp32/scripts/configure/10_write_env_files_esp32.sh
bash esp32/scripts/configure/20_prepare_idf_workspace_esp32.sh
bash esp32/scripts/configure/30_prepare_managed_components_esp32.sh
bash esp32/scripts/configure/40_prepare_sample_project_esp32.sh

bash esp32/scripts/verify/10_verify_idf_cli_esp32.sh
bash esp32/scripts/verify/20_verify_toolchain_target_esp32.sh
bash esp32/scripts/verify/30_verify_component_resolution_esp32.sh
bash esp32/scripts/verify/40_verify_sample_build_esp32.sh
```

### 7.2 Windows

PowerShell에서 저장소 루트 기준으로 실행하는 것을 권장한다.

```powershell
Set-Location C:\path\to\safe_deferral
```

#### Windows 실행 순서
```powershell
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\install\windows\00_preflight_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\install\windows\10_install_prereqs_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\install\windows\20_install_esp_idf_esp32_windows.ps1

powershell -ExecutionPolicy Bypass -File .\esp32\scripts\configure\10_write_env_files_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\configure\20_prepare_idf_workspace_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\configure\30_prepare_managed_components_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\configure\40_prepare_sample_project_esp32_windows.ps1

powershell -ExecutionPolicy Bypass -File .\esp32\scripts\verify\10_verify_idf_cli_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\verify\20_verify_toolchain_target_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\verify\30_verify_component_resolution_esp32_windows.ps1
powershell -ExecutionPolicy Bypass -File .\esp32\scripts\verify\40_verify_sample_build_esp32_windows.ps1
```

---

## 8. 성공 기준

ESP32 개발환경 구축 성공의 기준은 단순 설치 완료가 아니다.

최종적으로 다음이 모두 만족되어야 한다.

- `idf.py`가 정상 실행됨
- target 설정이 정상 동작함
- `idf.py reconfigure`가 성공함
- 샘플 프로젝트 build가 성공함
- build 산출물(`.bin`, `.elf`)이 생성됨

즉, **최종 성공 기준은 sample build success**다.

---

## 9. 현재 단계의 한계

현재 반영된 스크립트는 **개발환경 scaffold 초안**이다.

아직 남아 있는 작업:
- `install/*/30_install_extra_tools_esp32_*` 추가
- Windows용 USB serial driver/monitor 보강
- `firmware/templates/minimal_node/` 실제 최소 템플릿 추가
- flashing / monitor / serial port verify 스크립트 추가
- 실제 bounded node firmware 구현

즉, 지금은 **설치-구성-검증의 기본 골격**이 먼저 마련된 상태다.

---

## 10. 후속 작업 권장안

다음 단계로 권장되는 작업은 다음과 같다.

1. `esp32/firmware/templates/minimal_node/` 실제 템플릿 추가
2. `install/mac|linux|windows/30_install_extra_tools_*` 보강
3. serial port/USB driver 검증 스크립트 추가
4. flash / monitor verify 스크립트 추가
5. 이후 bounded node firmware 구현 시작

이후에야 ESP32 bounded node 펌웨어 코드를 안정적으로 구현할 수 있다.

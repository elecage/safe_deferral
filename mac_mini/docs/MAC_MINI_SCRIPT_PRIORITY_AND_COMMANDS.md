# MAC_MINI_SCRIPT_PRIORITY_AND_COMMANDS.md

## 목적

이 문서는 Mac mini 환경에서 `safe_deferral` 저장소의 스크립트를 **어떤 순서로 실행해야 하는지**를 명확히 정의하고, 그대로 복붙해서 실행할 수 있는 **명령 목록**을 제공하기 위한 운영 문서다.

이 문서는 다음 질문에 답한다.

- `install`과 `configure` 중 무엇을 먼저 실행해야 하는가?
- `verify`는 언제 실행해야 하는가?
- 실제로 어떤 명령을 어떤 순서로 입력하면 되는가?

---

## 결론

Mac mini에서는 반드시 다음 순서를 따른다.

1. **install**
2. **configure**
3. **verify**

즉,

- `install` 스크립트를 먼저 실행하고,
- 그 다음 `configure` 스크립트를 실행하며,
- 마지막에 `verify` 스크립트로 상태를 점검한다.

---

## 왜 이 순서여야 하는가

### 1. install 단계
이 단계는 실행 기반을 만든다.

예:
- Homebrew 의존성 설치
- Docker runtime 준비
- compose 스택 작업공간 준비
- Python venv 준비

즉, `configure`가 기대하는 도구와 경로를 먼저 만든다.

### 2. configure 단계
이 단계는 install 위에 실제 시스템 구성을 올린다.

예:
- `.env` 작성
- policy / schema 배포
- SQLite 설정
- Mosquitto 설정
- Home Assistant 설정
- Ollama 설정
- notification 설정

즉, 이미 준비된 실행 기반 위에 서비스 구성을 얹는 단계다.

### 3. verify 단계
이 단계는 구성된 시스템이 실제로 정상 상태인지 점검한다.

예:
- Docker 서비스 확인
- MQTT pub/sub 확인
- Ollama 추론 확인
- SQLite 확인
- env / asset 확인
- notification 확인
- 전체 서비스 종합 확인

따라서 `verify`는 반드시 마지막에 온다.

---

## Mac mini 스크립트 우선순위 정의

### 최상위 우선순위
1. `mac_mini/scripts/install/`
2. `mac_mini/scripts/configure/`
3. `mac_mini/scripts/verify/`

### 해석 원칙
- `configure`를 `install`보다 먼저 실행하지 않는다.
- `verify`를 `configure`보다 먼저 실행하지 않는다.
- 일부 스크립트만 재실행할 수는 있지만, **초기 bring-up** 기준 순서는 항상 `install → configure → verify`다.

---

## 현재 Mac mini install 순서

다음 순서를 권장한다.

1. `mac_mini/scripts/install/00_preflight.sh`
2. `mac_mini/scripts/install/10_install_homebrew_deps.sh`
3. `mac_mini/scripts/install/20_install_docker_runtime_mac.sh`
4. `mac_mini/scripts/install/21_prepare_compose_stack_mac.sh`
5. `mac_mini/scripts/install/30_setup_python_venv_mac.sh`

---

## 현재 Mac mini configure 순서

다음 순서를 권장한다.

1. `mac_mini/scripts/configure/70_write_env_files.sh`
2. `mac_mini/scripts/configure/50_deploy_policy_files.sh`
3. `mac_mini/scripts/configure/40_configure_sqlite.sh`
4. `mac_mini/scripts/configure/20_configure_mosquitto.sh`
5. `mac_mini/scripts/configure/10_configure_home_assistant.sh`
6. `mac_mini/scripts/configure/30_configure_ollama.sh`
7. `mac_mini/scripts/configure/60_configure_notifications.sh`

참고:
- 번호 순서와 실제 권장 실행 순서는 다를 수 있다.
- 현재 정리된 runtime 해석에서는 `.env`와 canonical asset 배포를 먼저 수행한 뒤 DB / broker / service / notification을 구성하는 흐름을 권장한다.

---

## 현재 Mac mini verify 순서

다음 순서를 권장한다.

1. `mac_mini/scripts/verify/10_verify_docker_services.sh`
2. `mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh`
3. `mac_mini/scripts/verify/30_verify_ollama_inference.sh`
4. `mac_mini/scripts/verify/40_verify_sqlite.sh`
5. `mac_mini/scripts/verify/50_verify_env_and_assets.sh`
6. `mac_mini/scripts/verify/60_verify_notifications.sh`
7. `mac_mini/scripts/verify/80_verify_services.sh`

---

## 복붙용 명령 목록

아래 명령은 **저장소 루트에서 실행**하는 것을 가정한다.

### 1. install 단계

```bash
bash mac_mini/scripts/install/00_preflight.sh
bash mac_mini/scripts/install/10_install_homebrew_deps.sh
bash mac_mini/scripts/install/20_install_docker_runtime_mac.sh
bash mac_mini/scripts/install/21_prepare_compose_stack_mac.sh
bash mac_mini/scripts/install/30_setup_python_venv_mac.sh
```

### 2. configure 단계

```bash
bash mac_mini/scripts/configure/70_write_env_files.sh
bash mac_mini/scripts/configure/50_deploy_policy_files.sh
bash mac_mini/scripts/configure/40_configure_sqlite.sh
bash mac_mini/scripts/configure/20_configure_mosquitto.sh
bash mac_mini/scripts/configure/10_configure_home_assistant.sh
bash mac_mini/scripts/configure/30_configure_ollama.sh
bash mac_mini/scripts/configure/60_configure_notifications.sh
```

### 3. verify 단계

```bash
bash mac_mini/scripts/verify/10_verify_docker_services.sh
bash mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh
bash mac_mini/scripts/verify/30_verify_ollama_inference.sh
bash mac_mini/scripts/verify/40_verify_sqlite.sh
bash mac_mini/scripts/verify/50_verify_env_and_assets.sh
bash mac_mini/scripts/verify/60_verify_notifications.sh
bash mac_mini/scripts/verify/80_verify_services.sh
```

---

## 한 번에 단계별로 실행하고 싶을 때

### install만 연속 실행

```bash
bash mac_mini/scripts/install/00_preflight.sh && \
bash mac_mini/scripts/install/10_install_homebrew_deps.sh && \
bash mac_mini/scripts/install/20_install_docker_runtime_mac.sh && \
bash mac_mini/scripts/install/21_prepare_compose_stack_mac.sh && \
bash mac_mini/scripts/install/30_setup_python_venv_mac.sh
```

### configure만 연속 실행

```bash
bash mac_mini/scripts/configure/70_write_env_files.sh && \
bash mac_mini/scripts/configure/50_deploy_policy_files.sh && \
bash mac_mini/scripts/configure/40_configure_sqlite.sh && \
bash mac_mini/scripts/configure/20_configure_mosquitto.sh && \
bash mac_mini/scripts/configure/10_configure_home_assistant.sh && \
bash mac_mini/scripts/configure/30_configure_ollama.sh && \
bash mac_mini/scripts/configure/60_configure_notifications.sh
```

### verify만 연속 실행

```bash
bash mac_mini/scripts/verify/10_verify_docker_services.sh && \
bash mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh && \
bash mac_mini/scripts/verify/30_verify_ollama_inference.sh && \
bash mac_mini/scripts/verify/40_verify_sqlite.sh && \
bash mac_mini/scripts/verify/50_verify_env_and_assets.sh && \
bash mac_mini/scripts/verify/60_verify_notifications.sh && \
bash mac_mini/scripts/verify/80_verify_services.sh
```

---

## 초기 bring-up용 전체 순서 예시

아래는 초기 세팅 시 사용할 수 있는 전체 순서 예시다.

```bash
bash mac_mini/scripts/install/00_preflight.sh && \
bash mac_mini/scripts/install/10_install_homebrew_deps.sh && \
bash mac_mini/scripts/install/20_install_docker_runtime_mac.sh && \
bash mac_mini/scripts/install/21_prepare_compose_stack_mac.sh && \
bash mac_mini/scripts/install/30_setup_python_venv_mac.sh && \
bash mac_mini/scripts/configure/70_write_env_files.sh && \
bash mac_mini/scripts/configure/50_deploy_policy_files.sh && \
bash mac_mini/scripts/configure/40_configure_sqlite.sh && \
bash mac_mini/scripts/configure/20_configure_mosquitto.sh && \
bash mac_mini/scripts/configure/10_configure_home_assistant.sh && \
bash mac_mini/scripts/configure/30_configure_ollama.sh && \
bash mac_mini/scripts/configure/60_configure_notifications.sh && \
bash mac_mini/scripts/verify/10_verify_docker_services.sh && \
bash mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh && \
bash mac_mini/scripts/verify/30_verify_ollama_inference.sh && \
bash mac_mini/scripts/verify/40_verify_sqlite.sh && \
bash mac_mini/scripts/verify/50_verify_env_and_assets.sh && \
bash mac_mini/scripts/verify/60_verify_notifications.sh && \
bash mac_mini/scripts/verify/80_verify_services.sh
```

---

## 재실행할 때의 원칙

### install 재실행이 필요한 경우
- Homebrew 의존성 누락
- Docker runtime 문제
- compose workspace 손상
- Python venv 문제

### configure 재실행이 필요한 경우
- `.env` 수정
- policy / schema 재배포
- SQLite 재설정
- broker / Home Assistant / Ollama / notification 재설정

### verify 재실행이 필요한 경우
- install 또는 configure 이후 상태 점검
- 일부 서비스가 비정상일 때 재확인
- 변경 반영 후 회귀 점검

---

## 최종 요약

Mac mini에서는 항상 아래 순서를 기본으로 생각하면 된다.

```text
install → configure → verify
```

가장 중요한 규칙은 다음 한 문장이다.

**Mac mini에서는 configure를 install보다 먼저 실행하지 말고, verify는 항상 마지막에 실행한다.**

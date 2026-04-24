# 지체장애인을 위한 프라이버시 인지 엣지 스마트홈 시스템

## 프로젝트 개요

* 신체적·언어적 제약 상황에서의 접근성 높은 상호작용을 위한 프라이버시 인지형 엣지 스마트홈 시스템이다.
* 본 시스템은 클라우드 의존 없이 로컬 엣지 허브에서 동작하며, 극도로 제한된 입력 환경에서도 사용자의 의도를 안전하게 처리할 수 있도록 설계된다.
* 본 시스템의 최우선 사용자 대상은 신체적, 언어적 제약(Physical and Speech Limitations)을 복합적으로 겪고 있어 상용 스마트홈 기기(일반 음성 비서, 터치스크린 등)를 독자적으로 사용하기 어려운 취약 계층이다.
  1. 중증 신체 장애인 및 운동 기능 저하 사용자
     * 뇌성마비(Cerebral Palsy), 근육병(Myopathy), 소아마비(Polio), 척수 손상, 뇌졸중 등으로 인해 상·하지의 미세한 운동 제어나 이동이 어려운 사용자
     * 스마트폰 터치나 정교한 스위치 조작이 어려워, 주먹으로 내리치거나 발로 차는 형태의 단일 물리 타격 버튼(single-hit or kick-style bounded button input) 같은 극도로 제한된 입력 수단에 의존하는 사용자
  2. 언어 및 발화 제약이 있는 사용자
     * 조음장애(Dysarthria) 또는 신체적 피로 등으로 인해 명확한 발음이 어려운 사용자
     * 기존 상용 음성 비서가 요구하는 표준 발화 조건을 만족하기 어려운 사용자
     * 본 시스템은 이러한 표준 밖 입력 환경에서도 bounded LLM assistance를 통해 의도 해석을 보조한다.
  3. 일상 기능 저하를 겪는 고령층
     * 노화로 인해 근력, 시력, 반응 속도, 인지 기능이 저하되어 일상적인 가사 활동과 안전 관리에 어려움을 겪는 사용자
  4. 보호자 및 활동지원사
     * 직접적인 1차 사용자는 아니지만, 시스템 생태계의 필수적인 2차 사용자
     * 시스템이 입력의 모호성, 컨텍스트 부족, 응급 판단 등을 감지해 Safe Deferral 또는 Caregiver Escalation 경로로 전환했을 때, 보안 처리된 아웃바운드 통신(Telegram 등)을 통해 상황 알림과 제한적 수동 개입 권한을 받는 주체
* 본 시스템은 Mac mini 시스템 + Raspberry Pi 5 시스템 + 다수의 ESP32 디바이스로 구성된다. 따라서 개발 코드도 각각 역할을 구분해 구현해야 한다.

---

## 현재 범위에 대한 중요한 해석

반드시 다음 두 범위를 구분할 것.

### 1. current implementation-facing scope
현재 구현 대상 범위에는 다음이 포함될 수 있다.
- lighting path
- representative sensing path
- doorlock representative interface path

### 2. authoritative autonomous low-risk Class 1 scope
현재 frozen low-risk action catalog 기준의 authoritative Class 1 autonomous low-risk action 범위는 아직 다음에 한정된다.
- `light_on`
- `light_off`
- target: `living_room_light`, `bedroom_light`

즉,
- doorlock은 현재 **구현 대상 범위**에는 포함되지만,
- 현재 frozen baseline 기준의 **authoritative autonomous Class 1 low-risk scope와 자동으로 동일시하면 안 된다.**

doorlock을 authoritative autonomous low-risk scope처럼 다루려면, 먼저 frozen 정책/실험 문서와 정합성을 맞춰야 한다.

### 3. doorlock에 대한 논문적 해석
문서와 구현에서 doorlock은 단순 편의 기능이 아니라 **representative sensitive actuation case**로 해석한다.

즉,
- doorlock의 중요성은 “문을 여는 기능 구현” 자체보다,
- **LLM 기반 의도 복원과 민감 액추에이션 통제 사이의 경계**를 드러내는 대표 사례라는 점에 있다.

현재 해석에서:
- LLM은 제한 입력과 컨텍스트를 바탕으로 intent candidate를 복원할 수 있다.
- 그러나 door unlock은 unrestricted autonomous execution path로 가면 안 된다.
- 현재 아키텍처 해석에서는 caregiver escalation, bounded manual approval, deterministic validation, ACK-based closed-loop verification, local audit logging 경로와 정렬되어야 한다.

---

## 프롬프트 문서 구조

프롬프트 문서는 더 이상 단일 파일로 관리하지 않는다.

### 인덱스
* `/common/docs/architecture/12_prompts.md`

### core system prompt set
* `/common/docs/architecture/12_prompts_core_system.md`

### nodes and evaluation prompt set
* `/common/docs/architecture/12_prompts_nodes_and_evaluation.md`

주의:
- `12_prompts.md`는 이제 전체 프롬프트 본문이 아니라 **index file**이다.
- 프롬프트 번호 체계는 분리 후에도 유지된다.
- ESP32/STM32/실험/논문 평가 관련 프롬프트는 `12_prompts_nodes_and_evaluation.md`를 본다.

---

## 논문 기여와 실험 문서에 대한 중요 해석

이 저장소의 최근 문서 갱신은 단순 구현 메모가 아니라, 논문 contribution과 실험 구조를 맞추는 방향으로 진행되었다.

반드시 아래 두 문서를 함께 해석할 것.

* `/common/docs/paper/01_paper_contributions.md`
* `/common/docs/required_experiments.md`

핵심 해석:
- 본 논문의 핵심은 LLM에게 더 많은 자율권을 주는 것이 아니다.
- 본 논문의 핵심은 **제한된 입력 환경에서 LLM이 의도 복원을 보조하되, 민감 액추에이션은 정책/스키마/validator/caregiver escalation으로 구조적으로 제한하는 것**이다.
- 따라서 실험도 단순 accuracy나 latency뿐 아니라,
  - safe deferral,
  - escalation correctness,
  - autonomous unlock blocked,
  - approval/ACK/audit completeness,
  - bounded authority 하의 intent recovery improvement
  를 보여주는 방향으로 설계해야 한다.

특히 `required_experiments.md`에는 Contribution 1 보강용 intent recovery evaluation이 추가되었다.
이 비교는 최소한 다음 세 조건을 포함할 수 있다.
- Direct Mapping Baseline
- Rule-only Context Baseline
- LLM-assisted Intent Recovery

---

## SESSION_HANDOFF 관리 원칙

`SESSION_HANDOFF`는 앞으로 **master + addendum 구조**로 관리한다.

### master handoff
* `/common/docs/runtime/SESSION_HANDOFF.md`

### addendum example
* `/common/docs/runtime/SESSION_HANDOFF_2026-04-24_PROMPT_REFACTOR_AND_EVAL_UPDATE.md`

원칙:
- `SESSION_HANDOFF.md`는 장기적인 master summary 역할을 한다.
- 문서가 너무 길어져 connector 기반 업데이트가 위험하거나, 큰 milestone/topic update가 생기면 **날짜/주제 기반 addendum 문서**를 추가한다.
- 이후 세션은 master만 보지 말고, 필요한 addendum도 함께 확인해야 한다.

---

## 반드시 먼저 읽을 문서 순서

1. `/common/policies/low_risk_actions_v1_1_0_FROZEN.json`
2. `/common/policies/policy_table_v1_1_2_FROZEN.json`
3. `/common/docs/required_experiments.md`
4. `/common/docs/paper/01_paper_contributions.md`
5. `/common/docs/runtime/SESSION_HANDOFF.md`
6. 최신 `SESSION_HANDOFF` addendum 문서들
7. `/CLAUDE.md`
8. `/common/docs/architecture/12_prompts.md`

그 다음 필요 시 아래를 읽는다.
- `/common/docs/architecture/12_prompts_core_system.md`
- `/common/docs/architecture/12_prompts_nodes_and_evaluation.md`
- `/integration/scenarios/scenario_manifest_rules.md`
- `/integration/scenarios/scenario_review_guide.md`
- `/integration/tests/integration_test_runner_skeleton.py`
- `/integration/tests/expected_outcome_comparator.py`
- 각 device-layer README 및 script

---

## 반드시 참고할 문서

### 최우선 기준 문서
* `/README.md`
* `/common/docs/required_experiments.md`
* `/common/docs/paper/01_paper_contributions.md`
* `/common/docs/runtime/SESSION_HANDOFF.md`
* 최신 `SESSION_HANDOFF` addendum 문서

### 아키텍처 문서
* `/common/docs/architecture/01_installation_target_classification.md`
* `/common/docs/architecture/02_mac_mini_build_sequence.md`
* `/common/docs/architecture/03_deployment_structure.md`
* `/common/docs/architecture/04_project_directory_structure.md`
* `/common/docs/architecture/05_automation_strategy.md`
* `/common/docs/architecture/06_implementation_plan.md`
* `/common/docs/architecture/07_task_breakdown.md`
* `/common/docs/architecture/08_additional_required_work.md`
* `/common/docs/architecture/09_recommended_next_steps.md`
* `/common/docs/architecture/10_install_script_structure.md`
* `/common/docs/architecture/11_configuration_script_structure.md`
* `/common/docs/architecture/12_prompts.md`
* `/common/docs/architecture/12_prompts_core_system.md`
* `/common/docs/architecture/12_prompts_nodes_and_evaluation.md`
* `/common/docs/architecture/13_doorlock_access_control_and_caregiver_escalation.md`

### 시나리오 / integration 문서
* `/integration/README.md`
* `/integration/requirements.md`
* `/integration/scenarios/README.md`
* `/integration/scenarios/scenario_manifest_rules.md`
* `/integration/scenarios/scenario_review_guide.md`
* `/integration/measurement/class_wise_latency_profiles.md`
* `/integration/tests/integration_test_runner_skeleton.py`
* `/integration/tests/expected_outcome_comparator.py`

### 환경 구축 문서
#### Mac mini
* `/mac_mini/docs/README.md`
* `/mac_mini/scripts/configure/10_configure_home_assistant.sh`
* `/mac_mini/scripts/configure/20_configure_mosquitto.sh`
* `/mac_mini/scripts/configure/30_configure_ollama.sh`
* `/mac_mini/scripts/configure/40_configure_sqlite.sh`
* `/mac_mini/scripts/configure/50_deploy_policy_files.sh`
* `/mac_mini/scripts/configure/60_configure_notifications.sh`
* `/mac_mini/scripts/configure/70_write_env_files.sh`
* `/mac_mini/scripts/install/00_preflight.sh`
* `/mac_mini/scripts/install/10_install_homebrew_deps.sh`
* `/mac_mini/scripts/install/20_install_docker_runtime_mac.sh`
* `/mac_mini/scripts/install/21_prepare_compose_stack_mac.sh`
* `/mac_mini/scripts/install/30_setup_python_venv_mac.sh`
* `/mac_mini/scripts/templates/docker-compose.template.yml`
* `/mac_mini/scripts/verify/10_verify_docker_services.sh`
* `/mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh`
* `/mac_mini/scripts/verify/30_verify_ollama_inference.sh`
* `/mac_mini/scripts/verify/40_verify_sqlite.sh`
* `/mac_mini/scripts/verify/50_verify_env_and_assets.sh`
* `/mac_mini/scripts/verify/60_verify_notifications.sh`
* `/mac_mini/scripts/verify/80_verify_services.sh`

#### Raspberry Pi 5
* `/rpi/docs/README.md`
* `/rpi/scripts/configure/10_write_env_files_rpi.sh`
* `/rpi/scripts/configure/20_sync_phase0_artifacts_rpi.sh`
* `/rpi/scripts/configure/30_configure_time_sync_rpi.sh`
* `/rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh`
* `/rpi/scripts/configure/50_configure_fault_profiles_rpi.sh`
* `/rpi/scripts/install/00_preflight_rpi.sh`
* `/rpi/scripts/install/10_install_system_packages_rpi.sh`
* `/rpi/scripts/install/20_create_python_venv_rpi.sh`
* `/rpi/scripts/install/30_install_python_deps_rpi.sh`
* `/rpi/scripts/install/40_install_time_sync_client_rpi.sh`
* `/rpi/scripts/verify/70_verify_rpi_base_runtime.sh`
* `/rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh`

#### ESP32
* `/esp32/docs/README.md`
* `/esp32/scripts/configure/10_write_env_files_esp32.sh`
* `/esp32/scripts/configure/20_prepare_idf_workspace_esp32.sh`
* `/esp32/scripts/configure/30_prepare_managed_components_esp32.sh`
* `/esp32/scripts/configure/40_prepare_sample_project_esp32.sh`
* `/esp32/scripts/configure/10_write_env_files_esp32_windows.ps1`
* `/esp32/scripts/configure/20_prepare_idf_workspace_esp32_windows.ps1`
* `/esp32/scripts/configure/30_prepare_managed_components_esp32_windows.ps1`
* `/esp32/scripts/configure/40_prepare_sample_project_esp32_windows.ps1`
* `/esp32/scripts/install/mac/00_preflight_esp32_mac.sh`
* `/esp32/scripts/install/mac/10_install_prereqs_esp32_mac.sh`
* `/esp32/scripts/install/mac/20_install_esp_idf_esp32_mac.sh`
* `/esp32/scripts/install/linux/00_preflight_esp32_linux.sh`
* `/esp32/scripts/install/linux/10_install_prereqs_esp32_linux.sh`
* `/esp32/scripts/install/linux/20_install_esp_idf_esp32_linux.sh`
* `/esp32/scripts/install/windows/00_preflight_esp32_windows.ps1`
* `/esp32/scripts/install/windows/10_install_prereqs_esp32_windows.ps1`
* `/esp32/scripts/install/windows/20_install_esp_idf_esp32_windows.ps1`
* `/esp32/scripts/verify/10_verify_idf_cli_esp32.sh`
* `/esp32/scripts/verify/20_verify_toolchain_target_esp32.sh`
* `/esp32/scripts/verify/30_verify_component_resolution_esp32.sh`
* `/esp32/scripts/verify/40_verify_sample_build_esp32.sh`
* `/esp32/scripts/verify/10_verify_idf_cli_esp32_windows.ps1`
* `/esp32/scripts/verify/20_verify_toolchain_target_esp32_windows.ps1`
* `/esp32/scripts/verify/30_verify_component_resolution_esp32_windows.ps1`
* `/esp32/scripts/verify/40_verify_sample_build_esp32_windows.ps1`

### 스키마
* `/common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json`
* `/common/schemas/context_schema_v1_0_0_FROZEN.json`
* `/common/schemas/candidate_action_schema_v1_0_0_FROZEN.json`
* `/common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json`
* `/common/schemas/validator_output_schema_v1_1_0_FROZEN.json`

### 정책
* `/common/policies/policy_table_v1_1_2_FROZEN.json`
* `/common/policies/low_risk_actions_v1_1_0_FROZEN.json`
* `/common/policies/output_profile_v1_1_0.json`
* `/common/policies/fault_injection_rules_v1_4_0_FROZEN.json`

---

## 코딩 규칙

* 테스트 코드는 항상 작성할 것
* 한글로 주석을 자세하게 달 것
* 파이썬은 항상 venv로 동작하게 할 것
* 파이썬 코딩 규칙은 PEP8을 따를 것
* integration 관련 코드를 작성할 때는 scenario / fixture / comparator / measurement 문서와 함께 정합성을 확인할 것
* 구현 중 문서와 코드가 충돌하면, 코드에 맞춰 임의 해석하지 말고 먼저 frozen baseline과 `required_experiments.md`를 기준으로 해석할 것
* 논문 기여를 직접 뒷받침하는 실험/평가 코드를 작성할 때는 `01_paper_contributions.md`와 `required_experiments.md`를 함께 확인할 것

---

## 절대 하지 말 것

- FROZEN 파일은 수정 금지
- 클라우드 API 호출 코드 작성 금지 (엣지 전용 시스템)
- 정책 파일 우회 로직 작성 금지
- deployment-local 파일(.env, runtime copy, synced copy)을 canonical truth처럼 취급 금지
- doorlock implementation scope를 현재 authoritative autonomous low-risk Class 1 scope로 임의 승격 금지
- 논문 contribution을 이유로 unrestricted autonomous sensitive actuation path를 정당화하지 말 것

---

## 작업 시작점

이번 코딩 시작점은 다음 순서를 따른다.

1. `mac_mini/code/` 아래의 **policy router** 구현
2. `mac_mini/code/` 아래의 **deterministic validator** 구현
3. `mac_mini/code/` 아래의 **safe deferral handler** 구현
4. 이후 audit logger / notification backend 순서로 진행

다른 영역을 먼저 구현해야 하는 특별한 이유가 없다면 이 순서를 기본으로 한다.

---

## 작업 순서

1. 반드시 먼저 읽을 문서를 읽고, 이를 기준으로 시나리오와 요구사항을 확인한다.
2. 현재 작업 범위에 해당하는 프롬프트 묶음을 `/common/docs/architecture/12_prompts.md`에서 찾고, 실제 본문은 split prompt files에서 선택한다.
3. 구현 시 스키마와 정책을 참조한다.
4. 빌드 또는 실행 전에는 install / configure / verify 상태가 완료되었는지 먼저 확인한다.
5. integration 관련 코드를 작성할 경우 scenario manifest, review guide, fixture, comparator 구조와 정합성을 확인한다.
6. `/common/docs/architecture/06_implementation_plan.md`, `/common/docs/architecture/07_task_breakdown.md`, `/common/docs/architecture/08_additional_required_work.md`, `/common/docs/architecture/10_install_script_structure.md`, `/common/docs/architecture/11_configuration_script_structure.md`, `/common/docs/required_experiments.md`, `/common/docs/paper/01_paper_contributions.md`, `/common/docs/runtime/SESSION_HANDOFF.md` 및 필요한 addendum 문서에 수정/추가사항이 생기면 같이 반영한다.

---

## 문서 충돌 시 해석 우선순위

문서가 충돌할 때는 다음 우선순위를 따른다.

1. FROZEN 정책/스키마
2. `/common/docs/required_experiments.md`
3. `/common/docs/paper/01_paper_contributions.md`
4. `/common/docs/runtime/SESSION_HANDOFF.md` 및 관련 addendum
5. device-layer README와 integration 문서
6. `CLAUDE.md`

즉, `CLAUDE.md`는 작업 안내 문서이지, canonical truth 자체는 아니다.

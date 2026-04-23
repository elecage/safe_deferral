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
      * 본 시스템은 이러한 표준 밖 입력 환경에서도 bounded LLM assistance를 통해 의도 해석을 보조한다
   3. 일상 기능 저하를 겪는 고령층
      * 노화로 인해 근력, 시력, 반응 속도, 인지 기능이 저하되어 일상적인 가사 활동과 안전 관리에 어려움을 겪는 사용자
   4. 보호자 및 활동지원사
      * 직접적인 1차 사용자는 아니지만, 시스템 생태계의 필수적인 2차 사용자
      * 시스템이 입력의 모호성, 컨텍스트 부족, 응급 판단 등을 감지해 Safe Deferral 또는 Caregiver Escalation 경로로 전환했을 때, 보안 처리된 아웃바운드 통신(Telegram 등)을 통해 상황 알림과 제한적 수동 개입 권한을 받는 주체
      * 본 시스템은 자유로운 대화나 정교한 조작이 어려운 복합 장애 당사자 및 고령자가 최소한의 bounded physical input만으로도 안전하게 스마트홈 기능을 사용할 수 있도록 돕는 포용적(inclusive) 접근성 지원 시스템이다.
  * 본 시스템은 MAC Mini 시스템 + 라즈베리파이 5 시스템 + 다수의 ESP32 디바이스로 구성된다. 따라서 개발 코드도 각각 구현된다.

## 프롬프트 묶음

  * /common/docs/architecture/12_prompts.md

## 반드시 참고할 문서
  * /README.md
  * /common/docs/required_experiments.md
  * /common/docs/architecture/01_installation_target_classification.md
  * /common/docs/architecture/02_mac_mini_build_sequence.md
  * /common/docs/architecture/03_deployment_structure.md
  * /common/docs/architecture/04_project_directory_structure.md
  * /common/docs/architecture/05_automation_strategy.md
  * /common/docs/architecture/06_implementation_plan.md
  * /common/docs/architecture/07_task_breakdown.md
  * /common/docs/architecture/08_additional_required_work.md
  * /common/docs/architecture/09_recommended_next_steps.md
  * /common/docs/architecture/10_install_script_structure.md
  * /common/docs/architecture/11_configuration_script_structure.md
    
### 시나리오
  * https://github.com/elecage/safe_deferral/tree/main/integration/scenarios
  * 시나리오에서 가장 기본이 되는 문서는 README.md와 scenario_review_guide.md이며, JSON 파일을 이용하여 시나리오를 확인할 
### 요구사항
  * https://github.com/elecage/safe_deferral/blob/main/integration/requirements.md
### 환경 구축 문서
#### MAC Mini
  * /mac_mini/docs/README.md
  * /mac_mini/scripts/configure/10_configure_home_assistant.sh
  * /mac_mini/scripts/configure/20_configure_mosquitto.sh
  * /mac_mini/scripts/configure/30_configure_ollama.sh
  * /mac_mini/scripts/configure/40_configure_sqlite.sh
  * /mac_mini/scripts/configure/50_deploy_policy_files.sh
  * /mac_mini/scripts/configure/60_configure_notifications.sh
  * /mac_mini/scripts/configure/70_write_env_files.sh
  * /mac_mini/scripts/install/00_preflight.sh
  * /mac_mini/scripts/install/10_install_homebrew_deps.sh
  * /mac_mini/scripts/install/20_install_docker_runtime_mac.sh
  * /mac_mini/scripts/install/21_prepare_compose_stack_mac.sh
  * /mac_mini/scripts/install/30_setup_python_venv_mac.sh
  * /mac_mini/scripts/templates/docker-compose.template.yml
  * /mac_mini/scripts/verify/10_verify_docker_services.sh
  * /mac_mini/scripts/verify/20_verify_mqtt_pubsub.sh
  * /mac_mini/scripts/verify/30_verify_ollama_inference.sh
  * /mac_mini/scripts/verify/40_verify_sqlite.sh
  * /mac_mini/scripts/verify/50_verify_env_and_assets.sh
  * /mac_mini/scripts/verify/60_verify_notifications.sh
  * /mac_mini/scripts/verify/80_verify_services.sh

#### Raspberry Pi-5
  * /rpi/docs/README.md
  * /rpi/scripts/configure/10_write_env_files_rpi.sh
  * /rpi/scripts/configure/20_sync_phase0_artifacts_rpi.sh
  * /rpi/scripts/configure/30_configure_time_sync_rpi.sh
  * /rpi/scripts/configure/40_configure_simulation_runtime_rpi.sh
  * /rpi/scripts/configure/50_configure_fault_profiles_rpi.sh
  * /rpi/scripts/install/00_preflight_rpi.sh
  * /rpi/scripts/install/10_install_system_packages_rpi.sh
  * /rpi/scripts/install/20_create_python_venv_rpi.sh
  * /rpi/scripts/install/30_install_python_deps_rpi.sh
  * /rpi/scripts/install/40_install_time_sync_client_rpi.sh
  * /rpi/scripts/verify/70_verify_rpi_base_runtime.sh
  * /rpi/scripts/verify/80_verify_rpi_closed_loop_audit.sh

#### ESP32
  * /esp32/docs/README.md
  * /esp32/scripts/configure/10_write_env_files_esp32.sh
  * /esp32/scripts/configure/20_prepare_idf_workspace_esp32.sh
  * /esp32/scripts/configure/30_prepare_managed_components_esp32.sh
  * /esp32/scripts/configure/40_prepare_sample_project_esp32.sh
  * /esp32/scripts/install/windows/00_preflight_esp32_windows.ps1
  * /esp32/scripts/install/windows/10_install_prereqs_esp32_windows.ps1
  * /esp32/scripts/install/windows/20_install_esp_idf_esp32_windows.ps1
  * /esp32/scripts/verify/10_verify_idf_cli_esp32.sh
  * /esp32/scripts/verify/20_verify_toolchain_target_esp32.sh
  * /esp32/scripts/verify/30_verify_component_resolution_esp32.sh
  * /esp32/scripts/verify/40_verify_sample_build_esp32.sh
  
### 스키마
  * /common/schemas/policy_router_input_schema_v1_1_1_FROZEN.json
  * /common/schemas/context_schema_v1_0_0_FROZEN.json
  * /common/schemas/candidate_action_schema_v1_0_0_FROZEN.json
  * /common/schemas/class_2_notification_payload_schema_v1_0_0_FROZEN.json
  * /common/schemas/validator_output_schema_v1_1_0_FROZEN.json

### 정책
  * /common/policies/policy_table_v1_1_2_FROZEN.json
  * /common/policies/low_risk_actions_v1_1_0_FROZEN.json
  * /common/policies/output_profile_v1_1_0.json
  * /common/policies/fault_injection_rules_v1_4_0_FROZEN.json

### 코딩 규칙
 * 테스트 코드는 항상 작성할 것
 * 한글로 주석을 자세하게 달것
 * 파이썬은 항상 venv로 동작하게 할 것
 * 파이썬 코딩 규칙은 PEP8을 따를 것
   
## 절대 하지 말 것
- FROZEN 파일은 수정 금지
- 클라우드 API 호출 코드 작성 금지 (엣지 전용 시스템)
- 정책 파일 우회 로직 작성 금지

## 작업 순서
1. 반드시 참고할 문서들을 읽고 이를 기준으로 한 시나리오와 요구사항을 확인
2. /common/docs/architecture/12_prompts.md에 정의된 프롬프트 1번부터 차례로 구현
3. 구현시 스키마와 정책을 참조
4. 빌드 후 실행을 할 경우 실행 전 설치 및 설정이 완료되었는지 확인하고, 만일 미비하다면 완료 후 실행 검증할것
5.  /common/docs/architecture/06_implementation_plan.md, /common/docs/architecture/07_task_breakdown.md, /common/docs/architecture/08_additional_required_work.md, /common/docs/architecture/10_install_script_structure.md, /common/docs/architecture/11_configuration_script_structure.md들은 코드를 개발하면서 수정사항이나 추가사항이 발생하면 반영할

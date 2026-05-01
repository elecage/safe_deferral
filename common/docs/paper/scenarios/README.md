# 논문용 시나리오 사용자 스토리

## 목적

이 디렉터리는 `integration/scenarios/` 아래의 scenario JSON 파일을 사람이 읽기 쉬운 한글 사용자 스토리로 풀어 설명한다.

JSON 파일은 실험과 검증을 위한 계약형 시나리오이고, 이 디렉터리의 Markdown 파일은 논문 작성, 시나리오 설명, 실험 의도 공유, 노드 개발 범위 이해를 위한 서술형 문서다.

## 작성 원칙

- 각 `*_scenario_skeleton.json` 파일은 대응되는 `*_scenario_user_story.md` 파일을 가진다.
- Markdown 문서는 JSON의 안전 경계, 입력 조건, 기대 결과를 바꾸지 않는다.
- Class 2 후보 제시, clarification payload, dashboard observation, MQTT topic, payload example은 실행 권한이 아니다.
- Doorlock은 현재 autonomous Class 1 low-risk action이 아니다.
- `doorbell_detected`는 방문자 context이며 door unlock authorization이 아니다.
- `environmental_context.doorbell_detected=true` + button trigger → **CLASS_1** 가능 (방문자 있는 상태의 일반 입력).
- `trigger_event.event_type=sensor, event_code=doorbell_detected` → **CLASS_2 (C208)** (초인종 자체가 트리거, caregiver escalation 필요).
- Class 2 clarification은 `safe_deferral/clarification/interaction`을 기준으로 설명한다.

## 시나리오 대응표

| JSON scenario | 사용자 스토리 |
|---|---|
| `integration/scenarios/baseline_scenario_skeleton.json` | `baseline_scenario_user_story.md` |
| `integration/scenarios/class0_e001_scenario_skeleton.json` | `class0_e001_scenario_user_story.md` |
| `integration/scenarios/class0_e002_scenario_skeleton.json` | `class0_e002_scenario_user_story.md` |
| `integration/scenarios/class0_e003_scenario_skeleton.json` | `class0_e003_scenario_user_story.md` |
| `integration/scenarios/class0_e004_scenario_skeleton.json` | `class0_e004_scenario_user_story.md` |
| `integration/scenarios/class0_e005_scenario_skeleton.json` | `class0_e005_scenario_user_story.md` |
| `integration/scenarios/class1_baseline_scenario_skeleton.json` | `class1_baseline_scenario_user_story.md` |
| `integration/scenarios/class2_insufficient_context_scenario_skeleton.json` | `class2_insufficient_context_scenario_user_story.md` |
| `integration/scenarios/class2_to_class1_low_risk_confirmation_scenario_skeleton.json` | `class2_to_class1_low_risk_confirmation_scenario_user_story.md` |
| `integration/scenarios/class2_to_class0_emergency_confirmation_scenario_skeleton.json` | `class2_to_class0_emergency_confirmation_scenario_user_story.md` |
| `integration/scenarios/class2_timeout_no_response_safe_deferral_scenario_skeleton.json` | `class2_timeout_no_response_safe_deferral_scenario_user_story.md` |
| `integration/scenarios/class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json` | `class2_caregiver_confirmation_doorlock_sensitive_scenario_user_story.md` |
| `integration/scenarios/stale_fault_scenario_skeleton.json` | `stale_fault_scenario_user_story.md` |
| `integration/scenarios/conflict_fault_scenario_skeleton.json` | `conflict_fault_scenario_user_story.md` |
| `integration/scenarios/missing_state_scenario_skeleton.json` | `missing_state_scenario_user_story.md` |


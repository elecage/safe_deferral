# SESSION_HANDOFF — Schema Compliance and C208 Clarification Path Bugfix

**Date:** 2026-05-01
**Branch:** main (direct commit e6df3f6)
**Tests:** 405/405 mac_mini

---

## 이번 세션에서 수정한 버그

### 1. publish_llm_candidate() / publish_validator_output() — additionalProperties 위반

**증상:**
- `safe_deferral/llm/candidate_action` 수신자(audit observer 등)가 페이로드를 schema 검증하면 거부.
- `safe_deferral/validator/output` 수신자가 동일하게 거부.

**원인:**
- `publish_llm_candidate()`: `audit_correlation_id`, `model_id`, `is_fallback`, `llm_boundary`, `timestamp_ms`를 payload에 추가했으나, `candidate_action_schema.json`이 `additionalProperties: false`로 `proposed_action`, `target_device`, `rationale_summary`, `deferral_reason`만 허용.
- `publish_validator_output()`: `audit_correlation_id`, `timestamp_ms`를 추가했으나, `validator_output_schema.json`이 `additionalProperties: false`로 `validation_status`, `routing_target`, `exception_trigger_id`, `executable_payload`, `deferral_reason`만 허용.

**수정 파일:** `mac_mini/code/telemetry_adapter/adapter.py`

```python
def publish_llm_candidate(self, llm_result) -> None:
    # llm_result.candidate는 LocalLlmAdapter가 이미 candidate_action_schema.json으로 검증한 dict
    self._publisher.publish(self._llm_topic, llm_result.candidate, qos=1)

def publish_validator_output(self, val_result) -> None:
    # val_result.to_dict()는 validator_output_schema.json 호환 필드만 반환
    self._publisher.publish(self._validator_topic, val_result.to_dict(), qos=1)
```

---

### 2. clarification_record — selection_source enum 위반

**증상:**
- `safe_deferral/clarification/interaction` 수신자가 `selection_result.selection_source` 필드를 schema 검증하면 거부.
- `clarification_interaction_schema.json`이 허용하는 enum: `bounded_input_node`, `voice_input`, `caregiver_confirmation`, `deterministic_emergency_evidence`, `timeout_or_no_response`, `none`
- 런타임에서 실제로 전달되는 값: `user_mqtt_button`, `user_mqtt_button_late`, `caregiver_telegram_inline_keyboard`

**수정 파일:** `mac_mini/code/class2_clarification_manager/manager.py`

`_SELECTION_SOURCE_MAP` 추가 및 `_build_record()`에서 저장 전 정규화:

| 런타임 값 | 스키마 enum 값 |
|---|---|
| `user_mqtt_button` | `bounded_input_node` |
| `user_mqtt_button_late` | `bounded_input_node` |
| `caregiver_telegram_inline_keyboard` | `caregiver_confirmation` |
| `timeout_or_no_response` | `timeout_or_no_response` (그대로) |

---

### 3. C208 — Class2ClarificationManager 미등록

**증상:**
- PolicyRouter가 `doorbell_detected` 센서 이벤트를 C208로 CLASS_2 라우팅하지만,
  `Class2ClarificationManager.start_session("C208", ...)` 호출 시 `_TRIGGER_TO_REASON`에 C208 없음.
- `unresolved_reason`이 폴백값인 `"insufficient_context"`로 기록.
- `_DEFAULT_CANDIDATES["insufficient_context"]`는 조명 도움(C1_LIGHTING_ASSISTANCE)을 첫 번째 후보로 제시 — doorlock-sensitive context에 부적절.
- notification payload `event_summary`에 C208 정보 없음.

**수정 파일:** `mac_mini/code/class2_clarification_manager/manager.py`

- `_TRIGGER_TO_REASON["C208"] = "visitor_context_sensitive_actuation_required"`
- `_TRIGGER_SUMMARY["C208"] = "방문자 감지 — 도어락 민감 경로로 Class 2 진입"`
- `_DEFAULT_CANDIDATES["visitor_context_sensitive_actuation_required"]` 추가:
  - 1순위: `C2_CAREGIVER_HELP` (보호자에게 방문자 확인 요청) — `CAREGIVER_CONFIRMATION`
  - 2순위: `C3_EMERGENCY_HELP` (긴급상황) — `CLASS_0`
  - 3순위: `C4_CANCEL_OR_WAIT` (취소하고 대기) — `SAFE_DEFERRAL`
  - **조명 도움(C1_LIGHTING_ASSISTANCE) 의도적으로 제외** — doorlock은 Class 1 카탈로그 밖

---

## 수정된 파일 요약

| 파일 | 수정 내용 |
|---|---|
| `mac_mini/code/telemetry_adapter/adapter.py` | `publish_llm_candidate()`, `publish_validator_output()` — schema-only 필드만 발행 |
| `mac_mini/code/class2_clarification_manager/manager.py` | C208 trigger 등록; `_build_record()`에 selection_source 정규화 |
| `mac_mini/code/tests/test_telemetry_adapter.py` | 스키마 위반 테스트로 교체 (`test_payload_only_schema_fields`, `test_no_audit_id_*`) |
| `mac_mini/code/tests/test_class2_clarification_manager.py` | `TestC208VisitorContext` (5개), `TestSelectionSourceNormalisation` (6개) 추가 |

---

## 확인된 동작

- `publish_llm_candidate()` 페이로드가 `candidate_action_schema.json` 허용 필드만 포함 ✅
- `publish_validator_output()` 페이로드가 `validator_output_schema.json` 허용 필드만 포함 ✅
- `clarification_record.selection_result.selection_source`가 항상 schema enum 값 ✅
- C208 세션의 `unresolved_reason = "visitor_context_sensitive_actuation_required"` ✅
- C208 세션 첫 번째 후보가 `CAREGIVER_CONFIRMATION` (조명 도움 없음) ✅
- 테스트: 405/405 ✅

---

## 주의사항

- `publish_llm_candidate()`는 이제 `llm_result.candidate`를 그대로 발행한다.
  LLM이 fallback 상태(`safe_deferral`)면 `deferral_reason`이 포함될 수 있으며 이는 schema 허용 필드.
  `audit_correlation_id`나 `model_id`가 필요한 observer는 `dashboard/observation` 또는 `audit/log` 토픽을 구독해야 함.
- C208 기본 후보는 3개(max=4 미만)이므로 LLM이 추가 후보를 공급하는 경우 최대 4개까지 허용.
  단, doorlock 관련 후보는 Class 1 카탈로그 밖이므로 LLM이 생성해도 Validator가 차단.

---

## 다음 세션 권장 작업

1. **전체 패키지 실험 재실행** — C208 포함 CLASS_2 시나리오 end-to-end 검증
2. **schema validator 통합 테스트** — `jsonschema`로 실제 발행 페이로드를 세 스키마에 검증
3. **audit/log 토픽 확인** — LLM candidate audit_correlation_id가 audit/log에 기록되는지 확인
   (publish_llm_candidate에서 제거됐으므로 별도 경로 필요시 AuditLogger 직접 사용)

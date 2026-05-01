# SESSION_HANDOFF — MQTT Topic Wiring Bugfix (LLM / Validator / Clarification)

**Date:** 2026-05-01
**Branch:** main (direct commit 8d96a04)
**Tests:** 394/394 mac_mini

---

## 이번 세션에서 수정한 버그

### 레지스트리 선언 토픽 3개가 실제로 발행되지 않던 문제

**증상:**
- `safe_deferral/llm/candidate_action` — 레지스트리에 publisher=`mac_mini.local_llm_adapter`로 선언되어 있으나 실제 발행 없음.
- `safe_deferral/validator/output` — 레지스트리에 publisher=`mac_mini.deterministic_validator`로 선언, RPi 대시보드 브릿지가 subscriber로 등록되어 있으나 실제 발행 없음.
- `safe_deferral/clarification/interaction` — 레지스트리에 publisher=`mac_mini.class2_clarification_manager`로 선언, RPi `class2_transition_verifier_optional`이 subscriber로 등록되어 있으나 실제 발행 없음.

**원인:** CLASS_1 경로에서 LLM 결과 및 Validator 결과는 in-process로만 전달되고 MQTT로 발행하지 않았음. CLASS_2 경로에서 `Class2ClarificationManager._build_record()`가 `clarification_interaction_schema.json` 호환 dict를 이미 만들었지만, `publish_class2_update()` 내에서 `dashboard/observation`에만 발행하고 `clarification/interaction`에는 발행하지 않았음.

---

## 수정 내용

### 수정 파일: `mac_mini/code/telemetry_adapter/adapter.py`

**`__init__`에 세 토픽 문자열 추가:**
```python
self._llm_topic: str = loader.get_topic("safe_deferral/llm/candidate_action")
self._validator_topic: str = loader.get_topic("safe_deferral/validator/output")
self._clarification_topic: str = loader.get_topic("safe_deferral/clarification/interaction")
```

**`publish_llm_candidate(llm_result)` 추가:**
- payload: `{audit_correlation_id, proposed_action, target_device, model_id, is_fallback, llm_boundary, timestamp_ms}`
- `safe_deferral/llm/candidate_action`으로 발행

**`publish_validator_output(val_result)` 추가:**
- payload: `val_result.to_dict()` + `{audit_correlation_id, timestamp_ms}`
- `safe_deferral/validator/output`으로 발행

**`publish_class2_update()` 확장:**
- 기존 `dashboard/observation` 발행에 이어, `class2_result.clarification_record`를
  `safe_deferral/clarification/interaction`으로 추가 발행.
- `clarification_record`는 `Class2ClarificationManager._build_record()`가
  `clarification_interaction_schema.json` 필수 필드(`clarification_id`,
  `unresolved_reason`, `candidate_choices`, `transition_target`, `llm_boundary`)를
  이미 모두 포함하므로 별도 변환 없음.

### 수정 파일: `mac_mini/code/main.py`

`_handle_class1()` 내:
```python
llm_result = self._llm.generate_candidate(ctx, audit_correlation_id=audit_id)
self._telemetry.publish_llm_candidate(llm_result)   # ← 추가

val_result = self._validator.validate(candidate, audit_correlation_id=audit_id)
self._telemetry.publish_validator_output(val_result) # ← 추가
self._telemetry.update_validation(val_result)
```

CLASS_2 interaction publish는 `publish_class2_update()`가 이미 호출되는 모든 분기
(user 선택, late user, caregiver 응답, Phase-2 timeout)를 커버하므로 추가 변경 없음.

---

## 수정된 파일 요약

| 파일 | 수정 내용 |
|---|---|
| `mac_mini/code/telemetry_adapter/adapter.py` | 세 토픽 로드; `publish_llm_candidate()`, `publish_validator_output()` 추가; `publish_class2_update()`에 clarification/interaction 발행 추가 |
| `mac_mini/code/main.py` | `_handle_class1()`에 두 publish 호출 추가 |
| `mac_mini/code/tests/test_telemetry_adapter.py` | `TestPublishLlmCandidate` (5개), `TestPublishValidatorOutput` (5개), `TestPublishClass2UpdateClarification` (4개) 추가 |

---

## 확인된 동작

- CLASS_1 이벤트 발생 시 `llm/candidate_action`, `validator/output` 발행 ✅
- CLASS_2 session 완료(user 선택, caregiver 응답, timeout 모두) 시 `clarification/interaction` 발행 ✅
- `dashboard/observation` 기존 발행 회귀 없음 ✅
- 테스트: 64/64 (telemetry adapter), 394/394 (mac_mini 전체) ✅

---

## 주의사항

- `publish_class2_update()`는 이제 publish를 두 번 호출함 (`dashboard/observation` + `clarification/interaction`).
  두 발행은 동일한 `class2_result.clarification_record`를 참조하므로 원자적이지 않으나,
  MQTT QoS=1이므로 실험 관측 목적으로는 충분함.
- `llm_boundary` 필드는 항상 `final_decision_allowed=False`, `actuation_authority_allowed=False`를
  포함해야 함. `LLMCandidateResult` 기본값이 이를 보장함.

---

## 다음 세션 권장 작업

1. **RPi 대시보드 브릿지 확인** — `validator/output` 및 `clarification/interaction` 수신 후 대시보드에 반영되는지 확인
2. **시나리오 검증 재실행** — `class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json` 포함 전체 패키지 실험에서 세 토픽 발행 확인
3. **audit_log 확인** — LLM candidate, validator output, clarification interaction이 `audit/log`에도 기록되는지 확인

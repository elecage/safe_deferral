# SESSION_HANDOFF — LLM-Driven Class 2 Candidate Generation, Phase 5 (Code-Only Implementation)

**Date:** 2026-05-01
**Tests:** 435/435 mac_mini fast suite (unchanged), 128 → 137 rpi (+9 new)
**Schema validation:** scenario skeletons 15/15 unchanged; no canonical asset edits in this PR

**Design baseline:** `common/docs/architecture/09_llm_driven_class2_candidate_generation_plan.md` (PR #86)
**Builds on:** PR #87 (Phase 1+2), PR #88 (Phase 3)

---

## 이번 세션의 범위

**하드웨어 미준비** 상태에서 진행 가능한 부분만 구현. design doc Phase 5의 평가 인프라(코드)만 추가하고 단위 테스트로 자체 검증. 실제 metric 값은 추후 Mac mini + Ollama + RPi + Telegram 환경에서 trial을 돌려야 의미를 가짐.

### Phase 5 metric 정의 재검토 (design doc 보완)

설계 문서가 처음 제안한 세 metric은 PR #87의 사전 검증 구조 때문에 **항상 100% 또는 0%**로 떨어지는 구조적 문제가 있었다:

| design doc 표현 | 문제 |
|---|---|
| `llm_candidate_admissibility_rate` | 어댑터가 out-of-catalog 후보를 사전에 드롭 → 항상 100% |
| `prompt_length_violation_rate` | 길이 초과 후보를 사전에 드롭 → 항상 0% |
| `llm_candidate_relevance_rate` | `submit_selection`이 unknown id 거부 → 항상 100% |

대신 **실제 LLM 품질을 정직하게 측정하는 4종 metric**을 산출:

- `llm_generated_rate` — clarification record 중 candidate_source=llm_generated 비율
- `default_fallback_rate` — 같은 분모에서 default_fallback 비율
- `llm_user_pickup_rate` — LLM 세션 중 사용자/보호자가 후보를 confirm한 비율 (LLM의 후보가 실제로 유용했는지)
- `default_fallback_user_pickup_rate` — 정적 fallback 세션의 같은 비율 (직접 비교용 baseline)

이 metric들은 LLM 어댑터의 사전 게이팅과 무관하게 의미 있는 값을 가진다. 운영 환경에서:
- `llm_generated_rate`가 낮다 → LLM 호출에 실패가 잦거나 bounded constraint가 너무 좁음 → 정책 조정 또는 prompt 튜닝 신호
- `llm_user_pickup_rate`가 `default_fallback_user_pickup_rate`보다 낮다 → LLM 후보가 정적 후보보다 사용자 의도와 어긋남 → prompt/context 표현 재검토

---

## 변경 파일 요약

| 파일 | 변경 |
|---|---|
| `rpi/code/clarification_store.py` | 신설. NotificationStore 패턴의 ring buffer (`add`, `find_by_correlation_id`, `clear`, `list_recent`). |
| `rpi/code/main.py` | `safe_deferral/clarification/interaction` 토픽을 `_MONITOR_TOPICS`에 추가. `ClarificationStore` 인스턴스 생성 + 메시지 디스패치 분기 + `PackageRunner` 생성자에 주입. |
| `rpi/code/experiment_package/runner.py` | `__init__`에 `clarification_store=None` 추가. 신규 `_await_clarification(correlation_id, observation)` 헬퍼: observation 후 최대 2초 동안 폴링(notification과 동일한 race tolerance). `_run_trial`이 `complete_trial(...)` / `timeout_trial(...)`에 `clarification_payload` 전달. |
| `rpi/code/experiment_package/trial_store.py` | `TrialResult.clarification_payload` 필드 추가 + `to_dict` 갱신. `complete_trial` / `timeout_trial` signature 확장 (backward compatible: 새 인자 default None). |
| `rpi/code/experiment_package/trial_store.py` | `_metrics_d`가 `class2_llm_quality` 서브블록 보고. 새 헬퍼 `_class2_llm_quality_block(trials)`. |
| `rpi/code/tests/test_rpi_components.py` | +9: `TestClarificationStore` (×2), `TestClass2LlmQualityBlock` (×6), `TestClarificationCapture` (×1, late-arrival race). |

---

## 안전 invariant (변동 없음)

본 PR은 평가 측 코드만 변경하며 운영 경로는 건드리지 않음. PR #87+#88에서 확립한 모든 invariant 그대로:
- LLM 후보 제안만, 실행은 validator가 catalog로 게이트
- catalog 외 action_hint/target_hint 즉시 드롭
- CLASS_0 후보 고정 템플릿 정규화
- caregiver-required path는 caregiver-first
- LLM 실패 → silent fallback
- catalog 인간 governance

추가 보장:
- ClarificationStore는 read-only ring buffer. 운영 actuator나 정책 수정 권한 없음.
- `_metrics_d`의 새 서브블록은 통계만 산출 — 어떠한 라우팅·실행 결정에도 영향 주지 않음.

---

## 주의사항

- **canonical asset 변경 없음.** 새 토픽 구독은 RPi 측 evaluation infrastructure만 영향. Mac mini는 PR #87부터 이미 같은 토픽으로 publish 중.
- **하드웨어 검증 필요:** 본 PR의 metric 값은 모두 합성 trial로 단위 검증됨. 실제 Mac mini + Ollama가 살아있는 환경에서 trial을 돌려야 LLM의 실 동작이 metric에 반영됨.
- **rejection_reason은 미캡처:** PR #87의 `Class2CandidateResult.rejection_reason`은 어댑터에서만 머무르고 manager의 clarification_record에는 들어가지 않음. fallback 사유 분포(`invalid_json`, `prompt_too_long`, `caregiver_first_violation` 등)를 metric으로 산출하려면 별도 PR에서:
  - manager가 LLM 결과를 session에 보관
  - clarification record에 `llm_rejection_reason` optional 필드 추가 (`clarification_interaction_schema` additive 확장)
  - `_class2_llm_quality_block`에 `rejection_reason_distribution` 추가

본 PR은 user pickup rate 비교라는 가장 직관적인 metric에 집중하고 rejection_reason 캡처는 follow-up.

---

## 다음 세션 권장 작업

1. **하드웨어 준비 후 E2E 재실행** — Phase 1+2+3+5 누적 효과 검증. 운영 환경에서 `class2_llm_quality` metric이 의미 있는 값을 가지는지 확인.
2. **(선택) rejection_reason 캡처** — clarification record에 `llm_rejection_reason` optional 필드 추가 + manager 변경 + metric 확장. 위 "주의사항" 참조.
3. **(선택) Package D vacuous-case (`notification_expected_count=0`) 표현 합의.**
4. **(deferred) Phase 6 — multi-turn refinement** — design doc §6.

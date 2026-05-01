# SESSION_HANDOFF — LLM Class 2 Integration P0 Safety Fixes (PR B)

**Date:** 2026-05-01
**Tests:** 440/440 mac_mini fast suite (was 435/435; +5 new), 137/137 rpi (unchanged)
**Schema validation:** 15/15 scenario skeletons pass; policy_table parses with new field

**Plan baseline:** `common/docs/architecture/10_llm_class2_integration_alignment_plan.md` (PR #90)

---

## 이번 세션의 범위

doc 10의 **P0 tier (운영 안전성 회귀 회복)** 3건을 한 PR에 일괄 처리. 사용자가 합의한 결정값(P0.1=옵션 b, P0.2=`global_constraints.llm_request_timeout_ms = 8000`, P0.3=delay 보수화)을 그대로 반영.

### P0.1 — LLM 호출이 MQTT 메시지 핸들러 스레드 차단 → 해소

**증상:** `Pipeline.handle_context()`가 paho-mqtt callback 스레드에서 실행되는데, CLASS_2 라우팅 시 `_handle_class2()`가 `start_session()`을 동기적으로 호출하고 그 안에서 `LocalLlmAdapter.generate_class2_candidates()` → `OllamaClient.complete()`(기본 60s 타임아웃) → 메시지 핸들러 스레드가 최대 60초 블록. 그동안 Class 0 응급 이벤트 포함 모든 다른 MQTT 메시지가 큐잉.

**수정 파일:** `mac_mini/code/class2_clarification_manager/manager.py`

- `__init__`이 `global_constraints.llm_request_timeout_ms`를 읽어 `self._llm_call_budget_s = timeout/1000 + 0.5`로 설정 (HTTP 종료 slack).
- 신규 `_call_llm_with_budget(pure_context_payload, unresolved_reason, audit_correlation_id)` 헬퍼:
  - daemon thread를 생성해 `generate_class2_candidates()` 호출
  - `worker.join(timeout=self._llm_call_budget_s)`
  - budget 초과 시 thread 포기 (daemon이라 프로세스 종료 시 reaped) + 정적 fallback 사용
  - 예외는 thread 내부에서 catch → 로그만 남기고 fallback
- `start_session()`이 직접 generator 호출 대신 `_call_llm_with_budget()` 사용.
- 결과: `start_session()`은 항상 `_llm_call_budget_s`(현재 8.5s) 안에 반환. 메시지 핸들러 스레드는 그 이상 블록되지 않음 → 응급 이벤트 지연 상한이 명확히 캡됨.

### P0.2 — `OllamaClient` 60s 타임아웃이 Class 2 30s 사용자 창보다 길었음 → 해소

**증상:** `OllamaClient(timeout_s=60)` 기본값이 `class2_clarification_timeout_ms=30000`(30s)보다 큼. LLM이 느리면 응답 그 자체가 사용자 창 전체를 잠식 가능.

**수정:**

| 파일 | 변경 |
|---|---|
| `common/policies/policy_table.json` | `global_constraints`에 `llm_request_timeout_ms = 8000` (기본값) + 자체 documenting `_llm_request_timeout_ms_description` 키 추가. P0.2 plan 참조. |
| `mac_mini/code/main.py` | Pipeline.__init__이 정책에서 `llm_request_timeout_ms`를 읽어 `OllamaClient(timeout_s=value/1000)`로 주입. Class 1 LLM 경로(`generate_candidate`)에도 동일하게 적용 — 기본 60s 글로벌 타임아웃이 Class 1 측에서도 같은 안전 invariant를 깨던 사전 존재 이슈도 같이 해소. |

### P0.3 — Runner auto-drive 지연 0.5s가 LLM 가변성을 고려 안 했음 → 보수화

**증상:** `_CLASS2_SELECTION_DRIVE_DELAY_S = 0.5`. P0.1 수정 전에는 LLM이 호출되는 동안 Mac mini가 응답 안 하면서 runner의 button이 너무 일찍 도착할 위험. P0.1+P0.2 적용 후에는 `start_session`이 ≤ 8.5s에 반환하고 `escalate_to_class2`가 즉시 초기 obs를 publish하므로 runner의 obs 감지는 정상이지만, CI/가상화 호스트의 약간 더 큰 thread startup latency를 위해 보수화.

**수정 파일:** `rpi/code/experiment_package/runner.py`

- `_CLASS2_SELECTION_DRIVE_DELAY_S` 0.5 → 1.0. comment에 P0.3 plan 참조 + 이론적 근거(thread startup margin) 명시.

---

## 새 테스트 (+5)

`mac_mini/code/tests/test_class2_clarification_manager.py::TestLlmCallBudget`:

1. `test_fast_llm_within_budget_uses_llm_candidates` — 0.05s LLM, budget 1s → LLM candidates 채택.
2. `test_slow_llm_exceeding_budget_falls_back` — 2s sleep LLM, budget 0.3s → 0.3s 안에 `start_session` 반환 + 정적 fallback. **P0.1의 핵심 회귀 방지**.
3. `test_llm_exception_falls_back_silently` — LLM raise → fallback.
4. `test_no_pure_context_skips_thread_entirely` — context 없으면 thread spawn 자체 안 함.
5. `test_budget_loaded_from_policy_table` — shipped 정책의 `llm_request_timeout_ms=8000`이 `_llm_call_budget_s=8.5`로 매핑됨.

mac_mini fast suite 435→440 (+5). rpi 137/137 unchanged. scenario 15/15 그대로.

---

## 안전 invariant 변동

**개선:**
- 메시지 핸들러 스레드 최대 블록 시간: 60s → 8.5s (Class 2 LLM 호출 한정). 응급 이벤트 응답 지연 상한 = 8.5s.
- LLM HTTP 호출 타임아웃: 60s → 8s (Class 1, Class 2 공통). LLM 자체가 hang되어도 8s 내 raise → 어댑터 fallback.

**미해결 (의도적 유지):**
- 응급 이벤트가 LLM 호출 중에 도착하면 0~8.5s 지연. 이는 옵션 (b) 선택의 명시적 tradeoff. doc 10 §6 (Open Decisions for the Maintainer)에서 합의됨.
- 진정한 무블록 처리는 옵션 (a) (정적 후보 먼저 announce, LLM은 백그라운드 upgrade)가 필요하나 invasive — 추후 별도 PR에서 검토 가능.

---

## 주의사항

- **canonical asset 변경 (1건):** `policy_table.json` `global_constraints`에 `llm_request_timeout_ms` 추가 (additive). `_llm_request_timeout_ms_description` 메타키도 함께. 어댑터의 fallback 키 stripping 로직(PR #88)이 이 메타키도 처리.
- **Class 1 경로 영향:** Class 1 `_handle_class1` → `LocalLlmAdapter.generate_candidate`도 같은 OllamaClient를 사용하므로, P0.2 변경으로 Class 1 LLM 호출도 60s → 8s로 단축. 사전 존재 이슈를 silent fix한 셈. mac_mini 기존 테스트 모두 통과(LocalLlmAdapter는 MockLlmClient 사용).
- **OllamaClient 자체 변경 없음:** `timeout_s` 인자는 PR #87 이전부터 존재. 단지 호출자(main.py)가 이제 정책 값을 명시적으로 전달.
- **Runner의 auto-drive 0.5→1.0 영향:** CLASS_2 trial 1개당 최대 0.5s 추가 시간. CI 영향 미미.

---

## 다음 세션 권장 작업

doc 10의 후속 tier (PR C / D / E / F):

1. **PR C — P1 문서 정합성 (mechanical, 코드 변경 없음)** — `00_architecture_index.md` 캐노니컬 스키마 목록, `01_system_architecture.md` Class 2 데이터 흐름, `03_payload_and_mqtt_contracts.md` RPi subscriber, `07_scenarios_and_evaluation.md` LLM 가변성, MQTT registry/matrix, asset_manifest, required_experiments.md §8.
2. **PR D — P2.1 expected fixture 가변성 허용** — `scenario_manifest_rules.md`에 LLM 모드 시 candidate_id 정확 일치 면제 규칙 + 영향 받는 expected fixture 코멘트.
3. **PR E — P2.2 trial timeout decomposition** — `_TRIAL_TIMEOUT_CLASS2_S`를 `_LLM_BUDGET_S + _USER_PHASE_TIMEOUT_S + _CAREGIVER_PHASE_TIMEOUT_S + slack`으로 분해.
4. **PR F (defer) — P2.3 class2_candidate_source_mode 비교 condition** — paper 평가 사이클 진입 시점에 결정.
5. **(선택, 추후 별도)** P0.1 옵션 (a) full-async 재구조화 — 응급 이벤트 0지연 보장이 필요할 때.

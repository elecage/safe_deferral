# SESSION_HANDOFF — LLM-Driven Class 2 Candidate Generation, Phases 1 + 2

**Date:** 2026-05-01
**Tests:** 456/456 mac_mini (was 435/435, +21 new), 128/128 rpi (unchanged)
**Schema validation:** new `class2_candidate_set_schema.json` well-formed; updated `clarification_interaction_schema.json` well-formed; all 15 scenario skeletons pass

**Design baseline:** `common/docs/architecture/09_llm_driven_class2_candidate_generation_plan.md` (PR #86)

---

## 이번 세션에서 수정한 내용

직전 PR #86에서 합의한 design doc의 **Phase 1 + Phase 2**를 한 PR에 함께 구현. Phase 1과 Phase 2는 API 경계에서 강하게 결합되어 있어 분리 머지의 이점이 적음.

### Phase 1 — `LocalLlmAdapter.generate_class2_candidates()`

**목표:** Class 2 clarification 매니저가 `start_session(candidate_choices=...)`에 그대로 넣을 수 있는 bounded 후보 세트를 LLM이 생성.

**신규/수정 파일:**

| 파일 | 변경 |
|---|---|
| `common/schemas/class2_candidate_set_schema.json` | 신설. LLM 후보 리스트 + provenance(`candidate_source`) + 적용된 bounded-variability 제약(echo) + LLM boundary const. |
| `mac_mini/code/local_llm_adapter/models.py` | `Class2CandidateResult` dataclass 추가. `is_usable` property로 manager가 빠르게 판별. |
| `mac_mini/code/local_llm_adapter/prompt_builder.py` | `build_class2_candidate_prompt()` 추가. context payload + unresolved_reason + low-risk catalog + 모든 bounded 제약을 prompt에 명시. |
| `mac_mini/code/local_llm_adapter/adapter.py` | `generate_class2_candidates()` 메서드 + `_normalize_class2_candidate()` + `_class2_fallback()` 헬퍼. `__init__`에서 `low_risk_actions.json`을 미리 로드해 catalog 검증 set 구성. |

**Bounded-variability 제약 (어댑터 모듈 상수, design doc §5와 일치):**

| 제약 | 값 |
|---|---|
| `max_prompt_length_chars` | 80 |
| `max_candidate_count` | 4 (manager의 `class2_max_candidate_options`와 정합, 더 작은 쪽 채택) |
| `prompt_must_be_question` | `True` (`?`/`？`로 끝나야 함) |
| `vocabulary_tier` | `plain_korean` |
| `forbidden_phrasings` | doorlock 관련 한·영 표현, "긴급 출동" 등 |

> **Phase 3 deferral:** 이 제약 블록은 design doc §5에서 `policy_table.json`의 새 `class2_conversational_prompt_constraints` 블록으로 옮겨갈 예정. 이번 PR은 어댑터 상수로 두어 Phase 1+2를 독립 머지. Phase 3은 후속 PR.

**LLM 출력 검증 흐름:**
1. Prompt 생성 후 LLM 호출 → JSON 추출 (실패 시 `default_fallback`)
2. `candidates` 배열이 비어있지 않은지 확인
3. 각 항목 `_normalize_class2_candidate()` 통과:
   - 필수 키 존재
   - `candidate_transition_target` enum 일치
   - **CLASS_0 후보는 무조건 `_FIXED_EMERGENCY_CANDIDATE` 템플릿으로 정규화** — LLM이 응급 발화를 임의 생성 못 함
   - prompt 길이 ≤ 80자
   - prompt가 물음표로 끝남
   - forbidden phrasings 없음
   - CLASS_1 후보의 `action_hint`는 `low_risk_actions.json` 내, `target_hint`는 해당 action의 `allowed_targets` 내
   - SAFE_DEFERRAL/CAREGIVER_CONFIRMATION 후보의 actuation hint는 강제 `None`
4. `unresolved_reason="caregiver_required_sensitive_path"`이면 caregiver 후보가 첫 번째여야 함 (없으면 fallback)
5. 정규화된 결과를 `class2_candidate_set_schema`로 한 번 더 검증
6. `Class2CandidateResult(candidate_source="llm_generated", ...)` 반환

**테스트 추가 (`test_local_llm_adapter.py::TestGenerateClass2Candidates`, 13개):**
- 정상 LLM 출력 채택
- 잘못된 JSON → fallback
- prompt 길이 초과 → 해당 후보 드롭
- 비-질문 prompt → 드롭
- catalog 외 action_hint → 드롭
- target_hint가 action의 허용 타겟 외 → 드롭
- forbidden phrasing(도어락) → 드롭
- LLM이 만든 임의 CLASS_0 후보 → 고정 템플릿으로 정규화 (강도/출동 운운 못 함)
- caregiver_required_sensitive_path에서 caregiver-first invariant
- caregiver 후보 없는 sensitive path → fallback
- max_candidates 제한 적용
- 빈 candidates 배열 → fallback (`no_candidates_array`)
- SAFE_DEFERRAL 후보의 action/target_hint 강제 null

### Phase 2 — `Class2ClarificationManager` LLM hook + Pipeline wiring + `candidate_source` audit

**목표:** 매니저가 LLM을 우선 호출하고, 실패 시 정적 `_DEFAULT_CANDIDATES`로 fallback. clarification record에 candidate_source 기록.

**수정 파일:**

| 파일 | 변경 |
|---|---|
| `mac_mini/code/class2_clarification_manager/manager.py` | `Class2CandidateGenerator` Protocol 정의(어댑터 직접 import 없이 duck-typing). `__init__(llm_candidate_generator=None)` 옵셔널 인자 추가. `start_session(pure_context_payload=...)` 옵셔널 인자 추가. LLM 우선 호출 + try/except로 안전 fallback. 세션에 `candidate_source` 동적 attribute 부여. `_build_record()`가 record에 `candidate_source` 키 포함. |
| `mac_mini/code/main.py` | `Pipeline.__init__`에서 `Class2ClarificationManager(llm_candidate_generator=self._llm)`로 LLM 어댑터 주입. `_handle_class2()`에서 `start_session(pure_context_payload=route_result.pure_context_payload)` 전달. `_escalate_c205()`는 변경 없음 (timeout-driven, pure_context 없음 → 정적 fallback). |
| `common/schemas/clarification_interaction_schema.json` | `candidate_source` enum 필드 추가 (`llm_generated`/`default_fallback`, optional, additionalProperties: false 그대로). |

**Provenance 우선순위:**
1. 명시적 `candidate_choices` 인자(테스트/오버라이드)
2. LLM 생성 (어댑터 등록 + `pure_context_payload` 제공 시)
3. 정적 `_DEFAULT_CANDIDATES` (모든 실패 경로)

**테스트 추가 (`test_class2_clarification_manager.py::TestLlmCandidateGeneratorHook`, 8개):**
- LLM 후보가 등록되면 매니저가 그대로 사용
- LLM이 default_fallback 반환 → 정적 fallback
- LLM이 예외 발생 → 정적 fallback (안전 invariant)
- `pure_context_payload` 없는 legacy 호출 → LLM 호출 안 됨
- 명시적 `candidate_choices` override → LLM 호출 안 됨
- clarification record에 `candidate_source="llm_generated"` 기록 (LLM 경로)
- clarification record에 `candidate_source="default_fallback"` 기록 (LLM 미사용)
- 새 `candidate_source` 필드 포함 record가 `clarification_interaction_schema` 검증 통과

---

## 추가/변경된 파일 요약

| 파일 | 종류 |
|---|---|
| `common/schemas/class2_candidate_set_schema.json` | 신설 (canonical schema 추가, additive) |
| `common/schemas/clarification_interaction_schema.json` | optional 필드 추가 (additive) |
| `mac_mini/code/local_llm_adapter/adapter.py` | API 추가 |
| `mac_mini/code/local_llm_adapter/models.py` | dataclass 추가 |
| `mac_mini/code/local_llm_adapter/prompt_builder.py` | 함수 추가 |
| `mac_mini/code/class2_clarification_manager/manager.py` | constructor + start_session signature 확장 |
| `mac_mini/code/main.py` | wiring 2곳 |
| `mac_mini/code/tests/test_local_llm_adapter.py` | +13 |
| `mac_mini/code/tests/test_class2_clarification_manager.py` | +8 |

mac_mini 435 → 456 (+21), rpi 128 그대로. 모두 통과.

---

## 안전 invariant (재확인)

본 PR이 깨지 않는 canonical boundaries:
- LLM은 후보 제안만 가능. 실행은 여전히 `DeterministicValidator`가 `low_risk_actions.json`으로 게이트.
- LLM이 catalog 외 action을 제안해도 `_normalize_class2_candidate()`에서 즉시 드롭 → 매니저는 그 후보를 보지 못함.
- LLM이 응급 후보 텍스트를 임의 생성해도 `_FIXED_EMERGENCY_CANDIDATE`로 정규화 → 응급 발화 진위는 LLM이 좌우하지 못함.
- LLM이 caregiver-required path에서 caregiver를 빠뜨리면 `caregiver_first_violation`으로 fallback.
- LLM이 죽거나 Ollama가 없으면 silent fallback → 매니저는 항상 작동.
- catalog 자체는 사람이 governance로 확장 (변동 없음).

---

## 주의사항

- **canonical schema 추가 (1건):** `class2_candidate_set_schema.json` 신설. 기존 어떤 자산도 영향 받지 않음 (additive).
- **canonical schema 확장 (1건):** `clarification_interaction_schema.json`에 optional `candidate_source` 추가. backward compatible — 기존 record가 이 필드 없어도 검증 통과.
- **`_DEFAULT_CANDIDATES`는 그대로 유지:** design doc Out of Scope §7대로 정적 테이블은 fallback과 audit 가독성을 위해 보존.
- **Phase 3 (policy 이전)은 별도 PR:** bounded-variability 상수가 어댑터 모듈에 있으므로, 운영 정책 조정이 필요해지면 Phase 3 PR에서 `policy_table.json`으로 옮길 것.
- **Phase 4 (TTS auto-pickup)는 자동:** `tts/speaker.py::announce_class2()`가 이미 `candidate.prompt`를 읽으므로, LLM이 contextual prompt를 생성하면 그대로 발화됨. 별도 코드 변경 없음.
- **Phase 5 (Package A 평가 metric)와 Phase 6 (multi-turn)은 deferred:** design doc §6 기준.
- **테스트 환경 Ollama:** 일부 기존 Pipeline 테스트는 Ollama 클라이언트가 실제로 localhost:11434를 시도하므로 환경에 따라 30~80초 소요. 이는 본 PR과 무관한 사전 이슈 (정확히 같은 동작이 PR #79부터 있었음).

---

## 다음 세션 권장 작업

1. **Phase 3 — `policy_table.json`에 `class2_conversational_prompt_constraints` 블록 추가**, 어댑터의 `_CLASS2_PROMPT_CONSTRAINTS`를 정책 로드값으로 대체. 운영 환경에서 제약값을 코드 변경 없이 조정 가능.
2. **하드웨어 준비 후 E2E 재실행** — LLM 우선 경로가 실 trial에서 정상 동작하는지 확인. mock에서 검증한 fallback 경로 + LLM 경로가 실 Ollama 응답으로 닫히는지.
3. **Phase 5 — Package A 평가 metric 추가:** `llm_candidate_admissibility_rate`, `llm_candidate_relevance_rate`, `prompt_length_violation_rate`. Trial 결과에서 `clarification_record.candidate_source`로 LLM/fallback 분리 측정 가능.
4. **(선택) `04_class2_clarification.md` §4 (LLM Role In Class 2) 보강** — 본 PR의 bounded-variability 제약과 candidate_source provenance를 canonical 문서에 명시.
5. **(deferred) Phase 6 multi-turn refinement** — design doc §6 Phase 6 참조.

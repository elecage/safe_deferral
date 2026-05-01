# SESSION_HANDOFF — LLM-Driven Class 2 Candidate Generation, Phase 3 (Policy-Loaded Constraints)

**Date:** 2026-05-01
**Tests:** 435/435 mac_mini fast suite (+4 new), 128/128 rpi (unchanged)
**Schema validation:** all 15 scenario skeletons pass; updated policy_table loads cleanly

**Design baseline:** `common/docs/architecture/09_llm_driven_class2_candidate_generation_plan.md` (PR #86)
**Builds on:** PR #87 (Phase 1 + Phase 2)

---

## 이번 세션에서 수정한 내용

Phase 1+2(PR #87)에서 어댑터 모듈 상수로 임시 보관했던 bounded-variability 제약을 canonical 정책 자산으로 이전. 운영자가 코드 변경 없이 prompt 길이·금지 표현·질문 강제 등을 조정 가능.

### Phase 3 변경 요약

| 자산 | 변경 |
|---|---|
| `common/policies/policy_table.json` | `global_constraints` 안에 `class2_conversational_prompt_constraints` 블록 신설 (`max_prompt_length_chars`, `prompt_must_be_question`, `must_include_target_action_in_prompt`, `vocabulary_tier`, `forbidden_phrasings`). `_description` 키로 이 블록의 의도와 안전 invariant를 함께 명시. |
| `mac_mini/code/local_llm_adapter/adapter.py` | `__init__`이 정책에서 블록을 로드하고 `_CLASS2_PROMPT_CONSTRAINTS_FALLBACK`과 머지. `max_candidate_count`는 별도 sibling field `class2_max_candidate_options`로부터 default 채움 (single source of truth). 모듈 상수는 `_FALLBACK` 접미사를 붙여 fallback 의도를 명확히 함. |
| `generate_class2_candidates()` | `self._class2_prompt_constraints`(정책 로드값)을 매 호출 snapshot, manager의 `max_candidates` 인자와 더 작은 값 채택. |
| `common/docs/architecture/04_class2_clarification.md` §4 | 새 §4.1 (Bounded-Variability Constraints), §4.2 (Catalog gating), §4.3 (Provenance audit `candidate_source`) 추가. canonical 문서가 LLM 경계를 명시. |

### 정책 로드 / fallback 우선순위
1. `policy_table.json::global_constraints.class2_conversational_prompt_constraints` 블록 (정상 경로)
2. 블록 누락 시 `_CLASS2_PROMPT_CONSTRAINTS_FALLBACK` 모듈 상수 (구버전 정책 호환)
3. `max_candidate_count`는 `class2_max_candidate_options`에서 가져옴 — 매니저와 어댑터가 같은 값 공유

### `_description` 처리
정책 블록에 self-documenting `_description` 키가 들어 있으나, 어댑터는 `_`로 시작하는 키를 모두 stripping해서 메타-키가 검증 로직에 새지 않게 함.

---

## 추가/변경된 테스트

`test_local_llm_adapter.py::TestClass2PromptConstraintsFromPolicy` (4개):
1. `test_constraints_loaded_from_policy_table` — 어댑터가 shipped policy의 값을 그대로 노출 (도어락 한·영 토큰 포함, `_description` stripping 확인).
2. `test_constraints_echoed_in_result_metadata` — `Class2CandidateResult.prompt_constraints_applied`에 정책 값이 그대로 echo됨.
3. `test_falls_back_when_policy_block_absent` — stub AssetLoader로 블록 없는 정책을 주입했을 때 모듈 fallback 사용.
4. `test_policy_constraints_actually_gate_validation` — 정책에서 `max_prompt_length_chars=5`로 좁히면 정상 후보가 즉시 거부되어 fallback으로 빠짐 (제약이 실제로 라이브임을 검증).

mac_mini fast suite 431→435 (+4). rpi 128 unchanged.

---

## 안전 invariant (변동 없음)

Phase 3은 데이터 이전(코드→정책)일 뿐 동작 변경 없음. PR #87에서 확립한 모든 invariant 그대로:
- LLM 후보 제안만, 실행은 validator가 catalog로 게이트
- catalog 외 action_hint/target_hint 즉시 드롭
- CLASS_0 후보 고정 템플릿 정규화
- caregiver-required path는 caregiver-first
- LLM 실패 → silent fallback
- catalog 인간 governance

---

## 주의사항

- **canonical asset 변경 (1건):** `policy_table.json` `global_constraints`에 새 블록 추가. 기존 필드는 그대로. additionalProperties 강제하는 schema는 없음 (정책 테이블 자체는 schema-controlled가 아님).
- **`04_class2_clarification.md`는 canonical doc:** §4 보강은 의미 변경이 아니라 PR #87+#88의 동작을 명문화.
- **Phase 3 이후 어댑터 동작 변경 없음:** shipped 정책 값과 모듈 fallback 값이 동일하므로 운영 환경에서 관찰 가능한 차이 없음. 운영자가 정책을 조정하기 시작할 때부터 의미가 살아남.

---

## 다음 세션 권장 작업 (design doc Phase 5+6, 미해결 이전 권장)

1. **하드웨어 준비 후 E2E 재실행** — Phase 1+2+3 누적 효과 검증.
2. **Phase 5 — Package A LLM-quality metrics 추가** — `clarification_record.candidate_source` 필드를 trial 결과에서 집계하여 `llm_candidate_admissibility_rate`, `llm_candidate_relevance_rate`, `prompt_length_violation_rate` 산출.
3. **(선택) Package D vacuous-case (`notification_expected_count=0`) 표현 합의.**
4. **(deferred) Phase 6 — multi-turn refinement** — design doc §6.

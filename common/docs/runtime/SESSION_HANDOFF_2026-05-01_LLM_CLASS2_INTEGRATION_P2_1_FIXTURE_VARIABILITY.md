# SESSION_HANDOFF — LLM Class 2 Integration P2.1 Fixture Variability Allowance (PR D)

**Date:** 2026-05-01
**Tests:** 440/440 mac_mini fast suite (unchanged), 137/137 rpi (unchanged) — docs/fixture-only PR
**Schema validation:** 15/15 scenario skeletons; all 5 expected_class2_* fixtures parse cleanly

**Plan baseline:** `common/docs/architecture/10_llm_class2_integration_alignment_plan.md` P2.1 (PR #90)
**Builds on:** PR #87/#88/#89/#91 (Phases 1+2+3+5+P0), PR #92 (P1)

---

## 이번 세션의 범위

doc 10의 **P2.1 (expected fixture LLM-variability allowance)** 처리. 코드 변경 없음. PR #87+#88+#89/#91이 도입한 LLM 모드에서 `candidate_id` / `prompt`가 가변이라는 사실을 시나리오 매니페스트 규칙과 expected fixture 양쪽에 반영.

### scenario_manifest_rules.md §7.5 신설 — LLM Mode Variability Allowance

§7.4 `transition_outcomes` 다음에 §7.5 추가. 핵심 내용:

**Stable contract surfaces (LLM 모드에서도 literal 비교 안전):**
- `candidate_transition_target` — schema enum 강제
- `action_hint` — `low_risk_actions.json` 카탈로그 강제 (어댑터 사전 필터)
- `target_hint` — action별 `allowed_targets` 강제 (어댑터 사전 필터)
- caregiver-required-sensitive-path 경로의 첫 후보는 항상 `CAREGIVER_CONFIRMATION` (어댑터 강제)
- **CLASS_0 후보는 LLM 모드에서도 고정 템플릿** (`{candidate_id: "C3_EMERGENCY_HELP", prompt: "긴급상황인가요?"}`) — 어댑터 정규화

**Variable surfaces (LLM 모드에서 literal 비교 금지):**
- `candidate_id` — LLM이 임의 short identifier 생성 가능
- `prompt` — context-driven TTS 텍스트 (bounded-variability 제약 안에서만)

**Static-mode (default_fallback) literal 비교는 그대로 안전.**

§7.5는 또 verifier에게 실용 가이드 제공: "literal id 대신 stable surface(transition_target + action_hint + target_hint)로 candidate를 locate한 다음 actual id를 record에서 읽어 downstream selection/audit에 사용".

### Expected fixture 갱신 (5개)

기존 literal id 필드는 **유지** (static-mode에서 그대로 작동). 대신 **machine-readable LLM-mode 메타필드**와 **`notes` 라인 1개**를 추가하여 verifier가 모드별로 매칭 전략을 선택할 수 있게 함:

| 파일 | 추가된 메타필드 | 추가된 note 요약 |
|---|---|---|
| `expected_class2_transition_class1.json` | `expected_selected_candidate_id_is_static_mode_literal: true`, `expected_selected_candidate_transition_target: "CLASS_1"`, `expected_selected_candidate_action_hint: "light_on"`, `expected_selected_candidate_target_hint_in_allowed_targets_for_action: true` | LLM 모드에서는 id가 다를 수 있음; `transition_target=CLASS_1 ∧ action_hint='light_on' ∧ target_hint∈allowed_targets`로 매칭 |
| `expected_class2_transition_class0.json` | `expected_selected_candidate_id_is_llm_normalized_literal: true`, `expected_selected_candidate_transition_target: "CLASS_0"`, action/target_hint=null | CLASS_0 후보는 어댑터 정규화로 인해 literal이 LLM 모드에서도 유지됨 |
| `expected_class2_caregiver_confirmation_doorlock_sensitive.json` | `expected_first_candidate_id_is_static_mode_literal: true`, action/target_hint=null | LLM 모드에서는 first candidate id 가변; `transition_target=CAREGIVER_CONFIRMATION` 강제 (어댑터 caregiver-first invariant) |
| `expected_class2_candidate_prompt.json` | 각 후보에 `candidate_id_is_static_mode_literal` / `candidate_id_is_llm_normalized_literal` 표시 | static 후보 3개(C1/C2/C4)는 LLM 모드에서 id 가변, CLASS_0(C3)만 LLM 모드에서도 literal 유지 |
| `expected_class2_timeout_safe_deferral.json` | (메타필드 추가 없음 — 이미 transition_target만 단언함) | mode-agnostic임을 명시; audit candidate_choices array 검사 시 모드 인식 권장 |

---

## 검증

- mac_mini 440/440 (unchanged — fixture/docs only)
- rpi 137/137 (unchanged)
- scenario skeletons 15/15 schema 통과
- 5 expected_class2_* fixtures 모두 JSON 파싱 OK + 추가 필드 schema 친화적 (이들은 free-form fixture라 schema constraint 없음)

---

## 안전 invariant 변동

없음. fixture·문서만 정정. 어떤 코드/스키마/정책 의미도 변경하지 않음.

---

## 주의사항

- **canonical asset 변경 없음.** `scenario_manifest_rules.md`는 manifest schema가 아니라 가이드 문서. expected_class2_* 파일은 fixture (test asset)로 schema 강제 없음.
- **새 메타필드는 가이드성 (advisory):** 기존 verifier가 이 필드를 알지 못하면 그냥 무시함. 새 verifier(또는 PR D 이후 작성될 LLM-mode-aware verifier)는 이 필드를 활용 가능.
- **CLASS_0 정규화 의존:** 본 PR의 "CLASS_0 literal stable" 주장은 PR #87의 `_FIXED_EMERGENCY_CANDIDATE` 어댑터 정규화에 의존함. 미래에 어댑터가 CLASS_0 정규화를 완화하면 expected_class2_transition_class0.json의 메타필드도 함께 수정해야 함.
- **`expected_first_candidate_transition_target`** 캐스트: doorlock fixture에서 이 값은 `CAREGIVER_CONFIRMATION`. 런타임은 canonical alias `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION`로 정규화하므로, verifier는 양쪽 모두 허용해야 함 (`_expected_transition_targets()` 헬퍼가 이미 처리).

---

## 다음 세션 권장 작업 (doc 10 후속 tier)

1. **PR E — P2.2 trial timeout decomposition** — `_TRIAL_TIMEOUT_CLASS2_S`를 정책 기반 phase별 합산으로 변환.
2. **PR F (defer) — P2.3 `class2_candidate_source_mode` 비교 condition** — paper 평가 사이클 진입 시점에.
3. **하드웨어 준비 후 E2E 재실행** — PR #87/#88/#89/#91/#92 + 이번 PR의 통합 효과를 실 trial로 검증.
4. **(선택, future)** P0.1 옵션 (a) full-async 재구조화.
5. **(선택)** 새 LLM-mode-aware verifier 작성 — 현재 verifier 인프라가 정비되면 이번 PR의 메타필드를 활용해 mode별 매칭 전략 자동 선택.

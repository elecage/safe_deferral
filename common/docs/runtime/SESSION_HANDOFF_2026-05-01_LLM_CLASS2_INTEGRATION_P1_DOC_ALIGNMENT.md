# SESSION_HANDOFF — LLM Class 2 Integration P1 Documentation Alignment (PR C)

**Date:** 2026-05-01
**Tests:** 440/440 mac_mini fast suite (unchanged), 137/137 rpi (unchanged) — docs-only PR
**Schema validation:** 15/15 scenario skeletons; asset_manifest + topic_registry parse cleanly with new entries

**Plan baseline:** `common/docs/architecture/10_llm_class2_integration_alignment_plan.md` (PR #90)
**Builds on:** PR #87 (Phase 1+2), PR #88 (Phase 3), PR #89 (Phase 5), PR #91 (P0 safety)

---

## 이번 세션의 범위

doc 10의 **P1 tier (문서 정합성)** 일괄 처리. 코드 변경 없음. PR #87/#88/#89/#91이 도입한 LLM-driven Class 2 candidate generation의 시스템적 영향이 active 아키텍처/MQTT/asset_manifest/required_experiments 문서에 누락되어 있던 부분을 모두 반영.

### P1.1 — Active architecture docs 갱신

| 파일 | 변경 |
|---|---|
| `00_architecture_index.md` §3 | `class2_candidate_set_schema.json`을 Current schema assets 목록에 추가. |
| `01_system_architecture.md` §7 | Class 2 데이터 흐름에 LLM upstream + 8s budget + silent fallback + `candidate_source` 명시. design plan 09/10 cross-reference. |
| `03_payload_and_mqtt_contracts.md` §7 | RPi가 evaluation 목적으로 `clarification/interaction` + `escalation/class2`를 구독함을 명시 (ClarificationStore, NotificationStore). 이 구독은 비-authoritative. `class2_candidate_set_schema.json`은 **MQTT 토픽에 절대 등장하지 않는** 어댑터-내부 페이로드임을 분리 명시. |
| `04_class2_clarification.md` §4.1 | `class2_candidate_set_schema.json` cross-reference + `llm_request_timeout_ms` 정책 + budget 계산 공식 명시. PR #91 P0.1/P0.2 참조. |
| `07_scenarios_and_evaluation.md` §9.1 | LLM 가변성 섹션 신설. LLM 모드(`candidate_source=llm_generated`)에서는 `candidate_id`/`prompt`가 변동하지만 `candidate_transition_target`/`action_hint`/`target_hint`는 어댑터가 강제하는 안정 contract surface임을 명시. expected fixture 매칭 가이드. |

### P1.2 — MQTT registry / matrix 갱신

| 파일 | 변경 |
|---|---|
| `common/mqtt/topic_registry.json` | `safe_deferral/clarification/interaction` subscribers에 `rpi.clarification_store_evaluation_capture` 추가, `safe_deferral/escalation/class2` subscribers에 `rpi.notification_store_evaluation_capture` 추가. observer_subscriber role도 동일. |
| `common/mqtt/publisher_subscriber_matrix.md` | 두 토픽 행에 RPi capture subscriber 추가 + RPi-side capture는 비-authoritative evaluation 전용임을 가독성 있게 명시. |
| `common/mqtt/topic_payload_contracts.md` | 신규 §7.5 (Adapter-internal schemas) 추가. `class2_candidate_set_schema.json`이 어떤 publisher/subscriber/topic도 갖지 않는 in-process payload임을 governance/verification 도구가 오해하지 않도록 분리 문서화. |

### P1.3 — Asset manifest와 required experiments

| 파일 | 변경 |
|---|---|
| `common/asset_manifest.json` | `current.schemas`에 `class2_candidate_set_schema` 등록. |
| `common/docs/required_experiments.md` §8.6 | Package D `class2_llm_quality` 서브블록 4종 metric 표 + 설명. 원안 metric 3종(`llm_candidate_admissibility_rate`, `prompt_length_violation_rate`, `llm_candidate_relevance_rate`)이 Phase 1+2의 사전 게이팅으로 항상 100%/0%가 되는 구조적 문제로 폐기되었음을 명기. PR #89 핸드오프 cross-reference. |

---

## 검증

- mac_mini fast suite 440/440 (unchanged — docs-only)
- rpi 137/137 (unchanged)
- scenario skeletons 15/15 schema 통과
- `asset_manifest.json` 파싱 OK + 새 엔트리 확인
- `topic_registry.json` 파싱 OK + 두 RPi capture subscriber 등록 확인

---

## 안전 invariant 변동

없음. 본 PR은 active 문서를 PR #87/#88/#89/#91 이후 실제 동작과 정합시키는 목적. 어떤 코드/스키마/정책 의미도 변경하지 않음. 새로 명시화한 사실:

- LLM이 Class 2 candidate generation을 도울 수 있다 (이미 코드 동작)
- Budget이 정책에서 온다 (이미 코드 동작)
- 실패 시 silent static fallback (이미 코드 동작)
- RPi가 두 토픽을 evaluation 목적으로 구독한다 (이미 코드 동작)
- `class2_candidate_set_schema`는 어댑터-내부 schema이지 wire contract가 아니다 (이미 코드 동작)

---

## 주의사항

- **canonical asset 변경 (3건, 전부 additive):**
  - `common/asset_manifest.json` — schemas 사전에 한 항 추가
  - `common/mqtt/topic_registry.json` — 두 토픽의 subscribers/subscriber_roles에 한 항씩 추가
  - `common/asset_manifest.json` (위와 동일)
  → 기존 어떤 fixture/스크립트/검증 흐름도 깨지지 않음 (additive only)
- **`07_scenarios_and_evaluation.md` §9.1의 fixture 가이드는 도움말이지 검증 도구의 강제 규칙이 아님.** 실제 expected fixture 매칭 완화는 PR D (P2.1)에서 `scenario_manifest_rules.md`에 codify될 예정.
- **`required_experiments.md` §8.5는 그대로 유지** (notification payload schema 검증은 그대로 Package D 핵심). §8.6은 *추가* 측정 항목.

---

## 다음 세션 권장 작업 (doc 10 후속 tier)

1. **PR D — P2.1 expected fixture LLM-variability allowance** — `scenario_manifest_rules.md`에 LLM 모드 시 candidate_id/prompt 정확 일치 면제 규칙 추가 + 영향 받는 expected fixture 코멘트.
2. **PR E — P2.2 trial timeout decomposition** — `_TRIAL_TIMEOUT_CLASS2_S`를 정책 기반 phase별 합산으로 변환.
3. **PR F (defer) — P2.3 `class2_candidate_source_mode` 비교 condition** — paper 평가 사이클 진입 시.
4. **(선택, future)** P0.1 옵션 (a) full-async 재구조화 — 응급 0지연 보장이 필요할 때.
5. **하드웨어 준비 후 E2E 재실행** — PR #87/#88/#89/#91/이번 PR의 통합 효과를 실 trial로 검증.

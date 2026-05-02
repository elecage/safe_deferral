# SESSION_HANDOFF — P0.1 Docs 01–04 Backfill for doc 12 features

**Date:** 2026-05-02
**Tests:** unchanged (docs-only PR; no code, schema, or scenario modified). mac_mini 589/589, rpi 168/168.
**Schema validation:** none modified.

**Plan baseline:** PR #1 of the post-doc-12 consistency backfill plan (`PLAN_2026-05-02_POST_DOC12_CONSISTENCY_BACKFILL.md`). Updates the four active read-order architecture docs to describe the doc 12 capabilities that landed in PRs #104–#111.

---

## 이번 세션의 범위

활성 read-order docs (00–04)가 doc 12 land 이전의 Class 2 모델만 다루고 있었음. Audit (PR #112)에서 8 영역의 drift 발견 — 본 PR은 그 중 docs 01–04를 closed.

각 doc은 doc 10/11/12를 cross-link만 하고 자체 핵심 내용을 인라인으로 추가 (read-order 따라가는 사람이 doc 10–12까지 안 가도 핵심을 알 수 있게).

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/docs/architecture/01_system_architecture.md` | §4 Mac mini 책임 list에 "scanning interaction mode + one-turn refinement" 추가, doc 04 §4.4–§4.6 cross-link. §5 RPi 책임 list에 "Package A의 4-dimensional comparison" 추가, doc 04 §4.7 cross-link. |
| `common/docs/architecture/02_safety_and_authority_boundaries.md` | 신규 §10 "Class 2 Modes Preserve Boundaries" — 5개 invariant 명시 (same candidate set + Validator gating, same low-risk catalog, silence ≠ consent, authority surface unchanged, Telegram caregiver path unchanged). 4개 routing-metadata comparison 필드가 LLM prompt / Class 0 / validator 모두에 영향 없음 명시. §10 → §11 source notes 번호 이동. |
| `common/docs/architecture/03_payload_and_mqtt_contracts.md` | §7 clarification 계약 섹션 확장: 5개 옵션 clarification_interaction 필드 표 (`candidate_source`/`input_mode`/`scan_history`/`scan_ordering_applied`/`refinement_history`). 신규 §7.1 "Routing-metadata fields for paper-eval" — 4개 routing_metadata 필드 표 with values + honored-by + plan refs. 4-dimensional comparison space 언급. |
| `common/docs/architecture/04_class2_clarification.md` | §4.3 candidate_source enum에 `static_only_forced` 추가. 신규 §4.4 Interaction Model (direct_select / scanning, AAC scanning 패턴, single_click/double_click/triple_hit/silence 매핑). 신규 §4.5 Multi-turn Refinement (opt-in flag, refinement_templates, state-aware refinement, bounded one-turn). 신규 §4.6 Deterministic Scanning Ordering (`source_order` vs `deterministic`, by_trigger_id buckets, context_overrides, scan_ordering_applied audit). 신규 §4.7 Paper-Eval Comparison Composition (4 orthogonal dimensions 표). §5 payload list에 5개 옵션 필드 (`candidate_source`/`input_mode`/`scan_history`/`scan_ordering_applied`/`refinement_history`) + backward-compat 명시. |

### 디자인 원칙

- **Cross-link, don't duplicate**: 각 doc은 doc 10/11/12에 대한 핵심 요약 + cross-link만. design rationale은 원본 doc에 그대로.
- **Backward compat 강조**: 모든 새 옵션 필드 / mode / 정책 default가 production 동작 변경 0임을 반복 명시.
- **4 dimension table**: 04 §4.7 + 03 §7.1에 동일 정보의 두 표 (clarification 측 vs routing-metadata 측). 두 doc 사이 cross-reference 명확.

### Boundary 관련 추가 (doc 02 §10)

5개 invariant를 명시적으로 doc화:
1. Same candidate set + Validator gating (모든 mode)
2. Same low-risk catalog (refinement, ordering 모두 catalog 안에 머무름)
3. Silence ≠ consent (모든 timeout path가 caregiver escalation)
4. Authority surface unchanged (audit 필드 추가는 새 권한 surface 아님)
5. Telegram caregiver path unchanged (`_run_caregiver_phase` shared)

### Test plan

```bash
cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 589 passed (unchanged)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 168 passed (unchanged)
```

본 PR은 docs only — 자동 테스트 변경 없음. doc 안정성은 cross-reference 정확성 (참조하는 §, 필드명, 값 enum, plan reference 모두 실제와 일치)에 의존. 수동 검증:
- 모든 §X.Y 참조가 실제로 존재 — 04 §4.4–§4.7, 03 §7.1, 02 §10 모두 신규 추가됨, cross-ref 일치.
- 모든 plan ref (PR #79/#101/#104/#107/#108/#109/#110/#111, doc 10/11/12) 실제 존재.
- 모든 enum 값 실제 schema와 일치 (`direct_select`/`scanning`, `source_order`/`deterministic`, `static_only`/`llm_assisted`, `static_only_forced`).

### Files touched

```
common/docs/architecture/01_system_architecture.md
common/docs/architecture/02_safety_and_authority_boundaries.md
common/docs/architecture/03_payload_and_mqtt_contracts.md
common/docs/architecture/04_class2_clarification.md
common/docs/runtime/SESSION_HANDOFF_2026-05-02_P0_1_DOCS_01_04_BACKFILL.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계 (PLAN doc §3 sequencing)

- **P0.2 (next)**: `common/mqtt/topic_payload_contracts.md` 갱신 + 3개 예제 payloads (`common/payloads/examples/`).
- 이후 P1 시나리오 PRs (3, 4, 5), P2 운영 tooling (6, 7), P3 정리 (8).

### Notes

- 본 PR은 8 PR backfill의 첫 번째. 후속 PR들이 doc 04 §4.4–§4.7을 reference로 사용 — schema/scenario/manifest 작업의 단일 source of truth로 작동.
- doc 04는 §4 sub-section이 6개로 늘어났음 (4.1–4.7). 향후 또 늘어나면 §4를 별도 doc으로 분리 고려 — 현재는 가독성 유지.
- 8 PR 모두 land 후 PLAN doc을 archive로 이동.

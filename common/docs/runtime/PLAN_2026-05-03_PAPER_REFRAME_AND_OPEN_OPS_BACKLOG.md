# PLAN — Paper-framing refinement + open operations backlog

**Date:** 2026-05-03
**Trigger:** User insight after Phase C results — LLM이 속도 이점이 아니라 "perception 확장성"이 핵심 정당성. 현 paper docs는 "bounded intent interpretation"까지만 framing되어 있고 확장성 측면은 명시되지 않음. Phase C 데이터(direct/rule_only는 1ms / LLM은 1.6s)가 기존 "속도" framing을 직접적으로 부정함.

**Why now:** 운영 backlog가 여러 갈래로 갈라져 있어 (Item 2 fix / multi-turn recovery / temp sweep / extensibility) 한 번 정리하지 않으면 우선순위가 뒤섞임. 사용자 요청대로 plan을 먼저 박고 진행.

---

## 1. Scope (이 plan이 커버하는 범위)

**즉시 수행 (이 plan과 함께 ship):**
- Step 1 — paper docs refinement (01_paper_contributions.md + required_experiments.md)

**Plan으로 등록만 (사용자 결정/타이밍 대기):**
- Step 2 — extensibility 실험 design (시나리오 + 매트릭스 + 코드)
- Step 3 — extensibility sweep 운영
- 나머지 backlog (multi-turn recovery / temp sweep / Item 2 / #1 retry)

**Out of scope:**
- 새 contribution 추가 (4 contributions 그대로 유지, 표현만 refine)
- canonical schema/policy 변경 — 단, Step 2가 schema enum 1-2 값 추가 필요할 수 있음 (그때 별 PR)

## 2. 핵심 framing 변화 (paper-level)

**Before (현 paper doc):**
- LLM = "bounded intent interpretation under sparse/ambiguous signals"
- 속도/지연에 대한 명시적 입장 없음
- 확장성/유지보수 측면 빈 지점

**After (refined):**
- LLM = "perception layer scalability under novel inputs" — 시간 단축 도구가 아님
- 명시적 인정: "LLM은 deterministic 모드보다 latency 1000배 느림 (Phase C: 1ms vs 1.6s p50, 4.8s p95)"
- 명시적 주장: "그러나 deterministic 모드는 enumerable한 input space에서만 동작; 새 노드/제스처/디바이스/context 차원이 추가될 때마다 코드 수정 필요. LLM은 자연어 인지로 generalize"
- **두 layer 분리의 진짜 의미**: perception은 generalize(LLM), authority는 enumerate(validator/policy)
- Phase C 데이터를 supporting evidence로 인용

이는 contribution 1과 2를 강화 — 새 contribution 추가가 아님.

## 3. Step 1 — Paper docs refinement (이번 PR)

### 3.1 `common/docs/paper/01_paper_contributions.md`

추가할 섹션 / 보강:
- **§2 (Core Research Position)**: 마지막 줄 보강 — "Sensitive physical actuation must not be delegated to the LLM ..." 뒤에 "while LLM-based perception is precisely the layer that scales as new input contexts and device classes are introduced." 한 문장 추가
- **§4 Contribution 1 보강**: "purely rule-based direct mapping would be too brittle or too limited"의 *왜*를 구체화 — operator-side scalability cost
- **§4 Contribution 2 보강**: "authority separation"의 진짜 의미 = "perception은 generalize, authority는 enumerate" 추가
- **§7 (NOT Overclaim)에 새 항목**: "We do NOT claim the LLM is faster than rule-based intent recovery. Phase C measurements show the opposite (1ms vs 1.6s p50, ~1000× slower). The LLM's role is perception extensibility, not latency reduction."
- **§9 (Experiments support)**: extensibility 실험을 supporting evidence 항목에 추가
- **§10 thesis-level**: 한 문장에 "perception scalability" 표현 포함

### 3.2 `common/docs/required_experiments.md`

추가:
- 새 절: **§5.8 Contribution 1 보강용: Extensibility Under Novel Input Configurations** — Phase C가 "rule이 cover하는 동일 input 영역"에서만 비교했음을 명시. Novel-input matrix 실험을 paper-evidence로 권장.
- 실험 design 명세: novel event_code / novel context combination / novel device-target inference 3 axis × {direct_mapping, rule_only, llm_assisted}
- 측정 지표: pass_rate per mode under novel input (deterministic 모드는 0~low, LLM은 high 예상)
- 운영 절차: schema enum 추가 → fixture 작성 → matrix 작성 → sweep
- §2.2 (Extended Experimental Scope)에 한 줄 추가

## 4. Step 2 — Extensibility 실험 (별 PR, 사용자 GO 후)

### Deliverables
| 파일 | 변경 |
|---|---|
| `common/schemas/context_schema.json` | button event_code enum에 1-2 값 추가 (e.g. `triple_click`, `long_long_press`) |
| `integration/tests/data/sample_*_novel_*.json` | 3-4 fixtures (novel event_code / novel context / novel device hint) |
| `integration/scenarios/*_extensibility_*.json` | 3-4 scenarios with `comparison_conditions[]` tagged |
| `integration/paper_eval/matrix_extensibility.json` | new matrix: 3 novel × 3 modes = 9 cells × 30 trials = 270 trials |

**예상 시간:** 코드/시나리오 ~1.5h + sweep 운영 ~30-60min.

### 성공 기준
- direct_mapping pass_rate < 30% on novel input
- rule_only pass_rate < 50%
- llm_assisted pass_rate > 80%
- 수치 자체보다 **차이 패턴**이 paper claim을 뒷받침

## 5. Step 3 — Extensibility sweep 운영 (Step 2 ship 후)

운영자(또는 자동) launcher → matrix_extensibility.json sweep → archive. paper digest 생성. ~1h 총.

## 6. 미루어진 backlog (별 plan들에서 트래킹)

다음 항목은 이 plan에 포함되지 **않으나** 잊지 않도록 명시:

| 항목 | 우선순위 | 비고 |
|---|---|---|
| **Multi-turn recovery sweep** | HIGH (paper integrity) | Phase C 2 cells가 invalid (Item 1 fix #143로 자동 skip 되지만 데이터 회수가 paper에 필요). 정책 임시 활성화 → 2 cells × 30 trials 재실행 ~30min. |
| **Item 2 fix** (cancel partial preservation) | MEDIUM (ops) | 운영 안정성. 코드 ~30min + tests + PR. |
| **Temp/top_p sweep** | LOW (보조 데이터) | 코드/스크립트는 #141 #142에서 ship됨. 16 combos × ~10min = ~2.7h. paper의 Contribution 1 보조 evidence (LLM stochasticity 정량화). |
| **#1 retry** (matrix_v1 timeout=240) | LOWEST | 9 incomplete trial 회수 — marginal. Phase C archive에 이미 351/360 있음. |
| **doc 13 update** | LOW (cosmetic) | extensibility 실험 ship 후 §9 Phase 표 업데이트. |

## 7. 디자인 원칙

- **Framing 우선, 코드 후순위**: 잘못된 framing 위에 데이터를 더 쌓으면 paper 작성 시 retrofit 비용 증가. 지금 framing을 박고 그 framing이 요구하는 evidence (extensibility)를 디자인하는 게 효율적.
- **기존 contributions 보존**: 4개 contribution 모두 유지. 표현만 refine. 새 contribution 추가는 paper scope creep.
- **Phase C 데이터 그대로 인용**: 이미 ship된 archive 활용 (재측정 불요). Multi-turn 두 셀만 별도 recovery.
- **No canonical asset 손상**: paper docs / required_experiments.md 변경, schema는 Step 2에서 enum append-only.

## 8. 안티-목표

- LLM의 speed 비교를 paper에 새 contribution으로 만들지 않음 (이미 부정적 결과)
- "LLM이 더 정확하다" 같은 무리한 주장 안 함 — pass_rate 데이터는 deterministic이 더 높음 (covered input 안에서). 차이는 input space coverage.
- 하드웨어 가용성 의존 작업 (실제 ESP32 노드와의 통합 테스트 등) 이 plan에 미포함.

## 9. 다음 단계

1. **이번 PR**: Step 1 ship (paper doc + required_experiments + 이 plan doc)
2. **이후 사용자 결정**: Step 2 진행 (반일) vs 다른 backlog 우선순위 처리

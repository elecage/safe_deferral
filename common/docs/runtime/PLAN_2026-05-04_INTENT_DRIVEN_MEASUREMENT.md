# PLAN — Intent-Driven Measurement (Scenario user_intent + intent_match_rate)

**Date:** 2026-05-04 (작업은 2026-05-03 후반에 시작, 자정 기준 새 날짜)
**Trigger:** User architectural feedback during PR #151 review:

> 기대값이 단순히 class 1, class 2여서는 안되고, 실제로 의도하는 바가 거실 등을 켜고 싶은 것인지, 침실 등을 켜고 싶은것인지 또는 끄고 싶은 것인지에 대한 최초 의도를 설정하고, 해당 의도대로 응답을 하는 시나리오가 나와야 되는 것이야.

PR #151의 outcome_match_rate는 "system이 actuation에 도달했나"를 측정하지만 "사용자가 의도한 actuation에 도달했나"는 묻지 못합니다. 같은 시나리오에서 사용자는 침실 등을 켜고 싶을 수 있는데 system이 거실 등을 끈다면, 현재 metric은 둘 다 match=✅로 표시 — 사실은 의도 빗나감.

이 PR은 그 gap을 닫는 **intent-driven measurement framework**를 도입합니다. Coverage 확장(scanning, multi-turn scripts, 다양한 cell)은 별 PR (#153)로 분리.

**Predecessor:** PR #151 (`9ed412f` Step 6 Class 2 clarification measurement) — `_user_response_script`, `outcome_match_rate`, observation_history 기반 trajectory 모두 적용 완료.

---

## 1. Problem statement

### 1.1 현재 측정의 한계

`01_paper_contributions.md §4 Contribution 1`은 "perception-side scalability"를 주장합니다. PR #151은 `outcome_match_rate`로 "system이 어떤 path든 actuation에 도달했나"를 측정 — 한 단계 진보. 그러나 paper-honest 분석에는 부족합니다:

| 시나리오 | 사용자 의도 | system 실행 | pass | match | **intent_match** |
|---|---|---|---|---|---|
| living=on, bedroom=off | bedroom_light on (켜고 싶음) | light_on bedroom | ✅ | ✅ | ✅ |
| 같음 | bedroom_light on | **light_off living** | ❌ | ✅ | **❌** |
| 같음 | bedroom_light on | safe_deferral | ❌ | ❌ | ❌ |

두 번째 row가 핵심: PR #151의 `outcome_match`는 두 actuation 모두 ✅로 처리. 사실은 system이 "사용자가 의도한 침실 등 켜기"가 아니라 "거실 등 끄기"를 했음 — semantic 불일치.

### 1.2 Paper-side 함의

§7.4의 second-half framing이 정량적이려면:

> The LLM is conservative under genuine ambiguity, **AND** the system's Class 2 dialogue recovers a measurable fraction of the **deferred intent** through user interaction.

**"deferred intent"**의 recovery는 system이 actuation에 도달했냐가 아니라 **사용자가 의도한 그 actuation에 도달했냐**. PR #151 framework는 첫 번째까지만 측정하고 두 번째는 측정 안 함.

### 1.3 가설 검증의 명확성

`matrix_extensibility.json` description은 가설을 명시:

> The user's actual intent — implied by occupancy + low ambient + bedroom_light=off + living_room_light already on — is light_on bedroom_light.

이 "actual intent"가 측정 framework에 인코딩되어야 합니다. 현재는 구두로만 명시되고 metric에 없음.

---

## 2. Scope

### 2.1 In scope (PR #152)

- **Scenario manifest extension**: `user_intent` 블록을 시나리오에 명시
  ```jsonc
  "user_intent": {
    "action": "light_on",         // light_on | light_off | safe_deferral | none
    "target_device": "bedroom_light",  // living_room_light | bedroom_light | none
    "rationale": "거실 등은 이미 켜져 있고 침실 등은 꺼져 있음 + occupancy + 저조도 → 침실 등 켜기 의도"
  }
  ```
- **Aggregator extension** (`paper_eval/aggregator.py`):
  - `_trial_intent_match(trial, scenario_intent)` per-trial helper
  - `_intent_match_rate(trials, scenario_intent)` per-cell aggregator
  - `CellResult.intent_match_rate: Optional[float]` field
  - `CellResult.intent_match_distribution: dict` (matched/unmatched/no_intent counts)
- **Digest extension** (`paper_eval/digest.py`):
  - New CSV column `intent_match_rate` (after `outcome_match_rate`)
  - Markdown table column "intent" (or "🎯") side-by-side with pass/match
- **Dashboard extension** (`rpi/code/dashboard/static/index.html`):
  - Per-cell breakdown table: new "intent" column
  - 결과분석 탭 per-trial table: new "Intent" column with ✅/❌
  - Hover titles distinguish strict pass / soft match / semantic intent
- **Paper doc § update** (`common/docs/paper/05_class2_clarification_measurement_methodology.md`):
  - 신규 §6 — Intent-driven measurement methodology
  - §2.1 (strict vs soft)에 intent_match를 third level로 추가
  - §4 enable/not-enable 목록 업데이트
- **Tests**: scenario loader, aggregator, digest, runner pass-through

### 2.2 Out of scope (PR #153 follow-up)

- **Scanning script 구현** (`scan_until_yes`, `accept_intended_via_scan`, `scan_all_no`)
  - Mac mini의 scan_input_adapter는 button events(double_click=no, single_click=yes)를 수신
  - Runner simulator가 sequence를 timing 맞춰 publish해야 함
- **Multi-turn refinement script** (`multi_turn_refine_then_accept`)
  - `class2_multi_turn_enabled` 정책 flag opt-in 필요
- **Coverage matrix v4** — 다양한 user_intent + script 조합으로 모든 transition path exercise
- **Per-trial drill-down view** in 결과분석 — observation_history 시각화

### 2.3 Why this split

PR #152는 measurement contract를 정의: scenario가 intent를 declare하고, system이 의도 일치 여부를 측정. PR #153은 그 contract 위에서 다양한 coverage scenarios를 쌓음. 분리하면 framework review가 깔끔하고, coverage 확장은 별 작업으로 reviewable.

---

## 3. Detailed design

### 3.1 Scenario `user_intent` 필드

기존 시나리오 매니페스트에 optional `user_intent` 블록 추가:

```jsonc
{
  "scenario_id": "SCN_EXTENSIBILITY_A_NOVEL_EVENT_CODE_BEDROOM_NEEDED",
  "title": "...",
  "description": "...",
  "user_intent": {
    "action": "light_on",
    "target_device": "bedroom_light",
    "rationale": "거실 등은 이미 켜져 있고 침실 등은 꺼져 있음 + occupancy + 저조도 → 침실 등 켜기 의도"
  },
  ...
}
```

`user_intent` 부재 시 — legacy scenario — `intent_match_rate`는 None (측정 안 됨, 기존 동작 보존).

### 3.2 Aggregator helpers

```python
def _trial_intent_match(trial: dict, intent: Optional[dict]) -> Optional[bool]:
    """Returns True/False/None.
    - None: scenario has no user_intent declared (legacy)
    - True: trial's final action+target matches intent
    - False: doesn't match (different action OR different target OR no actuation)
    """
    if not intent:
        return None
    final_action, final_target = _trial_final_action_target(trial)
    return (
        final_action == intent.get("action")
        and final_target == intent.get("target_device")
    )

def _intent_match_rate(trials: list, intent: Optional[dict]) -> Optional[float]:
    """None when intent absent OR no trials. Otherwise fraction matching."""
    if not intent or not trials:
        return None
    matched = sum(1 for t in trials if _trial_intent_match(t, intent))
    return round(matched / len(trials), 4)
```

`_aggregate_cell` reads scenario's user_intent (via `_load_cell_scenario_intent` helper) and computes the rate per cell.

### 3.3 New CellResult fields

```python
@dataclass
class CellResult:
    ...
    intent_match_rate: Optional[float] = None
    # Distribution: count of trials matching / not_matching / no_intent_declared
    intent_match_distribution: dict = field(default_factory=dict)
```

### 3.4 Digest CSV/Markdown

CSV append `intent_match_rate` after `outcome_match_rate` (same append-only pattern as PR #150).

Markdown table:
```
| cell_id | condition | n | pass | match | intent | p50 | p95 | trajectory | final action | notes |
```

### 3.5 Dashboard

**Paper-Eval Sweep tab** (per-cell): add column "intent" rendering `intent_match_rate.toFixed(4)` or `—` when None. Hover title: "intent_match_rate: 사용자 의도와 일치한 비율 (scenario.user_intent 대비 final_action/target 정확 일치)".

**결과분석 tab** (per-trial): add column "Intent" with ✅/❌/— icon. Hover title same as above. Derivation client-side via JS helper `_trialIntentMatch(trial, scenarioIntent)` — scenario_intent fetched from `/scenarios/{filename}` API alongside trial data.

### 3.6 Paper doc §6 — Intent-driven measurement methodology

새 § (paper-grade):

> **§6. Intent-driven measurement**
>
> The strict pass / soft outcome match split (§2.1) tells you whether the system reached *some* design-intent action. It does not tell you whether that action matched what the user actually intended. For an assistive smart home, the latter is the load-bearing claim.
>
> Each scenario therefore declares a `user_intent` block — the action/target the user *would have* selected had they been able to express it directly. The matrix's response simulator (or, on hardware, the real user) responds to the Class 2 candidate set; the runner records the system's final action/target; the aggregator computes `intent_match_rate` as the fraction of trials whose final outcome equals the declared intent.
>
> The three-level metric stack:
> - `pass_rate` (routing fidelity): observed_route_class == expected_route_class
> - `outcome_match_rate` (actuation fidelity): system reached *some* action consistent with expected_validation
> - `intent_match_rate` (semantic fidelity): system reached *the user's intended* action
>
> A cell where `outcome_match_rate > intent_match_rate` is a system that actuates correctly *in aggregate* but routes the user to the wrong action — a perception failure that strict and soft metrics both hide.

### 3.7 Tests

- `test_paper_eval_aggregator.py::TestTrialIntentMatch` (helper logic)
- `test_paper_eval_aggregator.py::TestIntentMatchRate` (cell-level aggregation, None propagation)
- `test_paper_eval_aggregator.py::TestAggregateCellWithIntent` (CellResult round-trip)
- `test_paper_eval_digest.py::TestDigestIntentMatchColumn` (CSV/MD render)
- `test_paper_eval_sweep.py` — scenario loader test for user_intent field
- `test_rpi_components.py` — runner fetches scenario.user_intent at trial creation time, attaches to trial (so aggregator can find it)

---

## 4. Implementation phases

| Phase | Work | Why this order |
|---|---|---|
| 4.1 | Scenario `user_intent` field + scenario loader | Smallest contract; downstream depends |
| 4.2 | TrialResult.user_intent_snapshot + runner pass-through | Trial carries scenario intent for aggregator |
| 4.3 | Aggregator helpers + CellResult fields | Compute the metric |
| 4.4 | Digest CSV/MD column | Surface in paper-grade artifacts |
| 4.5 | Dashboard column (Paper-Eval Sweep + 결과분석 tabs) | Surface in interactive analysis |
| 4.6 | Paper doc §6 | Document the methodology |
| 4.7 | Tests at every layer | After each phase |
| 4.8 | Update v3 matrix scenario with user_intent | Validate the chain end-to-end |
| 4.9 | Verify via re-running v3 debug5 sweep | Confirm intent_match column populates |

---

## 5. Risk register

| Risk | Mitigation |
|---|---|
| Scenarios without user_intent must keep working | All new fields are Optional; metric falls back to None |
| user_intent semantics could be confused with expected_validation | Paper doc §6 explicitly contrasts the three levels; dashboard tooltips repeat it |
| aggregator needs scenario_id to fetch intent — couples aggregator to scenario files | Solution: runner snapshots user_intent onto TrialResult at creation; aggregator reads from trial, not from disk |
| Per-trial JS rendering needs scenario lookup | Dashboard fetches scenario alongside metrics; cache to avoid N round-trips |

---

## 6. Files to change

```
# Aggregator + digest
rpi/code/paper_eval/aggregator.py            # _trial_intent_match, _intent_match_rate, CellResult fields
rpi/code/paper_eval/digest.py                # CSV column, MD column

# Trial pass-through
rpi/code/experiment_package/trial_store.py   # TrialResult.user_intent_snapshot
rpi/code/experiment_package/runner.py        # snapshot scenario.user_intent at trial creation

# Dashboard
rpi/code/dashboard/static/index.html         # per-cell + per-trial intent column

# Tests
rpi/code/tests/test_paper_eval_aggregator.py
rpi/code/tests/test_paper_eval_digest.py
rpi/code/tests/test_rpi_components.py

# Scenario data (one example update)
integration/scenarios/extensibility_a_novel_event_code_bedroom_needed_scenario_skeleton.json

# Paper docs
common/docs/paper/05_class2_clarification_measurement_methodology.md  # §6 new

# Plan + handoff
common/docs/runtime/PLAN_2026-05-04_INTENT_DRIVEN_MEASUREMENT.md  # this file
common/docs/runtime/SESSION_HANDOFF_2026-05-04_INTENT_DRIVEN_MEASUREMENT.md  # handoff
common/docs/runtime/SESSION_HANDOFF.md       # index update
```

No canonical policy/MQTT/schema asset changes. `user_intent` lives on scenario manifests — those are experimental artifacts, not canonical assets.

---

## 7. Backlog after this PR

Carried forward + new:

| Item | Priority | Notes |
|---|---|---|
| **PR #153 — Scanning + multi-turn scripts + coverage matrix v4** | HIGH | Builds directly on this PR's intent framework |
| Trial isolation bug | HIGH | context_node re-publish intercepted as CLASS_2 single_click |
| Per-trial drill-down view in 결과분석 | MEDIUM | Show observation_history timeline per trial |
| Caregiver-phase response scripts | MEDIUM | Telegram simulator for caregiver inline-keyboard |
| Hardware paper-grade verification | scheduled | per `05_class2_clarification_measurement_methodology.md §3` |

---

## 8. Cross-reference

| Document | Reference |
|---|---|
| `01_paper_contributions.md §4 Contribution 1` | This metric backs the perception-scalability claim with semantic fidelity, not just actuation fidelity |
| `01_paper_contributions.md §7.4` | Paper second-half framing now has three levels of evidence |
| `05_class2_clarification_measurement_methodology.md §2` | This PR adds §6 to document the third level |
| PR #151 / `2441eac` | Predecessor — `_user_response_script` + `outcome_match_rate` |
| Future PR #153 | Coverage expansion — depends on this PR's intent contract |

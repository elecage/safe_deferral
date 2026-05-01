# SESSION_HANDOFF — Notification-Schema Gate, Validator Re-entry Sharpening, Compound Target Parsing, Late Notification Tolerance, Notification Readiness Rate

**Date:** 2026-05-01
**Tests:** 435/435 mac_mini, 125/125 rpi (was 429/429, 112/112; +6 mac_mini, +13 rpi)
**Schema validation:** 15/15 scenario skeletons + class2_notification_payload + clarification example payload all pass

---

## 이번 세션에서 수정한 내용

다섯 follow-up 이슈 모두 직전 PR #80에서 닫은 CLASS_2 transition 루프의 잔여 결함 또는 schema/spec 불일치이므로 한 PR에 묶었다. 직전 권장작업과는 직접 겹치지 않는다.

### Issue 1: C208 / 비표준 trigger의 Class 2 notification이 schema 검증으로 publish 실패

**증상:**
- `class2_notification_payload_schema.json`의 `exception_trigger_id` enum이 C201–C207만 허용.
- `Class2ClarificationManager._build_notification`는 `C208`이나 `deferral_timeout` 같은 비-C201–C207 trigger에 대해 `exception_trigger_id: None`을 포함 → schema의 `type=string`에 걸려 `CaregiverEscalationBackend.send_notification()`가 ValidationError를 던지면서 publish 안 함.
- `mac_mini.main._build_notification`도 enum과 무관하게 None만 아니면 그대로 포함 → `EMERGENCY_BUTTON` 같은 임의 trigger도 schema fail.
- 결과: doorlock-sensitive caregiver notification 실험과 Package D가 실제로 닫히지 않음.

**수정:**

| 파일 | 변경 |
|---|---|
| `common/schemas/class2_notification_payload_schema.json` | `exception_trigger_id` enum에 `C208` 추가 (canonical Class 2 trigger 집합과 정합). |
| `mac_mini/code/class2_clarification_manager/manager.py` | `_CANONICAL_C2_TRIGGER_IDS` frozenset 도입. `_build_notification()`은 trigger가 enum 안일 때만 `exception_trigger_id` 키를 dict에 추가하고, 그 외에는 키를 완전히 omit. |
| `mac_mini/code/main.py` | `_CANONICAL_C2_TRIGGER_IDS` 도입 + `_build_notification()`이 enum 안일 때만 키 포함. None 또는 비표준 trigger는 키 자체가 없음. |

**테스트 추가:**

- `test_class2_clarification_manager.py::TestC208VisitorContext::test_c208_notification_passes_schema` — C208 timeout notification이 jsonschema 검증 통과 + `exception_trigger_id="C208"` 포함.
- `test_class2_clarification_manager.py::TestC208VisitorContext::test_non_canonical_trigger_omits_exception_trigger_id` — `deferral_timeout` 같은 비표준 trigger는 키가 dict에 없음.
- `test_pipeline_ack_escalation.py::TestBuildNotificationTriggerGating` (4개) — `_build_notification`의 canonical/non-canonical/None trigger gating + C208 schema 검증 통과.

### Issue 2: validator re-entry verdict가 rejected/no-ACK도 통과시킴

**증상:** `_is_pass()`가 `requires_validator_reentry_when_class1=True`일 때 `validation.validation_status` 존재 여부만 확인. 따라서 `rejected_escalation`도 pass, dispatcher가 안 돌아도 pass — bounded Class 1 실행 가능성 검증이 사실상 무력화.

**수정 파일:** `rpi/code/experiment_package/trial_store.py`

`_is_pass()` CLASS_2 + `observed_target=CLASS_1` 분기에서 `requires_validator_reentry_when_class1=True`인 경우:
- `obs.validation.validation_status == "approved"` 강제 (rejected/safe_deferral은 fail).
- `obs.ack.dispatch_status` 존재 강제 (validator는 통과했지만 dispatcher가 안 돌면 bounded execution 증거 없음 → fail).

**테스트 추가:**

- `test_validator_reentry_required_passes_with_approved_and_ack` — approved + ack → pass.
- `test_validator_reentry_required_fails_on_rejected` — rejected_escalation → fail (이전에는 pass였음).
- `test_validator_reentry_required_fails_without_ack` — approved + ack 없음 → fail.

### Issue 3: 복합 / 별칭 expected_transition_target이 exact-match로 판정

**증상:** 시나리오에는 `CLASS_1_OR_CLASS_0_OR_SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION`(복합), `CAREGIVER_CONFIRMATION`(별칭) 같은 값이 있으나 verdict는 문자열 정확 비교만 수행. 런타임은 caregiver/safe deferral 계열을 항상 `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION`로 canonicalize → 정상 결과도 fail.

**수정 파일:** `rpi/code/experiment_package/trial_store.py`, `rpi/code/experiment_package/runner.py`

- 새 헬퍼 `_expected_transition_targets(expected) -> Optional[set[str]]`: `_OR_`로 split, 각 토큰을 alias map으로 canonicalize. `CAREGIVER_CONFIRMATION` / `SAFE_DEFERRAL` → `SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION`. None 입력은 None 반환 (verdict가 target 검사 자체를 스킵).
- `_is_pass()`가 `if observed_target not in accepted` 형태로 검증.
- `PackageRunner._match_observation`도 같은 헬퍼 사용:
  - 단일 `{CLASS_1}` 기대만 `single_click` 자동 주입, `{CLASS_0}` 기대만 `triple_hit` 자동 주입.
  - 복합 기대(`{CLASS_1, CLASS_0, SAFE_DEFERRAL_...}`)는 자동 주입 없이 자연스러운 timeout/caregiver path를 그대로 검증.
  - 종료 조건도 동일하게 단일 기대일 때만 validation/escalation 블록 강제.

**테스트 추가:** `TestCompoundExpectedTransitionTarget` (7개) — 복합 매칭, alias 정규화, 헬퍼 단위 테스트.

### Issue 4: Package D notification이 observation보다 늦게 도착하면 누락

**증상:** timeout/caregiver fallback path는 `publish_class2_update`(observation)을 먼저 보내고 그 다음 `send_notification`을 보냄. Runner는 observation을 받자마자 `notification_store.find_by_correlation_id`을 한 번 조회 → 정상 notification을 `no_notification_count`로 집계.

**수정 파일:** `rpi/code/experiment_package/runner.py`

- `_await_notification(correlation_id, observation)` 헬퍼 신설. 즉시 한 번 조회 → 발견 시 반환. observation이 None(타임아웃)이면 추가 대기 없음. observation이 있으면 `_POST_OBS_NOTIFICATION_GRACE_S = 2.0`초 동안 0.25초 간격으로 폴링.
- `_run_trial`이 단순 `find_by_correlation_id` 대신 `_await_notification`을 사용.

**테스트 추가:** `TestNotificationLateArrival::test_notification_arriving_after_observation_is_captured` — observation 직후 0.3초 뒤에 notification을 발행하면 trial이 `notification_payload`를 캡처.

### Issue 5: Notification Readiness Rate 미산출

**증상:** `required_experiments.md` §8.4는 Package D 필수 지표에 `Notification Readiness Rate`를 포함했는데 `_metrics_d` 결과와 `definitions.py.required_metrics`에는 없음.

**수정:**

| 파일 | 변경 |
|---|---|
| `rpi/code/experiment_package/trial_store.py` | `_metrics_d`가 `notification_expected_count`(observation의 `class2.should_notify_caregiver`가 True인 trial 수, 기본 True 가정)와 `notification_readiness_rate`(`notifications_present / expected`)를 새 키로 보고. |
| `rpi/code/experiment_package/definitions.py` | Package D `required_metrics`에 `notification_readiness_rate` 추가. |

**테스트 추가:**

- `test_notification_readiness_rate_present` — 정상 notification → readiness=1.0.
- `test_notification_readiness_rate_missing_notification` — 누락 → readiness=0.0, no_notification_count=1.
- `test_notification_not_expected_when_should_notify_false` — `should_notify_caregiver=False`인 trial은 denominator에서 제외.

---

## 추가/변경된 테스트 요약

| 위치 | 클래스/그룹 | 개수 | 비고 |
|---|---|---|---|
| `mac_mini/code/tests/test_class2_clarification_manager.py` | `TestC208VisitorContext` (확장) | +2 | C208 schema validation, non-canonical trigger omission |
| `mac_mini/code/tests/test_pipeline_ack_escalation.py` | `TestBuildNotificationTriggerGating` (신설) | +4 | main._build_notification trigger gating |
| `rpi/code/tests/test_rpi_components.py` | `TestRequiresValidatorReentry` (확장) | +2 | rejected/no-ack가 fail로 분리됨 (기존 1개 갱신 포함) |
| `rpi/code/tests/test_rpi_components.py` | `TestCompoundExpectedTransitionTarget` (신설) | +7 | _OR_ 분해, alias 정규화, 헬퍼 단위 테스트 |
| `rpi/code/tests/test_rpi_components.py` | `TestPackageMetricsD` (확장) | +3 | notification_readiness_rate 산출 검증 |
| `rpi/code/tests/test_rpi_components.py` | `TestNotificationLateArrival` (신설) | +1 | observation 후 도착하는 notification 캡처 |

mac_mini 429→435 (+6), rpi 112→125 (+13). 모두 통과. 시나리오 15/15, class_2_notification_doorlock_sensitive payload 그리고 clarification example payload 모두 schema 통과.

---

## 주의사항

- **canonical schema 변경 (1건):** `class2_notification_payload_schema.json`의 `exception_trigger_id` enum에 `C208` 추가. 기존 enum은 모두 유지 — 추가만 했으므로 backward compatible.
- **verdict 강화 영향:** `requires_validator_reentry_when_class1=True`인 시나리오는 이제 dispatcher ACK까지 기록되어야 pass. 직전 PR의 `publish_class2_to_class1_outcome`가 approved일 때 ACK도 같이 채우므로 정상 흐름은 통과. 단, `target_hint`가 catalog 외 값이거나 validator가 reject하는 경우는 즉시 fail로 표시됨.
- **CLASS_0 transition 검증 강화:** 모든 CLASS_2 → CLASS_0 transition trial은 escalation block 필요 (직전 PR의 `publish_class2_to_class0_outcome`가 escalation을 항상 채움). 이전 dashboard 기반 테스트가 escalation을 만들지 않았다면 fail로 바뀌므로 헬퍼들을 점검.
- **Auto-drive 보수화:** 복합 expectation은 auto-drive하지 않음. 즉, `CLASS_1_OR_CLASS_0_OR_SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION` 시나리오는 단일 입력 publish 후 자연 타임아웃을 기다린다 — `_TRIAL_TIMEOUT_CLASS2_S=360s` 까지 대기 가능하므로 운영 시 user/caregiver 응답이 시간 내 도착해야 함. CI/실험 환경에서는 시간을 늘리거나 시나리오의 `expected_transition_target`을 단일값으로 좁힐 것.
- **Notification readiness 분모:** `class2.should_notify_caregiver` 미발행(observation 자체가 안 옴) trial은 기본 True로 가정해서 denominator에 포함. `should_notify_caregiver=False`로 명시된 경우만 제외.
- **Notification grace period:** `_POST_OBS_NOTIFICATION_GRACE_S=2.0`초. Telegram send_notification가 더 오래 걸리는 환경(예: HTTP retry)에서는 이 값을 늘릴 것.

---

## 다음 세션 권장 작업

1. **CLASS_2 → CLASS_1 / CLASS_0 E2E 실험 재실행** — verdict 강화 + canonicalize + late notification tolerance가 모두 자리 잡았으므로 실 결과 검증.
2. **`class2_to_class1_low_risk_confirmation_scenario_skeleton.json` dedicated fixture 연결** — 직전 세션에도 권장됨, 여전히 미완.
3. **(선택) `class_2_notification_doorlock_sensitive.json` example payload의 `exception_trigger_id`를 C203→C208로 정정** — payload 의도와 enum 의도 일치.
4. **(선택) `should_notify_caregiver` 명시 false인 시나리오 추가** — Notification Readiness Rate denominator 동작 운영 검증.
5. **(선택) audit_logger에 `experiment_mode` 기록** — Package A Table 5 trace 편의.

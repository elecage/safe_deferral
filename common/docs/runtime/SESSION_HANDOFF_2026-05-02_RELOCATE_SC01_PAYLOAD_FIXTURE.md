# SESSION_HANDOFF — Relocate sc01 Payload Fixture to Canonical Location

**Date:** 2026-05-02
**Tests:** mac_mini 700/700 unchanged. rpi 168/168 unchanged. Payload validates against `policy_router_input_schema.json` via `AssetLoader.make_schema_resolver`.
**Schema validation:** none modified.

**Plan baseline:** Follow-up to P3.8 (PR #120). The post-doc-12 audit and PR #120's "intentionally not done" list noted that `sc01_light_on_request.json` was a payload fixture misplaced under `integration/scenarios/` and needed coordinated relocation with `docs/setup/05_integration_run.md` updates. This PR completes that.

---

## 이번 세션의 범위

`integration/scenarios/sc01_light_on_request.json`은 scenario manifest가 아니라 `policy_router_input` payload 예제 (mosquitto_pub `-f` flag로 직접 발행하는 health-check 픽스처). `integration/scenarios/` 디렉토리는 scenario manifest 전용이라 이 파일은 misplaced. 적절한 canonical 위치는 다른 payload fixture들이 있는 `integration/tests/data/`이며, naming convention은 `sample_policy_router_input_*.json`.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `integration/scenarios/sc01_light_on_request.json` → `integration/tests/data/sample_policy_router_input_sc01_light_on_request.json` | `git mv` 한 번. 내용 변경 0. naming convention 정렬 (다른 sample_policy_router_input_*.json과 일치). |
| `docs/setup/05_integration_run.md` | 두 군데 (line 377, 393)의 `mosquitto_pub -f integration/scenarios/sc01_light_on_request.json` → `mosquitto_pub -f integration/tests/data/sample_policy_router_input_sc01_light_on_request.json`. |
| `common/docs/WORK_PLAN.md` | line 54 TODO 마킹 `[ ]` → `[x]` + 새 경로/이름 명시 + 재배치 사실 기록. |
| `mac_mini/code/tests/test_scenario_manifest_p2_6.py` | `_all_scenario_paths()`의 explicit exclusion에서 `sc01_light_on_request.json` 제거. 디렉토리에서 사라졌으므로 exclusion 자체가 불필요. 주석에 history 보존. |

### Validation

```bash
# Payload validates against its real schema
cd mac_mini/code && python -c "
from shared.asset_loader import AssetLoader
import json, jsonschema, pathlib
loader = AssetLoader()
schema = loader.load_schema('policy_router_input_schema.json')
resolver = loader.make_schema_resolver()
p = pathlib.Path('/.../integration/tests/data/sample_policy_router_input_sc01_light_on_request.json')
v = jsonschema.Draft7Validator(schema, resolver=resolver)
errors = list(v.iter_errors(json.load(open(p))))
assert not errors
"
# OK

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 700 passed (unchanged)

cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 168 passed (unchanged)
```

P2.6 verifier (test_scenario_manifest_p2_6.py)는 이제 22개 active scenario manifest를 자동 enumerate (sc01 자동 제외 — 디렉토리에 없음).

### Lingering historical references

다음 historical SESSION_HANDOFF들은 옛 위치를 reference하지만 convention에 따라 그대로 유지:
- `SESSION_HANDOFF_2026-04-28_PHASE1_FIXTURE_BOM_UPDATE.md` — 파일 처음 만들었을 때의 handoff
- `SESSION_HANDOFF_2026-05-02_P2_6_MANIFEST_COMPARISON_CONDITIONS_TAGGING.md` — P2.6에서 explicit exclusion 결정한 handoff
- `SESSION_HANDOFF_2026-05-02_P3_8_FIXTURE_COMMENT_CLEANUP.md` — P3.8에서 "별도 PR에 위임" 결정한 handoff

이들은 시점별 결정의 record로서 의미가 있으므로 retroactive 편집 안 함. 본 handoff가 "그 결정의 close-out" 역할.

### Boundary 영향

없음. 파일 위치 변경 + doc reference 동기화. Production runtime / canonical asset 변경 0.

### Files touched

```
integration/scenarios/sc01_light_on_request.json → integration/tests/data/sample_policy_router_input_sc01_light_on_request.json (renamed)
docs/setup/05_integration_run.md
common/docs/WORK_PLAN.md
mac_mini/code/tests/test_scenario_manifest_p2_6.py
common/docs/runtime/SESSION_HANDOFF_2026-05-02_RELOCATE_SC01_PAYLOAD_FIXTURE.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음

paper-eval matrix 실제 측정 셋업 — 시나리오/스크립트/분석 작업.

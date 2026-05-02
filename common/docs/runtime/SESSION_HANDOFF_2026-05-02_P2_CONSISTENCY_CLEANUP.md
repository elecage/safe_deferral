# SESSION_HANDOFF — P2 Cleanup (Audit Findings #1-#3)

**Date:** 2026-05-02
**Tests:** rpi 257/257 (was 235; +22 new). mac_mini 711/711 unchanged. Plus a small endpoint bug fix in `governance/ui_app.list_proposals` surfaced by the new tests.

**Plan baseline:** Closes the 3 P2 findings raised by the repo-wide consistency audit (#128 PR session). All non-blocking but accumulated drift / coverage gaps.

---

## 이번 세션의 범위

3개 P2 finding 한 PR로 정리. #2는 조사 결과 변경 불필요로 결론. #3은 실제 gap이 audit 추정보다 좁아서 가장 가치 있는 한 모듈 (governance/ui_app)만 cover.

### Finding #1 — `common/payloads/README.md` 파일 목록 backfill (수정)

**증상**: README에 listing되지 않은 3개 파일이 `common/payloads/examples/`에 실재.
- `clarification_interaction_scanning_yes_first.json` (PR #114)
- `clarification_interaction_multi_turn_refinement.json` (PR #114)
- `policy_router_input_paper_eval_all_modes.json` (PR #114)

**Fix**: README의 파일 트리 + 'Schema-governed example coverage' 표에 3개 항목 추가. 각 항목에 governing schema + 한 줄 설명 (scanning interaction with scan_history / multi-turn refinement with refinement_history / paper-eval all-modes reference).

### Finding #2 — Scanning scenarios `comparison_conditions[]` 태그 검토 (변경 불필요 결론)

**Audit 의견**: `class2_scanning_triple_hit_emergency_shortcut_scenario_skeleton.json`과 `class2_scanning_all_rejected_caregiver_escalation_scenario_skeleton.json`이 `["class2_scanning_input"]`만 태그. ordering 태그 추가 가능성 needs investigation.

**조사**:
- `triple_hit_emergency_shortcut`: 사용자가 emergency 옵션에 "yes" → emergency shortcut 실행 (잔여 옵션 안 들음). emergency-first 동작은 announce 순서와 무관 (emergency가 첫 번째든 마지막이든 동작 동일).
- `all_rejected_caregiver_escalation`: 사용자가 전 옵션 "no" → caregiver phase. 전부 거절이라 announce 순서와 outcome 무관.
- `class2_scanning_user_accept_first` (대조): 사용자가 첫 announce된 옵션 수락 → 어느 옵션이 첫 번째냐에 따라 결과가 달라지므로 ordering이 의미 있음. 이 시나리오만 `["class2_scanning_input", "class2_scan_source_order"]` 둘 다 태그.

**결론**: 두 시나리오 모두 ordering-agnostic 동작이므로 ordering 태그 **추가 불필요**. 매트릭스 v1의 `C2_D4_SCANNING_INPUT` 셀 (3개 시나리오 모두 사용)과 `C2_D3_SCAN_SOURCE_ORDER` 셀 (`user_accept_first`만 사용)의 분리도 이 분석과 일치. 변경 사항 없음.

### Finding #3 — rpi 모듈 unit test 부재 (governance/ui_app만 채움)

**Audit 의견**: `rpi/code/{main, governance, preflight, scenario_manager}` 전용 test 파일 없음.

**조사**: `tests/test_rpi_components.py`이 monolithic하지만 ExperimentManager / ScenarioManager / PreflightManager / GovernanceBackend 모두 이미 cover됨. **실제 진짜 gap**:
- `rpi/main.py` — service launcher 얇은 entry point, unit test 가치 낮음 (argparse + threading + signal handling만)
- `governance/ui_app.py` — 7 endpoint FastAPI app. backend는 GovernanceBackend (이미 test됨)이지만 endpoint layer (HTTP 검증, 400/404 분기, OpenAPI 노출)는 untested.

**Fix**: 신규 `rpi/code/tests/test_governance_ui_app.py` 22 테스트, FastAPI TestClient 사용:

| 영역 | 테스트 |
|---|---|
| `GET /governance/topics` (list) | 1 (shape 검증) |
| `GET /governance/topics/{topic}` | 2 (known returns 200, unknown returns 404) |
| `POST /governance/validate` | 4 (missing schema_name 400, missing payload 400, valid → is_valid=True, invalid → errors) |
| `GET /governance/validation-reports` | 2 (initially empty, populated after validate) |
| `GET /governance/validation-reports/export` | 1 (PlainTextResponse → JSON parsable) |
| `GET /governance/proposals` | 4 (initially empty, create requires topic, returns draft, status filter) |
| `GET /governance/proposals?status=...` invalid | 1 (returns 400 — caught a real bug) |
| `POST /governance/proposals/{id}/advance` | 4 (404 unknown, 400 missing status, 400 invalid status, 200 draft→proposed) |
| `GET /governance/proposals/export` | 2 (empty, populated) |
| **Boundary invariant** | 1 (live OpenAPI paths refuse forbidden substrings: actuation, command, publish, policy_table, schema_edit, caregiver/approve) |

**Bonus bug fix**: 신규 테스트가 `list_proposals`의 endpoint-level 미처리 ValueError 발견 (status="bogus" → 500). `try/except ValueError → HTTPException(400)` 패턴으로 수정 — `advance_proposal`의 기존 contract와 일관.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `common/payloads/README.md` | 트리 listing + Schema-governed table에 3개 entry backfill (clarification_interaction_scanning_yes_first / multi_turn_refinement / policy_router_input_paper_eval_all_modes). |
| `rpi/code/governance/ui_app.py` | `list_proposals`의 invalid status 400 normalization (advance_proposal과 동일 패턴). |
| `rpi/code/tests/test_governance_ui_app.py` (신규) | 22 integration tests, FastAPI TestClient, 모든 endpoint 분기 + boundary invariant. |
| `common/docs/runtime/SESSION_HANDOFF_2026-05-02_P2_CONSISTENCY_CLEANUP.md` (신규) | 본 핸드오프. |
| `common/docs/runtime/SESSION_HANDOFF.md` | index 업데이트. |

### 디자인 원칙

- **Audit는 추정, 코드가 진실**: P2 #2/#3 모두 audit가 broad-stroke 의심을 제기. 실제 코드/시나리오 직접 확인하니 #2는 변경 불필요, #3은 실제 gap이 좁음. "audit 결과를 모두 그대로 ship하지 말고 verify-then-fix" 원칙.
- **Boundary invariant test as code**: `governance/ui_app.py`의 docstring에 "no operational control publish / no caregiver approval spoofing"이 명시되어 있지만 자연어 약속만이었음. `test_no_publish_or_actuation_paths`가 OpenAPI introspection으로 forbidden substring 검사 — 누군가 actuation endpoint 추가 시 자동 차단.
- **Endpoint-level error normalization**: backend layer의 ValueError가 endpoint에서 catch 안 되면 500. 새 endpoint 추가 시 `try/except ValueError → HTTPException(400)` 패턴 일관 사용해야 함 (advance_proposal / list_proposals 모두 이제 일관).
- **Boundary 무영향**: schema / policy / topic 변경 0. governance/ui_app은 GovernanceBackend wrapper이고 backend는 이미 read-only + proposals-only로 enforce됨.

### Test plan

```bash
cd rpi/code && python -m pytest tests/test_governance_ui_app.py -v
# 22 passed in 0.59s

cd rpi/code && python -m pytest tests/ -q
# 257 passed (was 235; +22 new)

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 711 passed (unchanged)
```

### Files touched

```
common/payloads/README.md (modified — 3 entries added)
rpi/code/governance/ui_app.py (modified — list_proposals 400 normalization)
rpi/code/tests/test_governance_ui_app.py (new, 22 tests)
common/docs/runtime/SESSION_HANDOFF_2026-05-02_P2_CONSISTENCY_CLEANUP.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### 다음 단계

- **Phase 4 / Operations** — 하드웨어 가용성 대기. paper-eval matrix v1 sweep 1회 실행, variance 측정, doc 13 §11 open question #1 답변.
- 별건 가능: rpi/main.py service launcher behavior smoke test (signal/SIGTERM handling), test_rpi_components.py monolith 분리 (cosmetic — coverage 변화 없음, deferred).

### Notes

- audit가 "큰 누락"으로 보였던 것이 실제로는 한 모듈 (`governance/ui_app`)에 좁혀졌음 — finding을 verify하지 않고 그대로 implement했다면 거대한 test refactor PR이 생겼을 것. 이 패턴을 P2 진단 워크플로우로 유지: audit는 가설, 코드 verify가 fix scope을 정함.
- `test_no_publish_or_actuation_paths`의 forbidden substring list는 보수적: 새 endpoint 이름이 substring에 우연히 매칭되면 false positive. 운영 중 이런 일 생기면 substring → 정확한 path-prefix 매칭으로 구체화 권장.
- `list_proposals`의 ValueError → 400 normalization은 한 줄 변경이지만 같은 패턴 (parameter enum coercion)이 future endpoint에 반복될 가능성 있음. project-wide pattern으로 docs 보강 가치 있음 (별건).

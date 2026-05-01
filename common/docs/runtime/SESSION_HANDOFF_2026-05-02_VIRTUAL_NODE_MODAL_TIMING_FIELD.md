# SESSION_HANDOFF — Virtual Node Modal: simulated_response_timing_ms Field

**Date:** 2026-05-02
**Tests:** rpi 157/157 (was 149; +6 new `/nodes` endpoint round-trip cases + 2 previously httpx-skipped now run after `pip install httpx` on dev box). mac_mini 478/478 unchanged.
**Schema validation:** scenario JSON parse check passes; no canonical asset modified.

**Plan baseline:** Closes the second item in the post-PR #96 next-work menu. PR #96 added the `VirtualNodeProfile.simulated_response_timing_ms` model field + dashboard read path; this PR completes the "virtual node pre-configuration form" principle by letting the user set it through the modal.

---

## 이번 세션의 범위

PR #96에서 model + serialization + dashboard 표시는 이미 갖춰졌지만, 사용자가 dashboard에서 직접 advisory timing을 입력할 방법이 없었음. 결국 "(unset)"만 표기되거나 코드로만 설정 가능했음. 본 PR은 modal에 두 개 input field를 더해서 fidelity 원칙을 마무리.

### 변경 요약

| 파일 | 변경 |
|---|---|
| `rpi/code/dashboard/static/index.html` | modal에 `시뮬레이터 응답 시간` 그룹 추가 (user_response_ms / caregiver_response_ms 두 개 number input). 둘 다 비우면 unset (omit), 하나라도 채우면 dict로 전송. edit 시 기존 값 복원 (다른 키는 backend가 merge로 보존). env_sensor_node / device_state_node는 `/sim/nodes/*` 별도 endpoint로 가므로 timing 그룹 숨김. |
| `rpi/code/dashboard/app.py` | `/nodes` POST: `simulated_response_timing_ms` body 필드 수용 + dict 타입 검증. `/nodes/{id}` PUT: incoming dict를 기존 dict 위에 merge (None은 explicit clear, omit은 preserve). 두 modal 키만 보내도 다른 persona 키는 보존. |
| `rpi/code/tests/test_rpi_components.py` | `TestNodesEndpointTimingClaim` 6개 (omit-on-unset, POST round-trip, invalid type 400, PUT merge preserves other keys, explicit null clears, omitted preserves). httpx 미설치 환경에서는 skip. |

### 디자인 원칙 (PR #96의 "no dashboard hardcoding" 연장)

- **Modal은 두 known key만 노출** (user_response_ms, caregiver_response_ms) — 정책의 phase budget 두 개와 직접 비교되는 의미를 갖는 키.
- **Backend merge로 다른 키 보존** — 자유형 dict이므로 다른 simulator persona가 추가 키를 declare 가능. modal로 편집해도 그 키들은 유지됨.
- **Three-state input** —
  - 둘 다 비움 → field 자체 omit (dashboard "(unset)" 표기)
  - 하나라도 입력 → dict 전송 (PUT은 merge)
  - explicit null 전송 → 명시적 clear (modal에서는 발생 안 함; API 직접 호출 시)

### Fidelity flow 완성

```
정책 (canonical)        VirtualNodeProfile (declared)
        ↓                         ↓
runner phase budgets   simulated_response_timing_ms (modal로 입력 가능)
        ↓                         ↓
   API endpoint        node card ⏱ row + node API field
        ↓                         ↓
        └──── dashboard 비교 가능 (다음 작업 후보) ────┘
```

### Test plan

```bash
cd rpi/code && python -m pytest tests/test_rpi_components.py -q
# 157 passed in ~10s (149 prev + 6 new + 2 previously skipped now run)

cd mac_mini/code && python -m pytest tests/ -q --ignore=tests/test_pipeline.py
# 478 passed (unchanged)
```

httpx 의존성: 신규 6개 endpoint 테스트는 `fastapi.testclient.TestClient` 사용 → httpx 필요. 미설치 환경에서는 자동 skip (PR #96 패턴 그대로).

### Files touched

```
rpi/code/dashboard/app.py
rpi/code/dashboard/static/index.html
rpi/code/tests/test_rpi_components.py
common/docs/runtime/SESSION_HANDOFF_2026-05-02_VIRTUAL_NODE_MODAL_TIMING_FIELD.md (new)
common/docs/runtime/SESSION_HANDOFF.md (index update)
```

### Out of scope (next from the menu)

- ✅ #1 Phase 4 회귀 테스트 (PR #97)
- ✅ #3 Modal field for simulated_response_timing_ms (this PR)
- ⏭ #2 Trial detail UI — per-trial expandable row that surfaces `class2_phase_budgets_snapshot` (currently reachable only via export JSON)
- (Future) #4 Dashboard 비교 metric — declared `user_response_ms`가 정책 `user_phase_timeout_s * 1000`을 초과하면 ⚠ 표기 (PR #96 + 본 PR 위에서 자연스럽게 가능)

### Notes

- Authority boundary 변경 없음. 모든 추가는 read/write of advisory metadata로, dashboard remains read-only against canonical assets.
- Backend merge semantics는 explicit `None`은 clear, omit은 preserve로 명확히 구분되므로 future automation도 rely 가능.

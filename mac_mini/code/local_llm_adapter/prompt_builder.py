"""Prompt builder for the Local LLM Adapter (MM-02).

Authority rules encoded here:
  - trigger_event.timestamp_ms is MASKED (context_schema.json annotation).
  - routing_metadata is never included.
  - LLM is instructed to return JSON matching candidate_action_schema.json
    (Class 1 path) or class2_candidate_set_schema.json (Class 2 path).
  - Doorbell context is described as visitor presence only — never doorlock auth.
  - LLM output is explicitly framed as candidate guidance, not a decision.

Class 2 candidate generation prompts implement the
09_llm_driven_class2_candidate_generation_plan.md design — the LLM is given
the full pure_context_payload plus the unresolved_reason and the bounded
low-risk catalog, and is asked for ≤ N short interrogative prompts that
match how a TTS speaker would address the user. Bounded-variability
constraints are validated downstream in adapter.py; the prompt repeats
them so the LLM stays within budget on the first try.
"""

_SYSTEM_HEADER = """\
당신은 스마트홈 보조 시스템의 후보 행동 생성기입니다.
다음 규칙을 반드시 따르세요:
1. 응답은 반드시 아래 JSON 형식만 반환합니다. 설명 텍스트 없이 JSON만 출력합니다.
2. proposed_action은 반드시 "light_on", "light_off", "safe_deferral" 중 하나입니다.
3. target_device는 반드시 "living_room_light", "bedroom_light", "none" 중 하나입니다.
4. proposed_action이 "safe_deferral"이면 target_device는 반드시 "none"이고 deferral_reason을 포함합니다.
5. 조명 행동의 경우 target_device는 "none"이 될 수 없습니다.
6. 비상 상황, 도어락, 민감한 장치는 이 스키마의 범위 밖입니다 — 항상 safe_deferral로 처리합니다.
7. 방문자 감지(도어벨)가 True이면 반드시 safe_deferral로 처리합니다. 방문자 상황은 자율 조명 판단 범위를 벗어나며 보호자 확인이 필요합니다.
8. 이것은 후보 제안입니다. 최종 실행 결정권은 없습니다.

출력 JSON 스키마:
{
  "proposed_action": "light_on" | "light_off" | "safe_deferral",
  "target_device": "living_room_light" | "bedroom_light" | "none",
  "rationale_summary": "<선택사항, 최대 160자>",
  "deferral_reason": "<safe_deferral일 때 필수: ambiguous_target | insufficient_context | policy_restriction | unresolved_multi_candidate>"
}
"""


def build_prompt(pure_context_payload: dict, event_code: str) -> str:
    """Compose the LLM prompt from pure_context_payload.

    Masking rules:
      - trigger_event.timestamp_ms is excluded (per context_schema annotation).
      - routing_metadata is never passed.
      - device_states and environmental_context are included as-is.
    """
    trigger = pure_context_payload.get("trigger_event", {})
    env = pure_context_payload.get("environmental_context", {})
    devices = pure_context_payload.get("device_states", {})

    # Mask timestamp_ms — must not be sent to LLM
    event_type = trigger.get("event_type", "unknown")
    # event_code is passed in explicitly by the caller (already extracted upstream)

    env_lines = []
    if "temperature" in env:
        env_lines.append(f"  온도: {env['temperature']}°C")
    if "illuminance" in env:
        env_lines.append(f"  조도: {env['illuminance']} lux")
    if "occupancy_detected" in env:
        env_lines.append(f"  재실 감지: {env['occupancy_detected']}")
    if "smoke_detected" in env:
        env_lines.append(f"  연기 감지: {env['smoke_detected']}")
    if "gas_detected" in env:
        env_lines.append(f"  가스 감지: {env['gas_detected']}")
    if "doorbell_detected" in env:
        # doorbell is visitor presence context only — never doorlock authorization
        env_lines.append(f"  방문자 감지(도어벨): {env['doorbell_detected']}")

    device_lines = []
    for dev, state in devices.items():
        device_lines.append(f"  {dev}: {state}")

    env_block = "\n".join(env_lines) if env_lines else "  (정보 없음)"
    dev_block = "\n".join(device_lines) if device_lines else "  (정보 없음)"

    context_section = (
        f"트리거 이벤트:\n  유형: {event_type}, 코드: {event_code}\n\n"
        f"환경 상태:\n{env_block}\n\n"
        f"기기 상태:\n{dev_block}"
    )

    return f"{_SYSTEM_HEADER}\n\n현재 컨텍스트:\n{context_section}\n\n후보 행동 JSON:"


# ---------------------------------------------------------------------------
# Class 2 candidate generation prompt
# (09_llm_driven_class2_candidate_generation_plan.md Phase 1)
# ---------------------------------------------------------------------------

_CLASS2_SYSTEM_HEADER_TEMPLATE = """\
당신은 스마트홈 보조 시스템의 Class 2 명확화(clarification) 후보 생성기입니다.
사용자는 신체적·언어적 제약이 있어 짧고 명확한 질문 형태의 선택지가 필요합니다.

다음 규칙을 반드시 따르세요:
1. 응답은 반드시 JSON 객체 하나로만 반환합니다. 설명 텍스트 없이 JSON만 출력합니다.
2. 후보(candidates)는 최대 {max_candidates}개입니다.
3. 각 후보의 prompt는 최대 {max_prompt_length} 글자이며, 반드시 물음표("?")로 끝나는 한국어 질문이어야 합니다.
4. 각 후보는 candidate_id, prompt, candidate_transition_target을 반드시 포함합니다.
5. candidate_transition_target은 다음 중 하나입니다: "CLASS_1", "CLASS_0", "SAFE_DEFERRAL", "CAREGIVER_CONFIRMATION".
6. CLASS_1 후보의 action_hint는 반드시 다음 중 하나입니다: {allowed_actions}. target_hint는 반드시 다음 중 하나입니다: {allowed_targets}. 카탈로그 외의 동작이나 기기를 임의로 제안하지 마세요. 카탈로그 안의 안전한 후보가 없으면 SAFE_DEFERRAL이나 CAREGIVER_CONFIRMATION 후보만 반환합니다.
7. CLASS_0 후보는 반드시 candidate_id="C3_EMERGENCY_HELP", action_hint=null, target_hint=null이며 prompt는 "긴급상황인가요?" 형태의 짧은 확인 질문입니다. 임의로 응급을 선언하지 마세요.
8. CAREGIVER_CONFIRMATION 후보의 action_hint와 target_hint는 항상 null입니다.
9. 도어락, 도어 개방, 블라인드, TV, 가스밸브 등 카탈로그 밖의 액추에이터는 후보로 제시하지 마세요. 방문자 감지(도어벨)가 true이더라도 도어락 자율 제어를 제안하지 마세요.
10. unresolved_reason이 "caregiver_required_sensitive_path"이면 첫 번째 후보는 반드시 CAREGIVER_CONFIRMATION이어야 합니다.
11. 출력 JSON은 후보 행동만이 아니라 사용자의 현재 상황을 반영한 contextual 질문이어야 합니다(예: 어두운 거실 + 사용자 재실 → "거실 조명을 켜드릴까요?").

출력 JSON 스키마(class2_candidate_set_schema.json 부분 집합):
{{
  "candidates": [
    {{
      "candidate_id": "<짧은 식별자>",
      "prompt": "<{max_prompt_length}자 이내의 한국어 질문, '?'로 끝남>",
      "candidate_transition_target": "CLASS_1" | "CLASS_0" | "SAFE_DEFERRAL" | "CAREGIVER_CONFIRMATION",
      "action_hint": "<카탈로그 안 액션 | null>",
      "target_hint": "<카탈로그 안 타겟 | null>"
    }}
  ]
}}
"""


def build_class2_candidate_prompt(
    pure_context_payload: dict,
    unresolved_reason: str,
    max_candidates: int,
    max_prompt_length: int,
    allowed_actions: list[str],
    allowed_targets: list[str],
    event_code: str,
) -> str:
    """Compose a bounded Class 2 candidate-set prompt.

    The same masking rules as build_prompt apply: trigger_event.timestamp_ms
    is excluded; routing_metadata is never included.
    """
    trigger = pure_context_payload.get("trigger_event", {})
    env = pure_context_payload.get("environmental_context", {})
    devices = pure_context_payload.get("device_states", {})
    event_type = trigger.get("event_type", "unknown")

    env_lines = []
    if "temperature" in env:
        env_lines.append(f"  온도: {env['temperature']}°C")
    if "illuminance" in env:
        env_lines.append(f"  조도: {env['illuminance']} lux")
    if "occupancy_detected" in env:
        env_lines.append(f"  재실 감지: {env['occupancy_detected']}")
    if "smoke_detected" in env:
        env_lines.append(f"  연기 감지: {env['smoke_detected']}")
    if "gas_detected" in env:
        env_lines.append(f"  가스 감지: {env['gas_detected']}")
    if "doorbell_detected" in env:
        env_lines.append(f"  방문자 감지(도어벨): {env['doorbell_detected']}")
    device_lines = [f"  {dev}: {state}" for dev, state in devices.items()]

    env_block = "\n".join(env_lines) if env_lines else "  (정보 없음)"
    dev_block = "\n".join(device_lines) if device_lines else "  (정보 없음)"

    header = _CLASS2_SYSTEM_HEADER_TEMPLATE.format(
        max_candidates=max_candidates,
        max_prompt_length=max_prompt_length,
        allowed_actions=", ".join(f'"{a}"' for a in allowed_actions) or "(없음)",
        allowed_targets=", ".join(f'"{t}"' for t in allowed_targets) or "(없음)",
    )

    context_section = (
        f"트리거 이벤트:\n  유형: {event_type}, 코드: {event_code}\n\n"
        f"환경 상태:\n{env_block}\n\n"
        f"기기 상태:\n{dev_block}\n\n"
        f"unresolved_reason: {unresolved_reason}"
    )

    return f"{header}\n\n현재 컨텍스트:\n{context_section}\n\nClass 2 후보 JSON:"

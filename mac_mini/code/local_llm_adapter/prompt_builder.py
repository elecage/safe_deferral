"""Prompt builder for the Local LLM Adapter (MM-02).

Authority rules encoded here:
  - trigger_event.timestamp_ms is MASKED (context_schema.json annotation).
  - routing_metadata is never included.
  - LLM is instructed to return JSON matching candidate_action_schema.json.
  - Doorbell context is described as visitor presence only — never doorlock auth.
  - LLM output is explicitly framed as candidate guidance, not a decision.
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

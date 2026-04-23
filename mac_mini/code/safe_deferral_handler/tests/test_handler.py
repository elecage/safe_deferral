"""
Context-Integrity Safe Deferral Handler 단위 테스트.

frozen 정책 파일(policy_table_v1_1_2_FROZEN.json)을 실제로 로드하여 테스트한다.
타임아웃 값, 최대 시도 횟수를 테스트 내에서 하드코딩하지 않는다.

커버리지:
  1. 2-옵션 매핑 정상 동작
  2. 3-옵션 매핑 정상 동작
  3. 타임아웃 처리 (C201 emit)
  4. 유효하지 않은 후보 옵션 수 (1개 또는 4개+)
"""
import pytest
from pydantic import ValidationError

from safe_deferral_handler.handler import (
    build_clarification_options,
    emit_timeout_event,
    resolve_button_input,
    start_clarification_session,
    _get_timeout_ms,
    _get_max_attempts,
)
from safe_deferral_handler.models import (
    ButtonInput,
    ButtonMapping,
    ClarificationFlowStatus,
    ClarificationOption,
    DeferralHandlerInput,
)
from safe_deferral_handler.policy_loader import load_policy_table


# ── 헬퍼 ────────────────────────────────────────────────────────────────────

import time


def _make_two_options() -> list:
    return [
        ClarificationOption(
            button_mapping=ButtonMapping.ONE_HIT,
            action="light_on",
            target_device="living_room_light",
            display_label="light_on living_room_light",
        ),
        ClarificationOption(
            button_mapping=ButtonMapping.TWO_HITS,
            action="light_off",
            target_device="bedroom_light",
            display_label="light_off bedroom_light",
        ),
    ]


def _make_three_options() -> list:
    return [
        ClarificationOption(
            button_mapping=ButtonMapping.ONE_HIT,
            action="light_on",
            target_device="living_room_light",
            display_label="light_on living_room_light",
        ),
        ClarificationOption(
            button_mapping=ButtonMapping.TWO_HITS,
            action="light_on",
            target_device="bedroom_light",
            display_label="light_on bedroom_light",
        ),
        ClarificationOption(
            button_mapping=ButtonMapping.THREE_HITS,
            action="light_off",
            target_device="living_room_light",
            display_label="light_off living_room_light",
        ),
    ]


def _make_input(options: list, correlation_id: str = "test-deferral-001") -> DeferralHandlerInput:
    return DeferralHandlerInput(
        audit_correlation_id=correlation_id,
        deferral_reason="ambiguous_target",
        candidate_options=options,
    )


def _make_button(hit_count: int) -> ButtonInput:
    return ButtonInput(hit_count=hit_count, timestamp_ms=int(time.time() * 1000))


# ── 1. 2-옵션 매핑 정상 동작 ────────────────────────────────────────────────


class TestTwoOptionMapping:
    """2개 옵션으로 clarification 이 정상 동작해야 한다."""

    def test_session_start_returns_waiting(self):
        """session 시작 시 WAITING 상태를 반환해야 한다."""
        handler_input = _make_input(_make_two_options())
        result = start_clarification_session(handler_input)

        assert result.status == ClarificationFlowStatus.WAITING
        assert result.presented_options is not None
        assert len(result.presented_options) == 2

    def test_hit_1_selects_option_a(self):
        """1 hit → 옵션 A (첫 번째 옵션) 선택."""
        options = _make_two_options()
        handler_input = _make_input(options)
        result = resolve_button_input(handler_input, _make_button(1))

        assert result.status == ClarificationFlowStatus.RESOLVED
        assert result.resolved_option is not None
        assert result.resolved_option.action == "light_on"
        assert result.resolved_option.target_device == "living_room_light"

    def test_hit_2_selects_option_b(self):
        """2 hits → 옵션 B (두 번째 옵션) 선택."""
        options = _make_two_options()
        handler_input = _make_input(options)
        result = resolve_button_input(handler_input, _make_button(2))

        assert result.status == ClarificationFlowStatus.RESOLVED
        assert result.resolved_option.action == "light_off"
        assert result.resolved_option.target_device == "bedroom_light"

    def test_hit_3_on_two_options_stays_waiting(self):
        """2-옵션 상황에서 3 hits 는 범위 초과 → WAITING 유지."""
        options = _make_two_options()
        handler_input = _make_input(options)
        result = resolve_button_input(handler_input, _make_button(3))

        assert result.status == ClarificationFlowStatus.WAITING
        assert result.resolved_option is None

    def test_resolved_includes_presented_options(self):
        """RESOLVED 결과에도 presented_options 가 포함되어야 한다 (감사 목적)."""
        handler_input = _make_input(_make_two_options())
        result = resolve_button_input(handler_input, _make_button(1))

        assert result.presented_options is not None
        assert len(result.presented_options) == 2


# ── 2. 3-옵션 매핑 정상 동작 ────────────────────────────────────────────────


class TestThreeOptionMapping:
    """3개 옵션으로 clarification 이 정상 동작해야 한다."""

    def test_session_start_with_three_options(self):
        """3-옵션 session 시작 시 WAITING 상태와 3개 옵션을 반환해야 한다."""
        handler_input = _make_input(_make_three_options())
        result = start_clarification_session(handler_input)

        assert result.status == ClarificationFlowStatus.WAITING
        assert len(result.presented_options) == 3

    def test_hit_1_selects_first_of_three(self):
        """3-옵션에서 1 hit → 첫 번째 옵션."""
        options = _make_three_options()
        handler_input = _make_input(options)
        result = resolve_button_input(handler_input, _make_button(1))

        assert result.status == ClarificationFlowStatus.RESOLVED
        assert result.resolved_option.action == "light_on"
        assert result.resolved_option.target_device == "living_room_light"

    def test_hit_2_selects_second_of_three(self):
        """3-옵션에서 2 hits → 두 번째 옵션."""
        options = _make_three_options()
        handler_input = _make_input(options)
        result = resolve_button_input(handler_input, _make_button(2))

        assert result.status == ClarificationFlowStatus.RESOLVED
        assert result.resolved_option.target_device == "bedroom_light"

    def test_hit_3_selects_third_option(self):
        """3-옵션에서 3 hits → 세 번째 옵션."""
        options = _make_three_options()
        handler_input = _make_input(options)
        result = resolve_button_input(handler_input, _make_button(3))

        assert result.status == ClarificationFlowStatus.RESOLVED
        assert result.resolved_option.action == "light_off"
        assert result.resolved_option.target_device == "living_room_light"


# ── 3. 타임아웃 처리 ────────────────────────────────────────────────────────


class TestTimeoutHandling:
    """타임아웃 시 C201 을 emit 하고 TIMEOUT 상태를 반환해야 한다."""

    def test_timeout_returns_timeout_status(self):
        """타임아웃 처리 시 TIMEOUT 상태를 반환해야 한다."""
        handler_input = _make_input(_make_two_options())
        result = emit_timeout_event(handler_input)

        assert result.status == ClarificationFlowStatus.TIMEOUT

    def test_timeout_emits_c201_trigger(self):
        """타임아웃 결과에는 timeout_trigger_id=C201 이 있어야 한다."""
        handler_input = _make_input(_make_two_options())
        result = emit_timeout_event(handler_input)

        assert result.timeout_trigger_id == "C201"

    def test_timeout_includes_correlation_id(self):
        """타임아웃 결과에는 audit_correlation_id 가 유지되어야 한다."""
        handler_input = _make_input(_make_two_options(), correlation_id="timeout-test-999")
        result = emit_timeout_event(handler_input)

        assert result.audit_correlation_id == "timeout-test-999"

    def test_timeout_includes_presented_options(self):
        """타임아웃 결과에도 어떤 옵션이 제시됐는지 포함되어야 한다 (감사 목적)."""
        handler_input = _make_input(_make_two_options())
        result = emit_timeout_event(handler_input)

        assert result.presented_options is not None

    def test_timeout_no_resolved_option(self):
        """타임아웃 결과에는 resolved_option 이 없어야 한다."""
        handler_input = _make_input(_make_two_options())
        result = emit_timeout_event(handler_input)

        assert result.resolved_option is None

    def test_timeout_value_from_policy_file(self):
        """타임아웃 값은 frozen 정책 파일과 일치해야 한다."""
        policy = load_policy_table()
        expected = policy["global_constraints"][
            "default_context_integrity_safe_deferral_timeout_ms"
        ]
        assert _get_timeout_ms() == expected

    def test_max_attempts_from_policy_file(self):
        """최대 시도 횟수는 frozen 정책 파일과 일치해야 한다."""
        policy = load_policy_table()
        expected = policy["global_constraints"]["max_context_integrity_safe_deferral_attempts"]
        assert _get_max_attempts() == expected


# ── 4. 유효하지 않은 후보 옵션 수 ────────────────────────────────────────────


class TestInvalidCandidateOptionCount:
    """후보 옵션이 2개 미만이거나 3개 초과이면 오류가 발생해야 한다."""

    def test_single_option_input_rejected_by_pydantic(self):
        """1개 옵션은 Pydantic min_length=2 를 위반해야 한다."""
        with pytest.raises(ValidationError):
            DeferralHandlerInput(
                audit_correlation_id="test-001",
                deferral_reason="ambiguous_target",
                candidate_options=[_make_two_options()[0]],  # 1개 (min=2 위반)
            )

    def test_four_options_input_rejected_by_pydantic(self):
        """4개 옵션은 Pydantic max_length=3 을 위반해야 한다."""
        four_options = _make_three_options() + [
            ClarificationOption(
                button_mapping=ButtonMapping.ONE_HIT,  # 임시 - 4번째 매핑은 없음
                action="light_off",
                target_device="bedroom_light",
                display_label="extra",
            )
        ]
        with pytest.raises(ValidationError):
            DeferralHandlerInput(
                audit_correlation_id="test-001",
                deferral_reason="ambiguous_target",
                candidate_options=four_options,  # 4개 (max=3 위반)
            )

    def test_build_clarification_options_rejects_one_candidate(self):
        """build_clarification_options 는 1개 후보를 받으면 ValueError 를 발생시킨다."""
        with pytest.raises(ValueError):
            build_clarification_options(
                [{"action": "light_on", "target_device": "living_room_light"}]
            )

    def test_build_clarification_options_rejects_four_candidates(self):
        """build_clarification_options 는 4개 후보를 받으면 ValueError 를 발생시킨다."""
        four = [
            {"action": "light_on", "target_device": "living_room_light"},
            {"action": "light_off", "target_device": "living_room_light"},
            {"action": "light_on", "target_device": "bedroom_light"},
            {"action": "light_off", "target_device": "bedroom_light"},
        ]
        with pytest.raises(ValueError):
            build_clarification_options(four)

    def test_build_clarification_options_two_candidates(self):
        """build_clarification_options 는 2개 후보를 올바르게 변환해야 한다."""
        raw = [
            {"action": "light_on", "target_device": "living_room_light"},
            {"action": "light_off", "target_device": "bedroom_light"},
        ]
        options = build_clarification_options(raw)

        assert len(options) == 2
        assert options[0].button_mapping == ButtonMapping.ONE_HIT
        assert options[1].button_mapping == ButtonMapping.TWO_HITS

    def test_build_clarification_options_three_candidates(self):
        """build_clarification_options 는 3개 후보를 올바르게 변환해야 한다."""
        raw = [
            {"action": "light_on", "target_device": "living_room_light"},
            {"action": "light_on", "target_device": "bedroom_light"},
            {"action": "light_off", "target_device": "living_room_light"},
        ]
        options = build_clarification_options(raw)

        assert len(options) == 3
        assert options[2].button_mapping == ButtonMapping.THREE_HITS

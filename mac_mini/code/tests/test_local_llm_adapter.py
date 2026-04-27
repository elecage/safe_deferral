"""Tests for LocalLlmAdapter (MM-02)."""

import json
import pytest

from local_llm_adapter.adapter import LocalLlmAdapter
from local_llm_adapter.llm_client import MockLlmClient
from local_llm_adapter.models import LLMCandidateResult
from local_llm_adapter.prompt_builder import build_prompt

AUDIT_ID = "test_audit_mm02"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _ctx(
    event_type="button",
    event_code="single_click",
    temperature=22.0,
    occupancy=True,
    living_room_light="off",
    doorbell=False,
):
    return {
        "trigger_event": {
            "event_type": event_type,
            "event_code": event_code,
            "timestamp_ms": 1710000000000,   # must be masked
        },
        "environmental_context": {
            "temperature": temperature,
            "illuminance": 200,
            "occupancy_detected": occupancy,
            "smoke_detected": False,
            "gas_detected": False,
            "doorbell_detected": doorbell,
        },
        "device_states": {
            "living_room_light": living_room_light,
            "bedroom_light": "off",
            "living_room_blind": "open",
            "tv_main": "off",
        },
    }


def _mock_adapter(response: str) -> LocalLlmAdapter:
    client = MockLlmClient(fixed_response=response)
    return LocalLlmAdapter(llm_client=client)


def _valid_light_on_json(target="living_room_light"):
    return json.dumps({
        "proposed_action": "light_on",
        "target_device": target,
        "rationale_summary": "occupancy detected, low light",
    })


def _valid_safe_deferral_json(reason="ambiguous_target"):
    return json.dumps({
        "proposed_action": "safe_deferral",
        "target_device": "none",
        "deferral_reason": reason,
    })


# ------------------------------------------------------------------
# Happy-path: valid LLM output
# ------------------------------------------------------------------

class TestValidOutput:
    def test_light_on_living_room(self):
        adapter = _mock_adapter(_valid_light_on_json("living_room_light"))
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.proposed_action == "light_on"
        assert result.target_device == "living_room_light"
        assert result.is_fallback is False

    def test_light_on_bedroom(self):
        adapter = _mock_adapter(_valid_light_on_json("bedroom_light"))
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.proposed_action == "light_on"
        assert result.target_device == "bedroom_light"

    def test_light_off(self):
        response = json.dumps({
            "proposed_action": "light_off",
            "target_device": "living_room_light",
        })
        adapter = _mock_adapter(response)
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.proposed_action == "light_off"

    def test_safe_deferral_ambiguous(self):
        adapter = _mock_adapter(_valid_safe_deferral_json("ambiguous_target"))
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.is_safe_deferral is True
        assert result.is_fallback is False

    def test_safe_deferral_insufficient_context(self):
        adapter = _mock_adapter(_valid_safe_deferral_json("insufficient_context"))
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.candidate["deferral_reason"] == "insufficient_context"

    def test_result_type_is_llm_candidate_result(self):
        adapter = _mock_adapter(_valid_light_on_json())
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert isinstance(result, LLMCandidateResult)

    def test_audit_id_preserved(self):
        adapter = _mock_adapter(_valid_light_on_json())
        result = adapter.generate_candidate(_ctx(), "my-audit-mm02")
        assert result.audit_correlation_id == "my-audit-mm02"

    def test_model_id_from_client(self):
        adapter = _mock_adapter(_valid_light_on_json())
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.model_id == "mock"

    def test_llm_raw_response_stored(self):
        raw = _valid_light_on_json()
        adapter = _mock_adapter(raw)
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.llm_raw_response == raw


# ------------------------------------------------------------------
# Fallback on invalid LLM output
# ------------------------------------------------------------------

class TestFallback:
    def test_invalid_proposed_action_falls_back(self):
        bad = json.dumps({"proposed_action": "doorlock_open", "target_device": "none"})
        adapter = _mock_adapter(bad)
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.is_fallback is True
        assert result.proposed_action == "safe_deferral"

    def test_invalid_target_device_falls_back(self):
        bad = json.dumps({"proposed_action": "light_on", "target_device": "front_door"})
        adapter = _mock_adapter(bad)
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.is_fallback is True

    def test_safe_deferral_missing_deferral_reason_falls_back(self):
        bad = json.dumps({"proposed_action": "safe_deferral", "target_device": "none"})
        adapter = _mock_adapter(bad)
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.is_fallback is True

    def test_light_on_with_none_target_falls_back(self):
        bad = json.dumps({"proposed_action": "light_on", "target_device": "none"})
        adapter = _mock_adapter(bad)
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.is_fallback is True

    def test_unparseable_json_falls_back(self):
        adapter = _mock_adapter("거실 조명을 켜는 것이 좋겠습니다.")
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.is_fallback is True
        assert result.proposed_action == "safe_deferral"

    def test_empty_response_falls_back(self):
        adapter = _mock_adapter("")
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.is_fallback is True

    def test_fallback_candidate_is_safe_deferral(self):
        adapter = _mock_adapter("not json at all")
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.candidate["proposed_action"] == "safe_deferral"
        assert result.candidate["target_device"] == "none"
        assert result.candidate["deferral_reason"] == "insufficient_context"

    def test_fallback_llm_boundary_unchanged(self):
        adapter = _mock_adapter("bad output")
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        lb = result.llm_boundary
        assert lb["candidate_generation_only"] is True
        assert lb["final_decision_allowed"] is False
        assert lb["actuation_authority_allowed"] is False
        assert lb["emergency_trigger_authority_allowed"] is False

    def test_exception_in_client_falls_back(self):
        class _FailClient:
            model_id = "fail"
            def complete(self, prompt): raise RuntimeError("network error")

        adapter = LocalLlmAdapter(llm_client=_FailClient())
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.is_fallback is True


# ------------------------------------------------------------------
# Markdown fence / prose wrapping
# ------------------------------------------------------------------

class TestJsonExtraction:
    def test_json_inside_markdown_fence(self):
        raw = "```json\n" + _valid_light_on_json() + "\n```"
        adapter = _mock_adapter(raw)
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.is_fallback is False
        assert result.proposed_action == "light_on"

    def test_json_inside_plain_fence(self):
        raw = "```\n" + _valid_light_on_json() + "\n```"
        adapter = _mock_adapter(raw)
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.is_fallback is False

    def test_json_embedded_in_prose(self):
        raw = "알겠습니다. 다음과 같이 제안합니다:\n" + _valid_light_on_json() + "\n이상입니다."
        adapter = _mock_adapter(raw)
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.is_fallback is False
        assert result.proposed_action == "light_on"


# ------------------------------------------------------------------
# LLM boundary constants
# ------------------------------------------------------------------

class TestLlmBoundary:
    def test_boundary_candidate_generation_only(self):
        adapter = _mock_adapter(_valid_light_on_json())
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.llm_boundary["candidate_generation_only"] is True

    def test_boundary_no_final_decision(self):
        adapter = _mock_adapter(_valid_light_on_json())
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.llm_boundary["final_decision_allowed"] is False

    def test_boundary_no_actuation_authority(self):
        adapter = _mock_adapter(_valid_light_on_json())
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.llm_boundary["actuation_authority_allowed"] is False

    def test_boundary_no_emergency_authority(self):
        adapter = _mock_adapter(_valid_light_on_json())
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.llm_boundary["emergency_trigger_authority_allowed"] is False


# ------------------------------------------------------------------
# Prompt builder — masking and content
# ------------------------------------------------------------------

class TestPromptBuilder:
    def test_timestamp_not_in_prompt(self):
        ctx = _ctx()
        prompt = build_prompt(ctx, "single_click")
        assert "1710000000000" not in prompt

    def test_event_code_in_prompt(self):
        prompt = build_prompt(_ctx(), "double_click")
        assert "double_click" in prompt

    def test_temperature_in_prompt(self):
        prompt = build_prompt(_ctx(temperature=30.5), "single_click")
        assert "30.5" in prompt

    def test_occupancy_in_prompt(self):
        prompt = build_prompt(_ctx(occupancy=True), "single_click")
        assert "True" in prompt or "true" in prompt.lower()

    def test_doorbell_framed_as_visitor_context(self):
        prompt = build_prompt(_ctx(doorbell=True), "single_click")
        assert "도어벨" in prompt or "방문자" in prompt

    def test_device_states_in_prompt(self):
        prompt = build_prompt(_ctx(living_room_light="on"), "single_click")
        assert "living_room_light" in prompt

    def test_routing_metadata_not_in_prompt(self):
        ctx = _ctx()
        ctx["routing_metadata"] = {"network_status": "online", "source_node": "esp32"}
        prompt = build_prompt(ctx, "single_click")
        assert "routing_metadata" not in prompt
        assert "network_status" not in prompt

    def test_event_code_override(self):
        adapter = _mock_adapter(_valid_light_on_json())
        # event_code supplied explicitly should override what's in the payload
        result = adapter.generate_candidate(_ctx(event_code="long_press"), AUDIT_ID,
                                            event_code="single_click")
        assert result.is_fallback is False

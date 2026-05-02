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

    def test_light_on_with_empty_deferral_reason_is_accepted(self):
        # Real Ollama llama3.2 reproducibly emits `deferral_reason: ""` for
        # light_on/light_off responses (it follows the prompt's JSON example
        # too literally). The schema's `not.required: ["deferral_reason"]`
        # clause for non-deferral actions would otherwise reject this and
        # force a 100% fallback rate in production. _parse_and_validate
        # treats "" as field-absent (parallel to its None handling).
        with_empty = json.dumps({
            "proposed_action": "light_on",
            "target_device": "living_room_light",
            "rationale_summary": "lights off, user requested on",
            "deferral_reason": "",
        })
        adapter = _mock_adapter(with_empty)
        result = adapter.generate_candidate(_ctx(), AUDIT_ID)
        assert result.is_fallback is False
        assert result.proposed_action == "light_on"
        assert result.target_device == "living_room_light"
        assert "deferral_reason" not in result.candidate


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


# ==================================================================
# generate_class2_candidates (Phase 1 of LLM-driven Class 2 plan)
# ==================================================================

import json as _json


def _class2_response(*candidates) -> str:
    return _json.dumps({"candidates": list(candidates)})


def _valid_lighting_candidate() -> dict:
    return {
        "candidate_id": "C1_LIGHTING_ASSISTANCE",
        "prompt": "거실 조명을 켜드릴까요?",
        "candidate_transition_target": "CLASS_1",
        "action_hint": "light_on",
        "target_hint": "living_room_light",
    }


def _valid_caregiver_candidate() -> dict:
    return {
        "candidate_id": "C2_CAREGIVER_HELP",
        "prompt": "보호자에게 알려드릴까요?",
        "candidate_transition_target": "CAREGIVER_CONFIRMATION",
        "action_hint": None,
        "target_hint": None,
    }


class TestGenerateClass2Candidates:
    """LocalLlmAdapter.generate_class2_candidates produces a bounded candidate
    set or returns a default_fallback signalling the manager to use its
    static _DEFAULT_CANDIDATES table."""

    def test_valid_llm_set_is_accepted(self):
        adapter = _mock_adapter(_class2_response(
            _valid_lighting_candidate(), _valid_caregiver_candidate(),
        ))
        result = adapter.generate_class2_candidates(
            _ctx(event_code="double_click"),
            unresolved_reason="insufficient_context",
            max_candidates=4,
            audit_correlation_id=AUDIT_ID,
        )
        assert result.candidate_source == "llm_generated"
        assert result.is_usable is True
        assert len(result.candidates) == 2
        assert result.candidates[0]["candidate_id"] == "C1_LIGHTING_ASSISTANCE"
        assert result.candidates[0]["target_hint"] == "living_room_light"
        # bounded-variability constraints echoed
        assert result.prompt_constraints_applied["max_prompt_length_chars"] == 80
        assert result.prompt_constraints_applied["prompt_must_be_question"] is True

    def test_invalid_json_falls_back(self):
        adapter = _mock_adapter("this is not json")
        result = adapter.generate_class2_candidates(
            _ctx(), "insufficient_context", 4, AUDIT_ID,
        )
        assert result.candidate_source == "default_fallback"
        assert result.candidates == []
        assert result.rejection_reason == "invalid_json"

    def test_oversized_prompt_drops_candidate(self):
        bad = _valid_lighting_candidate()
        bad["prompt"] = "정말 정말 정말 " * 30 + "켜드릴까요?"  # > 80 chars
        adapter = _mock_adapter(_class2_response(bad, _valid_caregiver_candidate()))
        result = adapter.generate_class2_candidates(
            _ctx(), "insufficient_context", 4, AUDIT_ID,
        )
        assert result.candidate_source == "llm_generated"
        # bad lighting dropped, caregiver kept
        assert all(c["candidate_id"] != "C1_LIGHTING_ASSISTANCE" for c in result.candidates)
        assert any(c["candidate_id"] == "C2_CAREGIVER_HELP" for c in result.candidates)

    def test_non_question_prompt_dropped(self):
        bad = _valid_lighting_candidate()
        bad["prompt"] = "거실 조명을 켜겠습니다"  # statement, not question
        adapter = _mock_adapter(_class2_response(bad, _valid_caregiver_candidate()))
        result = adapter.generate_class2_candidates(
            _ctx(), "insufficient_context", 4, AUDIT_ID,
        )
        assert all(c["candidate_id"] != "C1_LIGHTING_ASSISTANCE" for c in result.candidates)

    def test_action_hint_outside_catalog_dropped(self):
        bad = _valid_lighting_candidate()
        bad["action_hint"] = "door_unlock"  # not in low_risk_actions
        bad["target_hint"] = "front_door_lock"
        adapter = _mock_adapter(_class2_response(bad, _valid_caregiver_candidate()))
        result = adapter.generate_class2_candidates(
            _ctx(), "insufficient_context", 4, AUDIT_ID,
        )
        ids = [c["candidate_id"] for c in result.candidates]
        assert "C1_LIGHTING_ASSISTANCE" not in ids

    def test_target_hint_outside_action_targets_dropped(self):
        bad = _valid_lighting_candidate()
        bad["target_hint"] = "tv_main"  # light_on doesn't allow tv_main
        adapter = _mock_adapter(_class2_response(bad, _valid_caregiver_candidate()))
        result = adapter.generate_class2_candidates(
            _ctx(), "insufficient_context", 4, AUDIT_ID,
        )
        ids = [c["candidate_id"] for c in result.candidates]
        assert "C1_LIGHTING_ASSISTANCE" not in ids

    def test_forbidden_phrasing_dropped(self):
        bad = _valid_lighting_candidate()
        bad["prompt"] = "도어락을 풀어드릴까요?"  # contains "도어락" forbidden token
        adapter = _mock_adapter(_class2_response(bad, _valid_caregiver_candidate()))
        result = adapter.generate_class2_candidates(
            _ctx(), "insufficient_context", 4, AUDIT_ID,
        )
        ids = [c["candidate_id"] for c in result.candidates]
        assert "C1_LIGHTING_ASSISTANCE" not in ids

    def test_class0_normalized_to_fixed_template(self):
        invented = {
            "candidate_id": "C_INVENTED_EMERGENCY",
            "prompt": "강도가 들어왔다고 보고 비상 출동시킬까요?",
            "candidate_transition_target": "CLASS_0",
            "action_hint": None,
            "target_hint": None,
        }
        adapter = _mock_adapter(_class2_response(_valid_lighting_candidate(), invented))
        result = adapter.generate_class2_candidates(
            _ctx(), "insufficient_context", 4, AUDIT_ID,
        )
        # The CLASS_0 entry must be collapsed to the safe template
        c0 = [c for c in result.candidates if c["candidate_transition_target"] == "CLASS_0"]
        assert len(c0) == 1
        assert c0[0]["candidate_id"] == "C3_EMERGENCY_HELP"
        assert c0[0]["prompt"] == "긴급상황인가요?"

    def test_caregiver_first_invariant_for_sensitive_path(self):
        """unresolved_reason=caregiver_required_sensitive_path must put a
        caregiver candidate first; if not present at all, fall back."""
        adapter = _mock_adapter(_class2_response(
            _valid_lighting_candidate(),  # CLASS_1 first
            _valid_caregiver_candidate(),
        ))
        result = adapter.generate_class2_candidates(
            _ctx(event_type="sensor", event_code="doorbell_detected"),
            "caregiver_required_sensitive_path",
            4, AUDIT_ID,
        )
        assert result.candidate_source == "llm_generated"
        assert result.candidates[0]["candidate_transition_target"] == "CAREGIVER_CONFIRMATION"

    def test_caregiver_required_with_no_caregiver_falls_back(self):
        adapter = _mock_adapter(_class2_response(_valid_lighting_candidate()))
        result = adapter.generate_class2_candidates(
            _ctx(),
            "caregiver_required_sensitive_path",
            4, AUDIT_ID,
        )
        assert result.candidate_source == "default_fallback"
        assert result.rejection_reason == "caregiver_first_violation"

    def test_max_candidates_enforced(self):
        """max_candidates from the manager caps the LLM output."""
        many = [_valid_caregiver_candidate() | {"candidate_id": f"C_{i}"} for i in range(6)]
        adapter = _mock_adapter(_class2_response(*many))
        result = adapter.generate_class2_candidates(
            _ctx(), "insufficient_context", max_candidates=2, audit_correlation_id=AUDIT_ID,
        )
        assert len(result.candidates) <= 2

    def test_empty_candidates_array_falls_back(self):
        adapter = _mock_adapter(_class2_response())  # candidates: []
        result = adapter.generate_class2_candidates(
            _ctx(), "insufficient_context", 4, AUDIT_ID,
        )
        assert result.candidate_source == "default_fallback"
        assert result.rejection_reason == "no_candidates_array"

    def test_safe_deferral_candidate_strips_actuation_hints(self):
        """Even if the LLM puts action_hint on a SAFE_DEFERRAL candidate, the
        adapter must clear it — only CLASS_1 candidates carry actuation hints."""
        sd = {
            "candidate_id": "C4_CANCEL_OR_WAIT",
            "prompt": "취소하고 대기할까요?",
            "candidate_transition_target": "SAFE_DEFERRAL",
            "action_hint": "light_on",
            "target_hint": "living_room_light",
        }
        adapter = _mock_adapter(_class2_response(sd))
        result = adapter.generate_class2_candidates(
            _ctx(), "insufficient_context", 4, AUDIT_ID,
        )
        assert result.candidates[0]["action_hint"] is None
        assert result.candidates[0]["target_hint"] is None


# ==================================================================
# Phase 3 — bounded-variability constraints loaded from policy_table
# ==================================================================

class TestClass2PromptConstraintsFromPolicy:
    """LocalLlmAdapter.__init__ must load
    global_constraints.class2_conversational_prompt_constraints from
    policy_table.json. Falls back to module defaults when the block is
    absent (older policy version)."""

    def test_constraints_loaded_from_policy_table(self):
        """The shipped policy_table includes the block; the adapter exposes it."""
        adapter = _mock_adapter("{}")
        c = adapter._class2_prompt_constraints
        assert c["max_prompt_length_chars"] == 80
        assert c["prompt_must_be_question"] is True
        assert c["vocabulary_tier"] == "plain_korean"
        # forbidden_phrasings must include both Korean and English doorlock tokens
        assert "도어락" in c["forbidden_phrasings"]
        assert "doorlock" in c["forbidden_phrasings"]
        # max_candidate_count comes from the sibling class2_max_candidate_options
        assert c["max_candidate_count"] == 4
        # The "_description" annotation in policy_table must NOT survive
        assert all(not k.startswith("_") for k in c.keys())

    def test_constraints_echoed_in_result_metadata(self):
        adapter = _mock_adapter(_class2_response(_valid_lighting_candidate()))
        result = adapter.generate_class2_candidates(
            _ctx(), "insufficient_context", 4, AUDIT_ID,
        )
        echoed = result.prompt_constraints_applied
        # Echoed constraints must match the loaded policy values
        for key in ("max_prompt_length_chars", "prompt_must_be_question",
                     "vocabulary_tier", "forbidden_phrasings"):
            assert echoed[key] == adapter._class2_prompt_constraints[key]

    def test_falls_back_when_policy_block_absent(self, tmp_path, monkeypatch):
        """If the policy_table lacks class2_conversational_prompt_constraints,
        the adapter must use the hardcoded fallback so it stays operational
        on older policy versions."""
        from local_llm_adapter.adapter import (
            LocalLlmAdapter,
            _CLASS2_PROMPT_CONSTRAINTS_FALLBACK,
        )
        from shared.asset_loader import AssetLoader

        # Build a minimal stand-in AssetLoader whose policy_table has no
        # class2_conversational_prompt_constraints block.
        real = AssetLoader()

        class _StubLoader:
            def load_schema(self, name): return real.load_schema(name)
            def make_schema_resolver(self): return real.make_schema_resolver()
            def load_low_risk_actions(self): return real.load_low_risk_actions()
            def load_policy_table(self):
                return {
                    "global_constraints": {
                        "class2_max_candidate_options": 4,
                    },
                }

        adapter = LocalLlmAdapter(
            llm_client=MockLlmClient(fixed_response="{}"),
            asset_loader=_StubLoader(),
        )
        for k, v in _CLASS2_PROMPT_CONSTRAINTS_FALLBACK.items():
            assert adapter._class2_prompt_constraints[k] == v
        # And max_candidate_count still comes from class2_max_candidate_options
        assert adapter._class2_prompt_constraints["max_candidate_count"] == 4

    def test_policy_constraints_actually_gate_validation(self, monkeypatch):
        """A tightened policy max_prompt_length_chars must force candidate rejection
        even for prompts that were acceptable under the previous cap."""
        from local_llm_adapter.adapter import LocalLlmAdapter
        from shared.asset_loader import AssetLoader
        real = AssetLoader()

        class _StubLoader:
            def load_schema(self, name): return real.load_schema(name)
            def make_schema_resolver(self): return real.make_schema_resolver()
            def load_low_risk_actions(self): return real.load_low_risk_actions()
            def load_policy_table(self):
                return {
                    "global_constraints": {
                        "class2_max_candidate_options": 4,
                        "class2_conversational_prompt_constraints": {
                            "max_prompt_length_chars": 5,  # very tight
                            "prompt_must_be_question": True,
                            "vocabulary_tier": "plain_korean",
                            "forbidden_phrasings": [],
                        },
                    },
                }

        adapter = LocalLlmAdapter(
            llm_client=MockLlmClient(
                fixed_response=_class2_response(_valid_lighting_candidate())
            ),
            asset_loader=_StubLoader(),
        )
        result = adapter.generate_class2_candidates(
            _ctx(), "insufficient_context", 4, AUDIT_ID,
        )
        # Lighting candidate prompt is much longer than 5 chars → rejected.
        # No other candidates → fallback.
        assert result.candidate_source == "default_fallback"

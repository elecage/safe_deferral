"""Tests for Class2ClarificationManager (MM-06)."""

import pytest

from class2_clarification_manager.manager import Class2ClarificationManager
from safe_deferral_handler.models import SessionStatus, TransitionTarget

AUDIT_ID = "test_audit_001"


@pytest.fixture(scope="module")
def manager():
    return Class2ClarificationManager()


# ------------------------------------------------------------------
# Session creation — trigger_id mapping
# ------------------------------------------------------------------

class TestSessionCreation:
    @pytest.mark.parametrize("trigger_id,expected_reason", [
        ("C201", "insufficient_context"),
        ("C202", "missing_policy_input"),
        ("C203", "unresolved_context_conflict"),
        ("C204", "sensor_staleness_detected"),
        ("C205", "actuation_ack_timeout"),
        ("C206", "insufficient_context"),
        ("C207", "timeout_or_no_response"),
        ("deferral_timeout", "timeout_or_no_response"),
    ])
    def test_trigger_id_mapped_to_unresolved_reason(self, manager, trigger_id, expected_reason):
        session = manager.start_session(trigger_id, AUDIT_ID)
        assert session.deferral_reason == expected_reason

    def test_unknown_trigger_id_falls_back_to_insufficient_context(self, manager):
        session = manager.start_session("C999", AUDIT_ID)
        assert session.deferral_reason == "insufficient_context"

    def test_candidate_count_within_policy_max(self, manager):
        for trigger_id in ("C202", "C203", "C204", "C206"):
            session = manager.start_session(trigger_id, AUDIT_ID)
            assert len(session.candidate_choices) <= 4

    def test_attempt_number_stored(self, manager):
        session = manager.start_session("C206", AUDIT_ID, attempt_number=2)
        assert session.attempt_number == 2

    def test_custom_clarification_id(self, manager):
        session = manager.start_session("C206", AUDIT_ID, clarification_id="c2-id-001")
        assert session.clarification_id == "c2-id-001"

    def test_audit_correlation_id_preserved(self, manager):
        session = manager.start_session("C206", "my-audit-abc")
        assert session.audit_correlation_id == "my-audit-abc"

    def test_custom_candidate_choices_override_defaults(self, manager):
        custom = [{"candidate_id": "MY_C1", "prompt": "Test", "candidate_transition_target": "CLASS_1",
                   "action_hint": "light_on", "target_hint": "bedroom_light"}]
        session = manager.start_session("C206", AUDIT_ID, candidate_choices=custom)
        assert len(session.candidate_choices) == 1
        assert session.candidate_choices[0].candidate_id == "MY_C1"


# ------------------------------------------------------------------
# Default candidate shape
# ------------------------------------------------------------------

class TestDefaultCandidates:
    def test_insufficient_context_has_class0_option(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        targets = {c.candidate_transition_target for c in session.candidate_choices}
        assert "CLASS_0" in targets

    def test_insufficient_context_has_class1_option(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        targets = {c.candidate_transition_target for c in session.candidate_choices}
        assert "CLASS_1" in targets

    def test_sensor_staleness_no_class1_option(self, manager):
        """Stale sensors should not offer a direct low-risk action path."""
        session = manager.start_session("C204", AUDIT_ID)
        targets = {c.candidate_transition_target for c in session.candidate_choices}
        assert "CLASS_1" not in targets

    def test_timeout_reason_no_class0_option(self, manager):
        """Repeated timeout → don't offer emergency path by default."""
        session = manager.start_session("C207", AUDIT_ID)
        targets = {c.candidate_transition_target for c in session.candidate_choices}
        assert "CLASS_0" not in targets

    def test_all_choices_require_confirmation(self, manager):
        for trigger_id in ("C202", "C203", "C206"):
            session = manager.start_session(trigger_id, AUDIT_ID)
            for c in session.candidate_choices:
                assert c.to_schema_dict()["requires_confirmation"] is True


# ------------------------------------------------------------------
# Selection → CLASS_1
# ------------------------------------------------------------------

class TestSelectionClass1:
    def test_class1_candidate_gives_class1_transition(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        c1 = next(c for c in session.candidate_choices if c.candidate_transition_target == "CLASS_1")
        result = manager.submit_selection(session, c1.candidate_id, "bounded_input_node", trigger_id="C206")
        assert result.transition_target == TransitionTarget.CLASS_1
        assert result.should_notify_caregiver is False
        assert result.notification_payload is None

    def test_class1_with_target_hint_is_ready(self, manager):
        custom = [{"candidate_id": "C1", "prompt": "거실?", "candidate_transition_target": "CLASS_1",
                   "action_hint": "light_on", "target_hint": "living_room_light"}]
        session = manager.start_session("C206", AUDIT_ID, candidate_choices=custom)
        result = manager.submit_selection(session, "C1", "bounded_input_node", trigger_id="C206")
        assert result.is_class1_ready is True
        assert result.action_hint == "light_on"
        assert result.target_hint == "living_room_light"

    def test_session_status_selected(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        c1 = next(c for c in session.candidate_choices if c.candidate_transition_target == "CLASS_1")
        manager.submit_selection(session, c1.candidate_id, "bounded_input_node", trigger_id="C206")
        assert session.status == SessionStatus.SELECTED


# ------------------------------------------------------------------
# Selection → CLASS_0
# ------------------------------------------------------------------

class TestSelectionClass0:
    def test_emergency_candidate_gives_class0_transition(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        c0 = next(c for c in session.candidate_choices if c.candidate_transition_target == "CLASS_0")
        result = manager.submit_selection(session, c0.candidate_id, "bounded_input_node", trigger_id="C206")
        assert result.transition_target == TransitionTarget.CLASS_0
        assert result.should_notify_caregiver is False

    def test_class0_llm_boundary_in_record(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        c0 = next(c for c in session.candidate_choices if c.candidate_transition_target == "CLASS_0")
        result = manager.submit_selection(session, c0.candidate_id, "bounded_input_node", trigger_id="C206")
        lb = result.clarification_record["llm_boundary"]
        assert lb["emergency_trigger_authority_allowed"] is False


# ------------------------------------------------------------------
# Selection → caregiver / safe deferral
# ------------------------------------------------------------------

class TestSelectionEscalation:
    def test_caregiver_candidate_escalates(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        cg = next(c for c in session.candidate_choices if c.candidate_transition_target == "CAREGIVER_CONFIRMATION")
        result = manager.submit_selection(session, cg.candidate_id, "bounded_input_node",
                                          trigger_id="C206", context_summary="거실 조명 요청")
        assert result.transition_target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
        assert result.should_notify_caregiver is True
        assert result.notification_payload is not None

    def test_cancel_candidate_escalates(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        cancel = next(c for c in session.candidate_choices if c.candidate_transition_target == "SAFE_DEFERRAL")
        result = manager.submit_selection(session, cancel.candidate_id, "bounded_input_node",
                                          trigger_id="C206")
        assert result.transition_target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
        assert result.should_notify_caregiver is True

    def test_unknown_candidate_id_treated_as_timeout(self, manager):
        """Unknown selection must never be treated as consent."""
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.submit_selection(session, "DOES_NOT_EXIST", "bounded_input_node", trigger_id="C206")
        assert result.transition_target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
        assert result.should_notify_caregiver is True


# ------------------------------------------------------------------
# Timeout / no-response
# ------------------------------------------------------------------

class TestTimeout:
    def test_timeout_escalates_to_caregiver(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.handle_timeout(session, trigger_id="C207")
        assert result.transition_target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
        assert result.should_notify_caregiver is True
        assert result.action_hint is None
        assert result.target_hint is None

    def test_timeout_never_assumes_intent(self, manager):
        session = manager.start_session("C202", AUDIT_ID)
        result = manager.handle_timeout(session, trigger_id="C207")
        assert result.transition_target != TransitionTarget.CLASS_1
        assert result.transition_target != TransitionTarget.CLASS_0

    def test_timeout_session_status_timed_out(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        manager.handle_timeout(session)
        assert session.status == SessionStatus.TIMED_OUT

    def test_timeout_preserves_candidate_choices_in_record(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        n = len(session.candidate_choices)
        result = manager.handle_timeout(session)
        assert len(result.clarification_record["candidate_choices"]) == n


# ------------------------------------------------------------------
# Retry logic
# ------------------------------------------------------------------

class TestRetry:
    def test_can_retry_within_max_attempts(self, manager):
        session = manager.start_session("C206", AUDIT_ID, attempt_number=1)
        assert manager.can_retry(session) is True

    def test_cannot_retry_at_max_attempts(self, manager):
        session = manager.start_session("C206", AUDIT_ID, attempt_number=2)
        assert manager.can_retry(session) is False

    def test_cannot_retry_beyond_max_attempts(self, manager):
        session = manager.start_session("C206", AUDIT_ID, attempt_number=3)
        assert manager.can_retry(session) is False

    def test_retry_session_increments_attempt(self, manager):
        session1 = manager.start_session("C206", AUDIT_ID, attempt_number=1)
        # Caller creates a new session with incremented attempt
        session2 = manager.start_session("C206", AUDIT_ID, attempt_number=session1.attempt_number + 1)
        assert session2.attempt_number == 2


# ------------------------------------------------------------------
# Notification payload
# ------------------------------------------------------------------

class TestNotificationPayload:
    def test_notification_has_required_fields(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.handle_timeout(session, trigger_id="C206", context_summary="온도 22도, 거실 조명 꺼짐")
        n = result.notification_payload
        assert n is not None
        for field in ("event_summary", "context_summary", "unresolved_reason", "manual_confirmation_path"):
            assert field in n, f"missing field: {field}"

    def test_notification_context_summary_passed_through(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.handle_timeout(session, context_summary="거실 조명 꺼짐, 점유 감지됨")
        assert "거실" in result.notification_payload["context_summary"]

    def test_notification_exception_trigger_id_c201_to_c207(self, manager):
        for trigger_id in ("C201", "C202", "C203", "C204", "C205", "C206", "C207"):
            session = manager.start_session(trigger_id, AUDIT_ID)
            result = manager.handle_timeout(session, trigger_id=trigger_id)
            assert result.notification_payload["exception_trigger_id"] == trigger_id

    def test_notification_not_emitted_on_class1_selection(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        c1 = next(c for c in session.candidate_choices if c.candidate_transition_target == "CLASS_1")
        result = manager.submit_selection(session, c1.candidate_id, "bounded_input_node", trigger_id="C206")
        assert result.notification_payload is None


# ------------------------------------------------------------------
# Clarification record schema shape
# ------------------------------------------------------------------

class TestClarificationRecord:
    def test_record_required_fields_present(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.handle_timeout(session)
        record = result.clarification_record
        for field in ("clarification_id", "unresolved_reason", "candidate_choices",
                      "transition_target", "llm_boundary"):
            assert field in record

    def test_record_source_layer_is_manager(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.handle_timeout(session)
        assert result.clarification_record["source_layer"] == "class2_clarification_manager"

    def test_record_llm_boundary_correct(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.handle_timeout(session)
        lb = result.clarification_record["llm_boundary"]
        assert lb["candidate_generation_only"] is True
        assert lb["final_decision_allowed"] is False
        assert lb["actuation_authority_allowed"] is False
        assert lb["emergency_trigger_authority_allowed"] is False


# ------------------------------------------------------------------
# C208 — visitor/doorlock-sensitive path
# ------------------------------------------------------------------

class TestC208VisitorContext:
    def test_c208_reason_is_caregiver_required_sensitive_path(self, manager):
        session = manager.start_session("C208", AUDIT_ID)
        assert session.deferral_reason == "caregiver_required_sensitive_path"

    def test_c208_first_candidate_is_caregiver_not_lighting(self, manager):
        """C208 must NOT offer lighting assistance as first choice."""
        session = manager.start_session("C208", AUDIT_ID)
        first = session.candidate_choices[0]
        assert first.candidate_transition_target == "CAREGIVER_CONFIRMATION"
        assert "C1_LIGHTING" not in first.candidate_id

    def test_c208_candidate_set_has_no_lighting_action(self, manager):
        session = manager.start_session("C208", AUDIT_ID)
        lighting_ids = [c for c in session.candidate_choices if c.action_hint == "light_on"]
        assert lighting_ids == []

    def test_c208_summary_mentions_doorlock_sensitive_path(self, manager):
        session = manager.start_session("C208", AUDIT_ID)
        result = manager.handle_timeout(session, trigger_id="C208")
        summary = result.notification_payload["event_summary"]
        assert "C208" not in summary or "도어락" in summary or "방문자" in summary

    def test_c208_record_unresolved_reason(self, manager):
        session = manager.start_session("C208", AUDIT_ID)
        result = manager.handle_timeout(session, trigger_id="C208")
        assert result.clarification_record["unresolved_reason"] == "caregiver_required_sensitive_path"

    def test_c208_notification_passes_schema(self, manager):
        """C208 timeout notification must validate against
        class2_notification_payload_schema (Issue #1 of 2026-05-01 follow-up)."""
        import jsonschema
        from shared.asset_loader import AssetLoader
        loader = AssetLoader()
        schema = loader.load_schema("class2_notification_payload_schema.json")
        session = manager.start_session("C208", AUDIT_ID)
        result = manager.handle_timeout(session, trigger_id="C208")
        # Should not raise
        jsonschema.validate(result.notification_payload, schema)
        # exception_trigger_id MUST be present and equal to C208 (not None)
        assert result.notification_payload.get("exception_trigger_id") == "C208"

    def test_non_canonical_trigger_omits_exception_trigger_id(self, manager):
        """deferral_timeout / arbitrary trigger IDs must omit the field entirely
        rather than emit None (which fails type=string in the schema)."""
        import jsonschema
        from shared.asset_loader import AssetLoader
        loader = AssetLoader()
        schema = loader.load_schema("class2_notification_payload_schema.json")
        session = manager.start_session("deferral_timeout", AUDIT_ID)
        result = manager.handle_timeout(session, trigger_id="deferral_timeout")
        assert "exception_trigger_id" not in result.notification_payload
        jsonschema.validate(result.notification_payload, schema)


# ------------------------------------------------------------------
# selection_source normalisation to schema enum
# ------------------------------------------------------------------

_SCHEMA_ALLOWED_SOURCES = {
    "bounded_input_node", "voice_input", "caregiver_confirmation",
    "deterministic_emergency_evidence", "timeout_or_no_response", "none",
}


class TestSelectionSourceNormalisation:
    def _first_c1_candidate(self, session):
        return next(
            c for c in session.candidate_choices
            if c.candidate_transition_target == "CLASS_1"
        )

    def test_user_mqtt_button_maps_to_bounded_input_node(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        c = self._first_c1_candidate(session)
        result = manager.submit_selection(session, c.candidate_id, "user_mqtt_button", trigger_id="C206")
        src = result.clarification_record["selection_result"]["selection_source"]
        assert src == "bounded_input_node"
        assert src in _SCHEMA_ALLOWED_SOURCES

    def test_user_mqtt_button_late_maps_to_bounded_input_node(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        c = self._first_c1_candidate(session)
        result = manager.submit_selection(session, c.candidate_id, "user_mqtt_button_late", trigger_id="C206")
        src = result.clarification_record["selection_result"]["selection_source"]
        assert src == "bounded_input_node"
        assert src in _SCHEMA_ALLOWED_SOURCES

    def test_caregiver_telegram_maps_to_caregiver_confirmation(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        c = self._first_c1_candidate(session)
        result = manager.submit_selection(
            session, c.candidate_id, "caregiver_telegram_inline_keyboard", trigger_id="C206"
        )
        src = result.clarification_record["selection_result"]["selection_source"]
        assert src == "caregiver_confirmation"
        assert src in _SCHEMA_ALLOWED_SOURCES

    def test_timeout_source_passes_through_unchanged(self, manager):
        session = manager.start_session("C206", AUDIT_ID)
        result = manager.handle_timeout(session, trigger_id="C206")
        src = result.clarification_record["selection_result"]["selection_source"]
        assert src == "timeout_or_no_response"
        assert src in _SCHEMA_ALLOWED_SOURCES

    def test_all_runtime_sources_normalise_to_schema_enum(self, manager):
        """All source strings that main.py passes must produce schema-allowed values."""
        runtime_sources = [
            "user_mqtt_button",
            "user_mqtt_button_late",
            "caregiver_telegram_inline_keyboard",
            "timeout_or_no_response",
        ]
        session = manager.start_session("C206", AUDIT_ID)
        c = self._first_c1_candidate(session)
        for src in runtime_sources:
            s2 = manager.start_session("C206", AUDIT_ID)
            result = manager.submit_selection(s2, c.candidate_id, src, trigger_id="C206")
            mapped = result.clarification_record["selection_result"]["selection_source"]
            assert mapped in _SCHEMA_ALLOWED_SOURCES, f"{src!r} → {mapped!r} not in schema enum"


# ------------------------------------------------------------------
# clarification_interaction_schema.json validation against actual records
# ------------------------------------------------------------------

class TestClarificationRecordSchemaCompliance:
    """Validate that published clarification_records pass jsonschema validation."""

    @pytest.fixture(scope="class")
    def schema_and_resolver(self):
        from shared.asset_loader import AssetLoader
        loader = AssetLoader()
        schema = loader.load_schema("clarification_interaction_schema.json")
        resolver = loader.make_schema_resolver()
        return schema, resolver

    def _validate(self, record, schema_and_resolver):
        import jsonschema
        schema, resolver = schema_and_resolver
        validator = jsonschema.Draft7Validator(schema=schema, resolver=resolver)
        errors = list(validator.iter_errors(record))
        return errors

    def test_timeout_record_passes_schema_for_every_trigger(self, manager, schema_and_resolver):
        for trigger_id in ("C201", "C202", "C203", "C204", "C205", "C206", "C207", "C208"):
            session = manager.start_session(trigger_id, AUDIT_ID)
            result = manager.handle_timeout(session, trigger_id=trigger_id)
            errors = self._validate(result.clarification_record, schema_and_resolver)
            assert not errors, (
                f"trigger={trigger_id} clarification_record failed schema: "
                + "; ".join(e.message for e in errors)
            )

    def test_user_selection_record_passes_schema(self, manager, schema_and_resolver):
        session = manager.start_session("C206", AUDIT_ID)
        c1 = next(c for c in session.candidate_choices if c.candidate_transition_target == "CLASS_1")
        result = manager.submit_selection(
            session, c1.candidate_id, "user_mqtt_button", trigger_id="C206"
        )
        errors = self._validate(result.clarification_record, schema_and_resolver)
        assert not errors, "; ".join(e.message for e in errors)

    def test_caregiver_selection_record_passes_schema(self, manager, schema_and_resolver):
        session = manager.start_session("C208", AUDIT_ID)
        cg = next(c for c in session.candidate_choices
                  if c.candidate_transition_target == "CAREGIVER_CONFIRMATION")
        result = manager.submit_selection(
            session, cg.candidate_id, "caregiver_telegram_inline_keyboard", trigger_id="C208"
        )
        errors = self._validate(result.clarification_record, schema_and_resolver)
        assert not errors, "; ".join(e.message for e in errors)

    def test_c208_unresolved_reason_in_schema_enum(self, manager, schema_and_resolver):
        """Regression: visitor_context_sensitive_actuation_required must NOT appear."""
        session = manager.start_session("C208", AUDIT_ID)
        result = manager.handle_timeout(session, trigger_id="C208")
        reason = result.clarification_record["unresolved_reason"]
        assert reason != "visitor_context_sensitive_actuation_required", (
            "C208 must map to caregiver_required_sensitive_path, not the policy-layer string"
        )
        errors = self._validate(result.clarification_record, schema_and_resolver)
        assert not errors, "; ".join(e.message for e in errors)


# ==================================================================
# LLM-driven candidate generation hook (Phase 2 of LLM-driven plan)
# ==================================================================

class _StubLlmGenerator:
    """In-memory stand-in for LocalLlmAdapter.generate_class2_candidates.

    The real adapter would call out to Ollama; tests use this so they don't
    block on a network round-trip and can exercise the manager's fallback
    contract precisely.
    """

    def __init__(self, candidates=None, raise_exc=None):
        self._candidates = candidates
        self._raise_exc = raise_exc
        self.calls = []

    def generate_class2_candidates(
        self, pure_context_payload, unresolved_reason, max_candidates,
        audit_correlation_id="",
    ):
        self.calls.append({
            "pure_context_payload": pure_context_payload,
            "unresolved_reason": unresolved_reason,
            "max_candidates": max_candidates,
            "audit_correlation_id": audit_correlation_id,
        })
        if self._raise_exc is not None:
            raise self._raise_exc

        from local_llm_adapter.models import Class2CandidateResult
        if self._candidates is None:
            # Simulate a default_fallback (LLM produced nothing usable)
            return Class2CandidateResult(
                candidates=[], candidate_source="default_fallback",
                generated_at_ms=0, model_id="static_default_fallback",
                rejection_reason="stub_no_candidates",
            )
        return Class2CandidateResult(
            candidates=self._candidates,
            candidate_source="llm_generated",
            generated_at_ms=0,
            model_id="stub-llm",
        )


class TestLlmCandidateGeneratorHook:
    def _llm_candidates(self):
        return [
            {
                "candidate_id": "LLM_C1_LIGHT",
                "prompt": "거실 조명을 켜드릴까요?",
                "candidate_transition_target": "CLASS_1",
                "action_hint": "light_on",
                "target_hint": "living_room_light",
            },
            {
                "candidate_id": "LLM_C2_CAREGIVER",
                "prompt": "보호자에게 알려드릴까요?",
                "candidate_transition_target": "CAREGIVER_CONFIRMATION",
                "action_hint": None,
                "target_hint": None,
            },
        ]

    def _ctx(self):
        return {
            "trigger_event": {"event_type": "button", "event_code": "double_click",
                              "timestamp_ms": 0},
            "environmental_context": {"temperature": 22, "illuminance": 50,
                                       "occupancy_detected": True,
                                       "smoke_detected": False, "gas_detected": False,
                                       "doorbell_detected": False},
            "device_states": {"living_room_light": "off", "bedroom_light": "off",
                              "living_room_blind": "open", "tv_main": "off"},
        }

    def test_llm_candidates_used_when_generator_present(self):
        stub = _StubLlmGenerator(candidates=self._llm_candidates())
        mgr = Class2ClarificationManager(llm_candidate_generator=stub)
        session = mgr.start_session(
            "C206", AUDIT_ID, pure_context_payload=self._ctx(),
        )
        ids = [c.candidate_id for c in session.candidate_choices]
        assert ids == ["LLM_C1_LIGHT", "LLM_C2_CAREGIVER"]
        assert getattr(session, "candidate_source") == "llm_generated"
        assert len(stub.calls) == 1
        assert stub.calls[0]["unresolved_reason"] == "insufficient_context"
        assert stub.calls[0]["audit_correlation_id"] == AUDIT_ID

    def test_falls_back_when_generator_returns_default(self):
        stub = _StubLlmGenerator(candidates=None)  # default_fallback shape
        mgr = Class2ClarificationManager(llm_candidate_generator=stub)
        session = mgr.start_session(
            "C206", AUDIT_ID, pure_context_payload=self._ctx(),
        )
        # Static defaults for insufficient_context start with C1_LIGHTING_ASSISTANCE
        assert session.candidate_choices[0].candidate_id == "C1_LIGHTING_ASSISTANCE"
        assert getattr(session, "candidate_source") == "default_fallback"

    def test_falls_back_when_generator_raises(self):
        stub = _StubLlmGenerator(raise_exc=RuntimeError("ollama down"))
        mgr = Class2ClarificationManager(llm_candidate_generator=stub)
        session = mgr.start_session(
            "C206", AUDIT_ID, pure_context_payload=self._ctx(),
        )
        assert session.candidate_choices[0].candidate_id == "C1_LIGHTING_ASSISTANCE"
        assert getattr(session, "candidate_source") == "default_fallback"

    def test_no_pure_context_means_no_llm_call(self):
        """Defensive: legacy callers omit pure_context_payload — manager must
        not attempt to call the LLM in that case."""
        stub = _StubLlmGenerator(candidates=self._llm_candidates())
        mgr = Class2ClarificationManager(llm_candidate_generator=stub)
        session = mgr.start_session("C206", AUDIT_ID)  # no pure_context_payload
        assert stub.calls == []
        assert getattr(session, "candidate_source") == "default_fallback"

    def test_explicit_candidates_override_skips_llm(self):
        """An explicit candidate_choices argument always wins."""
        stub = _StubLlmGenerator(candidates=self._llm_candidates())
        mgr = Class2ClarificationManager(llm_candidate_generator=stub)
        explicit = [{
            "candidate_id": "EXPLICIT", "prompt": "테스트?",
            "candidate_transition_target": "CLASS_1",
            "action_hint": "light_on", "target_hint": "living_room_light",
        }]
        session = mgr.start_session(
            "C206", AUDIT_ID,
            candidate_choices=explicit,
            pure_context_payload=self._ctx(),
        )
        assert stub.calls == []  # LLM not called
        assert session.candidate_choices[0].candidate_id == "EXPLICIT"

    def test_clarification_record_carries_candidate_source_llm(self):
        stub = _StubLlmGenerator(candidates=self._llm_candidates())
        mgr = Class2ClarificationManager(llm_candidate_generator=stub)
        session = mgr.start_session("C206", AUDIT_ID, pure_context_payload=self._ctx())
        result = mgr.submit_selection(session, "LLM_C1_LIGHT", "user_mqtt_button",
                                       trigger_id="C206")
        assert result.clarification_record["candidate_source"] == "llm_generated"

    def test_clarification_record_carries_candidate_source_fallback(self):
        # No LLM generator at all → default_fallback recorded
        mgr = Class2ClarificationManager()
        session = mgr.start_session("C206", AUDIT_ID, pure_context_payload=self._ctx())
        result = mgr.submit_selection(session, "C1_LIGHTING_ASSISTANCE",
                                       "user_mqtt_button", trigger_id="C206")
        assert result.clarification_record["candidate_source"] == "default_fallback"

    def test_refinement_disabled_by_default(self):
        """Phase 6.0 multi-turn is opt-in; default policy keeps the path off
        and submit_selection_or_refine behaves exactly like submit_selection."""
        mgr = Class2ClarificationManager()
        assert mgr._multi_turn_enabled is False
        # Picking C1_LIGHTING_ASSISTANCE (which DOES have a template) still
        # produces a terminal Class2Result because the flag is off.
        session = mgr.start_session("C206", AUDIT_ID, pure_context_payload=self._ctx())
        out = mgr.submit_selection_or_refine(
            session, "C1_LIGHTING_ASSISTANCE", "user_mqtt_button",
            trigger_id="C206",
        )
        from class2_clarification_manager.models import Class2Result
        assert isinstance(out, Class2Result)

    def test_static_only_mode_skips_llm_call(self):
        """Package A LLM-vs-static comparison (doc 10 §3.3 P2.3): when the
        runner sets candidate_source_mode='static_only', the manager must
        NOT call the LLM even if a generator and pure_context_payload are
        available. The session is recorded as static_only_forced so audit
        can distinguish 'forced static' from 'LLM tried and failed'."""
        stub = _StubLlmGenerator(candidates=self._llm_candidates())
        mgr = Class2ClarificationManager(llm_candidate_generator=stub)
        session = mgr.start_session(
            "C206", AUDIT_ID,
            pure_context_payload=self._ctx(),
            candidate_source_mode="static_only",
        )
        assert stub.calls == [], "LLM must not be called under static_only"
        assert session.candidate_choices[0].candidate_id == "C1_LIGHTING_ASSISTANCE"
        assert getattr(session, "candidate_source") == "static_only_forced"

    def test_llm_assisted_mode_keeps_default_behaviour(self):
        """candidate_source_mode='llm_assisted' is the existing default —
        LLM is consulted; outcome is 'llm_generated' when LLM succeeds."""
        stub = _StubLlmGenerator(candidates=self._llm_candidates())
        mgr = Class2ClarificationManager(llm_candidate_generator=stub)
        session = mgr.start_session(
            "C206", AUDIT_ID,
            pure_context_payload=self._ctx(),
            candidate_source_mode="llm_assisted",
        )
        assert len(stub.calls) == 1
        assert getattr(session, "candidate_source") == "llm_generated"

    def test_static_only_record_validates_against_schema(self):
        """The schema enum must include static_only_forced."""
        import jsonschema
        from shared.asset_loader import AssetLoader
        loader = AssetLoader()
        schema = loader.load_schema("clarification_interaction_schema.json")
        resolver = loader.make_schema_resolver()

        stub = _StubLlmGenerator(candidates=self._llm_candidates())
        mgr = Class2ClarificationManager(llm_candidate_generator=stub)
        session = mgr.start_session(
            "C206", AUDIT_ID, pure_context_payload=self._ctx(),
            candidate_source_mode="static_only",
        )
        result = mgr.submit_selection(session, "C1_LIGHTING_ASSISTANCE",
                                       "user_mqtt_button", trigger_id="C206")
        assert result.clarification_record["candidate_source"] == "static_only_forced"
        validator = jsonschema.Draft7Validator(schema, resolver=resolver)
        errors = list(validator.iter_errors(result.clarification_record))
        assert not errors, "; ".join(e.message for e in errors)

    def test_clarification_record_validates_against_schema(self):
        """candidate_source field is now in the clarification_interaction_schema —
        a record with it must still validate."""
        import jsonschema
        from shared.asset_loader import AssetLoader
        loader = AssetLoader()
        schema = loader.load_schema("clarification_interaction_schema.json")
        resolver = loader.make_schema_resolver()

        stub = _StubLlmGenerator(candidates=self._llm_candidates())
        mgr = Class2ClarificationManager(llm_candidate_generator=stub)
        session = mgr.start_session("C206", AUDIT_ID, pure_context_payload=self._ctx())
        result = mgr.submit_selection(session, "LLM_C1_LIGHT", "user_mqtt_button",
                                       trigger_id="C206")
        validator = jsonschema.Draft7Validator(schema, resolver=resolver)
        errors = list(validator.iter_errors(result.clarification_record))
        assert not errors, "; ".join(e.message for e in errors)


# ==================================================================
# P0.1 — _call_llm_with_budget thread + budget enforcement
# (10_llm_class2_integration_alignment_plan.md)
# ==================================================================

class _SlowStubGenerator:
    """Stub generator whose generate_class2_candidates() blocks for sleep_s
    before returning. Used to verify the manager's budget actually bounds
    the wait, not just the underlying HTTP timeout.
    """

    def __init__(self, sleep_s: float, candidates=None, raise_exc=None):
        import threading as _t
        self._sleep = sleep_s
        self._candidates = candidates
        self._raise_exc = raise_exc
        self.calls = 0
        self.completed = _t.Event()  # set when the runner thread actually finishes

    def generate_class2_candidates(self, **_kwargs):
        import time as _time
        from local_llm_adapter.models import Class2CandidateResult
        self.calls += 1
        _time.sleep(self._sleep)
        try:
            if self._raise_exc is not None:
                raise self._raise_exc
            if self._candidates is None:
                return Class2CandidateResult(
                    candidates=[], candidate_source="default_fallback",
                    generated_at_ms=0, model_id="static_default_fallback",
                )
            return Class2CandidateResult(
                candidates=self._candidates, candidate_source="llm_generated",
                generated_at_ms=0, model_id="slow-stub",
            )
        finally:
            self.completed.set()


class TestLlmCallBudget:
    """Regression: start_session must return within self._llm_call_budget_s
    even when the LLM hangs, so the MQTT message-handler thread cannot
    block indefinitely."""

    def _llm_candidates(self):
        return [{
            "candidate_id": "BUDGET_C1", "prompt": "테스트?",
            "candidate_transition_target": "CLASS_1",
            "action_hint": "light_on", "target_hint": "living_room_light",
        }]

    def _ctx(self):
        return {
            "trigger_event": {"event_type": "button", "event_code": "double_click",
                              "timestamp_ms": 0},
            "environmental_context": {"temperature": 22, "illuminance": 50,
                                       "occupancy_detected": True,
                                       "smoke_detected": False, "gas_detected": False,
                                       "doorbell_detected": False},
            "device_states": {"living_room_light": "off", "bedroom_light": "off",
                              "living_room_blind": "open", "tv_main": "off"},
        }

    def _make_manager(self, generator, budget_s):
        mgr = Class2ClarificationManager(llm_candidate_generator=generator)
        mgr._llm_call_budget_s = budget_s
        return mgr

    def test_fast_llm_within_budget_uses_llm_candidates(self):
        gen = _SlowStubGenerator(sleep_s=0.05, candidates=self._llm_candidates())
        mgr = self._make_manager(gen, budget_s=1.0)
        session = mgr.start_session("C206", AUDIT_ID, pure_context_payload=self._ctx())
        assert getattr(session, "candidate_source") == "llm_generated"
        assert session.candidate_choices[0].candidate_id == "BUDGET_C1"

    def test_slow_llm_exceeding_budget_falls_back(self):
        """If LLM takes longer than budget, manager abandons it and uses static.
        start_session must return within ~budget seconds, not within the LLM duration."""
        import time as _time
        gen = _SlowStubGenerator(sleep_s=2.0, candidates=self._llm_candidates())
        mgr = self._make_manager(gen, budget_s=0.3)
        t0 = _time.monotonic()
        session = mgr.start_session("C206", AUDIT_ID, pure_context_payload=self._ctx())
        elapsed = _time.monotonic() - t0
        # Generous upper bound — actual budget is 0.3 s.
        assert elapsed < 1.0, f"start_session blocked for {elapsed:.2f}s; budget was 0.3s"
        # Static fallback used
        assert getattr(session, "candidate_source") == "default_fallback"
        assert session.candidate_choices[0].candidate_id == "C1_LIGHTING_ASSISTANCE"

    def test_llm_exception_falls_back_silently(self):
        gen = _SlowStubGenerator(sleep_s=0.05, raise_exc=RuntimeError("ollama exploded"))
        mgr = self._make_manager(gen, budget_s=1.0)
        session = mgr.start_session("C206", AUDIT_ID, pure_context_payload=self._ctx())
        assert getattr(session, "candidate_source") == "default_fallback"

    def test_no_pure_context_skips_thread_entirely(self):
        gen = _SlowStubGenerator(sleep_s=0.05, candidates=self._llm_candidates())
        mgr = self._make_manager(gen, budget_s=1.0)
        # No pure_context_payload → no LLM call → no thread spawn
        session = mgr.start_session("C206", AUDIT_ID)
        assert gen.calls == 0
        assert getattr(session, "candidate_source") == "default_fallback"

    def test_budget_loaded_from_policy_table(self):
        """Default manager (no asset_loader override) computes the budget from
        global_constraints.llm_request_timeout_ms."""
        mgr = Class2ClarificationManager()
        # Shipped policy: llm_request_timeout_ms = 8000 → budget = 8.0 + 0.5
        assert abs(mgr._llm_call_budget_s - 8.5) < 0.01


# ==================================================================
# Phase 6.0 — Class 2 multi-turn refinement (doc 11)
# ==================================================================

class _StubLoaderForMultiTurn:
    """AssetLoader stub that overrides only class2_multi_turn_enabled.
    Other policy fields fall back to the real shipped values so the
    manager keeps its normal CLASS_2 timeout, max_attempts, etc."""

    def __init__(self, enabled: bool):
        from shared.asset_loader import AssetLoader
        self._real = AssetLoader()
        self._enabled = enabled

    def load_policy_table(self):
        policy = self._real.load_policy_table()
        policy["global_constraints"]["class2_multi_turn_enabled"] = self._enabled
        return policy

    def load_schema(self, name):
        return self._real.load_schema(name)

    def make_schema_resolver(self):
        return self._real.make_schema_resolver()


class TestMultiTurnRefinementDisabled:
    """Feature flag off (production default) → submit_selection_or_refine
    is a pass-through to submit_selection. No Phase 6 surface visible."""

    def test_returns_terminal_result_when_flag_off(self):
        mgr = Class2ClarificationManager(asset_loader=_StubLoaderForMultiTurn(False))
        session = mgr.start_session("C206", "audit-mt-off")
        out = mgr.submit_selection_or_refine(
            session, "C1_LIGHTING_ASSISTANCE", "user_mqtt_button",
        )
        from class2_clarification_manager.models import Class2Result
        assert isinstance(out, Class2Result)
        # Single-turn record must NOT carry refinement_history.
        assert "refinement_history" not in out.clarification_record


class TestMultiTurnRefinementEnabled:
    """Feature flag on → submit_selection_or_refine returns a refinement
    ClarificationSession when the chosen candidate has a template."""

    def _mgr(self):
        return Class2ClarificationManager(asset_loader=_StubLoaderForMultiTurn(True))

    def test_chosen_candidate_with_template_returns_refinement_session(self):
        mgr = self._mgr()
        session = mgr.start_session("C206", "audit-mt-1")
        out = mgr.submit_selection_or_refine(
            session, "C1_LIGHTING_ASSISTANCE", "user_mqtt_button",
        )
        from safe_deferral_handler.models import ClarificationSession
        assert isinstance(out, ClarificationSession)
        assert getattr(out, "is_refinement_turn") is True
        assert getattr(out, "parent_clarification_id") == session.clarification_id
        assert getattr(out, "parent_candidate_id") == "C1_LIGHTING_ASSISTANCE"
        # Refinement question is generic ('어느 방') because each per-room
        # choice carries the explicit verb that depends on current state
        # (doc 12 step 2-B state-aware refinement).
        assert getattr(out, "refinement_question") == "어느 방의 조명을 도와드릴까요?"
        # The refinement set is what the static template defined.
        ids = [c.candidate_id for c in out.candidate_choices]
        assert ids == ["REFINE_LIVING_ROOM", "REFINE_BEDROOM"]

    def test_chosen_candidate_without_template_stays_terminal(self):
        """C2_CAREGIVER_HELP has no refinement template → terminal."""
        mgr = self._mgr()
        session = mgr.start_session("C206", "audit-mt-2")
        out = mgr.submit_selection_or_refine(
            session, "C2_CAREGIVER_HELP", "user_mqtt_button",
        )
        from class2_clarification_manager.models import Class2Result
        assert isinstance(out, Class2Result)

    def test_unknown_candidate_id_falls_through_to_timeout(self):
        """Unknown id behaves like submit_selection — terminal escalation."""
        mgr = self._mgr()
        session = mgr.start_session("C206", "audit-mt-3")
        out = mgr.submit_selection_or_refine(
            session, "BOGUS_ID", "user_mqtt_button",
        )
        from class2_clarification_manager.models import Class2Result
        assert isinstance(out, Class2Result)

    def test_refinement_session_resolves_terminally_with_history(self):
        """Resolving the refinement session via submit_selection produces a
        terminal Class2Result whose record has exactly one refinement_history
        entry capturing the parent → refinement transition."""
        mgr = self._mgr()
        session = mgr.start_session("C206", "audit-mt-4")
        refinement = mgr.submit_selection_or_refine(
            session, "C1_LIGHTING_ASSISTANCE", "user_mqtt_button",
        )
        from safe_deferral_handler.models import ClarificationSession
        assert isinstance(refinement, ClarificationSession)

        result = mgr.submit_selection(
            refinement, "REFINE_BEDROOM", "user_mqtt_button",
            trigger_id="C206",
        )
        from class2_clarification_manager.models import Class2Result
        assert isinstance(result, Class2Result)
        # The terminal action must come from the refinement choice.
        assert result.action_hint == "light_on"
        assert result.target_hint == "bedroom_light"
        # refinement_history captures the parent → child step.
        history = result.clarification_record.get("refinement_history")
        assert history is not None and len(history) == 1
        entry = history[0]
        assert entry["turn_index"] == 1
        assert entry["parent_candidate_id"] == "C1_LIGHTING_ASSISTANCE"
        assert entry["selected_candidate_id"] == "REFINE_BEDROOM"

    def test_refinement_session_does_not_refine_again(self):
        """Multi-turn is bounded to ONE refinement. Calling
        submit_selection_or_refine on a refinement session must not
        produce a deeper refinement, even if the picked refinement
        candidate happens to have its own template (defensive)."""
        mgr = self._mgr()
        session = mgr.start_session("C206", "audit-mt-5")
        refinement = mgr.submit_selection_or_refine(
            session, "C1_LIGHTING_ASSISTANCE", "user_mqtt_button",
        )
        out = mgr.submit_selection_or_refine(
            refinement, "REFINE_LIVING_ROOM", "user_mqtt_button",
        )
        from class2_clarification_manager.models import Class2Result
        assert isinstance(out, Class2Result)

    def test_refinement_timeout_terminal_escalation_with_history(self):
        """Refinement turn timeout → terminal escalation; refinement_history
        records the unanswered turn so audit can tell the user picked the
        parent but didn't pick a refinement."""
        mgr = self._mgr()
        session = mgr.start_session("C206", "audit-mt-6")
        refinement = mgr.submit_selection_or_refine(
            session, "C1_LIGHTING_ASSISTANCE", "user_mqtt_button",
        )
        result = mgr.handle_timeout(refinement, trigger_id="C207")
        history = result.clarification_record.get("refinement_history")
        assert history is not None and len(history) == 1
        # selection_result records the timeout, and the entry mirrors it.
        sel = result.clarification_record["selection_result"]
        assert sel.get("confirmed") is False or sel.get("selected_candidate_id") in (None, "TIMEOUT")

    def test_refinement_record_validates_against_schema(self):
        """The schema must accept records with refinement_history."""
        import jsonschema
        from shared.asset_loader import AssetLoader
        loader = AssetLoader()
        schema = loader.load_schema("clarification_interaction_schema.json")
        resolver = loader.make_schema_resolver()

        mgr = self._mgr()
        session = mgr.start_session("C206", "audit-mt-7")
        refinement = mgr.submit_selection_or_refine(
            session, "C1_LIGHTING_ASSISTANCE", "user_mqtt_button",
        )
        result = mgr.submit_selection(
            refinement, "REFINE_LIVING_ROOM", "user_mqtt_button",
            trigger_id="C206",
        )
        validator = jsonschema.Draft7Validator(schema, resolver=resolver)
        errors = list(validator.iter_errors(result.clarification_record))
        assert not errors, "; ".join(e.message for e in errors)


class TestRefinementTemplates:
    """Static refinement template integrity."""

    def test_lookup_returns_none_for_unknown_id(self):
        from class2_clarification_manager.refinement_templates import (
            get_refinement_template,
        )
        assert get_refinement_template("DEFINITELY_NOT_A_REAL_ID") is None

    def test_lookup_returns_template_for_known_id(self):
        from class2_clarification_manager.refinement_templates import (
            get_refinement_template,
        )
        t = get_refinement_template("C1_LIGHTING_ASSISTANCE")
        assert t is not None
        assert len(t.refinement_choices) >= 2

    def test_all_refinement_targets_stay_in_low_risk_catalog(self):
        """Refinement candidates must not introduce new actuator authority.
        action_hint must be in the canonical low-risk light_on/light_off set
        (or None for non-CLASS_1 transitions); target_hint must be one of
        the canonical lighting targets."""
        from class2_clarification_manager.refinement_templates import (
            _REFINEMENT_TEMPLATES,
        )
        ALLOWED_ACTIONS = {None, "light_on", "light_off"}
        ALLOWED_TARGETS = {None, "living_room_light", "bedroom_light"}
        for parent_id, tpl in _REFINEMENT_TEMPLATES.items():
            for c in tpl.refinement_choices:
                assert c.action_hint in ALLOWED_ACTIONS, (parent_id, c)
                assert c.target_hint in ALLOWED_TARGETS, (parent_id, c)

    def test_refinement_question_within_policy_cap(self):
        """Refinement questions must respect the same prompt-length cap as
        initial prompts (Phase 4 invariant)."""
        import json
        import pathlib
        from class2_clarification_manager.refinement_templates import (
            _REFINEMENT_TEMPLATES,
        )
        policy_path = (
            pathlib.Path(__file__).resolve().parents[3]
            / "common" / "policies" / "policy_table.json"
        )
        with open(policy_path, encoding="utf-8") as f:
            policy = json.load(f)
        cap = int(
            policy["global_constraints"]
                  ["class2_conversational_prompt_constraints"]
                  ["max_prompt_length_chars"]
        )
        for parent_id, tpl in _REFINEMENT_TEMPLATES.items():
            assert len(tpl.refinement_question) <= cap, (parent_id, tpl)


# ==================================================================
# Phase 1 — Class 2 scanning input mode (doc 12)
# ==================================================================

class _StubLoaderForScanning:
    """AssetLoader stub that overrides only class2_input_mode default.
    Other policy fields fall back to shipped values so manager keeps
    its real timeouts, max_attempts, etc."""

    def __init__(self, default_mode: str = "direct_select",
                 per_option_timeout_ms: int = 8000):
        from shared.asset_loader import AssetLoader
        self._real = AssetLoader()
        self._mode = default_mode
        self._per_opt_ms = per_option_timeout_ms

    def load_policy_table(self):
        policy = self._real.load_policy_table()
        policy["global_constraints"]["class2_input_mode"] = self._mode
        policy["global_constraints"]["class2_scan_per_option_timeout_ms"] = self._per_opt_ms
        return policy

    def load_schema(self, name):
        return self._real.load_schema(name)

    def make_schema_resolver(self):
        return self._real.make_schema_resolver()


class TestScanningSessionInit:
    """start_session must initialise scanning state when input_mode='scanning'
    and leave it unset for direct_select sessions (production default)."""

    def test_default_session_is_direct_select(self):
        mgr = Class2ClarificationManager()
        session = mgr.start_session("C206", "audit-scan-1")
        assert getattr(session, "input_mode") == "direct_select"
        assert not hasattr(session, "current_option_index")
        assert not hasattr(session, "scan_history")

    def test_explicit_scanning_initialises_pointer_and_history(self):
        mgr = Class2ClarificationManager()
        session = mgr.start_session(
            "C206", "audit-scan-2", input_mode="scanning",
        )
        assert getattr(session, "input_mode") == "scanning"
        assert getattr(session, "current_option_index") == 0
        assert getattr(session, "scan_history") == []
        # Per-option timeout exposed for the scanning caller to drive.
        assert getattr(session, "scan_per_option_timeout_ms") == 8000

    def test_policy_default_scanning_enables_implicitly(self):
        """When the deployment sets class2_input_mode='scanning' in policy,
        every session defaults to scanning without an explicit argument."""
        mgr = Class2ClarificationManager(asset_loader=_StubLoaderForScanning("scanning"))
        session = mgr.start_session("C206", "audit-scan-3")
        assert getattr(session, "input_mode") == "scanning"
        assert getattr(session, "current_option_index") == 0

    def test_explicit_arg_overrides_policy_default(self):
        """Trial runner / scenario fixture can force a per-trial mode
        regardless of the deployment's policy default."""
        mgr = Class2ClarificationManager(asset_loader=_StubLoaderForScanning("scanning"))
        session = mgr.start_session(
            "C206", "audit-scan-4", input_mode="direct_select",
        )
        assert getattr(session, "input_mode") == "direct_select"
        assert not hasattr(session, "current_option_index")


class TestScanningResponseFlow:
    """submit_scan_response must accept yes (terminal), advance on no/silence,
    and escalate on final-option no/silence (silence ≠ consent invariant)."""

    def _scanning_session(self, mgr=None, audit_id="audit-scan-flow"):
        mgr = mgr or Class2ClarificationManager()
        return mgr, mgr.start_session("C206", audit_id, input_mode="scanning")

    def test_yes_on_first_option_terminal_class2_result(self):
        """response='yes' on the current option produces the terminal
        Class2Result for that candidate. scan_history records the yes turn."""
        mgr, session = self._scanning_session()
        first = session.candidate_choices[0]
        result = mgr.submit_scan_response(
            session, option_index=0, response="yes",
            input_source="user_mqtt_button", elapsed_ms=1234,
        )
        from class2_clarification_manager.models import Class2Result
        assert isinstance(result, Class2Result)
        # The terminal action matches the first candidate.
        assert result.action_hint == first.action_hint
        # scan_history is in the audit record with one yes entry.
        history = result.clarification_record.get("scan_history")
        assert history and len(history) == 1
        assert history[0]["response"] == "yes"
        assert history[0]["option_index"] == 0
        assert history[0]["candidate_id"] == first.candidate_id
        assert history[0]["elapsed_ms"] == 1234
        # input_mode attributed.
        assert result.clarification_record.get("input_mode") == "scanning"

    def test_no_on_non_final_option_advances_session(self):
        """response='no' on a non-final option returns the same session
        with current_option_index incremented and a 'no' entry recorded."""
        mgr, session = self._scanning_session()
        result = mgr.submit_scan_response(
            session, option_index=0, response="no",
            input_source="user_mqtt_button", elapsed_ms=8000,
        )
        from safe_deferral_handler.models import ClarificationSession
        assert isinstance(result, ClarificationSession)
        assert result is session  # same object, advanced
        assert getattr(session, "current_option_index") == 1
        assert getattr(session, "scan_history")[-1]["response"] == "no"

    def test_silence_on_non_final_option_advances(self):
        """Silence on a non-final option behaves like 'no' (auto-advance)
        but is recorded distinctly so audit can tell silence from refusal."""
        mgr, session = self._scanning_session()
        result = mgr.submit_scan_response(
            session, option_index=0, response="silence",
            input_source="timeout", elapsed_ms=8000,
        )
        from safe_deferral_handler.models import ClarificationSession
        assert isinstance(result, ClarificationSession)
        assert getattr(session, "current_option_index") == 1
        assert getattr(session, "scan_history")[-1]["response"] == "silence"

    def test_handle_scan_silence_convenience_method(self):
        mgr, session = self._scanning_session()
        result = mgr.handle_scan_silence(session, elapsed_ms=8000)
        from safe_deferral_handler.models import ClarificationSession
        assert isinstance(result, ClarificationSession)
        assert getattr(session, "current_option_index") == 1
        last = getattr(session, "scan_history")[-1]
        assert last["response"] == "silence"
        assert last["input_source"] == "timeout"

    def test_no_on_final_option_escalates_to_caregiver(self):
        """When every option has been rejected, the session escalates to
        SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION via the existing timeout
        pipeline. silence ≠ consent invariant preserved."""
        mgr, session = self._scanning_session()
        n = len(session.candidate_choices)
        # Walk through all but the last option as 'no'.
        for i in range(n - 1):
            mgr.submit_scan_response(
                session, option_index=i, response="no",
                input_source="user_mqtt_button",
            )
        # Final 'no' should escalate.
        result = mgr.submit_scan_response(
            session, option_index=n - 1, response="no",
            input_source="user_mqtt_button",
        )
        from class2_clarification_manager.models import Class2Result
        from safe_deferral_handler.models import TransitionTarget
        assert isinstance(result, Class2Result)
        assert result.transition_target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
        # All N rejections recorded.
        history = result.clarification_record["scan_history"]
        assert len(history) == n
        assert all(entry["response"] == "no" for entry in history)

    def test_silence_on_final_option_also_escalates(self):
        """Final-option silence == final-option no — silence never executes."""
        mgr, session = self._scanning_session()
        n = len(session.candidate_choices)
        for i in range(n - 1):
            mgr.submit_scan_response(
                session, option_index=i, response="no",
                input_source="user_mqtt_button",
            )
        result = mgr.handle_scan_silence(session)
        from class2_clarification_manager.models import Class2Result
        from safe_deferral_handler.models import TransitionTarget
        assert isinstance(result, Class2Result)
        assert result.transition_target == TransitionTarget.SAFE_DEFERRAL_OR_CAREGIVER_CONFIRMATION
        assert result.clarification_record["scan_history"][-1]["response"] == "silence"

    def test_stale_input_dropped_session_unchanged(self):
        """Input addressed to a previous option (race) is recorded as
        'dropped' but does not advance current_option_index."""
        mgr, session = self._scanning_session()
        # Advance to option 1 first.
        mgr.submit_scan_response(
            session, option_index=0, response="no",
            input_source="user_mqtt_button",
        )
        assert getattr(session, "current_option_index") == 1
        # Stale 'yes' for option 0 — must NOT accept.
        result = mgr.submit_scan_response(
            session, option_index=0, response="yes",
            input_source="user_mqtt_button",
        )
        from safe_deferral_handler.models import ClarificationSession
        assert isinstance(result, ClarificationSession)
        assert getattr(session, "current_option_index") == 1
        # Drop is audit-visible.
        last = getattr(session, "scan_history")[-1]
        assert last["response"] == "dropped"
        assert last["option_index"] == 0

    def test_out_of_range_option_index_recorded_as_dropped(self):
        """Defensive: an index past the candidate set is also dropped."""
        mgr, session = self._scanning_session()
        result = mgr.submit_scan_response(
            session, option_index=99, response="yes",
            input_source="user_mqtt_button",
        )
        from safe_deferral_handler.models import ClarificationSession
        assert isinstance(result, ClarificationSession)
        last = getattr(session, "scan_history")[-1]
        assert last["response"] == "dropped"
        assert last["candidate_id"] == "<out_of_range>"
        assert getattr(session, "current_option_index") == 0


class TestScanningGuardsAndSchema:
    """Defensive guards + schema compliance for scanning records."""

    def test_submit_scan_on_direct_select_session_raises(self):
        mgr = Class2ClarificationManager()
        session = mgr.start_session("C206", "audit-guard-1")  # direct_select
        with pytest.raises(ValueError, match="non-scanning session"):
            mgr.submit_scan_response(
                session, option_index=0, response="yes",
                input_source="user_mqtt_button",
            )

    def test_handle_scan_silence_on_direct_select_raises(self):
        mgr = Class2ClarificationManager()
        session = mgr.start_session("C206", "audit-guard-2")
        with pytest.raises(ValueError, match="non-scanning session"):
            mgr.handle_scan_silence(session)

    def test_invalid_scan_response_value_raises(self):
        mgr = Class2ClarificationManager()
        session = mgr.start_session("C206", "audit-guard-3", input_mode="scanning")
        with pytest.raises(ValueError, match="invalid scan response"):
            mgr.submit_scan_response(
                session, option_index=0, response="maybe",
                input_source="user_mqtt_button",
            )

    def test_scanning_record_validates_against_schema(self):
        """Records with input_mode='scanning' + scan_history must validate."""
        import jsonschema
        from shared.asset_loader import AssetLoader
        loader = AssetLoader()
        schema = loader.load_schema("clarification_interaction_schema.json")
        resolver = loader.make_schema_resolver()

        mgr = Class2ClarificationManager()
        session = mgr.start_session("C206", "audit-schema-1", input_mode="scanning")
        # Reject first, accept second.
        mgr.submit_scan_response(
            session, option_index=0, response="no",
            input_source="user_mqtt_button", elapsed_ms=8000,
        )
        result = mgr.submit_scan_response(
            session, option_index=1, response="yes",
            input_source="user_mqtt_button", elapsed_ms=2000,
        )
        validator = jsonschema.Draft7Validator(schema, resolver=resolver)
        errors = list(validator.iter_errors(result.clarification_record))
        assert not errors, "; ".join(e.message for e in errors)
        # And the record carries both audit fields.
        assert result.clarification_record["input_mode"] == "scanning"
        assert len(result.clarification_record["scan_history"]) == 2

    def test_direct_select_records_carry_input_mode_attribution(self):
        """Direct-select sessions carry input_mode='direct_select' for audit
        attribution but no scan_history."""
        mgr = Class2ClarificationManager()
        session = mgr.start_session("C206", "audit-schema-2")
        c1 = next(c for c in session.candidate_choices
                  if c.candidate_transition_target == "CLASS_1")
        result = mgr.submit_selection(
            session, c1.candidate_id, "user_mqtt_button", trigger_id="C206",
        )
        rec = result.clarification_record
        assert rec.get("input_mode") == "direct_select"
        assert "scan_history" not in rec


# ==================================================================
# Step 2-B — state-aware lighting + "다른 동작" option (doc 12)
# ==================================================================

def _ctx_with_devices(**device_states):
    """Minimal pure_context_payload with device_states populated."""
    return {
        "trigger_event": {
            "event_type": "button", "event_code": "single_click",
            "timestamp_ms": 0,
        },
        "environmental_context": {
            "temperature": 22.0, "illuminance": 200,
            "occupancy_detected": True, "smoke_detected": False,
            "gas_detected": False, "doorbell_detected": False,
        },
        "device_states": {
            "living_room_light": "off", "bedroom_light": "off",
            "living_room_blind": "closed", "tv_main": "off",
            **device_states,
        },
    }


class TestStateAwareLightingCandidates:
    """C1_LIGHTING_ASSISTANCE / OPT_LIVING_ROOM / OPT_BEDROOM should render
    state-aware prompts and action_hints based on device_states (doc 12 §2-B).
    Unknown device state defaults to 'off' (so prompt='켜드릴까요?',
    action_hint='light_on') for backward compat."""

    def test_off_state_yields_turn_on(self):
        mgr = Class2ClarificationManager()
        session = mgr.start_session(
            "C206", "audit-light-1",
            pure_context_payload=_ctx_with_devices(living_room_light="off"),
        )
        c1 = next(c for c in session.candidate_choices
                  if c.candidate_id == "C1_LIGHTING_ASSISTANCE")
        assert c1.action_hint == "light_on"
        assert c1.target_hint == "living_room_light"
        assert "켜드릴까요" in c1.prompt
        assert "거실" in c1.prompt
        # Sanity: policy prompt cap (Phase 4 invariant carried forward).
        assert len(c1.prompt) <= 80

    def test_on_state_yields_turn_off(self):
        mgr = Class2ClarificationManager()
        session = mgr.start_session(
            "C206", "audit-light-2",
            pure_context_payload=_ctx_with_devices(living_room_light="on"),
        )
        c1 = next(c for c in session.candidate_choices
                  if c.candidate_id == "C1_LIGHTING_ASSISTANCE")
        assert c1.action_hint == "light_off"
        assert "꺼드릴까요" in c1.prompt

    def test_default_off_when_no_pure_context_payload(self):
        """Backward compat: legacy callers that omit pure_context_payload
        still get a usable C1 candidate (default off-state semantics)."""
        mgr = Class2ClarificationManager()
        session = mgr.start_session("C206", "audit-light-3")
        c1 = next(c for c in session.candidate_choices
                  if c.candidate_id == "C1_LIGHTING_ASSISTANCE")
        assert c1.action_hint == "light_on"
        assert "켜드릴까요" in c1.prompt

    def test_unresolved_conflict_per_room_state_aware(self):
        """OPT_LIVING_ROOM / OPT_BEDROOM each respect their own room's state."""
        mgr = Class2ClarificationManager()
        session = mgr.start_session(
            "C203", "audit-light-4",
            pure_context_payload=_ctx_with_devices(
                living_room_light="on",
                bedroom_light="off",
            ),
        )
        opt_lr = next(c for c in session.candidate_choices
                      if c.candidate_id == "OPT_LIVING_ROOM")
        opt_br = next(c for c in session.candidate_choices
                      if c.candidate_id == "OPT_BEDROOM")
        assert opt_lr.action_hint == "light_off"
        assert "거실" in opt_lr.prompt and "꺼드릴까요" in opt_lr.prompt
        assert opt_br.action_hint == "light_on"
        assert "침실" in opt_br.prompt and "켜드릴까요" in opt_br.prompt

    def test_old_generic_prompt_no_longer_emitted(self):
        """The previous unnatural '조명 도움이 필요하신가요?' prompt should
        no longer surface for any default lighting candidate."""
        mgr = Class2ClarificationManager()
        for trigger in ("C201", "C202", "C203", "C206"):
            session = mgr.start_session(trigger, f"audit-prompt-{trigger}",
                                         pure_context_payload=_ctx_with_devices())
            for c in session.candidate_choices:
                assert "조명 도움이 필요하신가요" not in c.prompt


class TestOtherActionSafetyNet:
    """For lighting reasons, C4 candidate's prompt is replaced with
    '다른 동작이 필요하신가요?' — explicit safety net for 'system assumed
    wrong action'. candidate_id and transition target unchanged."""

    def test_lighting_reason_renames_c4_prompt(self):
        mgr = Class2ClarificationManager()
        session = mgr.start_session("C206", "audit-c4-1",
                                     pure_context_payload=_ctx_with_devices())
        c4 = next(c for c in session.candidate_choices
                  if c.candidate_id == "C4_CANCEL_OR_WAIT")
        assert "다른 동작이 필요하신가요" in c4.prompt
        # candidate_id and transition target unchanged for backward compat
        # (Telegram label, audit, integration fixtures).
        assert c4.candidate_transition_target == "SAFE_DEFERRAL"

    def test_non_lighting_reason_keeps_cancel_prompt(self):
        """sensor_staleness / actuation_ack_timeout / timeout_or_no_response
        / caregiver_required_sensitive_path don't assume a specific action,
        so 'cancel and wait' wording remains correct."""
        mgr = Class2ClarificationManager()
        for trigger in ("C204", "C205", "C207"):
            session = mgr.start_session(
                trigger, f"audit-c4-non-{trigger}",
                pure_context_payload=_ctx_with_devices(),
            )
            c4 = next(
                (c for c in session.candidate_choices
                 if c.candidate_id == "C4_CANCEL_OR_WAIT"),
                None,
            )
            if c4 is not None:
                assert "취소하고 대기" in c4.prompt
                assert "다른 동작" not in c4.prompt


class TestRefinementTemplateStateAware:
    """get_refinement_template renders REFINE_LIVING_ROOM / REFINE_BEDROOM
    candidates state-aware too (doc 12 §2-B + PR #102)."""

    def test_refinement_off_state_yields_turn_on(self):
        from class2_clarification_manager.refinement_templates import (
            get_refinement_template,
        )
        t = get_refinement_template(
            "C1_LIGHTING_ASSISTANCE",
            pure_context_payload=_ctx_with_devices(
                living_room_light="off", bedroom_light="off",
            ),
        )
        assert t is not None
        for c in t.refinement_choices:
            assert c.action_hint == "light_on"
            assert "켜드릴까요" in c.prompt

    def test_refinement_per_room_independent_state(self):
        from class2_clarification_manager.refinement_templates import (
            get_refinement_template,
        )
        t = get_refinement_template(
            "C1_LIGHTING_ASSISTANCE",
            pure_context_payload=_ctx_with_devices(
                living_room_light="on", bedroom_light="off",
            ),
        )
        lr = next(c for c in t.refinement_choices
                  if c.candidate_id == "REFINE_LIVING_ROOM")
        br = next(c for c in t.refinement_choices
                  if c.candidate_id == "REFINE_BEDROOM")
        assert lr.action_hint == "light_off"
        assert "꺼드릴까요" in lr.prompt
        assert br.action_hint == "light_on"
        assert "켜드릴까요" in br.prompt

    def test_refinement_no_payload_defaults_to_off_state(self):
        """Backward compat: PR #102 callers passing no payload still get
        usable refinement candidates (defaults to off-state semantics)."""
        from class2_clarification_manager.refinement_templates import (
            get_refinement_template,
        )
        t = get_refinement_template("C1_LIGHTING_ASSISTANCE")
        assert t is not None
        for c in t.refinement_choices:
            assert c.action_hint == "light_on"

    def test_refinement_question_is_generic(self):
        """Per-room choices carry the explicit verb, so the refinement
        question itself stays generic to fit both on/off cases."""
        from class2_clarification_manager.refinement_templates import (
            get_refinement_template,
        )
        t = get_refinement_template("C1_LIGHTING_ASSISTANCE")
        assert "도와드릴까요" in t.refinement_question
        assert "켜드릴까요" not in t.refinement_question
        assert "꺼드릴까요" not in t.refinement_question


# ==================================================================
# doc 12 §14 Phase 1.5 — deterministic ordering integrated in manager
# ==================================================================

class _StubLoaderForOrdering:
    """AssetLoader stub that overrides only the scanning ordering policy.
    Other policy fields fall back to shipped values."""

    def __init__(self, ordering_mode: str = "deterministic", rules=None):
        from shared.asset_loader import AssetLoader
        self._real = AssetLoader()
        self._mode = ordering_mode
        self._rules = rules

    def load_policy_table(self):
        policy = self._real.load_policy_table()
        # Force scanning so the manager applies ordering. Keep the rest
        # of the policy as shipped.
        policy["global_constraints"]["class2_input_mode"] = "scanning"
        policy["global_constraints"]["class2_scan_ordering_mode"] = self._mode
        if self._rules is not None:
            policy["global_constraints"]["class2_scan_ordering_rules"] = self._rules
        return policy

    def load_schema(self, name):
        return self._real.load_schema(name)

    def make_schema_resolver(self):
        return self._real.make_schema_resolver()


class TestScanOrderingManagerIntegration:
    """When input_mode='scanning' AND scan_ordering_mode='deterministic',
    start_session reorders candidate_choices using the policy rules and
    stashes the audit on the session."""

    def test_source_order_keeps_original_candidate_order(self):
        """Default ordering mode = source_order → no reordering, no audit."""
        mgr = Class2ClarificationManager(
            asset_loader=_StubLoaderForOrdering(ordering_mode="source_order"),
        )
        session = mgr.start_session("C206", "audit-ord-1")
        # Should not have ordering audit (source_order skips ranking).
        assert getattr(session, "scan_ordering_audit", None) is None

    def test_deterministic_reorders_per_trigger_bucket(self):
        """C208 bucket prioritizes CAREGIVER_CONFIRMATION first → C2 must
        come before any other CAREGIVER-bound candidate in the order."""
        rules = {
            "by_trigger_id": {
                "C208": ["CAREGIVER_CONFIRMATION", "CLASS_0", "SAFE_DEFERRAL"],
            }
        }
        mgr = Class2ClarificationManager(
            asset_loader=_StubLoaderForOrdering(rules=rules),
        )
        session = mgr.start_session("C208", "audit-ord-2",
                                     pure_context_payload={
                                         "trigger_event": {"event_type": "sensor",
                                                            "event_code": "doorbell_detected",
                                                            "timestamp_ms": 0},
                                         "environmental_context": {
                                             "doorbell_detected": True,
                                             "smoke_detected": False,
                                             "gas_detected": False,
                                         },
                                         "device_states": {},
                                     })
        ids = [c.candidate_id for c in session.candidate_choices]
        # First candidate must be the CAREGIVER_CONFIRMATION one (C2_CAREGIVER_HELP).
        assert session.candidate_choices[0].candidate_transition_target == "CAREGIVER_CONFIRMATION"
        # Audit recorded.
        audit = getattr(session, "scan_ordering_audit", None)
        assert audit is not None
        assert audit["matched_bucket"] == "C208"
        assert audit["final_order"] == ids

    def test_smoke_context_override_boosts_emergency(self):
        """When smoke is detected, CLASS_0 should come first regardless
        of what the trigger-bucket said."""
        rules = {
            "by_trigger_id": {"_default": ["CLASS_1", "CLASS_0", "CAREGIVER_CONFIRMATION"]},
            "context_overrides": [{
                "if_field": "environmental_context.smoke_detected",
                "if_equals": True,
                "boost_first": "CLASS_0",
            }],
        }
        mgr = Class2ClarificationManager(
            asset_loader=_StubLoaderForOrdering(rules=rules),
        )
        ctx = {
            "trigger_event": {"event_type": "button",
                               "event_code": "single_click",
                               "timestamp_ms": 0},
            "environmental_context": {
                "smoke_detected": True, "gas_detected": False,
                "doorbell_detected": False, "occupancy_detected": True,
                "temperature": 25, "illuminance": 50,
            },
            "device_states": {"living_room_light": "off"},
        }
        session = mgr.start_session("C206", "audit-ord-3",
                                     pure_context_payload=ctx)
        # First candidate is CLASS_0 (C3_EMERGENCY_HELP).
        assert session.candidate_choices[0].candidate_transition_target == "CLASS_0"
        audit = session.scan_ordering_audit
        assert any("smoke_detected" in s for s in audit["applied_overrides"])

    def test_explicit_arg_overrides_policy_default(self):
        """scan_ordering_mode='source_order' explicit arg overrides the
        policy default of deterministic — no reordering happens."""
        rules = {"by_trigger_id": {"C206": ["CLASS_0", "CLASS_1"]}}
        mgr = Class2ClarificationManager(
            asset_loader=_StubLoaderForOrdering(rules=rules),
        )
        # Capture source order without ordering for comparison.
        baseline_session = mgr.start_session(
            "C206", "audit-ord-4-base",
            scan_ordering_mode="source_order",
        )
        baseline_ids = [c.candidate_id for c in baseline_session.candidate_choices]
        assert getattr(baseline_session, "scan_ordering_audit", None) is None

        ordered_session = mgr.start_session(
            "C206", "audit-ord-4-ordered",
            scan_ordering_mode="deterministic",
        )
        ordered_ids = [c.candidate_id for c in ordered_session.candidate_choices]
        # Same candidate set, but order should reflect the rules.
        assert sorted(baseline_ids) == sorted(ordered_ids)
        # First candidate of ordered is CLASS_0.
        assert ordered_session.candidate_choices[0].candidate_transition_target == "CLASS_0"

    def test_direct_select_skips_ordering_even_when_policy_deterministic(self):
        """Ordering is meaningful only for scanning. direct_select displays
        all options at once, so no reordering should happen even if the
        policy says deterministic."""
        from shared.asset_loader import AssetLoader
        real = AssetLoader()
        class _LoaderDirectSelectDeterministic:
            def load_policy_table(self):
                p = real.load_policy_table()
                p["global_constraints"]["class2_input_mode"] = "direct_select"
                p["global_constraints"]["class2_scan_ordering_mode"] = "deterministic"
                return p
            def load_schema(self, n): return real.load_schema(n)
            def make_schema_resolver(self): return real.make_schema_resolver()

        mgr = Class2ClarificationManager(
            asset_loader=_LoaderDirectSelectDeterministic(),
        )
        session = mgr.start_session("C206", "audit-ord-5")
        assert getattr(session, "scan_ordering_audit", None) is None

    def test_ordering_record_validates_against_schema(self):
        """A clarification record carrying scan_ordering_applied must
        validate against the schema."""
        import jsonschema
        from shared.asset_loader import AssetLoader
        loader = AssetLoader()
        schema = loader.load_schema("clarification_interaction_schema.json")
        resolver = loader.make_schema_resolver()

        rules = {"by_trigger_id": {"C206": ["CLASS_1", "CLASS_0"]}}
        mgr = Class2ClarificationManager(
            asset_loader=_StubLoaderForOrdering(rules=rules),
        )
        session = mgr.start_session("C206", "audit-ord-6")
        # Resolve via submit_selection so we get a terminal record.
        c1 = next(c for c in session.candidate_choices
                  if c.candidate_transition_target == "CLASS_1")
        result = mgr.submit_selection(session, c1.candidate_id, "user_mqtt_button",
                                       trigger_id="C206")
        rec = result.clarification_record
        assert "scan_ordering_applied" in rec
        validator = jsonschema.Draft7Validator(schema, resolver=resolver)
        errors = list(validator.iter_errors(rec))
        assert not errors, "; ".join(e.message for e in errors)

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
        assert getattr(out, "refinement_question") == "어느 방의 조명을 켜드릴까요?"
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

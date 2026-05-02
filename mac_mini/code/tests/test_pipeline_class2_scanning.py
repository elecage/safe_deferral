"""Tests for the doc 12 Phase 4 scanning wiring in Pipeline.

These exercise the two main-loop pieces that change for scanning mode:

  1. _try_handle_as_user_selection's scanning branch (translates physical
     button events into the entry['scan_decision'] tuple the Phase 1 loop
     reads).
  2. _await_user_scanning_then_caregiver's per-option loop (announce →
     wait → translate decision → submit_scan_response / handle_scan_silence
     → terminal Class2Result OR escalate to caregiver).

Telegram and live MQTT are mocked out — the same approach as
test_pipeline_ack_escalation.py.
"""

from unittest.mock import MagicMock, patch

import pytest

# Stub out paho before main imports it (matches test_pipeline_ack_escalation pattern)
import sys
import types

_paho_module = types.ModuleType("paho")
_paho_mqtt_module = types.ModuleType("paho.mqtt")
_paho_client_stub = types.ModuleType("paho.mqtt.client")
_paho_client_stub.Client = MagicMock()
_paho_client_stub.MQTTv311 = 4
sys.modules.setdefault("paho", _paho_module)
sys.modules.setdefault("paho.mqtt", _paho_mqtt_module)
sys.modules.setdefault("paho.mqtt.client", _paho_client_stub)


class _MockPublisher:
    def __init__(self):
        self.published = []

    def publish(self, topic, payload, qos=1):
        self.published.append((topic, payload))


@pytest.fixture(scope="module")
def pipeline():
    with patch("main.AUDIT_DB_PATH", ":memory:"):
        import main  # noqa: PLC0415
        p = main.Pipeline(mqtt_publisher=_MockPublisher())
        yield p


def _start_scanning_session(pipeline, audit_id="audit-scan-pipe-001"):
    """Start a real Class2 scanning session and register it as the active
    pending session (mirrors what _await_user_scanning_then_caregiver does
    on entry — but without spawning the per-option thread)."""
    import threading
    session = pipeline._class2.start_session(
        trigger_id="C206",
        audit_correlation_id=audit_id,
        input_mode="scanning",
    )
    user_event = threading.Event()
    caregiver_event = threading.Event()
    entry = {
        "session": session,
        "event": user_event,
        "caregiver_event": caregiver_event,
        "trigger_id": "C206",
        "audit_id": audit_id,
        "selection": None,
        "scan_decision": None,
        "phase": 1,
        "input_mode": "scanning",
    }
    with pipeline._user_class2_lock:
        pipeline._pending_user_class2[session.clarification_id] = entry
    return session, entry, user_event


def _make_button_msg(event_code, audit_id="audit-scan-pipe-001"):
    return {
        "source_node_id": "esp32.bounded_input_node",
        "routing_metadata": {
            "audit_correlation_id": audit_id,
            "ingest_timestamp_ms": 0,
            "network_status": "online",
        },
        "pure_context_payload": {
            "trigger_event": {
                "event_type": "button",
                "event_code": event_code,
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
            },
        },
    }


# ==================================================================
# _try_handle_as_user_selection — scanning branch
# ==================================================================

class TestTryHandleAsUserSelectionScanning:
    """When entry['input_mode'] == 'scanning', a button event must be
    consumed (return True), produce the right scan_decision tuple, and
    wake the per-option event."""

    def test_single_click_records_yes_and_wakes_event(self, pipeline):
        session, entry, user_event = _start_scanning_session(
            pipeline, audit_id="audit-scan-tc-1",
        )
        # Position pointer at option 1 to verify current_option_index is used.
        with pipeline._user_class2_lock:
            session.current_option_index = 1
        try:
            assert user_event.is_set() is False
            consumed = pipeline._try_handle_as_user_selection(
                _make_button_msg("single_click", "audit-scan-tc-1")
            )
            assert consumed is True
            assert user_event.is_set() is True
            with pipeline._user_class2_lock:
                d = entry["scan_decision"]
            assert d == ("submit", 1, "yes")
        finally:
            with pipeline._user_class2_lock:
                pipeline._pending_user_class2.pop(session.clarification_id, None)

    def test_double_click_records_no(self, pipeline):
        session, entry, user_event = _start_scanning_session(
            pipeline, audit_id="audit-scan-tc-2",
        )
        try:
            consumed = pipeline._try_handle_as_user_selection(
                _make_button_msg("double_click", "audit-scan-tc-2")
            )
            assert consumed is True
            assert user_event.is_set() is True
            with pipeline._user_class2_lock:
                d = entry["scan_decision"]
            assert d[0] == "submit" and d[2] == "no"
        finally:
            with pipeline._user_class2_lock:
                pipeline._pending_user_class2.pop(session.clarification_id, None)

    def test_triple_hit_records_emergency(self, pipeline):
        session, entry, user_event = _start_scanning_session(
            pipeline, audit_id="audit-scan-tc-3",
        )
        try:
            consumed = pipeline._try_handle_as_user_selection(
                _make_button_msg("triple_hit", "audit-scan-tc-3")
            )
            assert consumed is True
            with pipeline._user_class2_lock:
                d = entry["scan_decision"]
            # First CLASS_0 candidate id (C3_EMERGENCY_HELP for insufficient_context)
            assert d[0] == "emergency"
            assert d[1] is not None
        finally:
            with pipeline._user_class2_lock:
                pipeline._pending_user_class2.pop(session.clarification_id, None)

    def test_unknown_event_consumed_without_decision(self, pipeline):
        """Block from normal pipeline but do NOT set a decision or wake event."""
        session, entry, user_event = _start_scanning_session(
            pipeline, audit_id="audit-scan-tc-4",
        )
        try:
            consumed = pipeline._try_handle_as_user_selection(
                _make_button_msg("long_press", "audit-scan-tc-4")
            )
            assert consumed is True   # blocked from normal pipeline
            assert user_event.is_set() is False
            with pipeline._user_class2_lock:
                assert entry["scan_decision"] is None
        finally:
            with pipeline._user_class2_lock:
                pipeline._pending_user_class2.pop(session.clarification_id, None)

    def test_direct_select_path_unaffected(self, pipeline):
        """Sanity: when input_mode is direct_select (the default), the new
        scanning branch must not be taken — the legacy single_click → first
        candidate mapping still applies."""
        import threading
        session = pipeline._class2.start_session(
            trigger_id="C206",
            audit_correlation_id="audit-scan-tc-5",
        )
        user_event = threading.Event()
        entry = {
            "session": session, "event": user_event,
            "caregiver_event": threading.Event(),
            "trigger_id": "C206", "audit_id": "audit-scan-tc-5",
            "selection": None, "phase": 1,
            # NOTE: no 'input_mode' key → defaults to direct_select branch
        }
        with pipeline._user_class2_lock:
            pipeline._pending_user_class2[session.clarification_id] = entry
        try:
            consumed = pipeline._try_handle_as_user_selection(
                _make_button_msg("single_click", "audit-scan-tc-5")
            )
            assert consumed is True
            with pipeline._user_class2_lock:
                # Direct-select sets 'selection' (a candidate_id), not 'scan_decision'.
                assert entry["selection"] == session.candidate_choices[0].candidate_id
                assert "scan_decision" not in entry or entry.get("scan_decision") is None
        finally:
            with pipeline._user_class2_lock:
                pipeline._pending_user_class2.pop(session.clarification_id, None)


# ==================================================================
# _await_user_scanning_then_caregiver — per-option loop
# ==================================================================

class TestAwaitUserScanningThenCaregiver:
    """Drive the scanning Phase 1 loop end-to-end by feeding button events
    on a side thread. Mocks Telegram + transition execution so we can
    assert on the pipeline's choice without external dependencies."""

    def _mock_external_side_effects(self, pipeline):
        """Record telemetry/transition/caregiver calls instead of executing."""
        recorded = {
            "transitions": [],
            "telemetry_class2": [],
            "caregiver_notifications": [],
            "tts": [],
        }
        pipeline._execute_class2_transition = (
            lambda r, a, t: recorded["transitions"].append((r, a, t))
        )
        pipeline._telemetry.publish_class2_update = (
            lambda a, r: recorded["telemetry_class2"].append((a, r))
        )
        pipeline._caregiver.send_notification = (
            lambda n: recorded["caregiver_notifications"].append(n) or MagicMock()
        )
        # TTS goes through self._tts; we keep the real speaker but capture
        # the last-emitted utterance count to verify announcements ran.
        original_speak = pipeline._tts.speak
        def _capture(text):
            recorded["tts"].append(text)
            try:
                original_speak(text)
            except Exception:
                pass
        pipeline._tts.speak = _capture
        return recorded

    def test_yes_on_first_option_terminal_no_caregiver(self, pipeline):
        """User says yes to option 0 → terminal CLASS_1 result published, no
        caregiver phase invoked. Verifies the happy-path scanning flow."""
        import threading

        recorded = self._mock_external_side_effects(pipeline)
        # Make caregiver Phase 2 a no-op marker so we can detect if it ran.
        run_caregiver_called = []
        original_run_cg = pipeline._run_caregiver_phase
        pipeline._run_caregiver_phase = (
            lambda *args, **kwargs: run_caregiver_called.append(args)
        )

        # Build a real scanning session (state-aware, lighting on so first
        # option is light_off — anything is fine, we just need a CLASS_1).
        session = pipeline._class2.start_session(
            trigger_id="C206",
            audit_correlation_id="audit-scan-flow-1",
            input_mode="scanning",
            pure_context_payload={"device_states": {"living_room_light": "off"}},
        )
        # Cut per-option timeout to keep the test fast.
        session.scan_per_option_timeout_ms = 5000

        # Inject a 'yes' decision shortly after the loop starts.
        def _inject_yes():
            import time
            time.sleep(0.05)
            with pipeline._user_class2_lock:
                entry = pipeline._pending_user_class2.get(session.clarification_id)
                if entry is None:
                    return
                entry["scan_decision"] = ("submit", 0, "yes")
                entry["event"].set()
        threading.Thread(target=_inject_yes, daemon=True).start()

        try:
            pipeline._await_user_scanning_then_caregiver(
                session, "C206", "audit-scan-flow-1",
            )
        finally:
            pipeline._run_caregiver_phase = original_run_cg

        assert len(recorded["transitions"]) == 1
        result, audit, trig = recorded["transitions"][0]
        # Terminal = CLASS_1 since user accepted the first lighting candidate.
        from class2_clarification_manager.models import Class2Result
        assert isinstance(result, Class2Result)
        assert result.action_hint == "light_on"  # off-state default
        assert audit == "audit-scan-flow-1"
        assert trig == "C206"
        assert run_caregiver_called == [], (
            "Caregiver Phase 2 must NOT run when user accepted in Phase 1"
        )
        # Pipeline pulled the entry off pending after success.
        with pipeline._user_class2_lock:
            assert session.clarification_id not in pipeline._pending_user_class2

    def test_all_silence_escalates_to_caregiver(self, pipeline):
        """If the user is silent on every option, Phase 1 runs through all
        N options and falls through to caregiver Phase 2. silence ≠ consent."""
        recorded = self._mock_external_side_effects(pipeline)
        run_caregiver_called = []
        original_run_cg = pipeline._run_caregiver_phase
        pipeline._run_caregiver_phase = (
            lambda *args, **kwargs: run_caregiver_called.append(args)
        )

        session = pipeline._class2.start_session(
            trigger_id="C206",
            audit_correlation_id="audit-scan-flow-2",
            input_mode="scanning",
        )
        # Very short per-option timeout — total wait ~ N * 0.1s.
        session.scan_per_option_timeout_ms = 100

        try:
            pipeline._await_user_scanning_then_caregiver(
                session, "C206", "audit-scan-flow-2",
            )
        finally:
            pipeline._run_caregiver_phase = original_run_cg

        # User-side did NOT pick a CLASS_1/0 action → no terminal transition
        # before caregiver phase. _run_caregiver_phase must have been called.
        assert len(run_caregiver_called) == 1, (
            "Caregiver Phase 2 must run after all options exhausted"
        )

    def test_emergency_shortcut_bypasses_remaining_loop(self, pipeline):
        """A triple_hit decision early in the loop accepts the CLASS_0
        candidate immediately and returns — no further options are
        announced, no caregiver phase runs."""
        import threading

        recorded = self._mock_external_side_effects(pipeline)
        run_caregiver_called = []
        original_run_cg = pipeline._run_caregiver_phase
        pipeline._run_caregiver_phase = (
            lambda *args, **kwargs: run_caregiver_called.append(args)
        )

        session = pipeline._class2.start_session(
            trigger_id="C206",
            audit_correlation_id="audit-scan-flow-3",
            input_mode="scanning",
        )
        session.scan_per_option_timeout_ms = 5000

        def _inject_emergency():
            import time
            time.sleep(0.05)
            cg_id = next(
                (c.candidate_id for c in session.candidate_choices
                 if c.candidate_transition_target == "CLASS_0"),
                None,
            )
            with pipeline._user_class2_lock:
                entry = pipeline._pending_user_class2.get(session.clarification_id)
                if entry is None:
                    return
                entry["scan_decision"] = ("emergency", cg_id)
                entry["event"].set()
        threading.Thread(target=_inject_emergency, daemon=True).start()

        try:
            pipeline._await_user_scanning_then_caregiver(
                session, "C206", "audit-scan-flow-3",
            )
        finally:
            pipeline._run_caregiver_phase = original_run_cg

        # Emergency shortcut produces a terminal transition.
        assert len(recorded["transitions"]) == 1
        result, _, _ = recorded["transitions"][0]
        from safe_deferral_handler.models import TransitionTarget
        assert result.transition_target == TransitionTarget.CLASS_0
        assert run_caregiver_called == []

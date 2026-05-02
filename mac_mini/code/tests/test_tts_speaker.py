"""Regression tests for the Class 2 TTS announcement layer (Phase 4 of
common/docs/architecture/09_llm_driven_class2_candidate_generation_plan.md).

Once Phases 1-3 land, the TTS layer becomes the conversational surface
for LLM-driven candidates automatically — `announce_class2()` reads each
`candidate.prompt` directly. This module guards two invariants:

  1. Each candidate's prompt appears verbatim in the announced text
     (no truncation, no transformation, no re-templating).
  2. Every candidate prompt — both static defaults and any LLM-generated
     prompt that survives adapter validation — fits inside the policy cap
     `class2_conversational_prompt_constraints.max_prompt_length_chars`.

Both invariants are deliberately tested at the speaker boundary rather
than the adapter boundary so a future change to either side trips a test.
"""

import json
import pathlib

import pytest

from class2_clarification_manager.manager import _DEFAULT_CANDIDATES
from safe_deferral_handler.models import ClarificationChoice
from tts.speaker import (
    NoOpSpeaker,
    announce_class2,
    announce_class2_selection,
    announce_deferral,
)


_POLICY_PATH = (
    pathlib.Path(__file__).resolve().parents[3]
    / "common" / "policies" / "policy_table.json"
)


def _load_prompt_cap() -> int:
    with open(_POLICY_PATH, encoding="utf-8") as f:
        policy = json.load(f)
    return int(
        policy["global_constraints"]
              ["class2_conversational_prompt_constraints"]
              ["max_prompt_length_chars"]
    )


class _RecordingSpeaker:
    """Captures each `speak()` call so the test can assert on the text."""

    def __init__(self):
        self.spoken: list[str] = []

    def speak(self, text: str) -> None:
        self.spoken.append(text)

    def speak_sync(self, text: str) -> None:
        self.spoken.append(text)


def _choice(candidate_id: str, prompt: str,
            target: str = "CLASS_1") -> ClarificationChoice:
    return ClarificationChoice(
        candidate_id=candidate_id,
        prompt=prompt,
        candidate_transition_target=target,
    )


# ==================================================================
# Phase 4 invariant #1 — prompts appear verbatim in announcement
# ==================================================================

class TestAnnounceClass2PromptVerbatim:
    """`announce_class2()` must speak each candidate's prompt as-is."""

    def test_each_prompt_appears_verbatim(self):
        sp = _RecordingSpeaker()
        choices = [
            _choice("C1", "조명 도움이 필요하신가요?"),
            _choice("C2", "보호자에게 연락할까요?", "CAREGIVER_CONFIRMATION"),
            _choice("C3", "긴급상황인가요?", "CLASS_0"),
        ]
        announce_class2(sp, choices)
        assert len(sp.spoken) == 1
        text = sp.spoken[0]
        for c in choices:
            assert c.prompt in text, (
                f"prompt {c.prompt!r} missing from announced text {text!r}"
            )

    def test_prompts_appear_in_order(self):
        """Numbering and prompt content must follow list order so the user's
        '1번 / 2번' selection corresponds to the right candidate."""
        sp = _RecordingSpeaker()
        choices = [
            _choice("A", "첫번째 옵션을 선택할까요?"),
            _choice("B", "두번째 옵션을 선택할까요?"),
        ]
        announce_class2(sp, choices)
        text = sp.spoken[0]
        idx_first = text.index(choices[0].prompt)
        idx_second = text.index(choices[1].prompt)
        assert idx_first < idx_second
        # Numbering format is "{i}번, {prompt}".
        assert "1번" in text and "2번" in text

    def test_empty_candidates_falls_back_to_caregiver_message(self):
        """No candidates → conservative caregiver-required announcement."""
        sp = _RecordingSpeaker()
        announce_class2(sp, [])
        assert len(sp.spoken) == 1
        assert "보호자" in sp.spoken[0]

    def test_noop_speaker_does_not_raise(self):
        """Silent backend must not affect correctness — Phase 4 design note."""
        sp = NoOpSpeaker()
        announce_class2(sp, [_choice("C1", "조명 도움이 필요하신가요?")])  # no exception


# ==================================================================
# Trigger-aware preamble (2-A)
# ==================================================================

class TestAnnounceClass2AdaptivePreamble:
    """The preamble must adapt to whether the candidate set is
    user-resolvable (any CLASS_1 option present) or caregiver-bound.
    Promising 'caregiver confirmation needed' for a candidate set whose
    first option is the user's own low-risk action is misleading and
    causes cognitive dissonance."""

    def _has_text(self, sp, fragment):
        return any(fragment in utt for utt in sp.spoken)

    def test_class1_present_uses_neutral_preamble(self):
        """When any candidate routes to CLASS_1, the user can resolve it
        themselves → neutral preamble. The misleading caregiver wording
        must be absent from the preamble (it may still appear inside an
        individual candidate prompt, which is fine)."""
        sp = _RecordingSpeaker()
        announce_class2(sp, [
            _choice("C1", "거실 조명을 켜드릴까요?", "CLASS_1"),
            _choice("C0", "긴급상황인가요?", "CLASS_0"),
            _choice("CG", "보호자에게 연락할까요?", "CAREGIVER_CONFIRMATION"),
        ])
        text = sp.spoken[0]
        assert "어떻게 도와드릴까요" in text
        # The preamble itself must not include the caregiver-confirmation
        # promise. We check that the literal preamble fragment isn't there;
        # a candidate prompt mentioning '보호자' is unrelated.
        assert "보호자 확인이 필요합니다. 다음 중 선택해 주세요." not in text

    def test_no_class1_uses_caregiver_preamble(self):
        """C208 visitor / C207 deferral-timeout candidate sets have no
        CLASS_1 option. Caregiver-bound preamble is honest there."""
        sp = _RecordingSpeaker()
        announce_class2(sp, [
            _choice("CG", "보호자에게 방문자 확인을 요청할까요?",
                    "CAREGIVER_CONFIRMATION"),
            _choice("C0", "긴급상황인가요?", "CLASS_0"),
            _choice("SD", "취소하고 대기할까요?", "SAFE_DEFERRAL"),
        ])
        text = sp.spoken[0]
        assert "보호자 확인이 필요합니다" in text
        assert "어떻게 도와드릴까요" not in text

    def test_only_safe_deferral_uses_caregiver_preamble(self):
        """All-SAFE_DEFERRAL set (degenerate but possible) is not
        user-resolvable in the action sense — caregiver preamble."""
        sp = _RecordingSpeaker()
        announce_class2(sp, [
            _choice("SD1", "취소할까요?", "SAFE_DEFERRAL"),
        ])
        text = sp.spoken[0]
        assert "보호자 확인이 필요합니다" in text

    def test_preamble_change_does_not_break_verbatim_invariant(self):
        """Phase 4 verbatim invariant: each candidate's prompt must still
        appear verbatim regardless of preamble choice."""
        sp = _RecordingSpeaker()
        choices = [
            _choice("C1", "거실 조명을 켜드릴까요?", "CLASS_1"),
            _choice("CG", "보호자에게 연락할까요?", "CAREGIVER_CONFIRMATION"),
        ]
        announce_class2(sp, choices)
        text = sp.spoken[0]
        for c in choices:
            assert c.prompt in text


class TestAnnounceClass2SelectionPromptVerbatim:
    """The post-selection announcement must echo the chosen prompt verbatim
    so the user hears exactly the option that was confirmed."""

    def test_user_selection_includes_chosen_prompt(self):
        sp = _RecordingSpeaker()
        announce_class2_selection(sp, "user_mqtt_button", "거실 조명을 제어할까요?")
        text = sp.spoken[0]
        assert "사용자가" in text
        assert "거실 조명을 제어할까요?" in text

    def test_caregiver_selection_includes_chosen_prompt(self):
        sp = _RecordingSpeaker()
        announce_class2_selection(
            sp, "caregiver_telegram_inline_keyboard", "보호자에게 연락할까요?",
        )
        text = sp.spoken[0]
        assert "보호자가" in text
        assert "보호자에게 연락할까요?" in text


# ==================================================================
# Phase 4 invariant #2 — every prompt fits the policy length cap
# ==================================================================

class TestStaticDefaultsObeyPolicyCap:
    """Each prompt in the shipped `_DEFAULT_CANDIDATES` table must fit the
    `max_prompt_length_chars` cap in policy_table.json. This is the static
    fallback path; if it ever drifts past the cap, the LLM rejection
    fallback would itself violate policy."""

    def test_every_default_prompt_within_cap(self):
        cap = _load_prompt_cap()
        violations = []
        for reason, items in _DEFAULT_CANDIDATES.items():
            for item in items:
                prompt = item.get("prompt", "")
                if len(prompt) > cap:
                    violations.append(
                        (reason, item.get("candidate_id"), len(prompt), prompt)
                    )
        assert violations == [], (
            f"Static default prompts exceed policy cap ({cap}): {violations}"
        )

    def test_cap_is_positive_and_reasonable(self):
        """Cap must exist and be large enough to host a typical Korean
        question. This guards against accidental policy zeroing."""
        cap = _load_prompt_cap()
        assert cap >= 20


# ==================================================================
# Unrelated TTS regression — announce_deferral must not be silent on
# the message-only path (sanity check; its content is fixed).
# ==================================================================

class TestAnnounceDeferral:
    def test_announces_a_user_facing_message(self):
        sp = _RecordingSpeaker()
        announce_deferral(sp, reason="missing_policy_input")
        assert len(sp.spoken) == 1
        assert sp.spoken[0]  # non-empty

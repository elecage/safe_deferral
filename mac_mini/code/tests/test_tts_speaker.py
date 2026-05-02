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
    announce_class2_option,
    announce_class2_scanning_start,
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
            # Use the post-state-aware-refactor prompt shape (PR #106) so the
            # fixture matches what the manager actually emits today. The
            # speaker's verbatim invariant is independent of the prompt text;
            # the test could use any string, but mirroring real prompts keeps
            # the fixture instructive.
            _choice("C1", "거실 조명을 켜드릴까요?"),
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
        announce_class2(sp, [_choice("C1", "거실 조명을 켜드릴까요?")])  # no exception


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


class TestAnnounceClass2SelectionFallback:
    """When the caller cannot supply a selection_label (e.g. legacy code
    path or LLM-generated candidate without a label), the announcement
    falls back to embedding the full prompt verbatim so the user still
    hears what was confirmed (awkward but never misleading)."""

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


class TestAnnounceClass2SelectionLabel:
    """When a candidate carries `selection_label`, the announcement uses the
    natural noun-phrase form ("사용자가 긴급 상황을 선택하셨습니다.") rather
    than echoing the full question prompt."""

    def test_label_form_used_when_provided(self):
        sp = _RecordingSpeaker()
        announce_class2_selection(
            sp, "user_mqtt_button",
            chosen_prompt="긴급상황인가요?",
            selection_label="긴급 상황",
        )
        text = sp.spoken[0]
        # Natural form — label + 을 (jongseong present in 황) + 선택하셨습니다
        assert text == "사용자가 긴급 상황을 선택하셨습니다."
        # Awkward verbatim prompt must NOT appear anywhere
        assert "긴급상황인가요?" not in text

    def test_label_picks_eul_for_jongseong(self):
        sp = _RecordingSpeaker()
        # "보호자 연락" ends in 락 (jongseong ㄱ) → 을
        announce_class2_selection(
            sp, "user_mqtt_button", "보호자에게 연락할까요?",
            selection_label="보호자 연락",
        )
        assert sp.spoken[0] == "사용자가 보호자 연락을 선택하셨습니다."

    def test_label_picks_reul_for_no_jongseong(self):
        sp = _RecordingSpeaker()
        # "조명 제어" ends in 어 (no jongseong) → 를
        announce_class2_selection(
            sp, "user_mqtt_button", "조명을 도와드릴까요?",
            selection_label="조명 제어",
        )
        assert sp.spoken[0] == "사용자가 조명 제어를 선택하셨습니다."

    def test_caregiver_prefix_with_label(self):
        sp = _RecordingSpeaker()
        announce_class2_selection(
            sp, "caregiver_telegram_inline_keyboard",
            "보호자에게 연락할까요?",
            selection_label="보호자 연락",
        )
        assert sp.spoken[0] == "보호자가 보호자 연락을 선택하셨습니다."

    def test_empty_label_falls_back_to_prompt(self):
        sp = _RecordingSpeaker()
        announce_class2_selection(
            sp, "user_mqtt_button", "거실 조명을 켜드릴까요?",
            selection_label="",
        )
        text = sp.spoken[0]
        assert "거실 조명을 켜드릴까요?" in text   # fallback used


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


# ==================================================================
# doc 12 Phase 2 — scanning TTS helpers
# ==================================================================

class TestAnnounceClass2ScanningStart:
    """Scanning preamble explains the interaction model once and tells
    the user how many questions to expect (working-memory budgeting)."""

    def test_speaks_total_count_and_yes_no_hint(self):
        sp = _RecordingSpeaker()
        announce_class2_scanning_start(sp, total_options=4)
        assert len(sp.spoken) == 1
        text = sp.spoken[0]
        assert "총 4개" in text
        assert "예" in text and "아니오" in text

    def test_zero_options_falls_back_to_caregiver(self):
        """Defensive: 0 options is a degenerate state; caregiver fallback
        keeps the silence-never-executes invariant."""
        sp = _RecordingSpeaker()
        announce_class2_scanning_start(sp, total_options=0)
        assert "보호자" in sp.spoken[0]

    def test_noop_speaker_safe(self):
        announce_class2_scanning_start(NoOpSpeaker(), total_options=3)


class TestAnnounceClass2Option:
    """Per-option scanning utterance must (a) carry the candidate prompt
    verbatim (PR #97 invariant), (b) include a position cue '{n}/{N}',
    and (c) use 1-based indexing for the user-facing position number."""

    def test_format_includes_position_cue_and_prompt_verbatim(self):
        sp = _RecordingSpeaker()
        ch = _choice("C1", "거실 조명을 켜드릴까요?", "CLASS_1")
        announce_class2_option(sp, option_index=0, candidate=ch, total_options=3)
        text = sp.spoken[0]
        assert text.startswith("1/3.")
        assert "거실 조명을 켜드릴까요?" in text

    def test_position_cue_uses_one_based_index(self):
        """option_index is 0-based internally; user hears 1-based numbers."""
        sp = _RecordingSpeaker()
        ch = _choice("C2", "보호자에게 연락할까요?", "CAREGIVER_CONFIRMATION")
        announce_class2_option(sp, option_index=2, candidate=ch, total_options=4)
        assert sp.spoken[0].startswith("3/4.")

    def test_prompt_verbatim_invariant(self):
        """PR #97 verbatim invariant carries into scanning: every per-option
        utterance must contain the candidate's prompt as-is."""
        sp = _RecordingSpeaker()
        ch = _choice("C0", "긴급상황인가요?", "CLASS_0")
        announce_class2_option(sp, option_index=1, candidate=ch, total_options=4)
        assert "긴급상황인가요?" in sp.spoken[0]

    def test_invalid_inputs_raise(self):
        sp = _RecordingSpeaker()
        ch = _choice("C1", "거실 조명을 켜드릴까요?", "CLASS_1")
        with pytest.raises(ValueError):
            announce_class2_option(sp, option_index=-1, candidate=ch, total_options=3)
        with pytest.raises(ValueError):
            announce_class2_option(sp, option_index=0, candidate=ch, total_options=0)

    def test_noop_speaker_safe(self):
        ch = _choice("C1", "거실 조명을 켜드릴까요?", "CLASS_1")
        announce_class2_option(NoOpSpeaker(), 0, ch, 3)


class TestScanningTTSCompositionFlow:
    """A typical scanning session: start preamble + N per-option utterances.
    Verify ordering and that each spoken utterance carries the right
    position cue and prompt."""

    def test_full_session_utterance_sequence(self):
        sp = _RecordingSpeaker()
        choices = [
            _choice("C1", "거실 조명을 켜드릴까요?", "CLASS_1"),
            _choice("C0", "긴급상황인가요?", "CLASS_0"),
            _choice("C4", "다른 동작이 필요하신가요?", "SAFE_DEFERRAL"),
        ]
        announce_class2_scanning_start(sp, total_options=len(choices))
        for i, c in enumerate(choices):
            announce_class2_option(sp, option_index=i, candidate=c,
                                    total_options=len(choices))
        # 1 preamble + 3 per-option = 4 utterances
        assert len(sp.spoken) == 4
        assert "총 3개" in sp.spoken[0]
        for i, c in enumerate(choices, 1):
            assert sp.spoken[i].startswith(f"{i}/3.")
            assert c.prompt in sp.spoken[i]

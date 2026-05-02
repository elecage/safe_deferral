"""TTS Speaker (MM-TTS).

Provides audible feedback for key pipeline events so users with severe
physical or speech limitations can hear system state without looking at
a screen.

Authority boundary:
  - TTS is output-only notification.  It does not drive policy decisions,
    validator approval, actuator commands, or caregiver confirmation.
  - Silence (TTS disabled / NoOp) must never affect system correctness.

Backends (in preference order):
  1. MacOsSaySpeaker  — macOS `say` command (no extra dependencies).
     Korean voice: Yuna (pre-installed on macOS).  Falls back to system
     default voice if Yuna is unavailable.
  2. NoOpSpeaker      — silent; used when TTS_ENABLED=false or on
     non-macOS platforms.

Environment variables:
  TTS_ENABLED   "true" (default) | "false" — disable all speech output.
  TTS_VOICE     macOS voice name, default "Yuna" (Korean).
  TTS_RATE      words-per-minute passed to `say -r`, default "" (system default).
"""

import logging
import os
import platform
import subprocess
import threading
from typing import Optional, Protocol

log = logging.getLogger("sd.tts")

# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

class TtsSpeaker(Protocol):
    """Minimal interface for text-to-speech output."""

    def speak(self, text: str) -> None:
        """Speak text asynchronously.  Never blocks the calling thread."""
        ...

    def speak_sync(self, text: str) -> None:
        """Speak text and wait until utterance finishes."""
        ...


# ---------------------------------------------------------------------------
# NoOp (silent)
# ---------------------------------------------------------------------------

class NoOpSpeaker:
    """Silent speaker — used when TTS is disabled or platform unsupported."""

    def speak(self, text: str) -> None:
        log.debug("TTS(NoOp): %r", text)

    def speak_sync(self, text: str) -> None:
        log.debug("TTS(NoOp sync): %r", text)


# ---------------------------------------------------------------------------
# macOS `say` backend
# ---------------------------------------------------------------------------

class MacOsSaySpeaker:
    """TTS via the macOS built-in `say` command.

    speak() fires a daemon thread and returns immediately.
    speak_sync() blocks until the utterance finishes.

    A single serial lock (_lock) prevents overlapping utterances —
    the previous one is cancelled if a new one arrives while it is
    still playing.

    Yuna is the pre-installed Korean voice on macOS.  If the voice is
    not found, `say` falls back to the system default voice automatically.
    """

    def __init__(self, voice: str = "Yuna", rate: str = "") -> None:
        self._voice = voice
        self._rate = rate
        self._lock = threading.Lock()
        self._current: Optional[subprocess.Popen] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def speak(self, text: str) -> None:
        """Start speech in a daemon thread; return immediately."""
        threading.Thread(
            target=self._run,
            args=(text,),
            daemon=True,
            name="tts-say",
        ).start()

    def speak_sync(self, text: str) -> None:
        """Speak and block until done."""
        self._run(text)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self, text: str) -> None:
        cmd = ["say", "-v", self._voice]
        if self._rate:
            cmd += ["-r", self._rate]
        cmd.append(text)

        with self._lock:
            # Cancel any currently running utterance
            if self._current and self._current.poll() is None:
                self._current.terminate()
                self._current.wait()
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self._current = proc
            except FileNotFoundError:
                log.warning("TTS: `say` command not found — TTS disabled for this call")
                return
            except Exception as exc:
                log.warning("TTS: failed to start `say`: %s", exc)
                return

        # Wait outside the lock so other threads can preempt
        try:
            proc.wait()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def make_speaker() -> TtsSpeaker:
    """Create the appropriate TTS speaker from environment variables.

    Returns MacOsSaySpeaker on macOS when TTS_ENABLED != 'false',
    otherwise NoOpSpeaker.
    """
    enabled = os.environ.get("TTS_ENABLED", "true").lower() not in ("false", "0", "no")
    if not enabled:
        log.info("TTS disabled via TTS_ENABLED env var.")
        return NoOpSpeaker()

    if platform.system() != "Darwin":
        log.info("TTS: platform is %s, not macOS — using NoOp.", platform.system())
        return NoOpSpeaker()

    voice = os.environ.get("TTS_VOICE", "Yuna")
    rate = os.environ.get("TTS_RATE", "")
    log.info("TTS: macOS `say` speaker (voice=%s rate=%s)", voice, rate or "default")
    return MacOsSaySpeaker(voice=voice, rate=rate)


# ---------------------------------------------------------------------------
# Canned announcement helpers
# ---------------------------------------------------------------------------

_ACTION_KO: dict[str, str] = {
    "light_on":  "조명을 켭니다",
    "light_off": "조명을 끕니다",
}

_DEVICE_KO: dict[str, str] = {
    "living_room_light": "거실",
    "bedroom_light":     "침실",
}


def announce_dispatch(speaker: TtsSpeaker, action: str, target_device: str) -> None:
    """Announce a CLASS_1 approved actuation."""
    device = _DEVICE_KO.get(target_device, target_device)
    verb   = _ACTION_KO.get(action, action)
    text = f"{device} {verb}."
    log.info("TTS announce_dispatch: %r", text)
    speaker.speak(text)


def announce_emergency(speaker: TtsSpeaker, trigger_id: str) -> None:
    """Announce a CLASS_0 emergency."""
    text = f"긴급 상황이 감지되었습니다. 보호자에게 알립니다."
    log.info("TTS announce_emergency: %r (trigger=%s)", text, trigger_id)
    speaker.speak(text)


def announce_deferral(speaker: TtsSpeaker, reason: str) -> None:
    """Announce a safe deferral."""
    text = "처리가 유예되었습니다. 잠시 후 다시 시도해 주세요."
    log.info("TTS announce_deferral: %r (reason=%s)", text, reason)
    speaker.speak(text)


def announce_class2(speaker: TtsSpeaker, candidates: list) -> None:
    """Read out CLASS_2 candidate choices so the user can hear options.

    The preamble adapts to the candidate set:
      - If any candidate routes to CLASS_1 (a low-risk action the user can
        confirm themselves), a neutral 'how can I help' preamble is used.
        Promising 'caregiver confirmation needed' here is misleading because
        most picks won't actually involve the caregiver.
      - Otherwise (all candidates route to caregiver / emergency / deferral —
        e.g. C208 doorlock-sensitive, C207 deferral timeout), the
        caregiver-bound preamble is honest and used.

    Empty candidate set falls back to caregiver preamble (defensive — the
    only safe announcement when the manager has nothing to offer).
    """
    if not candidates:
        speaker.speak("보호자 확인이 필요합니다.")
        return

    has_user_resolvable = any(
        getattr(c, "candidate_transition_target", None) == "CLASS_1"
        for c in candidates
    )
    if has_user_resolvable:
        preamble = "어떻게 도와드릴까요? 다음 중 선택해 주세요."
    else:
        preamble = "보호자 확인이 필요합니다. 다음 중 선택해 주세요."

    prompts = [c.prompt for c in candidates]
    parts = [preamble]
    for i, prompt in enumerate(prompts, 1):
        parts.append(f"{i}번, {prompt}")
    text = " ".join(parts)
    log.info("TTS announce_class2: %d candidates (caregiver_preamble=%s)",
             len(candidates), not has_user_resolvable)
    speaker.speak(text)


def announce_class2_scanning_start(speaker: TtsSpeaker, total_options: int) -> None:
    """Preamble for a Class 2 scanning session (doc 12 Phase 2).

    Spoken ONCE at the start of a scanning session to set the user's
    expectation that questions will arrive sequentially and a single
    yes / no per turn is the expected response. Counts the total number
    of upcoming questions so the user has a sense of progress.

    Subsequent per-option utterances are produced by announce_class2_option.
    """
    if total_options <= 0:
        speaker.speak("보호자 확인이 필요합니다.")
        return
    text = (
        f"질문을 하나씩 드리겠습니다. 총 {total_options}개입니다. "
        "예 또는 아니오로 답해 주세요."
    )
    log.info("TTS announce_class2_scanning_start: %d options", total_options)
    speaker.speak(text)


def announce_class2_option(
    speaker: TtsSpeaker,
    option_index: int,
    candidate,
    total_options: int,
) -> None:
    """One scanning-turn utterance (doc 12 Phase 2).

    Format: '{n}/{N}. {candidate.prompt}' — the leading position cue
    ('1/3', '2/3', ...) tells the user how many options remain, which
    is a cognitive aid (working memory budgeting) and an accessibility
    aid (knowing 'this is the last chance' affects answer choice).

    The candidate.prompt is included verbatim so the Phase 4 verbatim
    invariant from PR #97 carries forward into scanning mode.
    """
    if option_index < 0 or total_options <= 0:
        raise ValueError(
            f"invalid option_index={option_index} or total_options={total_options}"
        )
    n = option_index + 1  # 1-based for the user
    text = f"{n}/{total_options}. {candidate.prompt}"
    log.info(
        "TTS announce_class2_option: %d/%d candidate_id=%s",
        n, total_options, getattr(candidate, "candidate_id", "<?>"),
    )
    speaker.speak(text)


def announce_class2_selection(
    speaker: TtsSpeaker,
    selection_source: str,
    chosen_prompt: str,
) -> None:
    """Announce who made a CLASS_2 selection and what was chosen.

    Called after both user (Phase 1) and caregiver (Phase 2) selections so
    the user receives audible feedback on which option was confirmed.

    selection_source examples: "user_mqtt_button", "caregiver_telegram_inline_keyboard",
    "user_mqtt_button_late".
    chosen_prompt: the human-readable prompt string from the selected candidate
    (e.g. "조명 도움이 필요하신가요?", "거실 조명을 제어할까요?").
    """
    if "caregiver" in selection_source:
        prefix = "보호자가"
    else:
        prefix = "사용자가"
    text = f"{prefix} '{chosen_prompt}'을(를) 선택했습니다."
    log.info("TTS announce_class2_selection: %r", text)
    speaker.speak(text)

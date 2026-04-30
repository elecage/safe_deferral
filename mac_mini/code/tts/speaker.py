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

    Speaks a preamble then each candidate prompt in order.
    """
    if not candidates:
        speaker.speak("보호자 확인이 필요합니다.")
        return

    prompts = [c.prompt for c in candidates]
    parts = ["보호자 확인이 필요합니다. 다음 중 선택해 주세요."]
    for i, prompt in enumerate(prompts, 1):
        parts.append(f"{i}번, {prompt}")
    text = " ".join(parts)
    log.info("TTS announce_class2: %d candidates", len(candidates))
    speaker.speak(text)

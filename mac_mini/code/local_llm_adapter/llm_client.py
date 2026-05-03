"""LLM client protocol and implementations (MM-02).

OllamaClient  — production, calls local Ollama HTTP API.
MockLlmClient — deterministic, for experiments and unit tests.
"""

from typing import Optional, Protocol


class LlmClient(Protocol):
    """Minimal interface the adapter needs from an LLM backend."""

    def complete(self, prompt: str) -> str:
        """Return the model's text completion for the given prompt."""
        ...

    @property
    def model_id(self) -> str: ...


class OllamaClient:
    """Production client — calls the local Ollama REST API.

    Default endpoint: http://localhost:11434/api/generate
    Requires `requests` package (lazy import so tests never need it).

    Sampling parameters (temperature, top_p) are tunable so paper-eval
    sweeps can quantify how LLM stochasticity affects routing accuracy.
    Defaults match the historic hardcoded values (temperature=0.2, top_p
    not sent → Ollama default 0.9) so existing callers see no behaviour
    change.
    """

    _DEFAULT_URL = "http://localhost:11434/api/generate"
    _DEFAULT_TEMPERATURE = 0.2

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = _DEFAULT_URL,
        timeout_s: int = 60,
        temperature: float = _DEFAULT_TEMPERATURE,
        top_p: Optional[float] = None,
    ) -> None:
        self._model = model
        self._url = base_url
        self._timeout = timeout_s
        self._temperature = temperature
        self._top_p = top_p

    @property
    def model_id(self) -> str:
        return self._model

    def complete(self, prompt: str) -> str:
        import requests  # lazy import

        options = {"temperature": self._temperature}
        if self._top_p is not None:
            options["top_p"] = self._top_p
        resp = requests.post(
            self._url,
            json={
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": options,
            },
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")


class MockLlmClient:
    """Deterministic mock client for experiments and unit tests.

    Returns a fixed JSON string that the adapter will parse and validate.
    Use `set_response()` to change the returned value between test cases.
    """

    def __init__(self, fixed_response: Optional[str] = None) -> None:
        self._response = (
            fixed_response if fixed_response is not None
            else (
                '{"proposed_action": "light_on", "target_device": "living_room_light", '
                '"rationale_summary": "mock: occupancy detected, light requested"}'
            )
        )

    @property
    def model_id(self) -> str:
        return "mock"

    def set_response(self, response: str) -> None:
        self._response = response

    def complete(self, prompt: str) -> str:
        return self._response

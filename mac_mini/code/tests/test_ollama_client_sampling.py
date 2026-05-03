"""Tests for OllamaClient sampling-parameter handling.

Paper-eval sweeps vary temperature × top_p across a grid to quantify
how LLM stochasticity affects routing accuracy. Defaults must keep
historic behaviour (temperature=0.2, top_p unset → Ollama default 0.9)
so existing callers see no behaviour change.
"""

from unittest.mock import MagicMock, patch

import pytest

from local_llm_adapter.llm_client import OllamaClient


def _mock_ollama_response(text: str = "{}"):
    """Build a mock requests.post return that emulates an Ollama success."""
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"response": text}
    return resp


class TestDefaults:
    def test_default_temperature_is_0_2(self):
        client = OllamaClient(model="llama3.1")
        assert client._temperature == 0.2

    def test_default_top_p_is_none(self):
        client = OllamaClient(model="llama3.1")
        assert client._top_p is None


class TestSentOptions:
    def test_default_sends_temperature_only(self):
        """Without explicit top_p, options must NOT include 'top_p' so
        Ollama applies its own default (0.9). Sending top_p=null would
        be valid JSON but communicates 'force null' which is different."""
        client = OllamaClient(model="m")
        with patch("requests.post", return_value=_mock_ollama_response()) as mock_post:
            client.complete("p")
        sent = mock_post.call_args.kwargs["json"]
        assert sent["options"] == {"temperature": 0.2}
        assert "top_p" not in sent["options"]

    def test_explicit_temperature_passed_through(self):
        client = OllamaClient(model="m", temperature=0.7)
        with patch("requests.post", return_value=_mock_ollama_response()) as mock_post:
            client.complete("p")
        sent = mock_post.call_args.kwargs["json"]
        assert sent["options"]["temperature"] == 0.7

    def test_explicit_top_p_passed_through(self):
        client = OllamaClient(model="m", top_p=0.5)
        with patch("requests.post", return_value=_mock_ollama_response()) as mock_post:
            client.complete("p")
        sent = mock_post.call_args.kwargs["json"]
        assert sent["options"]["top_p"] == 0.5
        # Temperature default still present too.
        assert sent["options"]["temperature"] == 0.2

    def test_both_params_passed_together(self):
        client = OllamaClient(model="m", temperature=0.4, top_p=0.6)
        with patch("requests.post", return_value=_mock_ollama_response()) as mock_post:
            client.complete("p")
        opts = mock_post.call_args.kwargs["json"]["options"]
        assert opts == {"temperature": 0.4, "top_p": 0.6}

    def test_zero_temperature_is_kept_not_dropped(self):
        """Greedy sampling (temperature=0.0) is a valid paper-eval value
        and must be sent, not silently replaced with the default."""
        client = OllamaClient(model="m", temperature=0.0)
        with patch("requests.post", return_value=_mock_ollama_response()) as mock_post:
            client.complete("p")
        opts = mock_post.call_args.kwargs["json"]["options"]
        assert opts["temperature"] == 0.0

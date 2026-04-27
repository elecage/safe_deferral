"""Local LLM Adapter (MM-02).

Accepts pure_context_payload from upstream components, composes a bounded
prompt, calls the injected LLM client, validates the response against
candidate_action_schema.json, and returns an LLMCandidateResult.

Authority boundary (02_safety_and_authority_boundaries.md §4):
  - Output is candidate guidance only.
  - No final class decision, no validator approval, no actuator command,
    no emergency trigger declaration, no doorlock authorization.
  - Invalid or unparseable LLM output always falls back to safe_deferral.
  - trigger_event.timestamp_ms is masked before prompt composition.
  - routing_metadata is never passed to the LLM.
"""

import json
import re
from typing import Optional

import jsonschema

from local_llm_adapter.llm_client import LlmClient, MockLlmClient
from local_llm_adapter.models import LLMCandidateResult
from local_llm_adapter.prompt_builder import build_prompt
from shared.asset_loader import AssetLoader

_SAFE_DEFERRAL_FALLBACK = {
    "proposed_action": "safe_deferral",
    "target_device": "none",
    "deferral_reason": "insufficient_context",
}


class LocalLlmAdapter:
    """Bounded LLM candidate generator.

    Typical usage:
        adapter = LocalLlmAdapter()                    # uses MockLlmClient
        adapter = LocalLlmAdapter(OllamaClient())      # production
        result  = adapter.generate_candidate(
            pure_context_payload, audit_correlation_id="abc-123"
        )
    """

    def __init__(
        self,
        llm_client: Optional[LlmClient] = None,
        asset_loader: Optional[AssetLoader] = None,
    ) -> None:
        loader = asset_loader or AssetLoader()
        self._schema = loader.load_schema("candidate_action_schema.json")
        self._resolver = loader.make_schema_resolver()
        self._client: LlmClient = llm_client or MockLlmClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_candidate(
        self,
        pure_context_payload: dict,
        audit_correlation_id: str = "",
        event_code: Optional[str] = None,
    ) -> LLMCandidateResult:
        """Generate a bounded candidate action from context.

        pure_context_payload must conform to context_schema.json.
        trigger_event.timestamp_ms is masked automatically before prompting.

        Returns LLMCandidateResult with is_fallback=True if the LLM response
        is invalid, unparseable, or a call exception occurs.
        """
        code = (
            event_code
            or pure_context_payload.get("trigger_event", {}).get("event_code", "unknown")
        )
        prompt = build_prompt(pure_context_payload, code)

        raw_response: Optional[str] = None
        try:
            raw_response = self._client.complete(prompt)
            candidate = self._parse_and_validate(raw_response)
            return LLMCandidateResult(
                candidate=candidate,
                is_fallback=False,
                audit_correlation_id=audit_correlation_id,
                llm_raw_response=raw_response,
                model_id=self._client.model_id,
            )
        except Exception:
            return LLMCandidateResult(
                candidate=dict(_SAFE_DEFERRAL_FALLBACK),
                is_fallback=True,
                audit_correlation_id=audit_correlation_id,
                llm_raw_response=raw_response,
                model_id=self._client.model_id,
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_and_validate(self, raw: str) -> dict:
        """Extract JSON from raw LLM text and validate against schema.

        Raises ValueError / jsonschema.ValidationError on failure so that
        generate_candidate() can catch and return the safe fallback.
        """
        candidate = self._extract_json(raw)
        validator = jsonschema.Draft7Validator(self._schema, resolver=self._resolver)
        errors = list(validator.iter_errors(candidate))
        if errors:
            raise jsonschema.ValidationError(errors[0].message)
        return candidate

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract the first JSON object from LLM text output.

        LLMs occasionally wrap JSON in markdown fences or add surrounding prose.
        """
        text = text.strip()
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Strip markdown fences
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced:
            return json.loads(fenced.group(1))
        # Find first {...} block
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        if brace:
            return json.loads(brace.group(0))
        raise ValueError(f"No JSON object found in LLM output: {text[:120]!r}")

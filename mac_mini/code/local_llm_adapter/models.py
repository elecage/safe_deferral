"""Data models for the Local LLM Adapter (MM-02)."""

from dataclasses import dataclass, field
from typing import Optional


_LLM_BOUNDARY = {
    "candidate_generation_only": True,
    "final_decision_allowed": False,
    "actuation_authority_allowed": False,
    "emergency_trigger_authority_allowed": False,
}


@dataclass
class LLMCandidateResult:
    """Output of LocalLlmAdapter.generate_candidate().

    Authority boundary:
      - candidate is guidance only.
      - It must pass through DeterministicValidator before any dispatch.
      - is_fallback=True means the LLM failed or produced invalid output;
        safe_deferral is always the conservative fallback.
    """

    candidate: dict                    # validated against candidate_action_schema.json
    is_fallback: bool                  # True when LLM output was invalid/unparseable
    audit_correlation_id: str
    llm_raw_response: Optional[str]    # raw text for audit; None in mock mode
    model_id: str                      # e.g. "llama3.2" or "mock"
    llm_boundary: dict = field(default_factory=lambda: dict(_LLM_BOUNDARY))

    @property
    def proposed_action(self) -> str:
        return self.candidate.get("proposed_action", "safe_deferral")

    @property
    def target_device(self) -> str:
        return self.candidate.get("target_device", "none")

    @property
    def is_safe_deferral(self) -> bool:
        return self.proposed_action == "safe_deferral"

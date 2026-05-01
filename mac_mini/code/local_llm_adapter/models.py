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


@dataclass
class Class2CandidateResult:
    """Output of LocalLlmAdapter.generate_class2_candidates().

    Authority boundary:
      - candidate set is guidance only — it does not authorize execution.
      - Class2ClarificationManager owns the static fallback; this result
        merely tells the manager whether usable LLM candidates are available.

    Fields:
      candidates: list of candidate dicts compatible with
        Class2ClarificationManager._DEFAULT_CANDIDATES item shape:
        {candidate_id, prompt, candidate_transition_target,
         action_hint, target_hint}. Empty list means "fall back".
      candidate_source: "llm_generated" or "default_fallback".
      rejection_reason: short string explaining why LLM output was rejected
        (only set when candidate_source=default_fallback). Audit-visible.
      generated_at_ms: wall-clock generation timestamp.
      model_id: LLM model identifier or "static_default_fallback".
      llm_raw_response: raw text for audit (None in mock or fallback mode).
      prompt_constraints_applied: echo of bounded-variability constraints.
    """

    candidates: list                   # validated against class2_candidate_set_schema.json
    candidate_source: str              # "llm_generated" | "default_fallback"
    generated_at_ms: int
    model_id: str
    rejection_reason: Optional[str] = None
    llm_raw_response: Optional[str] = None
    prompt_constraints_applied: Optional[dict] = None
    llm_boundary: dict = field(default_factory=lambda: dict(_LLM_BOUNDARY))

    @property
    def is_usable(self) -> bool:
        """True when the manager should adopt these candidates as-is."""
        return self.candidate_source == "llm_generated" and bool(self.candidates)

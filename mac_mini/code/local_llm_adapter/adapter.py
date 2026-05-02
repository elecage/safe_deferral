"""Local LLM Adapter (MM-02).

Accepts pure_context_payload from upstream components, composes a bounded
prompt, calls the injected LLM client, validates the response against
candidate_action_schema.json, and returns an LLMCandidateResult.

Class 2 candidate generation
(09_llm_driven_class2_candidate_generation_plan.md Phase 1):
  generate_class2_candidates() produces a bounded set of clarification
  candidates the Class2ClarificationManager can hand straight to
  start_session(candidate_choices=...). Each candidate's prompt is
  constrained for accessibility (length, must-be-question, no jargon),
  each action_hint must be in low_risk_actions.json, and CLASS_0 candidates
  are restricted to a fixed safe template so the LLM cannot invent
  emergency rationales. Invalid LLM output returns a default_fallback
  result so the manager can use its static _DEFAULT_CANDIDATES.

Authority boundary (02_safety_and_authority_boundaries.md §4):
  - Output is candidate guidance only.
  - No final class decision, no validator approval, no actuator command,
    no emergency trigger declaration, no doorlock authorization.
  - Invalid or unparseable LLM output always falls back to safe_deferral
    (Class 1 path) or default_fallback (Class 2 path).
  - trigger_event.timestamp_ms is masked before prompt composition.
  - routing_metadata is never passed to the LLM.
"""

import json
import re
import time
from typing import Optional

import jsonschema

from local_llm_adapter.llm_client import LlmClient, MockLlmClient
from local_llm_adapter.models import Class2CandidateResult, LLMCandidateResult
from local_llm_adapter.prompt_builder import (
    build_class2_candidate_prompt,
    build_prompt,
)
from shared.asset_loader import AssetLoader

_SAFE_DEFERRAL_FALLBACK = {
    "proposed_action": "safe_deferral",
    "target_device": "none",
    "deferral_reason": "insufficient_context",
}

# Bounded-variability constraints for Class 2 candidate prompts.
# (09_llm_driven_class2_candidate_generation_plan.md §5.)
#
# Authoritative source: policy_table.json
#   global_constraints.class2_conversational_prompt_constraints
# loaded at LocalLlmAdapter.__init__. The literal below is the safe fallback
# used only when the policy block is missing (e.g. older policy_table that
# pre-dates Phase 3) so the adapter is never blocked by a missing policy
# entry. Operations should adjust the policy block, not this fallback.
_CLASS2_PROMPT_CONSTRAINTS_FALLBACK: dict = {
    "max_prompt_length_chars": 80,
    "prompt_must_be_question": True,
    "must_include_target_action_in_prompt": False,
    "vocabulary_tier": "plain_korean",
    "forbidden_phrasings": [
        "unlock", "doorlock", "open the door", "도어락", "잠금 해제",
        "emergency dispatch", "긴급 출동",
    ],
}

# Question-marker characters accepted as "ends with a question mark".
_QUESTION_MARKERS = ("?", "？")

# Fixed CLASS_0 candidate template — the LLM may decide whether to include
# an emergency option, but it cannot invent the wording or candidate_id.
_FIXED_EMERGENCY_CANDIDATE: dict = {
    "candidate_id": "C3_EMERGENCY_HELP",
    "prompt": "긴급상황인가요?",
    "candidate_transition_target": "CLASS_0",
    "action_hint": None,
    "target_hint": None,
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
        self._class2_schema = loader.load_schema("class2_candidate_set_schema.json")
        self._resolver = loader.make_schema_resolver()
        self._client: LlmClient = llm_client or MockLlmClient()
        # Pre-extract the canonical low-risk action / target sets so the
        # Class 2 candidate validator can reject LLM proposals that reference
        # actions outside the catalog before they ever reach the manager.
        catalog = loader.load_low_risk_actions()
        self._allowed_actions: set[str] = set()
        self._allowed_targets_by_action: dict[str, set[str]] = {}
        for entry in catalog.get("allowed_actions_taxonomy", []):
            action = entry.get("action")
            if action:
                self._allowed_actions.add(action)
                self._allowed_targets_by_action[action] = set(entry.get("allowed_targets", []))
        # Phase 3: load bounded-variability constraints from
        # policy_table.json::global_constraints.class2_conversational_prompt_constraints.
        # Falls back to the module default when the block is missing so older
        # policy versions remain usable.
        try:
            policy = loader.load_policy_table()
        except Exception:
            policy = {}
        gc = (policy.get("global_constraints") or {})
        policy_constraints = gc.get("class2_conversational_prompt_constraints") or {}
        # Strip the optional self-documenting "_description" key before applying.
        policy_constraints = {
            k: v for k, v in policy_constraints.items() if not k.startswith("_")
        }
        merged_constraints: dict = dict(_CLASS2_PROMPT_CONSTRAINTS_FALLBACK)
        merged_constraints.update(policy_constraints)
        # max_candidate_count is sourced from the existing
        # class2_max_candidate_options policy field — keep a single source of
        # truth so the manager's cap and the adapter's cap cannot drift.
        merged_constraints.setdefault(
            "max_candidate_count", gc.get("class2_max_candidate_options", 4),
        )
        self._class2_prompt_constraints: dict = merged_constraints

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
    # Class 2 candidate generation (Phase 1 of 09_llm_driven_class2_*)
    # ------------------------------------------------------------------

    def generate_class2_candidates(
        self,
        pure_context_payload: dict,
        unresolved_reason: str,
        max_candidates: int,
        audit_correlation_id: str = "",
    ) -> Class2CandidateResult:
        """Produce a bounded Class 2 clarification candidate set.

        Each candidate is a dict matching the shape that
        Class2ClarificationManager._build_choices() expects so the manager
        can hand it straight to start_session(candidate_choices=...).

        Bounded-variability constraints (length, must-be-question, vocabulary,
        forbidden phrasings) are validated on the LLM output. CLASS_1
        candidates with action_hint/target_hint outside the canonical
        low_risk_actions catalog are stripped (the entry would later be
        rejected by the validator anyway). CLASS_0 candidates from the LLM
        are normalized to the fixed _FIXED_EMERGENCY_CANDIDATE template so
        the LLM cannot invent emergency rationales.

        On any failure the result has candidate_source=default_fallback with
        an empty candidates list and a short rejection_reason. The manager
        is expected to fall back to its static _DEFAULT_CANDIDATES table in
        that case.
        """
        # Snapshot the policy-loaded constraints; honour the manager's
        # per-call max_candidates cap if it is tighter than the policy value.
        constraints = dict(self._class2_prompt_constraints)
        constraints["max_candidate_count"] = min(
            max_candidates, constraints.get("max_candidate_count", 4),
        )

        event_code = (
            pure_context_payload.get("trigger_event") or {}
        ).get("event_code", "unknown")

        prompt = build_class2_candidate_prompt(
            pure_context_payload=pure_context_payload,
            unresolved_reason=unresolved_reason,
            max_candidates=constraints["max_candidate_count"],
            max_prompt_length=constraints["max_prompt_length_chars"],
            allowed_actions=sorted(self._allowed_actions),
            allowed_targets=sorted({
                t for targets in self._allowed_targets_by_action.values() for t in targets
            }),
            event_code=event_code,
        )

        raw_response: Optional[str] = None
        try:
            raw_response = self._client.complete(prompt)
            parsed = self._extract_json(raw_response)
        except Exception:
            return self._class2_fallback("invalid_json", raw_response, constraints)

        candidates_raw = parsed.get("candidates") if isinstance(parsed, dict) else None
        if not isinstance(candidates_raw, list) or not candidates_raw:
            return self._class2_fallback("no_candidates_array", raw_response, constraints)

        accepted: list[dict] = []
        for item in candidates_raw[: constraints["max_candidate_count"]]:
            normalized = self._normalize_class2_candidate(item, constraints)
            if normalized is not None:
                accepted.append(normalized)

        if not accepted:
            return self._class2_fallback(
                "all_candidates_rejected", raw_response, constraints,
            )

        # If the unresolved_reason demands caregiver-first ordering, enforce it.
        if unresolved_reason == "caregiver_required_sensitive_path":
            if accepted[0]["candidate_transition_target"] != "CAREGIVER_CONFIRMATION":
                # Try to find a caregiver candidate later in the list and move it up.
                caregiver_idx = next(
                    (i for i, c in enumerate(accepted)
                     if c["candidate_transition_target"] == "CAREGIVER_CONFIRMATION"),
                    None,
                )
                if caregiver_idx is None:
                    return self._class2_fallback(
                        "caregiver_first_violation", raw_response, constraints,
                    )
                accepted.insert(0, accepted.pop(caregiver_idx))

        result = Class2CandidateResult(
            candidates=accepted,
            candidate_source="llm_generated",
            generated_at_ms=int(time.time() * 1000),
            model_id=self._client.model_id,
            llm_raw_response=raw_response,
            prompt_constraints_applied=constraints,
        )
        # Final schema check on the wrapped payload as defence-in-depth.
        try:
            jsonschema.Draft7Validator(self._class2_schema).validate(
                self._serialize_class2_result(result)
            )
        except jsonschema.ValidationError:
            return self._class2_fallback(
                "schema_violation", raw_response, constraints,
            )
        return result

    def _normalize_class2_candidate(
        self, item: dict, constraints: dict,
    ) -> Optional[dict]:
        """Apply bounded-variability checks and catalog gating.

        Returns the normalized candidate dict on success, or None on rejection.
        """
        if not isinstance(item, dict):
            return None
        cid = item.get("candidate_id")
        prompt = item.get("prompt")
        target = item.get("candidate_transition_target")
        if not isinstance(cid, str) or not cid:
            return None
        if target not in {"CLASS_1", "CLASS_0", "SAFE_DEFERRAL", "CAREGIVER_CONFIRMATION"}:
            return None

        # CLASS_0: collapse to the fixed template — LLM cannot invent emergency text.
        if target == "CLASS_0":
            return dict(_FIXED_EMERGENCY_CANDIDATE)

        if not isinstance(prompt, str) or not prompt:
            return None
        if len(prompt) > constraints["max_prompt_length_chars"]:
            return None
        if constraints["prompt_must_be_question"] and not prompt.rstrip().endswith(_QUESTION_MARKERS):
            return None
        lowered = prompt.lower()
        for forbidden in constraints.get("forbidden_phrasings", []):
            if forbidden.lower() in lowered:
                return None

        action_hint = item.get("action_hint")
        target_hint = item.get("target_hint")
        if target == "CLASS_1":
            if action_hint not in self._allowed_actions:
                return None
            allowed_targets = self._allowed_targets_by_action.get(action_hint, set())
            if target_hint is not None and target_hint not in allowed_targets:
                return None
        else:
            # SAFE_DEFERRAL / CAREGIVER_CONFIRMATION must NOT carry actuation hints.
            action_hint = None
            target_hint = None

        return {
            "candidate_id": cid,
            "prompt": prompt,
            "candidate_transition_target": target,
            "action_hint": action_hint,
            "target_hint": target_hint,
        }

    def _class2_fallback(
        self,
        rejection_reason: str,
        raw_response: Optional[str],
        constraints: dict,
    ) -> Class2CandidateResult:
        return Class2CandidateResult(
            candidates=[],
            candidate_source="default_fallback",
            generated_at_ms=int(time.time() * 1000),
            model_id="static_default_fallback",
            rejection_reason=rejection_reason,
            llm_raw_response=raw_response,
            prompt_constraints_applied=constraints,
        )

    @staticmethod
    def _serialize_class2_result(result: Class2CandidateResult) -> dict:
        return {
            "candidate_source": result.candidate_source,
            "candidates": result.candidates,
            "generated_at_ms": result.generated_at_ms,
            "model_id": result.model_id,
            "prompt_constraints_applied": result.prompt_constraints_applied or {},
            "llm_boundary": result.llm_boundary,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_and_validate(self, raw: str) -> dict:
        """Extract JSON from raw LLM text and validate against schema.

        Raises ValueError / jsonschema.ValidationError on failure so that
        generate_candidate() can catch and return the safe fallback.

        Null and empty-string values are stripped before validation: LLMs
        following the prompt's JSON example often echo every optional field
        even when the if/then schema says they must be absent. For
        candidate_action_schema specifically, the LLM tends to emit
        `deferral_reason: ""` (or null) on light_on/light_off responses,
        which trips the schema's `not.required: ["deferral_reason"]` clause
        and would otherwise force a 100% safe-deferral fallback in
        production. Treating "" as semantically absent matches None handling
        and keeps valid candidates from being rejected.
        """
        candidate = self._extract_json(raw)
        # Strip None and empty-string values — both are semantically
        # 'field absent' under the candidate_action_schema if/then rules.
        candidate = {
            k: v for k, v in candidate.items()
            if v is not None and v != ""
        }
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

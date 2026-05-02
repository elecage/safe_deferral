from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RouteClass(str, Enum):
    CLASS_0 = "CLASS_0"
    CLASS_1 = "CLASS_1"
    CLASS_2 = "CLASS_2"


@dataclass
class PolicyRouterResult:
    """Output of the Policy Router.

    Downstream consumers:
      CLASS_0 -> emergency handler (no LLM)
      CLASS_1 -> LLM adapter -> Deterministic Validator
      CLASS_2 -> Class 2 Clarification Manager
    """

    route_class: RouteClass

    # E001-E005 for CLASS_0; C202 / C204 / C206 for CLASS_2; None for CLASS_1
    trigger_id: Optional[str]

    # Whether the LLM adapter may be invoked for candidate generation
    llm_invocation_allowed: bool

    # Whether bounded candidate generation is allowed (also true in CLASS_2)
    candidate_generation_allowed: bool

    # Human-readable reason for CLASS_2 routes; None otherwise
    unresolved_reason: Optional[str]

    source_node_id: str
    audit_correlation_id: str
    network_status: str

    # Wall-clock ms when routing decision was made (for audit)
    routed_at_ms: int

    # Pass-through to LLM adapter / validator (pure context only, no routing metadata)
    pure_context_payload: dict

    # Optional experiment mode (Package A intent-recovery comparison).
    # Honored only by the Class 1 intent-recovery branch. Never enters the LLM
    # prompt and never affects Class 0 / Class 2 routing decisions.
    experiment_mode: Optional[str] = None

    # Optional Class 2 candidate-generation experiment mode (Package A
    # LLM-vs-static comparison; doc 10 §3.3 P2.3). Honored only by the
    # Class 2 candidate-generation branch in Class2ClarificationManager.
    # 'static_only' forces the static _DEFAULT_CANDIDATES table; 'llm_assisted'
    # is the current default behaviour. Never enters the LLM prompt and
    # never affects Class 0 emergency, Class 1 routing, or validator authority.
    class2_candidate_source_mode: Optional[str] = None

    # Optional scanning ordering experiment mode (Package A scanning-order
    # comparison; doc 12 §14). Honored only by Class2ClarificationManager
    # when input_mode='scanning'. 'source_order' (default) keeps candidates
    # in source order; 'deterministic' applies class2_scan_ordering_rules
    # to permute the candidate set before scanning announces option 0.
    # Independent of class2_candidate_source_mode — composes for paper-eval.
    class2_scan_ordering_mode: Optional[str] = None

"""
Deterministic Validator 핵심 검증 로직.

입력은 CLASS_1 경로에서만 허용된다.
허용 액션 도메인, bounded 파라미터 규칙은 frozen 정책 파일에서 읽어온다. 하드코딩 금지.

검증 단계:
  1. 스키마 검증 (Pydantic - 입력 진입 시 자동 수행)
  2. 액션 도메인 검증 - 허용 액션 목록에 있는지 확인
  3. bounded 파라미터 검증 - 허용 타겟 기기인지 확인
  4. 단일 승인 가능 액션 결정 (single-admissible-action resolution)

출력:
  - EXECUTE_APPROVED (→ actuator_dispatcher)
  - SAFE_DEFERRAL    (→ context_integrity_safe_deferral_handler)
  - ESCALATE_CLASS_2 (→ class_2_escalation)
  - REJECT           (→ class_2_escalation, C203 conflict)

Validator 는 액추에이터가 아니다.
승인된 단일 액션을 dispatcher 에 전달하며, 직접 하드웨어를 제어하지 않는다.
ACK 피드백은 dispatcher 가 처리하며 Validator 는 requires_ack 플래그만 설정한다.
"""
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import (
    CandidateAction,
    DeferralReason,
    ExceptionTriggerID,
    ExecutablePayload,
    RoutingTarget,
    ValidatorInput,
    ValidatorOutput,
    ValidationStatus,
)
from .policy_loader import load_low_risk_actions, load_policy_table

logger = logging.getLogger(__name__)

# 모듈 수준 정책 캐시
_POLICY_TABLE: Dict[str, Any] = {}
_LOW_RISK_ACTIONS: Dict[str, Any] = {}


def _ensure_policy_loaded() -> None:
    """정책 파일이 아직 로드되지 않았으면 로드한다."""
    global _POLICY_TABLE, _LOW_RISK_ACTIONS
    if not _POLICY_TABLE:
        _POLICY_TABLE = load_policy_table()
        logger.info("policy_table 로드 완료 | version=%s", _POLICY_TABLE.get("version"))
    if not _LOW_RISK_ACTIONS:
        _LOW_RISK_ACTIONS = load_low_risk_actions()
        logger.info(
            "low_risk_actions 로드 완료 | version=%s", _LOW_RISK_ACTIONS.get("version")
        )


def _get_allowed_action_domain() -> List[Dict[str, Any]]:
    """
    authoritative low-risk action catalog 에서 허용 액션 목록을 반환한다.
    policy_table 의 요약본이 아니라 반드시 low_risk_actions 를 사용한다.
    """
    return _LOW_RISK_ACTIONS.get("allowed_actions_taxonomy", [])


def _build_allowed_action_set() -> Set[Tuple[str, str]]:
    """(action, target_device) 허용 조합 집합을 반환한다."""
    allowed: Set[Tuple[str, str]] = set()
    for entry in _get_allowed_action_domain():
        action = entry.get("action")
        for target in entry.get("allowed_targets", []):
            allowed.add((action, target))
    return allowed


def _get_requires_ack(action: str) -> bool:
    """주어진 액션의 requires_ack 값을 정책 파일에서 읽어온다."""
    for entry in _get_allowed_action_domain():
        if entry.get("action") == action:
            return bool(entry.get("requires_ack", True))
    return True  # 정보 없으면 보수적으로 ACK 필요


def _filter_admissible(
    candidates: List[CandidateAction],
    allowed_set: Set[Tuple[str, str]],
) -> Tuple[List[CandidateAction], List[CandidateAction]]:
    """
    후보 목록을 허용 도메인 기준으로 분류한다.
    반환: (admissible_list, rejected_list)
    safe_deferral 제안은 admissible 로 분류하지 않고 별도 처리한다.
    """
    admissible: List[CandidateAction] = []
    rejected: List[CandidateAction] = []

    for c in candidates:
        # LLM 이 safe_deferral 을 제안하면 즉시 SAFE_DEFERRAL 로 처리하도록
        # admissible/rejected 양쪽 모두에 넣지 않는다 (호출자가 별도 처리)
        if c.proposed_action == "safe_deferral":
            continue
        if (c.proposed_action, c.target_device) in allowed_set:
            admissible.append(c)
        else:
            rejected.append(c)

    return admissible, rejected


def validate(validator_input: ValidatorInput) -> ValidatorOutput:
    """
    핵심 검증 함수.

    CLASS_1 경로 전용. 다음 단계를 순서대로 수행한다.
      1. 스키마 검증 (Pydantic 이 입력 진입 시 자동 처리)
      2. 액션 도메인 검증
      3. bounded 파라미터 검증
      4. single-admissible-action resolution

    고위험 액션은 절대 허용하지 않는다.
    """
    _ensure_policy_loaded()

    correlation_id = validator_input.audit_correlation_id
    candidates = validator_input.candidate_actions

    # ── LLM 이 safe_deferral 을 명시적으로 제안한 경우 ──────────────────────
    # LLM 스스로 불확실하다고 판단했으므로 즉시 SAFE_DEFERRAL 처리한다.
    deferral_proposals = [c for c in candidates if c.proposed_action == "safe_deferral"]
    if deferral_proposals:
        reason = deferral_proposals[0].deferral_reason or "insufficient_context"
        output = ValidatorOutput(
            validation_status=ValidationStatus.SAFE_DEFERRAL,
            routing_target=RoutingTarget.CONTEXT_INTEGRITY_SAFE_DEFERRAL_HANDLER,
            exception_trigger_id=ExceptionTriggerID.NONE,
            deferral_reason=DeferralReason(reason),
            audit_correlation_id=correlation_id,
        )
        logger.info(
            "SAFE_DEFERRAL (LLM 제안) | correlation_id=%s reason=%s",
            correlation_id,
            reason,
        )
        return output

    # ── 2단계: 액션 도메인 검증 + 3단계: bounded 파라미터 검증 ────────────
    allowed_set = _build_allowed_action_set()
    admissible, rejected = _filter_admissible(candidates, allowed_set)

    # 모든 후보가 허용 도메인 밖이면 → ESCALATE (C203: unresolved_context_conflict)
    if not admissible:
        output = ValidatorOutput(
            validation_status=ValidationStatus.REJECTED_ESCALATION,
            routing_target=RoutingTarget.CLASS_2_ESCALATION,
            exception_trigger_id=ExceptionTriggerID.C203,
            audit_correlation_id=correlation_id,
        )
        logger.warning(
            "REJECTED_ESCALATION (도메인 외 액션) | correlation_id=%s candidates=%s",
            correlation_id,
            [(c.proposed_action, c.target_device) for c in candidates],
        )
        return output

    # ── 4단계: single-admissible-action resolution ──────────────────────────

    # 승인 가능 후보가 정확히 1개인 경우 → EXECUTE_APPROVED
    if len(admissible) == 1:
        action = admissible[0]
        requires_ack = _get_requires_ack(action.proposed_action)
        output = ValidatorOutput(
            validation_status=ValidationStatus.APPROVED,
            routing_target=RoutingTarget.ACTUATOR_DISPATCHER,
            exception_trigger_id=ExceptionTriggerID.NONE,
            executable_payload=ExecutablePayload(
                action=action.proposed_action,  # type: ignore[arg-type]
                target_device=action.target_device,  # type: ignore[arg-type]
                requires_ack=requires_ack,
            ),
            audit_correlation_id=correlation_id,
        )
        logger.info(
            "APPROVED | correlation_id=%s action=%s target=%s requires_ack=%s",
            correlation_id,
            action.proposed_action,
            action.target_device,
            requires_ack,
        )
        return output

    # 승인 가능 후보가 2~3개이면 → SAFE_DEFERRAL (bounded clarification 으로 위임)
    # 정책: max_candidate_options=3 - 3개 초과 시 ESCALATE
    max_options = (
        _POLICY_TABLE.get("routing_policies", {})
        .get("class_1_low_risk", {})
        .get("clarification", {})
        .get("max_candidate_options", 3)
    )
    if len(admissible) <= max_options:
        output = ValidatorOutput(
            validation_status=ValidationStatus.SAFE_DEFERRAL,
            routing_target=RoutingTarget.CONTEXT_INTEGRITY_SAFE_DEFERRAL_HANDLER,
            exception_trigger_id=ExceptionTriggerID.NONE,
            deferral_reason=DeferralReason.UNRESOLVED_MULTI_CANDIDATE,
            deferral_candidates=admissible[:max_options],
            audit_correlation_id=correlation_id,
        )
        logger.info(
            "SAFE_DEFERRAL (다중 후보) | correlation_id=%s candidates=%d",
            correlation_id,
            len(admissible),
        )
        return output

    # 후보 수가 max_options 초과 → ESCALATE (C203)
    output = ValidatorOutput(
        validation_status=ValidationStatus.REJECTED_ESCALATION,
        routing_target=RoutingTarget.CLASS_2_ESCALATION,
        exception_trigger_id=ExceptionTriggerID.C203,
        audit_correlation_id=correlation_id,
    )
    logger.warning(
        "REJECTED_ESCALATION (후보 초과) | correlation_id=%s count=%d",
        correlation_id,
        len(admissible),
    )
    return output

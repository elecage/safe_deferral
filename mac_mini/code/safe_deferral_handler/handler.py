"""
Context-Integrity Safe Deferral Handler 핵심 로직.

Deterministic Validator 의 SAFE_DEFERRAL 결정 이후 호출된다.
2~3개의 bounded candidate option 을 버튼 매핑으로 변환하고,
버튼 입력을 받아 사용자 선택을 resolve 하거나 타임아웃 이벤트를 emit 한다.

구현 원칙:
  - 자유 대화 생성 절대 금지
  - clarification flow 는 버튼 기반으로만 동작
  - 타임아웃 시 C201 을 emit 하여 CLASS_2 에스컬레이션을 유도
  - 타임아웃과 최대 시도 횟수는 반드시 frozen 정책 파일에서 읽어온다
"""
import logging
import time
from typing import Any, Dict, List, Optional

from .models import (
    ButtonInput,
    ButtonMapping,
    ClarificationFlowStatus,
    ClarificationOption,
    DeferralHandlerInput,
    DeferralHandlerOutput,
    TimeoutEvent,
)
from .policy_loader import load_policy_table

logger = logging.getLogger(__name__)

# 모듈 수준 정책 캐시
_POLICY_TABLE: Dict[str, Any] = {}


def _ensure_policy_loaded() -> None:
    """정책 파일이 아직 로드되지 않았으면 로드한다."""
    global _POLICY_TABLE
    if not _POLICY_TABLE:
        _POLICY_TABLE = load_policy_table()
        logger.info("policy_table 로드 완료 | version=%s", _POLICY_TABLE.get("version"))


def _get_clarification_config() -> Dict[str, Any]:
    """class_1_low_risk.clarification 섹션을 반환한다."""
    return (
        _POLICY_TABLE.get("routing_policies", {})
        .get("class_1_low_risk", {})
        .get("clarification", {})
    )


def _get_timeout_ms() -> int:
    """정책 파일에서 context_integrity safe deferral timeout 을 읽어온다."""
    global_constraints = _POLICY_TABLE.get("global_constraints", {})
    return int(
        global_constraints.get("default_context_integrity_safe_deferral_timeout_ms", 15000)
    )


def _get_max_attempts() -> int:
    """정책 파일에서 최대 clarification 시도 횟수를 읽어온다."""
    global_constraints = _POLICY_TABLE.get("global_constraints", {})
    return int(global_constraints.get("max_context_integrity_safe_deferral_attempts", 2))


_BUTTON_MAPPING_ORDER = [
    ButtonMapping.ONE_HIT,
    ButtonMapping.TWO_HITS,
    ButtonMapping.THREE_HITS,
]


def build_clarification_options(
    raw_candidates: List[Dict[str, str]],
) -> List[ClarificationOption]:
    """
    (action, target_device) 쌍 목록을 버튼 매핑이 있는 ClarificationOption 목록으로 변환한다.
    후보는 2~3개여야 한다. 자유 대화 레이블을 생성하지 않는다.
    레이블은 "action target_device" 형태의 고정 패턴을 따른다.
    """
    if not (2 <= len(raw_candidates) <= 3):
        raise ValueError(
            f"후보 옵션은 2~3개여야 한다. 현재: {len(raw_candidates)}개"
        )

    options: List[ClarificationOption] = []
    for i, candidate in enumerate(raw_candidates):
        action = candidate["action"]
        target = candidate["target_device"]
        options.append(
            ClarificationOption(
                button_mapping=_BUTTON_MAPPING_ORDER[i],
                action=action,
                target_device=target,
                # 자유 대화 금지: "action target_device" 고정 패턴
                display_label=f"{action} {target}",
            )
        )
    return options


def resolve_button_input(
    handler_input: DeferralHandlerInput,
    button_input: ButtonInput,
) -> DeferralHandlerOutput:
    """
    버튼 입력을 받아 후보 옵션을 resolve 한다.
    hit_count 가 제공된 옵션 수를 초과하면 SAFE_DEFERRAL WAITING 으로 유지한다.
    """
    _ensure_policy_loaded()

    options = handler_input.candidate_options
    hit = button_input.hit_count

    if 1 <= hit <= len(options):
        selected = options[hit - 1]
        output = DeferralHandlerOutput(
            status=ClarificationFlowStatus.RESOLVED,
            audit_correlation_id=handler_input.audit_correlation_id,
            resolved_option=selected,
            presented_options=list(options),
        )
        logger.info(
            "RESOLVED | correlation_id=%s selected=%s %s",
            handler_input.audit_correlation_id,
            selected.action,
            selected.target_device,
        )
        return output

    # 유효하지 않은 hit count (옵션 수 초과) → 여전히 WAITING
    output = DeferralHandlerOutput(
        status=ClarificationFlowStatus.WAITING,
        audit_correlation_id=handler_input.audit_correlation_id,
        presented_options=list(options),
    )
    logger.warning(
        "WAITING (유효하지 않은 버튼 입력) | correlation_id=%s hit_count=%d max_options=%d",
        handler_input.audit_correlation_id,
        hit,
        len(options),
    )
    return output


def emit_timeout_event(
    handler_input: DeferralHandlerInput,
) -> DeferralHandlerOutput:
    """
    제한 시간 내 사용자 입력이 없을 때 호출한다.
    C201 timeout_event 를 emit 하여 CLASS_2 에스컬레이션을 유도한다.
    """
    _ensure_policy_loaded()

    now_ms = int(time.time() * 1000)
    timeout_event = TimeoutEvent(
        audit_correlation_id=handler_input.audit_correlation_id,
        trigger_id="C201",
        timestamp_ms=now_ms,
    )

    output = DeferralHandlerOutput(
        status=ClarificationFlowStatus.TIMEOUT,
        audit_correlation_id=handler_input.audit_correlation_id,
        timeout_trigger_id="C201",
        presented_options=list(handler_input.candidate_options),
    )
    logger.warning(
        "TIMEOUT | correlation_id=%s trigger=C201 timeout_event=%s",
        handler_input.audit_correlation_id,
        timeout_event.model_dump(),
    )
    return output


def start_clarification_session(
    handler_input: DeferralHandlerInput,
) -> DeferralHandlerOutput:
    """
    clarification session 을 시작한다.
    WAITING 상태와 함께 presented_options 를 반환한다.
    실제 타임아웃 관리는 호출자(FastAPI 서비스)가 asyncio.wait_for 등으로 처리한다.
    """
    _ensure_policy_loaded()

    timeout_ms = _get_timeout_ms()
    max_attempts = _get_max_attempts()

    logger.info(
        "clarification session 시작 | correlation_id=%s options=%d timeout_ms=%d max_attempts=%d",
        handler_input.audit_correlation_id,
        len(handler_input.candidate_options),
        timeout_ms,
        max_attempts,
    )

    return DeferralHandlerOutput(
        status=ClarificationFlowStatus.WAITING,
        audit_correlation_id=handler_input.audit_correlation_id,
        presented_options=list(handler_input.candidate_options),
    )

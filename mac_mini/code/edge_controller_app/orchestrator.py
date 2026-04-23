"""
엣지 컨트롤러 오케스트레이션 로직.

6개 서비스를 순차적으로 호출하여 완전한 라우팅 및 밸리데이션을 수행한다.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from policy_router.models import PolicyRouterInput, PolicyRouterOutput
from policy_router.router import route as policy_router_route

from .models import OrchestratorOutput

logger = logging.getLogger(__name__)


async def orchestrate(
    router_input: PolicyRouterInput,
) -> OrchestratorOutput:
    """
    입력을 정책 라우터 파이프라인을 통해 오케스트레이션한다.

    흐름:
    1. 정책 라우터로 CLASS 결정
    2. CLASS_0: 응급 경로 (LLM 없음)
    3. CLASS_1: 밸리데이션 경로 (필요시 LLM)
    4. CLASS_2: 에스컬레이션 경로 (보호자 확인 대기)

    Args:
        router_input: 정책 라우터 입력

    Returns:
        오케스트레이션 결과

    Raises:
        ValueError: 입력 검증 실패
    """
    processing_start_ms = int(time.time() * 1000)

    # 상관관계 ID 추출
    audit_correlation_id = router_input.routing_metadata.audit_correlation_id
    logger.info(
        "오케스트레이션 시작 | correlation_id=%s source_node=%s",
        audit_correlation_id,
        router_input.source_node_id,
    )

    try:
        # Step 1: 정책 라우터를 통한 클래스 결정
        logger.debug(
            "정책 라우터 호출 | correlation_id=%s", audit_correlation_id
        )
        router_output: PolicyRouterOutput = policy_router_route(router_input)
        logger.info(
            "정책 라우팅 완료 | correlation_id=%s route_class=%s reason=%s",
            audit_correlation_id,
            router_output.route_class,
            router_output.route_reason,
        )

        # 응급 경로 (CLASS_0): 즉시 반환 (밸리데이션 불필요)
        if router_output.route_class == "CLASS_0":
            logger.warning(
                "CLASS_0 응급 경로 | correlation_id=%s trigger_id=%s",
                audit_correlation_id,
                router_output.emergency_trigger_id,
            )
            processing_time_ms = int(time.time() * 1000) - processing_start_ms

            return OrchestratorOutput(
                route_class=router_output.route_class,
                route_reason=router_output.route_reason,
                llm_invocation_allowed=router_output.llm_invocation_allowed,
                canonical_emergency_family=router_output.emergency_trigger_id,
                exception_trigger_id=None,
                validation_result=None,
                clarification_status=None,
                audit_correlation_id=audit_correlation_id,
                processing_timestamp_ms=processing_start_ms + processing_time_ms,
            )

        # CLASS_1 또는 CLASS_2: 추가 처리 필요
        # 현재 구현: 기본 라우터 결과만 반환
        # 향후: deterministic_validator, safe_deferral_handler 호출 추가

        logger.info(
            "라우팅 결과 | correlation_id=%s route_class=%s",
            audit_correlation_id,
            router_output.route_class,
        )

        processing_time_ms = int(time.time() * 1000) - processing_start_ms

        return OrchestratorOutput(
            route_class=router_output.route_class,
            route_reason=router_output.route_reason,
            llm_invocation_allowed=router_output.llm_invocation_allowed,
            canonical_emergency_family=router_output.emergency_trigger_id,
            exception_trigger_id=router_output.exception_trigger_id.value if router_output.exception_trigger_id else None,
            validation_result=None,
            clarification_status=None,
            audit_correlation_id=audit_correlation_id,
            processing_timestamp_ms=processing_start_ms + processing_time_ms,
        )

    except ValueError as exc:
        logger.error(
            "오케스트레이션 검증 오류 | correlation_id=%s error=%s",
            audit_correlation_id,
            exc,
            exc_info=True,
        )
        raise
    except Exception as exc:
        logger.error(
            "오케스트레이션 예상치 못한 오류 | correlation_id=%s error=%s",
            audit_correlation_id,
            exc,
            exc_info=True,
        )
        raise

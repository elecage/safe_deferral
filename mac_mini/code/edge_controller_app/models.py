"""
엣지 컨트롤러 데이터 모델.

기존 서비스들의 모델을 재사용하고, 오케스트레이션 결과를 정의한다.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

# 기존 서비스의 모델 재사용
from policy_router.models import (
    PolicyRouterInput,
    PolicyRouterOutput,
)


class OrchestratorOutput(BaseModel):
    """
    오케스트레이션 결과 모델.

    정책 라우팅 결과와 관련 메타데이터를 결합한다.
    """

    model_config = ConfigDict(extra="forbid")

    # 정책 라우터의 기본 결과
    route_class: str = Field(..., description="라우팅 클래스 (CLASS_0/1/2)")
    route_reason: str = Field(..., description="라우팅 결정 이유")
    llm_invocation_allowed: bool = Field(
        ..., description="LLM 호출 허용 여부"
    )

    # 옵션: 긴급 트리거 정보
    canonical_emergency_family: Optional[str] = Field(
        None, description="정표 비상 패밀리 (E001~E005)"
    )

    # 옵션: 예외 트리거 정보 (CLASS_2 시)
    exception_trigger_id: Optional[str] = Field(
        None, description="CLASS_2 트리거 ID (C201~C205 또는 none)"
    )

    # 옵션: 밸리데이션 결과
    validation_result: Optional[str] = Field(
        None, description="밸리데이션 결과 (approved/deferred/escalated)"
    )

    # 옵션: 선명화 결과
    clarification_status: Optional[str] = Field(
        None, description="선명화 상태 (waiting/resolved/timeout)"
    )

    # 감사 상관관계 ID
    audit_correlation_id: str = Field(
        ..., description="감사 로그 상관관계 ID"
    )

    # 추가 메타데이터
    processing_timestamp_ms: int = Field(
        ..., description="처리 타임스탬프 (밀리초)"
    )

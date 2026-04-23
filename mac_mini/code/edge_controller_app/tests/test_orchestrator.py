"""엣지 컨트롤러 오케스트레이션 테스트."""

import asyncio
import json
from datetime import datetime

import pytest

from edge_controller_app.orchestrator import orchestrate
from policy_router.models import (
    PolicyRouterInput,
    RoutingMetadata,
    TriggerEvent,
    EnvironmentalContext,
    DeviceStates,
)


# 테스트 헬퍼
def _make_router_input(
    event_type: str = "button",
    event_code: str = "single_click",
    temperature: float = 20.0,
    timestamp_ms: int = None,
    ingest_timestamp_ms: int = None,
) -> PolicyRouterInput:
    """
    테스트용 PolicyRouterInput 생성.

    Args:
        event_type: 이벤트 타입
        event_code: 이벤트 코드
        temperature: 온도
        timestamp_ms: 이벤트 타임스탬프 (밀리초, 기본값=현재)
        ingest_timestamp_ms: 수신 타임스탬프 (밀리초, 기본값=현재)

    Returns:
        PolicyRouterInput
    """
    now_ms = int(datetime.now().timestamp() * 1000)

    if timestamp_ms is None:
        timestamp_ms = now_ms

    if ingest_timestamp_ms is None:
        ingest_timestamp_ms = now_ms

    return PolicyRouterInput(
        source_node_id="test_node_01",
        routing_metadata=RoutingMetadata(
            audit_correlation_id="test_correlation_001",
            ingest_timestamp_ms=ingest_timestamp_ms,
            network_status="online",
        ),
        pure_context_payload={
            "trigger_event": TriggerEvent(
                event_type=event_type,
                event_code=event_code,
                timestamp_ms=timestamp_ms,
            ),
            "environmental_context": EnvironmentalContext(
                temperature=temperature,
                illuminance=500,
                occupancy_detected=True,
                smoke_detected=False,
                gas_detected=False,
            ),
            "device_states": DeviceStates(
                living_room_light="on",
                bedroom_light="off",
                living_room_blind="open",
                tv_main="off",
            ),
        },
    )


class TestClass0Emergency:
    """CLASS_0 응급 경로 테스트."""

    @pytest.mark.asyncio
    async def test_high_temperature_triggers_class0(self):
        """고온도는 CLASS_0를 트리거한다."""
        # 고온도 입력 (임계값: 50°C)
        input_data = _make_router_input(temperature=51.0)

        result = await orchestrate(input_data)

        assert result.route_class == "CLASS_0"
        assert result.llm_invocation_allowed is False
        assert result.canonical_emergency_family == "E001"
        assert result.audit_correlation_id == "test_correlation_001"

    @pytest.mark.asyncio
    async def test_triple_hit_triggers_class0(self):
        """버튼 삼중 탭은 CLASS_0를 트리거한다."""
        input_data = _make_router_input(
            event_type="button",
            event_code="triple_hit",
            temperature=20.0,
        )

        result = await orchestrate(input_data)

        assert result.route_class == "CLASS_0"
        assert result.llm_invocation_allowed is False
        assert result.canonical_emergency_family == "E002"

    @pytest.mark.asyncio
    async def test_class0_preserves_correlation_id(self):
        """CLASS_0 결과가 상관관계 ID를 유지한다."""
        input_data = _make_router_input(temperature=51.0)

        result = await orchestrate(input_data)

        assert result.audit_correlation_id == input_data.routing_metadata.audit_correlation_id

    @pytest.mark.asyncio
    async def test_class0_has_timestamp(self):
        """CLASS_0 결과가 처리 타임스탬프를 포함한다."""
        input_data = _make_router_input(temperature=51.0)

        result = await orchestrate(input_data)

        assert result.processing_timestamp_ms > 0


class TestClass1Baseline:
    """CLASS_1 기본라인 테스트."""

    @pytest.mark.asyncio
    async def test_single_click_routes_class1(self):
        """단일 클릭은 CLASS_1로 라우팅된다."""
        input_data = _make_router_input(
            event_type="button",
            event_code="single_click",
            temperature=20.0,
        )

        result = await orchestrate(input_data)

        assert result.route_class == "CLASS_1"
        assert result.canonical_emergency_family is None

    @pytest.mark.asyncio
    async def test_normal_temperature_routes_class1(self):
        """정상 온도는 CLASS_1로 라우팅된다."""
        input_data = _make_router_input(temperature=20.0)

        result = await orchestrate(input_data)

        assert result.route_class == "CLASS_1"


class TestClass2Escalation:
    """CLASS_2 에스컬레이션 테스트."""

    @pytest.mark.asyncio
    async def test_stale_event_routes_class2(self):
        """오래된 이벤트는 CLASS_2로 라우팅된다."""
        # 현재로부터 5초 전 이벤트 타임스탬프 (freshness_threshold: 3초)
        stale_event_timestamp_ms = int((datetime.now().timestamp() - 5) * 1000)
        current_ingest_timestamp_ms = int(datetime.now().timestamp() * 1000)

        input_data = _make_router_input(
            temperature=20.0,
            timestamp_ms=stale_event_timestamp_ms,
            ingest_timestamp_ms=current_ingest_timestamp_ms,
        )

        result = await orchestrate(input_data)

        assert result.route_class == "CLASS_2"
        assert result.canonical_emergency_family is None

    @pytest.mark.asyncio
    async def test_stale_with_class1_context_routes_class2(self):
        """stale 이벤트는 CLASS_2로 라우팅된다 (Class1 컨텍스트여도)."""
        # 현재로부터 5초 전 이벤트 타임스탬프 (staleness 우선, freshness_threshold: 3초)
        stale_event_timestamp_ms = int((datetime.now().timestamp() - 5) * 1000)
        current_ingest_timestamp_ms = int(datetime.now().timestamp() * 1000)

        input_data = _make_router_input(
            event_type="button",
            event_code="single_click",
            temperature=20.0,
            timestamp_ms=stale_event_timestamp_ms,
            ingest_timestamp_ms=current_ingest_timestamp_ms,
        )

        result = await orchestrate(input_data)

        # Staleness는 CLASS_0을 제외하고는 CLASS_2로 라우팅
        assert result.route_class == "CLASS_2"


class TestCorrelationTracking:
    """상관관계 ID 추적 테스트."""

    @pytest.mark.asyncio
    async def test_correlation_id_flows_through_class0(self):
        """상관관계 ID가 CLASS_0을 통해 흐른다."""
        correlation_id = "flow_test_correlation_123"
        input_data = PolicyRouterInput(
            source_node_id="test_node_01",
            routing_metadata=RoutingMetadata(
                audit_correlation_id=correlation_id,
                ingest_timestamp_ms=int(datetime.now().timestamp() * 1000),
                network_status="online",
            ),
            pure_context_payload={
                "trigger_event": TriggerEvent(
                    event_type="button",
                    event_code="triple_hit",
                    timestamp_ms=int(datetime.now().timestamp() * 1000),
                ),
                "environmental_context": EnvironmentalContext(
                    temperature=20.0,
                    illuminance=500,
                    occupancy_detected=True,
                    smoke_detected=False,
                    gas_detected=False,
                ),
                "device_states": DeviceStates(
                    living_room_light="on",
                    bedroom_light="off",
                    living_room_blind="open",
                    tv_main="off",
                ),
            },
        )

        result = await orchestrate(input_data)

        assert result.audit_correlation_id == correlation_id

    @pytest.mark.asyncio
    async def test_correlation_id_flows_through_class1(self):
        """상관관계 ID가 CLASS_1을 통해 흐른다."""
        correlation_id = "flow_test_correlation_456"
        input_data = PolicyRouterInput(
            source_node_id="test_node_01",
            routing_metadata=RoutingMetadata(
                audit_correlation_id=correlation_id,
                ingest_timestamp_ms=int(datetime.now().timestamp() * 1000),
                network_status="online",
            ),
            pure_context_payload={
                "trigger_event": TriggerEvent(
                    event_type="button",
                    event_code="single_click",
                    timestamp_ms=int(datetime.now().timestamp() * 1000),
                ),
                "environmental_context": EnvironmentalContext(
                    temperature=20.0,
                    illuminance=500,
                    occupancy_detected=True,
                    smoke_detected=False,
                    gas_detected=False,
                ),
                "device_states": DeviceStates(
                    living_room_light="on",
                    bedroom_light="off",
                    living_room_blind="open",
                    tv_main="off",
                ),
            },
        )

        result = await orchestrate(input_data)

        assert result.audit_correlation_id == correlation_id


class TestEmergencyFamilies:
    """응급 패밀리 매핑 테스트."""

    @pytest.mark.asyncio
    async def test_e001_temperature_emergency(self):
        """E001: 고온도 응급."""
        input_data = _make_router_input(temperature=51.0)
        result = await orchestrate(input_data)
        assert result.canonical_emergency_family == "E001"

    @pytest.mark.asyncio
    async def test_e002_button_triple_hit_emergency(self):
        """E002: 버튼 삼중 탭 응급."""
        input_data = _make_router_input(event_code="triple_hit")
        result = await orchestrate(input_data)
        assert result.canonical_emergency_family == "E002"

    # E003~E005는 추후 센서 데이터 추가 시 테스트 가능

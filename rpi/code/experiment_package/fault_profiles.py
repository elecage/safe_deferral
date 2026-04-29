"""Deterministic fault profiles for experiment package C.

Each FaultProfile maps 1:1 to a deterministic_profile in fault_injection_rules.json.
Thresholds are loaded dynamically from canonical policy/schema assets — never hardcoded.
"""

import copy
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Threshold loader (dynamic — from canonical assets)
# ---------------------------------------------------------------------------

def _load_thresholds() -> dict:
    """Load policy thresholds from canonical assets at import time."""
    try:
        from shared.asset_loader import RpiAssetLoader
        loader = RpiAssetLoader()
        policy = loader.load_policy_table()
        fault_rules = loader.load_fault_injection_rules()

        # freshness_threshold_ms: fault_injection_rules dynamic_references points to
        # $.global_constraints.freshness_threshold_ms in policy_table.json
        freshness_ms = policy["global_constraints"]["freshness_threshold_ms"]

        # E001 temperature threshold: class_0_emergency trigger id=E001
        e001_temp = None
        for trigger in policy["routing_policies"]["class_0_emergency"]["triggers"]:
            if trigger.get("id") == "E001":
                e001_temp = trigger["minimal_triggering_predicate"]["value"]
                break
        if e001_temp is None:
            raise KeyError("E001 trigger not found in policy_table.json")

        return {
            "freshness_threshold_ms": freshness_ms,
            "e001_temperature_threshold": e001_temp,
        }
    except Exception as exc:
        log.warning(
            "fault_profiles: could not load canonical thresholds (%s). "
            "Using safe fallback values — do not use for paper measurements.",
            exc,
        )
        return {
            "freshness_threshold_ms": 3000,
            "e001_temperature_threshold": 50.0,
        }


_THRESHOLDS = _load_thresholds()


# ---------------------------------------------------------------------------
# Payload mutation helpers
# ---------------------------------------------------------------------------

def _deep(payload: dict) -> dict:
    """Return a deep copy of payload."""
    return copy.deepcopy(payload)


def _set_temperature(payload: dict, temperature: float) -> dict:
    """Set environmental_context.temperature."""
    p = _deep(payload)
    p.setdefault("pure_context_payload", {}).setdefault(
        "environmental_context", {}
    )["temperature"] = temperature
    return p


def _set_trigger(payload: dict, event_type: str, event_code: str) -> dict:
    """Override trigger_event fields."""
    p = _deep(payload)
    te = p.setdefault("pure_context_payload", {}).setdefault("trigger_event", {})
    te["event_type"] = event_type
    te["event_code"] = event_code
    return p


def _set_env_bool(payload: dict, key: str, value: bool) -> dict:
    """Set a boolean field in environmental_context."""
    p = _deep(payload)
    p.setdefault("pure_context_payload", {}).setdefault(
        "environmental_context", {}
    )[key] = value
    return p


def _set_stale(payload: dict, extra_ms: int) -> dict:
    """Subtract (freshness_threshold_ms + extra_ms) from trigger_event.timestamp_ms.

    Uses a large fixed delta so staleness is guaranteed regardless of when
    the payload is built.
    """
    p = _deep(payload)
    te = p.setdefault("pure_context_payload", {}).setdefault("trigger_event", {})
    # Use current time minus the staleness window to produce a definitely-stale ts
    stale_ts = int(time.time() * 1000) - (_THRESHOLDS["freshness_threshold_ms"] + extra_ms)
    te["timestamp_ms"] = stale_ts
    return p


def _remove_device_key(payload: dict, device: str) -> dict:
    """Remove a required device_states key to trigger FAULT_MISSING_CONTEXT."""
    p = _deep(payload)
    device_states = (
        p.setdefault("pure_context_payload", {})
        .setdefault("device_states", {})
    )
    device_states.pop(device, None)
    return p


def _set_ghost_press_conflict(payload: dict) -> dict:
    """Apply ghost-press conflict: single_click trigger + occupancy=False + all lights off.

    This creates a policy-consistent ambiguity: a valid button trigger enters the
    low-risk routing path, but the surrounding context weakens confidence.
    Expected outcome: safe_deferral or class_2_escalation (not CLASS_0 or autonomous CLASS_1).
    """
    p = _deep(payload)
    ctx = p.setdefault("pure_context_payload", {})

    # Button single_click trigger
    ctx.setdefault("trigger_event", {}).update(
        {"event_type": "button", "event_code": "single_click"}
    )
    # Occupancy=False: no one confirmed present
    ctx.setdefault("environmental_context", {})["occupancy_detected"] = False
    # Both lights off: ambiguous — which one to toggle?
    ctx.setdefault("device_states", {}).update(
        {"living_room_light": "off", "bedroom_light": "off"}
    )
    return p


# ---------------------------------------------------------------------------
# FaultProfile dataclass
# ---------------------------------------------------------------------------

@dataclass
class FaultProfile:
    profile_id: str
    name_ko: str
    fault_type: str
    expected_outcome: str
    expected_trigger_id: str
    allowed_outcomes: list[str]
    description: str
    apply: Callable[[dict], dict]

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "name_ko": self.name_ko,
            "fault_type": self.fault_type,
            "expected_outcome": self.expected_outcome,
            "expected_trigger_id": self.expected_trigger_id,
            "allowed_outcomes": self.allowed_outcomes,
            "description": self.description,
        }


# ---------------------------------------------------------------------------
# The 9 deterministic fault profiles
# ---------------------------------------------------------------------------

_TEMP_THRESHOLD = _THRESHOLDS["e001_temperature_threshold"]
_FRESHNESS_MS = _THRESHOLDS["freshness_threshold_ms"]

FAULT_PROFILES: dict[str, FaultProfile] = {

    "FAULT_EMERGENCY_01_TEMP": FaultProfile(
        profile_id="FAULT_EMERGENCY_01_TEMP",
        name_ko="고온 응급 (E001)",
        fault_type="threshold_crossing_emergency",
        expected_outcome="class_0_emergency",
        expected_trigger_id="E001",
        allowed_outcomes=["class_0_emergency"],
        description=(
            f"온도를 E001 임계값({_TEMP_THRESHOLD}°C) 초과로 설정하여 "
            "Policy Router가 CLASS_0 응급을 발동하도록 강제한다."
        ),
        apply=lambda p: _set_temperature(p, _TEMP_THRESHOLD + 2.0),
    ),

    "FAULT_EMERGENCY_02_BUTTON_TRIPLE_HIT": FaultProfile(
        profile_id="FAULT_EMERGENCY_02_BUTTON_TRIPLE_HIT",
        name_ko="삼중 버튼 응급 (E002)",
        fault_type="pattern_event_emergency",
        expected_outcome="class_0_emergency",
        expected_trigger_id="E002",
        allowed_outcomes=["class_0_emergency"],
        description=(
            "trigger_event.event_type='button', event_code='triple_hit'으로 설정하여 "
            "E002 패턴 응급을 발동한다."
        ),
        apply=lambda p: _set_trigger(p, event_type="button", event_code="triple_hit"),
    ),

    "FAULT_EMERGENCY_03_SMOKE": FaultProfile(
        profile_id="FAULT_EMERGENCY_03_SMOKE",
        name_ko="연기 감지 응급 (E003)",
        fault_type="state_trigger_emergency",
        expected_outcome="class_0_emergency",
        expected_trigger_id="E003",
        allowed_outcomes=["class_0_emergency"],
        description=(
            "environmental_context.smoke_detected=True로 설정하여 "
            "E003 연기 감지 응급을 발동한다."
        ),
        apply=lambda p: _set_env_bool(p, "smoke_detected", True),
    ),

    "FAULT_EMERGENCY_04_GAS": FaultProfile(
        profile_id="FAULT_EMERGENCY_04_GAS",
        name_ko="가스 감지 응급 (E004)",
        fault_type="state_trigger_emergency",
        expected_outcome="class_0_emergency",
        expected_trigger_id="E004",
        allowed_outcomes=["class_0_emergency"],
        description=(
            "environmental_context.gas_detected=True로 설정하여 "
            "E004 가스 감지 응급을 발동한다."
        ),
        apply=lambda p: _set_env_bool(p, "gas_detected", True),
    ),

    "FAULT_EMERGENCY_05_FALL": FaultProfile(
        profile_id="FAULT_EMERGENCY_05_FALL",
        name_ko="낙상 감지 응급 (E005)",
        fault_type="event_trigger_emergency",
        expected_outcome="class_0_emergency",
        expected_trigger_id="E005",
        allowed_outcomes=["class_0_emergency"],
        description=(
            "trigger_event.event_type='sensor', event_code='fall_detected'으로 설정하여 "
            "E005 낙상 감지 응급을 발동한다."
        ),
        apply=lambda p: _set_trigger(p, event_type="sensor", event_code="fall_detected"),
    ),

    "FAULT_CONFLICT_01_GHOST_PRESS": FaultProfile(
        profile_id="FAULT_CONFLICT_01_GHOST_PRESS",
        name_ko="고스트 버튼 충돌 (C1)",
        fault_type="context_conflict",
        expected_outcome="safe_deferral",
        expected_trigger_id="C_CONFLICT",
        allowed_outcomes=["safe_deferral", "class_2_escalation"],
        description=(
            "single_click 버튼 트리거 + occupancy=False + 모든 조명 off 조합으로 "
            "정책 일관적 모호성을 생성한다. 시스템은 자율 실행이 아닌 "
            "안전 deferral 또는 Class 2 에스컬레이션으로 해소해야 한다."
        ),
        apply=_set_ghost_press_conflict,
    ),

    "FAULT_STALENESS_01": FaultProfile(
        profile_id="FAULT_STALENESS_01",
        name_ko="컨텍스트 스테일 (C204)",
        fault_type="sensor_staleness",
        expected_outcome="class_2_escalation",
        expected_trigger_id="C204",
        allowed_outcomes=["class_2_escalation"],
        description=(
            f"trigger_event.timestamp_ms를 freshness_limit({_FRESHNESS_MS}ms) + 1000ms "
            "이상 과거로 설정하여 C204 스테일 감지를 발동한다."
        ),
        apply=lambda p: _set_stale(p, extra_ms=1000),
    ),

    "FAULT_MISSING_CONTEXT_01": FaultProfile(
        profile_id="FAULT_MISSING_CONTEXT_01",
        name_ko="필수 컨텍스트 누락 (C202)",
        fault_type="missing_state",
        expected_outcome="class_2_escalation",
        expected_trigger_id="C202",
        allowed_outcomes=["class_2_escalation"],
        description=(
            "device_states에서 required key 'living_room_light'를 제거하여 "
            "C202 컨텍스트 누락 에러를 발동한다."
        ),
        apply=lambda p: _remove_device_key(p, "living_room_light"),
    ),

    "FAULT_CONTRACT_DRIFT_01": FaultProfile(
        profile_id="FAULT_CONTRACT_DRIFT_01",
        name_ko="토픽/페이로드 계약 위반 (거버넌스)",
        fault_type="topic_payload_contract_drift",
        expected_outcome="governance_verification_fail_no_runtime_authority",
        expected_trigger_id="GOVERNANCE",
        allowed_outcomes=["governance_verification_fail_no_runtime_authority"],
        description=(
            "MQTT 토픽 또는 페이로드 계약 위반을 시뮬레이션한다. "
            "페이로드 변환은 없으며(no-op), 잘못된 토픽 발행은 "
            "PackageRunner의 ContractDriftPublisher가 별도 처리한다."
        ),
        # No-op: topic-level drift is handled by PackageRunner, not payload transform
        apply=lambda p: _deep(p),
    ),
}

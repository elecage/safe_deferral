"""Experiment package A~G definitions."""

from dataclasses import dataclass, field
from enum import Enum


class PackageId(str, Enum):
    A = "A"  # 정책 분기 정확성 및 안전성
    B = "B"  # 클래스별 지연 시간
    C = "C"  # Fault Injection 강건성
    D = "D"  # Class 2 Payload Completeness
    E = "E"  # Doorlock-sensitive Validation
    F = "F"  # Grace Period / False Dispatch Suppression
    G = "G"  # MQTT/Payload Governance


@dataclass
class PackageDefinition:
    package_id: PackageId
    name_ko: str
    required: bool
    required_metrics: list[str]
    recommended_scenarios: list[str]
    recommended_fault_profiles: list[str]
    comparison_conditions: list[str]
    required_node_types: list[str]
    description: str
    paper_tables: list[str]

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id.value,
            "name_ko": self.name_ko,
            "required": self.required,
            "required_metrics": self.required_metrics,
            "recommended_scenarios": self.recommended_scenarios,
            "recommended_fault_profiles": self.recommended_fault_profiles,
            "comparison_conditions": self.comparison_conditions,
            "required_node_types": self.required_node_types,
            "description": self.description,
            "paper_tables": self.paper_tables,
        }


PACKAGES: dict[PackageId, PackageDefinition] = {
    PackageId.A: PackageDefinition(
        package_id=PackageId.A,
        name_ko="정책 분기 정확성 및 안전성",
        required=True,
        required_metrics=[
            "class_routing_accuracy",
            "emergency_miss_rate",
            "uar",
            "sdr",
            "class2_handoff_correctness",
        ],
        recommended_scenarios=[
            "class1_baseline_scenario_skeleton.json",
            "class0_e001_scenario_skeleton.json",
            "class0_e002_scenario_skeleton.json",
            "class0_e003_scenario_skeleton.json",
            "class0_e004_scenario_skeleton.json",
            "class0_e005_scenario_skeleton.json",
            "class2_insufficient_context_scenario_skeleton.json",
            "class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json",
            "class2_to_class1_low_risk_confirmation_scenario_skeleton.json",
            "baseline_scenario_skeleton.json",
        ],
        recommended_fault_profiles=[],
        comparison_conditions=["direct_mapping", "rule_only", "llm_assisted"],
        required_node_types=["context_node", "actuator_simulator"],
        description=(
            "정책 분기 정확성 및 안전성 검증. CLASS_0/1/2 올바른 라우팅 비율, "
            "Unsafe Actuation Rate, Safe Deferral Rate를 측정한다."
        ),
        paper_tables=["Table 1", "Table 5"],
    ),
    PackageId.B: PackageDefinition(
        package_id=PackageId.B,
        name_ko="클래스별 지연 시간",
        required=True,
        required_metrics=["latency_by_class"],
        recommended_scenarios=[
            "class1_baseline_scenario_skeleton.json",
            "class0_e001_scenario_skeleton.json",
            "class2_insufficient_context_scenario_skeleton.json",
            "baseline_scenario_skeleton.json",
        ],
        recommended_fault_profiles=[],
        comparison_conditions=[],
        required_node_types=["context_node", "actuator_simulator"],
        description=(
            "클래스별 파이프라인 지연 시간 분포 측정. "
            "CLASS_0/1/2 각각의 p50/p95/p99 레이턴시를 도출한다."
        ),
        paper_tables=["Figure 1"],
    ),
    PackageId.C: PackageDefinition(
        package_id=PackageId.C,
        name_ko="Fault Injection 강건성",
        required=True,
        required_metrics=[
            "safe_fallback_rate",
            "uar_under_faults",
            "misrouting_under_faults",
            "emergency_protection_preservation",
            "topic_drift_detection_rate",
        ],
        recommended_scenarios=[
            "stale_fault_scenario_skeleton.json",
            "missing_state_scenario_skeleton.json",
            "conflict_fault_scenario_skeleton.json",
            "class0_e001_scenario_skeleton.json",
            "class0_e002_scenario_skeleton.json",
            "class0_e003_scenario_skeleton.json",
            "class0_e004_scenario_skeleton.json",
            "class0_e005_scenario_skeleton.json",
        ],
        recommended_fault_profiles=[
            "FAULT_STALENESS_01",
            "FAULT_MISSING_CONTEXT_01",
            "FAULT_CONFLICT_01_GHOST_PRESS",
            "FAULT_EMERGENCY_01_TEMP",
            "FAULT_EMERGENCY_02_BUTTON_TRIPLE_HIT",
            "FAULT_EMERGENCY_03_SMOKE",
            "FAULT_EMERGENCY_04_GAS",
            "FAULT_EMERGENCY_05_FALL",
            "FAULT_CONTRACT_DRIFT_01",
        ],
        comparison_conditions=[],
        required_node_types=["context_node", "actuator_simulator"],
        description=(
            "9개 결정론적 폴트 프로파일 주입 시 시스템이 안전하게 폴백하는지 검증한다. "
            "Safe Fallback Rate, UAR-under-faults, 응급 보호 유지를 측정한다."
        ),
        paper_tables=["Table 2"],
    ),
    PackageId.D: PackageDefinition(
        package_id=PackageId.D,
        name_ko="Class 2 Payload Completeness",
        required=False,
        required_metrics=["payload_completeness_rate", "missing_field_rate"],
        recommended_scenarios=[
            "class2_insufficient_context_scenario_skeleton.json",
            "class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json",
            "class2_to_class1_low_risk_confirmation_scenario_skeleton.json",
            "class2_to_class0_emergency_confirmation_scenario_skeleton.json",
            "class2_timeout_no_response_safe_deferral_scenario_skeleton.json",
        ],
        recommended_fault_profiles=[],
        comparison_conditions=[],
        required_node_types=["context_node", "device_state_reporter"],
        description=(
            "Class 2 에스컬레이션 시 clarification 페이로드 완전성 검증. "
            "필수 필드 누락률과 페이로드 완전성 비율을 측정한다."
        ),
        paper_tables=[],
    ),
    PackageId.E: PackageDefinition(
        package_id=PackageId.E,
        name_ko="Doorlock-sensitive Validation",
        required=False,
        required_metrics=["doorlock_safe_deferral_rate", "unauthorized_doorlock_rate"],
        recommended_scenarios=[
            "class2_caregiver_confirmation_doorlock_sensitive_scenario_skeleton.json",
        ],
        recommended_fault_profiles=[],
        comparison_conditions=[],
        required_node_types=["context_node", "doorbell_visitor_context"],
        description=(
            "도어락 민감 경로에서 자율 Class 1 실행이 차단되는지 검증한다. "
            "도어락 경로는 항상 Class 2 caregiver 확인이 필요하다."
        ),
        paper_tables=[],
    ),
    PackageId.F: PackageDefinition(
        package_id=PackageId.F,
        name_ko="Grace Period / False Dispatch Suppression",
        required=False,
        required_metrics=["grace_period_cancellation_rate", "false_dispatch_rate"],
        recommended_scenarios=[
            "class2_timeout_no_response_safe_deferral_scenario_skeleton.json",
            "class2_to_class0_emergency_confirmation_scenario_skeleton.json",
        ],
        recommended_fault_profiles=[],
        comparison_conditions=[],
        required_node_types=["context_node", "actuator_simulator"],
        description=(
            "유예 기간 내 취소 동작과 타임아웃 시 안전 deferral 전환이 올바르게 동작하는지 검증한다."
        ),
        paper_tables=[],
    ),
    PackageId.G: PackageDefinition(
        package_id=PackageId.G,
        name_ko="MQTT/Payload Governance",
        required=False,
        required_metrics=["governance_pass_rate", "topic_drift_detection_rate"],
        recommended_scenarios=[
            "baseline_scenario_skeleton.json",
            "class1_baseline_scenario_skeleton.json",
            "class2_insufficient_context_scenario_skeleton.json",
        ],
        recommended_fault_profiles=["FAULT_CONTRACT_DRIFT_01"],
        comparison_conditions=[],
        required_node_types=["context_node"],
        description=(
            "MQTT 토픽/페이로드 거버넌스 검증. 토픽 드리프트 감지율과 "
            "페이로드 계약 준수율을 측정한다."
        ),
        paper_tables=["Table 6"],
    ),
}

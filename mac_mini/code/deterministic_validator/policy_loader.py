"""
frozen 정책/스키마 파일 로더 (deterministic_validator 전용).
허용 액션, bounded 파라미터 범위를 절대 하드코딩하지 않고 이 모듈을 통해 읽어온다.
"""
import json
from pathlib import Path
from typing import Any, Dict

# mac_mini/code/deterministic_validator/policy_loader.py 기준 4단계 상위가 리포지토리 루트
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

POLICY_TABLE_PATH = _REPO_ROOT / "common/policies/policy_table_v1_1_2_FROZEN.json"
LOW_RISK_ACTIONS_PATH = _REPO_ROOT / "common/policies/low_risk_actions_v1_1_0_FROZEN.json"


def load_policy_table() -> Dict[str, Any]:
    """policy_table_v1_1_2_FROZEN.json 을 읽어 dict 로 반환한다."""
    with open(POLICY_TABLE_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_low_risk_actions() -> Dict[str, Any]:
    """low_risk_actions_v1_1_0_FROZEN.json 을 읽어 dict 로 반환한다."""
    with open(LOW_RISK_ACTIONS_PATH, encoding="utf-8") as f:
        return json.load(f)

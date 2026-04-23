"""
frozen 정책 파일 로더 (caregiver_confirmation_backend 전용).
허용 액션 목록을 절대 하드코딩하지 않고 이 모듈을 통해 읽어온다.
"""
import json
from pathlib import Path
from typing import Any, Dict

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

LOW_RISK_ACTIONS_PATH = _REPO_ROOT / "common/policies/low_risk_actions_v1_1_0_FROZEN.json"


def load_low_risk_actions() -> Dict[str, Any]:
    """low_risk_actions_v1_1_0_FROZEN.json 을 읽어 dict 로 반환한다."""
    with open(LOW_RISK_ACTIONS_PATH, encoding="utf-8") as f:
        return json.load(f)

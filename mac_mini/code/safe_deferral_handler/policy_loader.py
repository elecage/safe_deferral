"""
frozen 정책 파일 로더 (safe_deferral_handler 전용).
타임아웃, 최대 시도 횟수 등을 절대 하드코딩하지 않고 이 모듈을 통해 읽어온다.
"""
import json
from pathlib import Path
from typing import Any, Dict

# mac_mini/code/safe_deferral_handler/policy_loader.py 기준 4단계 상위가 리포지토리 루트
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

POLICY_TABLE_PATH = _REPO_ROOT / "common/policies/policy_table_v1_1_2_FROZEN.json"


def load_policy_table() -> Dict[str, Any]:
    """policy_table_v1_1_2_FROZEN.json 을 읽어 dict 로 반환한다."""
    with open(POLICY_TABLE_PATH, encoding="utf-8") as f:
        return json.load(f)

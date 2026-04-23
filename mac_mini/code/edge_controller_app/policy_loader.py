"""
엣지 컨트롤러 정책 파일 로더.

frozen baseline 정책 및 스키마를 로드한다.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Frozen baseline 파일 경로 계산
_REPO_ROOT = Path(__file__).resolve().parents[4]
POLICY_TABLE_PATH = _REPO_ROOT / "common/policies/policy_table_v1_1_2_FROZEN.json"
LOW_RISK_ACTIONS_PATH = _REPO_ROOT / "common/policies/low_risk_actions_v1_1_0_FROZEN.json"
FAULT_RULES_PATH = _REPO_ROOT / "common/policies/fault_injection_rules_v1_4_0_FROZEN.json"


def load_policy_table() -> Dict[str, Any]:
    """
    정책 테이블 로드.

    Returns:
        정책 테이블 딕셔너리

    Raises:
        FileNotFoundError: 정책 파일을 찾을 수 없는 경우
        json.JSONDecodeError: JSON 파싱 오류
    """
    try:
        with open(POLICY_TABLE_PATH, encoding="utf-8") as f:
            policy_table = json.load(f)
        logger.info(
            "정책 테이블 로드 완료 | path=%s version=%s",
            POLICY_TABLE_PATH,
            policy_table.get("version", "unknown"),
        )
        return policy_table
    except FileNotFoundError:
        logger.error("정책 테이블 파일 없음 | path=%s", POLICY_TABLE_PATH)
        raise
    except json.JSONDecodeError as exc:
        logger.error("정책 테이블 JSON 파싱 오류 | path=%s error=%s", POLICY_TABLE_PATH, exc)
        raise


def load_low_risk_actions() -> Dict[str, Any]:
    """
    저위험 액션 카탈로그 로드.

    Returns:
        저위험 액션 딕셔너리

    Raises:
        FileNotFoundError: 정책 파일을 찾을 수 없는 경우
        json.JSONDecodeError: JSON 파싱 오류
    """
    try:
        with open(LOW_RISK_ACTIONS_PATH, encoding="utf-8") as f:
            actions = json.load(f)
        logger.info(
            "저위험 액션 카탈로그 로드 완료 | path=%s version=%s",
            LOW_RISK_ACTIONS_PATH,
            actions.get("version", "unknown"),
        )
        return actions
    except FileNotFoundError:
        logger.error("저위험 액션 카탈로그 파일 없음 | path=%s", LOW_RISK_ACTIONS_PATH)
        raise
    except json.JSONDecodeError as exc:
        logger.error(
            "저위험 액션 카탈로그 JSON 파싱 오류 | path=%s error=%s",
            LOW_RISK_ACTIONS_PATH,
            exc,
        )
        raise


def load_fault_rules() -> Dict[str, Any]:
    """
    장애 주입 규칙 로드.

    Returns:
        장애 주입 규칙 딕셔너리

    Raises:
        FileNotFoundError: 규칙 파일을 찾을 수 없는 경우
        json.JSONDecodeError: JSON 파싱 오류
    """
    try:
        with open(FAULT_RULES_PATH, encoding="utf-8") as f:
            rules = json.load(f)
        logger.info(
            "장애 주입 규칙 로드 완료 | path=%s version=%s",
            FAULT_RULES_PATH,
            rules.get("version", "unknown"),
        )
        return rules
    except FileNotFoundError:
        logger.error("장애 주입 규칙 파일 없음 | path=%s", FAULT_RULES_PATH)
        raise
    except json.JSONDecodeError as exc:
        logger.error(
            "장애 주입 규칙 JSON 파싱 오류 | path=%s error=%s", FAULT_RULES_PATH, exc
        )
        raise

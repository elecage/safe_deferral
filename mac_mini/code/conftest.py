"""
pytest 실행 시 mac_mini/code/ 를 PYTHONPATH에 추가한다.
리포지토리 루트에서 pytest mac_mini/code/ 로 실행할 때 필요하다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

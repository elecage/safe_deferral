"""테스트 설정."""

import sys
from pathlib import Path

# mac_mini/code 디렉토리를 Python path에 추가
_CODE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_CODE_DIR))

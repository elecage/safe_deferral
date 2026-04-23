"""
DB 스키마 초기화 스크립트.

사용법:
  python -m audit_logging_service.init_schema
  python -m audit_logging_service.init_schema --db-path /path/to/audit_log.db
"""
import argparse
import logging
from pathlib import Path

from .db import AuditDB, DEFAULT_DB_PATH

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="감사 로그 DB 스키마 초기화")
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"SQLite DB 파일 경로 (기본값: {DEFAULT_DB_PATH})",
    )
    args = parser.parse_args()

    logger.info("DB 스키마 초기화 시작 | path=%s", args.db_path)
    with AuditDB(db_path=args.db_path) as db:
        db.init_schema()
        mode = db.get_wal_mode()
        logger.info("초기화 완료 | journal_mode=%s", mode)


if __name__ == "__main__":
    main()

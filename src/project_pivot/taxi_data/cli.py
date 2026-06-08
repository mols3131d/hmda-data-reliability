"""Taxi 데이터 적재 CLI."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from project_pivot.logger import configure_logging
from project_pivot.taxi_data.database import DuckDBConnectionManager
from project_pivot.taxi_data.ingestion import (
    YELLOW_TRIPDATA_TABLE,
    load_yellow_tripdata_partition,
)


def build_parser() -> argparse.ArgumentParser:
    """Taxi 데이터 CLI 파서를 생성한다."""

    parser = argparse.ArgumentParser(prog="project-pivot-taxi")
    subparsers = parser.add_subparsers(dest="command", required=True)

    load_partition = subparsers.add_parser(
        "load-partition",
        help="옐로우 택시 일자 파티션을 raw 테이블에 적재한다.",
    )
    load_partition.add_argument("--database", type=Path, required=True)
    load_partition.add_argument("--partition-date", required=True)
    load_partition.add_argument("--source", type=Path, nargs="+", required=True)
    load_partition.add_argument("--table-name", default=YELLOW_TRIPDATA_TABLE)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """명령행 인자를 파싱하고 선택한 적재 작업을 실행한다."""

    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "load-partition":
        return _load_partition(args)
    parser.error(f"지원하지 않는 명령입니다: {args.command}")


def _load_partition(args: argparse.Namespace) -> int:
    with DuckDBConnectionManager(args.database) as connection:
        load_yellow_tripdata_partition(
            connection,
            args.source,
            args.partition_date,
            table_name=args.table_name,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

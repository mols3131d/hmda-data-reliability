"""Pipeline pipeline 실행 CLI."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from project_pivot.hmda_data.errors import HMDADataLoadError
from project_pivot.logger import configure_logging, get_logger
from project_pivot.pipeline._errors import PipelineRuntimeError
from project_pivot.pipeline._request import PipelineRunRequest
from project_pivot.pipeline._runner import run_pipeline
from project_pivot.reliability.errors import ReliabilityError

_LOGGER = get_logger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    """Pipeline pipeline CLI 파서를 생성한다."""

    parser = argparse.ArgumentParser(prog="project-pivot-pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser(
        "run",
        help="Pipeline pipeline을 실행하고 JSON 결과를 파일로 저장한다.",
    )
    run.add_argument(
        "--output",
        type=Path,
        default=Path("scratch/evaluation/pipeline_run_result.json"),
        help="pipeline result JSON 저장 경로.",
    )
    run.add_argument("--database", type=Path, default=Path("data/project_pivot.duckdb"))
    run.add_argument("--source-root", type=Path, default=Path("data/raw/hmda"))
    run.add_argument("--source-year", type=int, default=2025)
    run.add_argument("--source-file")
    run.add_argument(
        "--report-path",
        type=Path,
        default=Path("scratch/evaluation/pipeline_run_report.md"),
        help="evaluation report Markdown 저장 경로.",
    )
    run.add_argument(
        "--run-dbt-build",
        action="store_true",
        help="raw 적재 후 dbt build까지 실행한다.",
    )
    run.add_argument(
        "--run-backfill",
        action="store_true",
        help="승인된 backfill과 사후 profile validation을 실행한다.",
    )
    run.add_argument(
        "--simulate-row-count-ratio",
        type=float,
        default=0.25,
        help="Pipeline incident 재현용 current row count 비율.",
    )

    return parser


def _run_pipeline(args: argparse.Namespace) -> int:
    request = PipelineRunRequest(
        database_path=args.database,
        source_root=args.source_root,
        source_year=args.source_year,
        source_file=args.source_file,
        report_path=args.report_path,
        run_dbt_build=args.run_dbt_build,
        run_backfill=args.run_backfill,
        simulate_row_count_ratio=args.simulate_row_count_ratio,
    )
    try:
        result = run_pipeline(request)
    except (PipelineRuntimeError, ReliabilityError, HMDADataLoadError) as exc:
        _LOGGER.error("Pipeline pipeline 실행 실패", extra={"error": str(exc)})
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    _LOGGER.info(
        "Pipeline pipeline 결과 저장 완료", extra={"output_path": str(args.output)}
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """명령행 인자를 파싱하고 Pipeline pipeline을 실행한다."""

    configure_logging()
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return _run_pipeline(args)
    parser.error(f"지원하지 않는 명령입니다: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())

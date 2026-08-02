#!/usr/bin/env python3
"""HMDA EDA representative memory fixture를 생성한다."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from project_pivot.hmda_data.eda import prepare_hmda_eda_fixture


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-directory",
        type=Path,
        default=Path("data/samples/hmda/eda-memory-v1"),
    )
    parser.add_argument("--row-count", type=int, default=5_000_000)
    parser.add_argument("--seed", type=int, default=20_250_731)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = prepare_hmda_eda_fixture(
        args.output_directory,
        row_count=args.row_count,
        seed=args.seed,
    )
    print(json.dumps(manifest.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

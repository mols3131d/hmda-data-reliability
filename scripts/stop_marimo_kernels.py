#!/usr/bin/env python3
"""현재 프로젝트의 marimo IPC 커널을 종료한다."""

from __future__ import annotations

import argparse
import os
import signal
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL_COMMAND = "-m marimo._ipc.launch_kernel"
PROJECT_PYTHON = str(ROOT / ".venv" / "bin" / "python")


def kernel_pids() -> list[int]:
    """현재 프로젝트 가상환경에서 실행 중인 marimo 커널 PID를 반환한다."""
    pids: list[int] = []
    for process_dir in Path("/proc").glob("[0-9]*"):
        try:
            command = (
                (process_dir / "cmdline").read_bytes().replace(b"\0", b" ").decode()
            )
        except (FileNotFoundError, PermissionError, UnicodeDecodeError):
            continue
        if PROJECT_PYTHON in command and KERNEL_COMMAND in command:
            pids.append(int(process_dir.name))
    return sorted(pids)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="종료 대상만 출력")
    parser.add_argument(
        "--force",
        action="store_true",
        help="5초 후에도 남은 커널에 SIGKILL 전송",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pids = kernel_pids()
    if not pids:
        print("실행 중인 프로젝트 marimo 커널이 없습니다.")
        return 0

    print(f"marimo 커널: {', '.join(map(str, pids))}")
    if args.dry_run:
        return 0

    for pid in pids:
        os.kill(pid, signal.SIGTERM)
    time.sleep(0.2)

    remaining = kernel_pids()
    if remaining and args.force:
        for pid in remaining:
            os.kill(pid, signal.SIGKILL)
        remaining = kernel_pids()

    if remaining:
        print(f"종료 대기 중: {', '.join(map(str, remaining))}")
        return 1

    print("marimo 커널을 종료했습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

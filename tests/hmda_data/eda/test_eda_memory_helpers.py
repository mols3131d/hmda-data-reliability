"""HMDA EDA memory report 판정 테스트."""

from __future__ import annotations

import pytest

from project_pivot.hmda_data.eda import (
    assess_memory_runs,
    parse_gnu_time_report,
)

pytestmark = pytest.mark.unit


def test_parse_gnu_time_report() -> None:
    """GNU time의 peak RSS와 elapsed 값을 읽는다."""

    parsed = parse_gnu_time_report(
        """
        Elapsed (wall clock) time (h:mm:ss or m:ss): 1:02.50
        Maximum resident set size (kbytes): 123456
        """
    )

    assert parsed == {"peak_rss_kib": 123456, "elapsed_seconds": 62.5}


@pytest.mark.parametrize(
    ("peak_ratio", "expected_status"),
    [(0.8, "passed"), (0.86, "improvement_needed")],
)
def test_assess_memory_runs_applies_margin(
    peak_ratio: float,
    expected_status: str,
) -> None:
    """세 반복의 최대 peak가 85% threshold를 적용하는지 검증한다."""

    process_limit_bytes = 1024**3
    peak_rss_kib = int(process_limit_bytes * peak_ratio / 1024)
    runs = [
        {
            "run": run_number,
            "exit_code": 0,
            "resource_status": "passed",
            "output_validation": "passed",
            "peak_rss_kib": peak_rss_kib,
            "temp_disk_bytes": 100,
        }
        for run_number in range(1, 4)
    ]

    assessment = assess_memory_runs(
        runs,
        process_limit_bytes=process_limit_bytes,
        temp_disk_limit_bytes=1024,
    )

    assert assessment["status"] == expected_status


def test_assess_memory_runs_fails_incomplete_result() -> None:
    """세 반복 중 invariant 실패가 있으면 전체 결과를 실패시킨다."""

    runs = [
        {
            "run": run_number,
            "exit_code": 0,
            "resource_status": "passed",
            "output_validation": "failed" if run_number == 2 else "passed",
            "peak_rss_kib": 100,
            "temp_disk_bytes": 100,
        }
        for run_number in range(1, 4)
    ]

    assessment = assess_memory_runs(
        runs,
        process_limit_bytes=1024**3,
        temp_disk_limit_bytes=1024,
    )

    assert assessment == {
        "status": "failed",
        "reason": "process, resource, temp disk, or output validation failed",
        "failed_runs": [2],
    }


def test_assess_memory_runs_fails_temp_disk_limit() -> None:
    """전용 temp directory가 설정된 disk budget을 넘으면 실패한다."""

    runs = [
        {
            "run": run_number,
            "exit_code": 0,
            "resource_status": "passed",
            "output_validation": "passed",
            "peak_rss_kib": 100,
            "temp_disk_bytes": 2048 if run_number == 3 else 100,
        }
        for run_number in range(1, 4)
    ]

    assessment = assess_memory_runs(
        runs,
        process_limit_bytes=1024**3,
        temp_disk_limit_bytes=1024,
    )

    assert assessment["status"] == "failed"
    assert assessment["failed_runs"] == [3]


def test_assess_memory_runs_fails_resource_limit_or_timeout() -> None:
    """OOM 또는 timeout으로 표시된 process run은 전체 결과를 실패시킨다."""

    runs = [
        {
            "run": run_number,
            "exit_code": 124 if run_number == 1 else 0,
            "resource_status": "failed" if run_number == 1 else "passed",
            "output_validation": "failed" if run_number == 1 else "passed",
            "peak_rss_kib": 100,
            "temp_disk_bytes": 100,
        }
        for run_number in range(1, 4)
    ]

    assessment = assess_memory_runs(
        runs,
        process_limit_bytes=1024**3,
        temp_disk_limit_bytes=1024,
    )

    assert assessment["status"] == "failed"
    assert assessment["failed_runs"] == [1]

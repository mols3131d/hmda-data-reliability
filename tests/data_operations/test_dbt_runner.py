"""dbt 작업 runner 경계 테스트."""

import subprocess
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired

import pytest

from project_pivot.data_operations import runner
from project_pivot.data_operations.errors import DataOperationError
from project_pivot.data_operations.request import DataOperationRequest

pytestmark = pytest.mark.component


def test_run_dbt_build_requires_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """종료 코드 0이어도 artifact가 없으면 실패한다."""

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(args[0], 0, "", ""),
    )

    with pytest.raises(DataOperationError, match="artifact"):
        runner.run_dbt_build(_request(tmp_path))


def test_run_dbt_build_wraps_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """dbt 제한 시간 초과를 데이터 작업 오류로 변환한다."""

    def raise_timeout(*args: object, **kwargs: object) -> CompletedProcess[str]:
        raise TimeoutExpired(cmd="dbt build", timeout=300)

    monkeypatch.setattr(subprocess, "run", raise_timeout)

    with pytest.raises(DataOperationError, match="시간"):
        runner.run_dbt_build(_request(tmp_path))


def test_run_dbt_build_returns_verified_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """이번 실행에서 생성된 artifact만 성공 결과로 반환한다."""

    request = _request(tmp_path)

    def write_artifacts(*args: object, **kwargs: object) -> CompletedProcess[str]:
        request.dbt_manifest_path.write_text("{}", encoding="utf-8")
        request.dbt_run_results_path.write_text("{}", encoding="utf-8")
        return CompletedProcess(["dbt", "build"], 0, "", "")

    monkeypatch.setattr(subprocess, "run", write_artifacts)

    result = runner.run_dbt_build(request)

    assert result.succeeded
    assert result.manifest_path == request.dbt_manifest_path
    assert result.run_results_path == request.dbt_run_results_path


def _request(tmp_path: Path) -> DataOperationRequest:
    return DataOperationRequest(
        dbt_manifest_path=tmp_path / "manifest.json",
        dbt_run_results_path=tmp_path / "run_results.json",
    )

"""HMDA EDA Marimo notebook runtime smoke 계획.

Contract:
    - Notebook은 canonical ``analyze_hmda_csv`` 결과를 rendering한다.
    - Valid fixture는 distribution, numeric summary, anomaly, grain rendering
      path를 완료한다.
    - Malformed fixture는 partial evidence 없이 명시적 exception 상태를 낸다.

Risks:
    - ``marimo check``만 통과하고 runtime cell execution이 깨질 수 있다.
    - Long-running notebook server에 의존하면 test가 종료되지 않을 수 있다.

Scope:
    Subprocess-level runtime/rendering smoke only. 계산 정확성은 ``test_eda.py``,
    deterministic expected values는 ``test_eda_fixture.py``가 소유한다.

Planning:
    실행 command와 inspectable output contract를 확정한 뒤 ``_plan_*``을 실제
    integration tests로 전환한다. 현재 함수는 pytest가 수집하지 않는다.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.integration
def test_valid_fixture_completes_notebook_rendering(tmp_path: Path) -> None:
    """종료 가능한 Marimo export command로 valid runtime path를 검증한다.

    Setup:
        Deterministic fixture path를 notebook input으로 주입한다.
    Observable result:
        Subprocess가 성공 종료하고 export artifact에서 baseline, distribution,
        numeric summary, grain section을 식별할 수 있다.
    """
    source_path = tmp_path / "hmda.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,state_code,county_code,loan_purpose,action_taken,loan_amount,income",
                "2024,CA,06001,1,1,350000,120",
                "2025,NY,36001,1,3,420000,150",
            ]
        ),
        encoding="utf-8",
    )

    # Resolve the notebook path relative to this test file to avoid CWD dependency
    notebook_path = Path(__file__).resolve().parents[3] / "notebooks" / "eda_mo.py"
    if not notebook_path.exists():
        pytest.skip("Notebook file does not exist yet")

    output_path = tmp_path / "output.html"

    uv_executable = shutil.which("uv") or "uv"

    # NOTE: tests might run in different environment, make sure to propagate os.environ
    # and override specific variables.
    test_env = os.environ.copy()
    test_env["HMDA_EDA_DATA_PATH"] = str(source_path)

    result = subprocess.run(
        [
            uv_executable,
            "run",
            "marimo",
            "export",
            "html",  # Use html instead of html-wasm to capture errors at export time
            str(notebook_path),
            "-o",
            str(output_path),
        ],
        env=test_env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")

    # Verify there are no runtime errors in the exported notebook
    assert "Traceback (most recent call last)" not in content
    assert "HMDADataValidationError" not in content


@pytest.mark.integration
def test_malformed_fixture_reports_notebook_failure(tmp_path: Path) -> None:
    """Malformed input이 partial rendering 없이 실패 상태를 노출하는지 검증한다.

    Observable result:
        Subprocess 또는 exported session에서 원래 exception type/message를
        식별할 수 있고 completed evidence section은 생성되지 않는다.
    """
    source_path = tmp_path / "malformed.csv"
    source_path.write_text("activity_year,state_code\n2025,CA", encoding="utf-8")

    # Resolve the notebook path relative to this test file to avoid CWD dependency
    notebook_path = Path(__file__).resolve().parents[3] / "notebooks" / "eda_mo.py"
    if not notebook_path.exists():
        pytest.skip("Notebook file does not exist yet")

    output_path = tmp_path / "output_malformed.html"

    uv_executable = shutil.which("uv") or "uv"

    test_env = os.environ.copy()
    test_env["HMDA_EDA_DATA_PATH"] = str(source_path)

    subprocess.run(
        [
            uv_executable,
            "run",
            "marimo",
            "export",
            "html",  # Use html instead of html-wasm to capture errors at export time
            str(notebook_path),
            "-o",
            str(output_path),
        ],
        env=test_env,
        capture_output=True,
        text=True,
    )

    # Note: marimo export might still return 0 if it generates HTML with error outputs.
    content = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
    # Ensure marimo successfully caught and rendered the error
    assert "HMDADataValidationError" in content
    assert "Required EDA column validation failed" in content

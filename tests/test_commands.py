"""Repository Node command runner contract tests."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts._commands as commands


@pytest.mark.unit
def test_run_npm_exec_uses_explicit_package_binary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """npm exec에 package와 실행 binary를 모두 명시한다."""

    captured: dict[str, object] = {}
    monkeypatch.setattr(commands.shutil, "which", lambda name: "/usr/bin/npm")

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        check: bool,
    ) -> SimpleNamespace:
        captured.update(command=command, cwd=cwd, check=check)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert (
        commands.run_npm_exec(
            "rulesync@latest",
            "rulesync",
            ("install", "--frozen"),
            cwd=tmp_path,
        )
        == 0
    )
    assert captured == {
        "command": [
            "/usr/bin/npm",
            "exec",
            "--yes",
            "--package=rulesync@latest",
            "--",
            "rulesync",
            "install",
            "--frozen",
        ],
        "cwd": tmp_path,
        "check": False,
    }


@pytest.mark.unit
def test_run_npm_exec_requires_npm(monkeypatch: pytest.MonkeyPatch) -> None:
    """npm이 없으면 package 실행을 시작하지 않고 명확히 실패한다."""

    monkeypatch.setattr(commands.shutil, "which", lambda _name: None)

    with pytest.raises(RuntimeError, match="npm is required"):
        commands.run_npm_exec("rulesync@latest", "rulesync", (), cwd=Path("."))

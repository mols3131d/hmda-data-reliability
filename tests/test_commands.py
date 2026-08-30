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


@pytest.mark.unit
def test_run_npm_preserves_windows_agent_arguments(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Windows에서도 Agent source가 cmd.exe 명령어로 재해석되지 않는다."""

    npm = r"C:\Program Files\nodejs\npm.cmd"
    captured: dict[str, object] = {}
    monkeypatch.setattr(commands.os, "name", "nt")
    monkeypatch.setattr(
        commands.shutil,
        "which",
        lambda name: npm if name == "npm.cmd" else None,
    )

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        check: bool,
    ) -> SimpleNamespace:
        captured.update(command=command, cwd=cwd, check=check)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    agent_source = r"C:\R&D\skills"
    args = (
        "exec",
        "--yes",
        "--package=skills@latest",
        "--",
        "skills",
        "use",
        agent_source,
        "--skill",
        "review",
        "--agent",
        "codex",
    )

    assert commands.run_npm(args, cwd=tmp_path) == 0
    assert captured == {
        "command": [npm, *args],
        "cwd": tmp_path,
        "check": False,
    }

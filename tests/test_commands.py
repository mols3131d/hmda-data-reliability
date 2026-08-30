"""Repository Node command runner contract tests."""

from __future__ import annotations

import os
import shutil
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
def test_run_npm_uses_node_for_windows_npm_cmd(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Windows npm.cmd 대신 node.exe로 npm CLI를 직접 실행한다."""

    npm = tmp_path / "npm.cmd"
    node = tmp_path / "node.exe"
    npm_cli = tmp_path / "node_modules" / "npm" / "bin" / "npm-cli.js"
    npm.touch()
    node.touch()
    npm_cli.parent.mkdir(parents=True)
    npm_cli.touch()

    captured: dict[str, object] = {}
    monkeypatch.setattr(commands.os, "name", "nt")
    monkeypatch.setattr(commands, "Path", type(tmp_path))
    monkeypatch.setattr(
        commands.shutil,
        "which",
        lambda name: str(npm) if name == "npm.cmd" else None,
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
        "command": [str(node), str(npm_cli), *args],
        "cwd": tmp_path,
        "check": False,
    }


@pytest.mark.unit
def test_run_local_node_tool_uses_npm_on_windows(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Windows local Node tool도 .cmd wrapper 대신 npm을 사용한다."""

    monkeypatch.setattr(commands.os, "name", "nt")
    executable = commands.local_node_tool_path("biome", cwd=tmp_path)
    executable.parent.mkdir(parents=True)
    executable.touch()

    captured: dict[str, object] = {}

    def fake_run_npm(args: tuple[str, ...], *, cwd: Path) -> int:
        captured.update(args=args, cwd=cwd)
        return 0

    monkeypatch.setattr(commands, "run_npm", fake_run_npm)

    assert commands.run_local_node_tool("biome", ("check", "file"), cwd=tmp_path) == 0
    assert captured == {
        "args": (
            "exec",
            "--offline",
            "--prefix",
            str(tmp_path / ".local" / "tooling"),
            "--",
            "biome",
            "check",
            "file",
        ),
        "cwd": tmp_path,
    }


@pytest.mark.component
@pytest.mark.skipif(os.name != "nt", reason="requires Windows npm and Node")
def test_run_npm_preserves_windows_agent_arguments_at_process_boundary(
    tmp_path: Path,
) -> None:
    """실제 Windows 프로세스 경계에서도 Agent source 인자를 보존한다."""

    npm = shutil.which("npm.cmd")
    node = shutil.which("node.exe") or shutil.which("node")
    if npm is None or node is None:
        pytest.fail("npm.cmd and node.exe are required for this Windows test")

    capture = tmp_path / "argv.txt"
    script = tmp_path / "capture.js"
    script.write_text(
        "const fs = require('node:fs');\n"
        "fs.writeFileSync(process.argv[2], process.argv[3], 'ascii');\n",
        encoding="ascii",
    )

    source = r"C:\R&D\skills"
    args = (
        "exec",
        "--offline",
        "--",
        node,
        str(script),
        str(capture),
        source,
    )

    assert commands.run_npm(args, cwd=tmp_path) == 0
    assert capture.read_text(encoding="ascii") == source

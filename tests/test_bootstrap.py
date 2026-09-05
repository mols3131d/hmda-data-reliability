"""Repository bootstrap workflow contract tests."""

from __future__ import annotations

import runpy
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SCRIPT = REPO_ROOT / "scripts" / "bootstrap.py"


def _load_bootstrap(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[tuple[object, ...]],
) -> dict[str, object]:
    commands = ModuleType("_commands")

    def fake_run(command: Sequence[str], *, cwd: Path) -> int:
        calls.append(("run", tuple(command), cwd))
        return 0

    def fake_run_npm(args: Sequence[str], *, cwd: Path) -> int:
        calls.append(("run_npm", tuple(args), cwd))
        return 0

    def fake_run_npm_exec(
        package: str,
        binary: str,
        args: Sequence[str],
        *,
        cwd: Path,
    ) -> int:
        calls.append(("run_npm_exec", package, binary, tuple(args), cwd))
        return 0

    def fake_local_node_tool_path(tool: str, *, cwd: Path) -> Path:
        return cwd / ".local" / "tooling" / tool

    commands.__dict__["run"] = fake_run
    commands.__dict__["run_npm"] = fake_run_npm
    commands.__dict__["run_npm_exec"] = fake_run_npm_exec
    commands.__dict__["local_node_tool_path"] = fake_local_node_tool_path
    monkeypatch.setitem(sys.modules, "_commands", commands)
    return runpy.run_path(str(BOOTSTRAP_SCRIPT), run_name="test_bootstrap")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("action", "expected_labels"),
    [
        (
            "setup",
            ("dependencies", "git hooks", "agent assets", "node tools", "openspec"),
        ),
        ("session", ("dependencies", "agent assets", "node tools")),
        ("update", ("agent assets", "openspec", "node tools")),
    ],
)
def test_bootstrap_action_selects_expected_steps(
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    expected_labels: tuple[str, ...],
) -> None:
    """Each bootstrap action keeps its documented ordered operation set."""
    namespace = _load_bootstrap(monkeypatch, [])

    steps = namespace["_steps"]
    assert callable(steps)
    assert tuple(label for label, _step in steps(action)) == expected_labels


@pytest.mark.unit
def test_bootstrap_dependency_sync_uses_locked_uv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dependency bootstrap delegates to uv sync with the lockfile enforced."""
    calls: list[tuple[object, ...]] = []
    namespace = _load_bootstrap(monkeypatch, calls)
    shutil_module = namespace["shutil"]
    monkeypatch.setattr(shutil_module, "which", lambda name: "/usr/bin/uv")

    sync_dependencies = namespace["_sync_dependencies"]
    assert callable(sync_dependencies)
    assert sync_dependencies() == 0
    assert calls == [("run", ("uv", "sync", "--locked"), REPO_ROOT)]


@pytest.mark.unit
def test_bootstrap_openspec_sync_preserves_cli_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OpenSpec refresh uses the expected package, binary, action, and cwd."""
    calls: list[tuple[object, ...]] = []
    namespace = _load_bootstrap(monkeypatch, calls)

    sync_openspec = namespace["_sync_openspec"]
    assert callable(sync_openspec)
    assert sync_openspec() == 0
    assert calls == [
        (
            "run_npm_exec",
            "@fission-ai/openspec@latest",
            "openspec",
            ("update",),
            REPO_ROOT,
        )
    ]

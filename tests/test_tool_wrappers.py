"""CLI wrapper forwarding contract tests."""

from __future__ import annotations

import runpy
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"


def _load_script(
    monkeypatch: pytest.MonkeyPatch,
    script_name: str,
    commands_module: ModuleType,
) -> dict[str, object]:
    monkeypatch.setitem(sys.modules, "_commands", commands_module)
    return runpy.run_path(str(SCRIPTS_DIR / script_name), run_name=f"test_{script_name}")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("script_name", "tool_name"),
    [("biome.py", "biome"), ("tombi.py", "tombi")],
)
def test_local_node_wrapper_forwards_tool_and_cli_args(
    monkeypatch: pytest.MonkeyPatch,
    script_name: str,
    tool_name: str,
) -> None:
    """Biome/Tombi wrappers preserve tool identity, argv, and repository cwd."""
    calls: list[tuple[str, tuple[str, ...], Path]] = []
    commands = ModuleType("_commands")

    def fake_run_local_node_tool(
        tool: str,
        args: Sequence[str],
        *,
        cwd: Path,
    ) -> int:
        calls.append((tool, tuple(args), cwd))
        return 17

    setattr(commands, "run_local_node_tool", fake_run_local_node_tool)
    namespace = _load_script(monkeypatch, script_name, commands)
    monkeypatch.setattr(sys, "argv", [script_name, "check", "example.txt"])

    main = namespace["main"]
    assert callable(main)
    assert main() == 17
    assert calls == [(tool_name, ("check", "example.txt"), REPO_ROOT)]


@pytest.mark.unit
def test_rulesync_wrapper_forwards_package_binary_and_args(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rulesync wrapper preserves package, binary, args, and repository cwd."""
    calls: list[tuple[str, str, tuple[str, ...], Path]] = []
    commands = ModuleType("_commands")

    def fake_run_npm_exec(
        package: str,
        binary: str,
        args: Sequence[str],
        *,
        cwd: Path,
    ) -> int:
        calls.append((package, binary, tuple(args), cwd))
        return 23

    setattr(commands, "run_npm_exec", fake_run_npm_exec)
    namespace = _load_script(monkeypatch, "rulesync.py", commands)

    run = namespace["_run"]
    assert callable(run)
    assert run(("generate", "--check")) == 23
    assert calls == [
        ("rulesync@latest", "rulesync", ("generate", "--check"), REPO_ROOT)
    ]

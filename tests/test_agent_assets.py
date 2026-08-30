"""Agent Asset lifecycle and execution command tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import scripts.agent_assets as agent_assets


@pytest.mark.unit
def test_run_action_starts_selected_skill_with_selected_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run action이 Skills CLI의 use 경계로 선택값을 전달한다."""

    captured: dict[str, object] = {}

    def fake_run_npm_exec(
        package: str,
        binary: str,
        args: tuple[str, ...],
        *,
        cwd: Path,
    ) -> int:
        captured.update(package=package, binary=binary, args=args, cwd=cwd)
        return 0

    monkeypatch.setattr(agent_assets, "run_npm_exec", fake_run_npm_exec)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "agent_assets.py",
            "run",
            "owner/skills",
            "--skill",
            "review",
            "--agent",
            "codex",
        ],
    )

    assert agent_assets.main() == 0
    assert captured == {
        "package": "skills@latest",
        "binary": "skills",
        "args": ("use", "owner/skills", "--skill", "review", "--agent", "codex"),
        "cwd": agent_assets.REPO_ROOT,
    }

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
    """`run` 서브커맨드가 Skills CLI로 선택된 인자를 정확히 전달하는지 검증한다.

    검증 불변식:
    - 패키지: `skills@latest`
    - 바이너리: `skills`
    - 커맨드라인 아규먼트: `("use", source, "--skill", skill, "--agent", agent)`
    - 작업 디렉토리(cwd): 저장소 루트(`REPO_ROOT`)
    - 종료 코드: 0 반환
    """

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

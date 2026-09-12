#!/usr/bin/env python3
"""Install or update repository-managed Agent Assets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from _commands import run, run_npm_exec
except ModuleNotFoundError:
    from scripts._commands import run, run_npm_exec

REPO_ROOT = Path(__file__).resolve().parents[1]
RULESYNC_SCRIPT = REPO_ROOT / "scripts" / "rulesync.py"
ROUTE_SCRIPT = REPO_ROOT / "scripts" / "generate_agent_routes.py"
SKILLS_LOCK = REPO_ROOT / "skills-lock.json"

_SKILLS_ACTIONS: dict[str, tuple[str, ...]] = {
    "install": ("experimental_install",),
    "update": ("update", "--project", "--yes"),
}


def _run_script(path: Path, *args: str) -> int:
    """파이썬 서브스크립트를 현재 인터프리터로 저장소 루트에서 실행한다.

    Args:
        path: 실행할 스크립트의 절대 경로.
        *args: 스크립트에 전달할 커맨드라인 인자 목록.

    Returns:
        하위 프로세스 종료 코드.
    """
    return run([sys.executable, str(path), *args], cwd=REPO_ROOT)


def _run_skills(action: str) -> int:
    """Skills CLI를 실행하여 에셋을 설치하거나 외부 소스를 업데이트한다.

    `skills-lock.json` 부재 시 실행을 건너뛰고 0을 반환한다.

    Args:
        action: 수행할 액션 (`"install"` 또는 `"update"`).

    Returns:
        프로세스 종료 코드 (파일 미존재로 스킵 시 0).
    """
    if not SKILLS_LOCK.is_file():
        print("skills-lock.json not found; skipping Skills CLI.")
        return 0
    return run_npm_exec(
        "skills@latest",
        "skills",
        _SKILLS_ACTIONS[action],
        cwd=REPO_ROOT,
    )


def _run_agent(source: str, skill: str, agent: str) -> int:
    """Start one supported agent with a selected external Skill.

    Args:
        source: Skills CLI가 지원하는 Skill 소스 (예: GitHub 레포지토리).
        skill: 활성화할 스킬 이름.
        agent: 지원되는 에이전트 식별자 (예: `codex`, `claude-code`).

    Returns:
        프로세스 종료 코드.
    """
    return run_npm_exec(
        "skills@latest",
        "skills",
        ("use", source, "--skill", skill, "--agent", agent),
        cwd=REPO_ROOT,
    )


def _sync(action: str) -> int:
    """Agent Assets를 순차적으로 동기화한다.

    실행 순서(Ordering Invariant):
    1. Rulesync 스크립트 실행 (`scripts/rulesync.py <action>`):
       - Rulesync 실패 시 즉시 중단하고 해당 오류 코드 반환.
    2. Skills CLI 실행 (`skills <action>`):
       - `skills-lock.json`이 있는 경우 보조 external skills 동기화.
    3. Chatbot route 인덱스 생성 (`scripts/generate_agent_routes.py`):
       - Rulesync 및 Skills CLI 완료 후 최종 라우팅 인덱스 갱신.

    Returns:
        0 (모두 성공) 또는 최초/최종 실패 종료 코드.
    """
    rulesync_code = _run_script(RULESYNC_SCRIPT, action)
    if rulesync_code != 0:
        return rulesync_code

    skills_code = _run_skills(action)
    routes_code = _run_script(ROUTE_SCRIPT)
    return skills_code or routes_code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Restore locked Agent Assets or update their managed sources."
    )
    subparsers = parser.add_subparsers(dest="action", required=True)
    for action, help_text in (
        ("install", "install locked assets"),
        ("update", "update managed sources"),
    ):
        subparsers.add_parser(action, help=help_text)

    run_parser = subparsers.add_parser(
        "run",
        help="start a supported agent with one selected Skill",
    )
    run_parser.add_argument("source", help="Skill source accepted by the Skills CLI")
    run_parser.add_argument("--skill", required=True, help="Skill name to activate")
    run_parser.add_argument(
        "--agent",
        required=True,
        help="supported agent identifier, for example codex or claude-code",
    )
    args = parser.parse_args()

    try:
        if args.action == "run":
            return _run_agent(args.source, args.skill, args.agent)
        return _sync(args.action)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate chatbot routing indexes from repository-owned routing metadata."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / ".agents" / "skills"
RULE_ROUTE_SOURCE = REPO_ROOT / ".rulesync" / "rules" / "codex-root.md"
ROUTE_ROOT = REPO_ROOT / ".agents" / "route"

SKILLS_META = {
    "kind": "skills",
    "instructions": (
        "name과 description으로 현재 task에 관련된 Skill을 모두 선택하고 선택한 source만 읽는다. "
        "일치하는 Skill이 없으면 읽지 않는다. Task intent가 materially 바뀌면 다시 선택한다. "
        "이 파일은 derived discovery metadata이며 각 SKILL.md가 authoritative source다."
    ),
}
RULES_META = {
    "kind": "rules",
    "instructions": (
        "Known target path마다 globs를 비교해 일치하는 Rule source를 모두 읽는다. "
        "Target path가 없으면 Rule source를 선로드하지 않는다. "
        "Target path가 materially 바뀌면 다시 계산한다. "
        "이 파일은 derived discovery metadata이며 각 canonical Rule이 authoritative source다."
    ),
}
PATH_RULE_ROW = re.compile(r"^\|\s*\[[^]]+\]\(([^)]+)\)\s*\|\s*(.*?)\s*\|$")
BACKTICK_VALUE = re.compile(r"`([^`]+)`")


def load_frontmatter(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return {}

    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise SystemExit(f"unterminated frontmatter: {path}") from exc

    data = yaml.safe_load("\n".join(lines[1:end])) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"frontmatter must be a mapping: {path}")
    return data


def relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def normalized_text(value: object, *, field: str, path: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"missing {field}: {path}")
    return " ".join(value.split())


def skill_entries() -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for path in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
        meta = load_frontmatter(path)
        entries.append(
            {
                "name": normalized_text(meta.get("name"), field="name", path=path),
                "description": normalized_text(
                    meta.get("description"), field="description", path=path
                ),
                "source": relative(path),
            }
        )
    return entries


def rule_entries() -> list[dict[str, object]]:
    text = RULE_ROUTE_SOURCE.read_text(encoding="utf-8")
    try:
        section = text.split("## Path Rules", 1)[1]
    except IndexError as exc:
        raise SystemExit(f"Path Rules section not found: {RULE_ROUTE_SOURCE}") from exc
    section = section.split("\n## ", 1)[0]

    entries: list[dict[str, object]] = []
    seen: set[str] = set()
    for line in section.splitlines():
        match = PATH_RULE_ROW.match(line.strip())
        if not match:
            continue

        source = match.group(1)
        globs = BACKTICK_VALUE.findall(match.group(2))
        if not globs:
            raise SystemExit(f"missing Path Rule selector: {line}")
        if source in seen:
            raise SystemExit(f"duplicate Path Rule source: {source}")

        source_path = REPO_ROOT / source
        if not source_path.is_file():
            raise SystemExit(f"Path Rule source not found: {source}")

        seen.add(source)
        entries.append({"source": source, "globs": globs})

    if not entries:
        raise SystemExit(f"no Path Rules found: {RULE_ROUTE_SOURCE}")
    return entries


def render(meta: dict[str, str], entries: list[dict[str, object]]) -> str:
    rows: list[dict[str, object]] = [{"_meta": meta}, *entries]
    return "\n".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows
    ) + "\n"


def generated_routes() -> dict[Path, str]:
    return {
        ROUTE_ROOT / "skills.jsonl": render(SKILLS_META, skill_entries()),
        ROUTE_ROOT / "rules.jsonl": render(RULES_META, rule_entries()),
    }


def check_routes(routes: dict[Path, str]) -> int:
    stale = [
        path
        for path, expected in routes.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != expected
    ]
    for path in stale:
        print(f"stale route: {relative(path)}")
    return 1 if stale else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate .agents/route Skill and Rule indexes."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when generated routes differ from committed files",
    )
    args = parser.parse_args()

    routes = generated_routes()
    if args.check:
        return check_routes(routes)

    ROUTE_ROOT.mkdir(parents=True, exist_ok=True)
    for path, content in routes.items():
        path.write_text(content, encoding="utf-8")
        print(f"generated {relative(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

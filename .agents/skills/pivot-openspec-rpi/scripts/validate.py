#!/usr/bin/env python3
"""Validate the Pivot OpenSpec RPI Agent Skill package."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_FILES = {
    "SKILL.md",
    "references/principles.md",
    "references/workflow.md",
    "references/research.md",
    "references/review.md",
    "references/adoption.md",
    "templates/research.md",
    "templates/review.md",
    "tests/acceptance-criteria.md",
    "tests/scenarios.yaml",
}

FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
LINK_RE = re.compile(r"\[[^\]]+\]\((?!https?://|#)([^)]+)\)")
PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate(root: Path) -> list[str]:
    errors: list[str] = []

    if root.name != "pivot-openspec-rpi":
        fail(errors, f"skill directory must be named 'pivot-openspec-rpi': {root}")

    for relative in sorted(REQUIRED_FILES):
        if not (root / relative).is_file():
            fail(errors, f"missing required file: {relative}")

    skill_path = root / "SKILL.md"
    if not skill_path.is_file():
        return errors

    skill_text = skill_path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(skill_text)
    if not match:
        fail(errors, "SKILL.md must start with YAML frontmatter")
    else:
        frontmatter = match.group("body")
        keys = [
            line.split(":", 1)[0].strip()
            for line in frontmatter.splitlines()
            if line and not line.startswith((" ", "\t"))
        ]
        if keys != ["name", "description"]:
            fail(errors, "frontmatter must contain only name then description")
        if not re.search(r"^name:\s*pivot-openspec-rpi\s*$", frontmatter, re.MULTILINE):
            fail(errors, "frontmatter name must be 'pivot-openspec-rpi'")
        if "Use when" not in frontmatter:
            fail(errors, "description must include positive trigger guidance")
        if "Do not use" not in frontmatter:
            fail(errors, "description must include anti-trigger guidance")

    if len(skill_text.splitlines()) > 500:
        fail(errors, "SKILL.md must stay under 500 lines")

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if path.name.lower() == "readme.md":
            fail(errors, f"extraneous README is not allowed: {relative}")

        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".py"}:
            continue

        text = path.read_text(encoding="utf-8")
        if "\t" in text:
            fail(errors, f"tab character found: {relative}")

        if path.suffix.lower() == ".md":
            for target in LINK_RE.findall(text):
                target_path = (path.parent / target.split("#", 1)[0]).resolve()
                try:
                    target_path.relative_to(root.resolve())
                except ValueError:
                    fail(
                        errors,
                        f"relative link escapes skill root: {relative} -> {target}",
                    )
                    continue
                if not target_path.exists():
                    fail(errors, f"broken relative link: {relative} -> {target}")

        if relative.startswith("references/") and PLACEHOLDER_RE.search(text):
            fail(errors, f"reference contains unresolved placeholder: {relative}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "skill_root",
        nargs="?",
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args()

    root = Path(args.skill_root).resolve()
    errors = validate(root)

    if errors:
        print("Pivot OpenSpec RPI validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Pivot OpenSpec RPI validation passed: {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

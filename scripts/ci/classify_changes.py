"""Classify changed paths into Actions validation flags and ordered targets."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field, fields
from fnmatch import fnmatchcase
from pathlib import Path

from changed_files import changed_paths, entrypoint
from classify_openspec import classify_openspec_path

DEPENDENCY_INPUTS = (".python-version", "pyproject.toml", "uv.lock")
CI_SOURCE_ROOT = "scripts/ci"
CI_TEST_ROOT = "tests/scripts/ci"


def matches(path: str, *patterns: str) -> bool:
    return any(fnmatchcase(path, pattern) for pattern in patterns)


def add_unique(targets: list[str], target: str) -> None:
    if target not in targets:
        targets.append(target)


@dataclass
class Scope:
    json: bool = False
    markdown: bool = False
    openspec: bool = False
    openspec_archived: bool = False
    openspec_bulk: bool = False
    tests: bool = False
    toml: bool = False
    python: bool = False
    lock: bool = False
    build: bool = False
    lefthook: bool = False
    routes: bool = False
    tach: bool = False
    zizmor: bool = False
    full_tests: bool = False
    full_type: bool = False
    openspec_spec_targets: list[str] = field(default_factory=list)
    openspec_change_targets: list[str] = field(default_factory=list)
    targets: list[str] = field(default_factory=list)
    type_targets: list[str] = field(default_factory=list)

    def add_target(self, target: str) -> None:
        add_unique(self.targets, target)

    def add_type_target(self, target: str) -> None:
        add_unique(self.type_targets, target)

    def add_focused_test(self, target: str) -> None:
        self.tests = True
        self.add_target(target)
        self.add_type_target(target)

    def require_full_test_and_type(self) -> None:
        self.tests = self.full_tests = self.python = self.full_type = True

    def outputs(self) -> str:
        lines = []
        for attribute in fields(self):
            value = getattr(self, attribute.name)
            encoded = str(value).lower() if isinstance(value, bool) else " ".join(value)
            lines.append(f"{attribute.name}={encoded}\n")
        return "".join(lines)


def _select_execution_scope(path: str, scope: Scope, dependency_changed: bool) -> None:
    if path == "lefthook.yml":
        scope.lefthook = True
    elif dependency_changed or matches(path, "dbt/*.sql", "dbt/*.yml", "dbt/*.yaml"):
        scope.require_full_test_and_type()
    elif matches(path, ".github/workflows/*", f"{CI_SOURCE_ROOT}/*"):
        scope.add_focused_test(CI_TEST_ROOT)
        if path.endswith(".py"):
            scope.add_type_target(CI_SOURCE_ROOT)
    elif matches(path, "src/*", "scripts/*.py"):
        scope.require_full_test_and_type()
    elif matches(path, f"{CI_TEST_ROOT}/*"):
        if Path(CI_TEST_ROOT).is_dir():
            scope.add_focused_test(CI_TEST_ROOT)
        else:
            scope.require_full_test_and_type()
    elif path.startswith("tests/"):
        directory = f"tests/{path.split('/')[1]}"
        if (
            Path(directory).is_dir()
            and Path(directory).name != "__pycache__"
            and not any(character in directory for character in " \t")
        ):
            scope.add_focused_test(directory)
        else:
            scope.require_full_test_and_type()
    elif path.endswith(".py"):
        scope.require_full_test_and_type()


def classify(paths: list[str]) -> Scope:
    scope = Scope()
    for path in paths:
        if not path or path.startswith("inbox/"):
            continue
        if matches(
            path,
            ".github/workflows/*.yml",
            ".github/workflows/*.yaml",
            "action.yml",
            "action.yaml",
            "*/action.yml",
            "*/action.yaml",
        ):
            scope.zizmor = True
        exists = Path(path).is_file()
        dependency_changed = path in DEPENDENCY_INPUTS
        if matches(
            path,
            ".rulesync/rules/*",
            ".rulesync/skills/*/SKILL.md",
            "rulesync.jsonc",
            "rulesync.lock",
            "skills-lock.json",
            ".agents/route/*",
            "scripts/agent_routes/*",
        ):
            scope.routes = True
        if exists and matches(path, "*.json", "*.jsonc"):
            scope.json = True
        if exists and matches(path, "*.toml"):
            scope.toml = True
        if path.endswith(".py") or dependency_changed:
            scope.python = True
        if dependency_changed:
            scope.lock = scope.build = True
        if matches(path, "src/hmda_reliability/*", "README.md", "LICENSE"):
            scope.build = True
        if dependency_changed or matches(
            path,
            "tach.toml",
            "src/*.py",
            "tests/scripts/test_tach*.py",
            "tests/review_ai/test_dependency_boundaries.py",
        ):
            scope.tach = True

        classify_openspec_path(path, scope)
        if path.endswith(".md"):
            scope.markdown |= exists
            continue

        _select_execution_scope(path, scope, dependency_changed)
    return scope


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?")
    parser.add_argument("--stdin", action="store_true")
    parser.add_argument("--markdown-paths", action="store_true")
    args = parser.parse_args()
    paths = sys.stdin.read().split("\n") if args.stdin else changed_paths()
    if any("\n" in path or "\r" in path for path in paths):
        print("Changed paths contain unsupported line breaks", file=sys.stderr)
        raise SystemExit(1)
    if args.markdown_paths:
        for path in paths:
            if (
                path.endswith(".md")
                and not path.startswith("inbox/")
                and Path(path).is_file()
            ):
                print(path)
        return
    output = classify(paths).outputs()
    if args.output:
        with Path(args.output).open("a", encoding="utf-8") as destination:
            destination.write(output)
    else:
        print(output, end="")


if __name__ == "__main__":
    entrypoint(main)

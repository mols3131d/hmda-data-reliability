"""Classify changed paths into Actions validation flags and ordered targets."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field, fields
from fnmatch import fnmatchcase
from pathlib import Path

from changed_files import changed_paths, entrypoint
from classify_openspec import classify_openspec_path

DOMAIN_CONSUMERS = {
    "data_platform": (
        "data_platform",
        "hmda_data",
        "reliability",
        "review_ai",
        "data_operations",
        "orchestration",
        "dbt",
    ),
    "hmda_data": (
        "hmda_data",
        "reliability",
        "review_ai",
        "data_operations",
        "orchestration",
        "dbt",
    ),
    "data_operations": ("reliability", "data_operations", "orchestration"),
    "reliability": ("reliability", "review_ai", "data_operations", "orchestration"),
    "review_ai": ("review_ai",),
    "runtime_ai": ("runtime_ai", "review_ai"),
    "orchestration": ("orchestration",),
}
SCRIPT_TESTS = {
    "scripts/agent_assets.py": ("tests/scripts/test_agent_assets.py",),
    "scripts/_commands.py": (
        "tests/scripts/test_commands.py",
        "tests/scripts/test_tool_wrappers.py",
        "tests/scripts/test_bootstrap.py",
        "tests/scripts/test_agent_assets.py",
    ),
    "scripts/bootstrap.py": ("tests/scripts/test_bootstrap.py",),
    "scripts/biome.py": ("tests/scripts/test_tool_wrappers.py",),
    "scripts/tombi.py": ("tests/scripts/test_tool_wrappers.py",),
    "scripts/generate_docs_indexes.py": (
        "tests/scripts/test_generate_docs_indexes.py",
    ),
    "scripts/validate_inbox_artifacts.py": (
        "tests/scripts/test_validate_inbox_artifacts.py",
    ),
    "scripts/log_agent_event.py": ("tests/scripts/test_log_agent_event.py",),
    "scripts/run_actual_source.py": ("tests/hmda_data/eda/test_eda_evidence.py",),
    "scripts/run_agentic_review_live.py": ("tests/review_ai/test_live_harness.py",),
}


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
    runtime_smoke: bool = False
    tach: bool = False
    full_unit: bool = False
    full_tests: bool = False
    full_type: bool = False
    openspec_spec_targets: list[str] = field(default_factory=list)
    openspec_change_targets: list[str] = field(default_factory=list)
    targets: list[str] = field(default_factory=list)
    ci_targets: list[str] = field(default_factory=list)
    type_targets: list[str] = field(default_factory=list)

    def add_target(self, target: str) -> None:
        add_unique(self.targets, target)

    def add_ci_target(self, target: str) -> None:
        add_unique(self.ci_targets, target)
        self.add_target(target)

    def add_type_target(self, target: str) -> None:
        add_unique(self.type_targets, target)

    def add_focused_test(self, target: str) -> None:
        self.tests = True
        self.add_target(target)
        self.add_type_target(target)

    def full_test_scope(self) -> None:
        self.tests = self.full_tests = self.full_unit = self.full_type = True

    def outputs(self) -> str:
        lines = []
        for attribute in fields(self):
            value = getattr(self, attribute.name)
            encoded = str(value).lower() if isinstance(value, bool) else " ".join(value)
            lines.append(f"{attribute.name}={encoded}\n")
        return "".join(lines)


def add_domain_closure(scope: Scope, domain: str) -> None:
    if domain not in DOMAIN_CONSUMERS:
        scope.full_unit = scope.full_type = True
        return
    for consumer in DOMAIN_CONSUMERS[domain]:
        scope.add_target(f"tests/{consumer}")
        for directory in (f"src/hmda_reliability/{consumer}", f"tests/{consumer}"):
            if Path(directory).is_dir():
                scope.add_type_target(directory)


def classify(paths: list[str]) -> Scope:
    scope = Scope()
    for path in paths:
        if not path or path.startswith("inbox/"):
            continue
        exists = Path(path).is_file()
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
        if path in ("scripts/biome.py", "scripts/bootstrap.py"):
            scope.json = True
        if path in ("scripts/tombi.py", "scripts/bootstrap.py"):
            scope.toml = True
        if matches(path, "*.py", ".python-version", "pyproject.toml", "uv.lock"):
            scope.python = True
        if path in (".python-version", "pyproject.toml", "uv.lock"):
            scope.lock = scope.build = True
        if matches(path, "src/hmda_reliability/*", "README.md", "LICENSE"):
            scope.build = True
        if matches(
            path,
            ".python-version",
            "tach.toml",
            "pyproject.toml",
            "uv.lock",
            "src/*.py",
            "tests/scripts/test_tach*.py",
            "tests/review_ai/test_dependency_boundaries.py",
        ):
            scope.tach = True

        classify_openspec_path(path, scope)
        if path.endswith(".md"):
            scope.markdown |= exists
            continue

        if path == "lefthook.yml":
            scope.lefthook = True
        elif path in (".python-version", "pyproject.toml", "uv.lock"):
            scope.tests = scope.runtime_smoke = scope.full_unit = scope.full_type = True
        elif matches(path, "dbt/*.sql", "dbt/*.yml", "dbt/*.yaml"):
            scope.tests = True
            for domain in ("dbt", "data_operations", "reliability", "orchestration"):
                scope.add_target(f"tests/{domain}")
        elif matches(path, ".github/workflows/*", "scripts/ci/*"):
            scope.tests = True
            scope.add_ci_target("tests/scripts/ci")
            if path.endswith(".py"):
                scope.add_type_target("scripts/ci")
                scope.add_type_target("tests/scripts/ci")
        elif matches(path, "scripts/agent_routes/*.py"):
            scope.add_focused_test("tests/scripts/test_generate_agent_routes.py")
            scope.add_type_target("scripts/agent_routes")
        elif path in SCRIPT_TESTS:
            for target in SCRIPT_TESTS[path]:
                scope.add_focused_test(target)
            if path == "scripts/_commands.py":
                scope.add_type_target("scripts")
        elif matches(path, "scripts/*.py"):
            scope.tests = scope.full_unit = scope.full_type = True
        elif path == "src/hmda_reliability/logger.py":
            scope.tests = scope.full_type = True
            scope.add_target("tests/scripts/test_log_agent_event.py")
        elif matches(path, "src/hmda_reliability/*/*"):
            scope.tests = True
            add_domain_closure(scope, path.split("/")[2])
        elif matches(path, "tests/test_*.py") or path in (
            "tests/scripts/ci/test_ci_classifier_openspec.py",
            "tests/scripts/ci/test_ci_classifier_python.py",
        ):
            if exists:
                scope.tests = True
                scope.add_target(path)
        elif matches(path, "tests/scripts/ci/test_*.py"):
            if exists:
                scope.tests = True
                scope.add_ci_target(path)
        elif matches(path, "tests/scripts/ci/*.py", "tests/scripts/__init__.py"):
            scope.tests = True
            scope.add_ci_target("tests/scripts/ci")
        elif matches(path, "tests/scripts/test_*.py"):
            if exists:
                scope.tests = True
                scope.add_target(path)
        elif matches(path, "tests/*/*"):
            scope.tests = True
            domain = path.split("/")[1]
            if domain in (*DOMAIN_CONSUMERS, "dbt"):
                scope.add_target(f"tests/{domain}")
            else:
                scope.full_unit = scope.full_type = True
        elif matches(path, "src/hmda_reliability/*", "tests/*"):
            scope.tests = scope.full_unit = scope.full_type = True
        elif path.endswith(".py"):
            scope.full_type = True
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

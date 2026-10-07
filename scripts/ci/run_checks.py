"""Run one selected CI check in the prepared prospective-merge workspace."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from changed_files import collect_changed_files, entrypoint, environment_targets, run


def markdown() -> None:
    files = collect_changed_files(patterns=("*.md",))
    if not files:
        return
    print(
        "Markdown formatting diagnostics (informational; docs lint runs separately):",
        flush=True,
    )
    run(["rumdl", "fmt", *files])
    diff = run(["git", "diff", "--", *files], capture=True)
    if diff:
        print("Markdown formatting suggestions (non-blocking):", flush=True)
        print(diff, end="", flush=True)
        if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
            with Path(summary).open("a", encoding="utf-8") as output:
                output.write(
                    "### Markdown formatting suggestions\n\n"
                    "CI applied safe formatting changes only in its "
                    "disposable workspace; "
                    "formatting-only drift does not fail this check.\n\n"
                    f"```diff\n{diff}```\n"
                )
    docs = [path for path in files if path.startswith("docs/")]
    if docs:
        run(["rumdl", "check", *docs])


def python() -> None:
    files = collect_changed_files(patterns=("*.py",))
    if files:
        run(["uv", "run", "--no-sync", "ruff", "check", *files])
        run(["uv", "run", "--no-sync", "ruff", "format", "--check", *files])
    if os.environ.get("FULL_TYPE", "false") == "true":
        run(["uv", "run", "--no-sync", "ty", "check", "--exclude", "inbox/**"])
        return
    targets = [*environment_targets("TYPE_TARGETS"), *files]
    if targets:
        run(["uv", "run", "--no-sync", "ty", "check", *targets])


def openspec() -> None:
    validate = [
        "npm",
        "exec",
        "--yes",
        "--package",
        "@fission-ai/openspec@1.12.0",
        "--",
        "openspec",
        "validate",
    ]
    if os.environ.get("BULK", "false") == "true":
        run([*validate, "--all", "--strict"])
        return
    specs = environment_targets("SPEC_TARGETS")
    changes = environment_targets("CHANGE_TARGETS")
    for target in specs:
        run([*validate, target, "--type", "spec", "--strict"])
    for target in changes:
        run([*validate, target, "--type", "change", "--strict"])
    archived = os.environ.get("ARCHIVED", "false") == "true"
    if archived:
        run([*validate, "--archived"])
    if not specs and not changes and not archived:
        print(
            "OpenSpec changed paths were not assigned a validation target",
            file=sys.stderr,
        )
        raise SystemExit(1)


def pytest() -> None:
    common = [
        "uv",
        "run",
        "--no-sync",
        "pytest",
        "-q",
        "-p",
        "no:sugar",
        "--color=no",
        "--tb=short",
        "-ra",
    ]
    selected_args = (
        ["--ignore=tests/review_ai/test_dependency_boundaries.py"]
        if os.environ.get("BOUNDARIES_CHECKED", "false") == "true"
        else []
    )
    if os.environ.get("FULL_TESTS", "false") == "true":
        run([*common, *selected_args, "-n", "auto", "-m", "not memory and not stress"])
        return
    if os.environ.get("FULL_UNIT", "false") == "true":
        run([*common, "-n", "auto", "-m", "unit and not memory and not stress"])
        ci_targets = environment_targets("CI_TARGETS")
        if ci_targets:
            run([*common, "-m", "not unit and not memory and not stress", *ci_targets])
        return
    targets = environment_targets("TARGETS")
    if targets:
        parallel = ["-n", "auto"] if len(targets) >= 3 else []
        run(
            [
                *common,
                *selected_args,
                *parallel,
                "-m",
                "not memory and not stress",
                *targets,
            ]
        )


def json() -> None:
    files = collect_changed_files(patterns=("*.json", "*.jsonc"))
    if files:
        run(["python", "scripts/biome.py", "check", *files])


def toml() -> None:
    files = collect_changed_files(patterns=("*.toml",))
    if files:
        run(["python", "scripts/tombi.py", "format", "--check", *files])
        run(["python", "scripts/tombi.py", "lint", *files])


def tooling() -> None:
    packages = []
    if os.environ.get("JSON", "false") == "true":
        packages.append("@biomejs/biome@2")
    if os.environ.get("TOML", "false") == "true":
        packages.append("tombi@1")
    if packages:
        run(
            [
                "npm",
                "install",
                "--prefix",
                ".local/tooling",
                "--no-save",
                "--package-lock=false",
                *packages,
            ]
        )


def main() -> None:
    checks = {
        "markdown": markdown,
        "python": python,
        "openspec": openspec,
        "pytest": pytest,
        "json": json,
        "toml": toml,
        "tooling": tooling,
    }
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("check", choices=checks)
    args = parser.parse_args()
    checks[args.check]()


if __name__ == "__main__":
    entrypoint(main)

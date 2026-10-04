from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CI_SCRIPTS = REPO_ROOT / "scripts/ci"
CLASSIFIER_SCRIPT = CI_SCRIPTS / "classify_changes.sh"


def run_classifier(paths: list[str], *, repo_root: Path = REPO_ROOT) -> dict[str, str]:
    """Execute the classifier script against the provided paths via stdin."""
    proc = subprocess.run(
        ["bash", str(CLASSIFIER_SCRIPT), "--stdin"],
        input="\n".join(paths) + "\n",
        capture_output=True,
        text=True,
        check=True,
        cwd=repo_root,
    )
    result: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, val = line.split("=", 1)
            result[key.strip()] = val.strip()
    return result


def run_markdown_paths(paths: list[str]) -> list[str]:
    """Return changed Markdown paths selected for validation."""
    proc = subprocess.run(
        ["bash", str(CLASSIFIER_SCRIPT), "--stdin", "--markdown-paths"],
        input="\n".join(paths) + "\n",
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    )
    return proc.stdout.splitlines()


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def commit_change(repo: Path, files: dict[str, str | None]) -> None:
    for name, content in files.items():
        path = repo / name
        if content is None:
            path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "-c", "commit.gpgsign=false", "commit", "-qm", "test change")


def run_step(
    name: str,
    repo: Path,
    env: dict[str, str],
    *args: str,
    **overrides: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(CI_SCRIPTS / name), *args],
        cwd=repo,
        env=env | overrides,
        capture_output=True,
        text=True,
        check=False,
    )


def tool_calls(env: dict[str, str]) -> list[list[str]]:
    log = Path(env["CI_LOG"])
    return (
        [json.loads(line) for line in log.read_text().splitlines()]
        if log.exists()
        else []
    )

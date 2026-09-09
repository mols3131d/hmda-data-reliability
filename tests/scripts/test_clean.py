"""Tests for safe repository and /tmp cleanup boundaries."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path, PurePosixPath

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "clean_script_under_test", REPO_ROOT / "scripts/clean.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("scripts/clean.py를 import할 수 없습니다")
clean = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = clean
_SPEC.loader.exec_module(clean)


def _tracked_index(*paths: str) -> clean.TrackedIndex:
    return clean.TrackedIndex(
        verified=True,
        paths=frozenset(PurePosixPath(path) for path in paths),
    )


def _write(path: Path, content: str = "cache") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.mark.unit
def test_tmp_patterns_match_only_allow_listed_direct_children(tmp_path: Path) -> None:
    """Project /tmp patterns are matched at the temporary-root boundary."""
    tmp_root = tmp_path / "tmp"
    repo_root = tmp_path / "repo"
    tmp_root.mkdir()
    repo_root.mkdir()
    for name in (
        "test.duckdb.tmp",
        "airflow_recon_123",
        "pytest-of-user",
        "pr123-review-456",
    ):
        _write(tmp_root / name / "payload.bin")
    _write(tmp_root / "unrelated.duckdb.tmpx")

    plan = clean.build_cleanup_plan(
        scope="tmp",
        repo_root=repo_root,
        tmp_root=tmp_root,
    )

    assert [candidate.path.name for candidate in plan.candidates] == [
        "airflow_recon_123",
        "pr123-review-456",
        "pytest-of-user",
        "test.duckdb.tmp",
    ]
    assert all(candidate.scope == "tmp" for candidate in plan.candidates)
    assert plan.total_size_bytes == 4 * len("cache")


@pytest.mark.unit
def test_repo_discovery_preserves_protected_paths(tmp_path: Path) -> None:
    """Cache discovery never descends into protected data or environment roots."""
    repo_root = tmp_path / "repo"
    tmp_root = tmp_path / "tmp"
    repo_root.mkdir()
    tmp_root.mkdir()

    for relative in (
        "src/__pycache__/module.pyc",
        ".pytest_cache/nodeids",
        ".hypothesis/examples/example",
        ".ruff_cache/content",
        ".mypy_cache/3.13/cache.json",
        ".rumdl_cache/result",
        ".testmondata",
        ".testmondata.hash",
        "dbt/target/manifest.json",
        "dbt/logs/dbt.log",
        ".tmp/run/output.json",
        ".local/airflow/airflow.db",
        ".local/worktrees/worktree/file.txt",
        "artifacts/result.xml",
        "artifacts/result.html",
    ):
        _write(repo_root / relative)

    for relative in (
        ".venv/__pycache__/venv.pyc",
        "data/raw/__pycache__/raw.pyc",
        "data/samples/__pycache__/sample.pyc",
        "data/metadata/__pycache__/metadata.pyc",
        "data/lakehouse/__pycache__/lakehouse.pyc",
        "data/hmda_reliability.duckdb",
        "artifacts/keep.json",
    ):
        _write(repo_root / relative)

    plan = clean.build_cleanup_plan(
        scope="repo",
        repo_root=repo_root,
        tmp_root=tmp_root,
        tracked_index=_tracked_index(),
    )

    relative_targets = {
        candidate.path.relative_to(repo_root).as_posix()
        for candidate in plan.candidates
    }
    assert relative_targets == {
        "src/__pycache__",
        ".pytest_cache",
        ".hypothesis",
        ".ruff_cache",
        ".mypy_cache",
        ".rumdl_cache",
        ".testmondata",
        ".testmondata.hash",
        "dbt/target",
        "dbt/logs",
        ".tmp",
        ".local/airflow",
        ".local/worktrees",
        "artifacts/result.xml",
        "artifacts/result.html",
    }
    assert not any(path.startswith((".venv", "data/")) for path in relative_targets)
    assert (repo_root / "data/raw/__pycache__/raw.pyc").exists()
    assert (repo_root / ".venv/__pycache__/venv.pyc").exists()


@pytest.mark.unit
def test_tracked_file_inside_candidate_is_skipped(tmp_path: Path) -> None:
    """A cache target containing any tracked file is never deleted wholesale."""
    repo_root = tmp_path / "repo"
    tmp_root = tmp_path / "tmp"
    repo_root.mkdir()
    tmp_root.mkdir()
    _write(repo_root / "artifacts/result.xml")
    _write(repo_root / "artifacts/untracked.html")

    plan = clean.build_cleanup_plan(
        scope="repo",
        repo_root=repo_root,
        tmp_root=tmp_root,
        tracked_index=_tracked_index("artifacts/result.xml"),
    )

    assert not any(
        candidate.path == repo_root / "artifacts/result.xml"
        for candidate in plan.candidates
    )
    skipped = {item.path: item.reason for item in plan.skipped}
    assert skipped[repo_root / "artifacts/result.xml"]
    assert "tracked" in skipped[repo_root / "artifacts/result.xml"]
    assert (repo_root / "artifacts/result.xml").exists()


@pytest.mark.unit
def test_repo_cleanup_fails_closed_when_git_state_is_unavailable(
    tmp_path: Path,
) -> None:
    """Repository cleanup skips candidates when tracked state cannot be verified."""
    repo_root = tmp_path / "repo"
    tmp_root = tmp_path / "tmp"
    repo_root.mkdir()
    tmp_root.mkdir()
    _write(repo_root / ".pytest_cache/nodeids")
    tracked_index = clean.TrackedIndex(
        verified=False,
        paths=frozenset(),
        error="Git tracked state unavailable",
    )

    plan = clean.build_cleanup_plan(
        scope="repo",
        repo_root=repo_root,
        tmp_root=tmp_root,
        tracked_index=tracked_index,
    )

    assert not plan.candidates
    assert plan.skipped[0].path == repo_root / ".pytest_cache"
    assert plan.skipped[0].reason == "Git tracked state unavailable"
    assert (repo_root / ".pytest_cache/nodeids").exists()


@pytest.mark.unit
def test_symlink_ancestor_is_skipped_before_fixed_target_cleanup(
    tmp_path: Path,
) -> None:
    """A fixed target below a symlink ancestor cannot reach protected data."""
    repo_root = tmp_path / "repo"
    tmp_root = tmp_path / "tmp"
    repo_root.mkdir()
    tmp_root.mkdir()
    protected_target = repo_root / "data/raw/target"
    _write(protected_target / "payload.bin")
    try:
        (repo_root / "dbt").symlink_to(repo_root / "data/raw", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable in this environment")

    plan = clean.build_cleanup_plan(
        scope="repo",
        repo_root=repo_root,
        tmp_root=tmp_root,
        tracked_index=_tracked_index(),
    )

    assert not plan.candidates
    assert any(
        item.path == repo_root / "dbt/target" and "symlink ancestor" in item.reason
        for item in plan.skipped
    )
    assert (protected_target / "payload.bin").exists()


@pytest.mark.unit
def test_dry_run_reports_size_without_deleting(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI dry-run is observable and mutation-free."""
    repo_root = tmp_path / "repo"
    tmp_root = tmp_path / "tmp"
    repo_root.mkdir()
    tmp_root.mkdir()
    target = repo_root / ".tmp" / "payload.bin"
    _write(target, "x" * 1_000_000)
    monkeypatch.setattr(clean, "REPO_ROOT", repo_root)
    monkeypatch.setattr(clean, "TMP_ROOT", tmp_root)
    monkeypatch.setattr(clean, "_load_tracked_index", lambda _root: _tracked_index())

    exit_code = clean.main(["--repo-only", "--dry-run"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "DRY RUN" in captured.out
    assert "1.00 MB" in captured.out
    assert target.exists()


@pytest.mark.unit
def test_yes_deletes_only_safe_targets_and_keeps_protected_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit --yes removes allow-listed cache while preserving data boundary."""
    repo_root = tmp_path / "repo"
    tmp_root = tmp_path / "tmp"
    repo_root.mkdir()
    tmp_root.mkdir()
    _write(repo_root / ".pytest_cache/nodeids")
    _write(repo_root / "data/raw/keep.csv")
    monkeypatch.setattr(clean, "REPO_ROOT", repo_root)
    monkeypatch.setattr(clean, "TMP_ROOT", tmp_root)
    monkeypatch.setattr(clean, "_load_tracked_index", lambda _root: _tracked_index())

    exit_code = clean.main(["--repo-only", "--yes"])

    assert exit_code == 0
    assert not (repo_root / ".pytest_cache").exists()
    assert (repo_root / "data/raw/keep.csv").exists()


@pytest.mark.unit
def test_non_interactive_delete_requires_explicit_yes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mutation is blocked when neither --yes nor an interactive confirmation exists."""
    repo_root = tmp_path / "repo"
    tmp_root = tmp_path / "tmp"
    repo_root.mkdir()
    tmp_root.mkdir()
    target = repo_root / ".pytest_cache/nodeids"
    _write(target)
    monkeypatch.setattr(clean, "REPO_ROOT", repo_root)
    monkeypatch.setattr(clean, "TMP_ROOT", tmp_root)
    monkeypatch.setattr(clean, "_load_tracked_index", lambda _root: _tracked_index())
    monkeypatch.setattr(clean.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(clean.sys.stdout, "isatty", lambda: False)

    exit_code = clean.main(["--repo-only"])

    assert exit_code == 2
    assert target.exists()

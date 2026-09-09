#!/usr/bin/env python3
"""Safely remove repository and system temporary artifacts.

The command only considers explicit cache/artifact patterns. Repository targets
are deleted only after their resolved path is checked, Git-tracked paths are
verified, and protected directories are excluded.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
import stat
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = Path("/tmp")

TMP_PATTERNS = (
    "test.duckdb*",
    "airflow_recon_*",
    "pytest-of-*",
    "pr*-review*",
)
CACHE_DIRECTORY_NAMES = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".hypothesis",
        ".ruff_cache",
        ".mypy_cache",
        ".rumdl_cache",
    }
)
REPO_DIRECTORY_TARGETS = (
    Path("dbt/target"),
    Path("dbt/logs"),
    Path(".tmp"),
    Path(".local/airflow"),
    Path(".local/worktrees"),
)
PROTECTED_REPO_PATHS = (
    Path(".git"),
    Path(".venv"),
    Path("data/raw"),
    Path("data/samples"),
    Path("data/metadata"),
    Path("data/lakehouse"),
    Path("data/hmda_reliability.duckdb"),
)
PROTECTED_DIRECTORY_NAMES = frozenset({".git", ".venv"})
ARTIFACT_SUFFIXES = frozenset({".xml", ".html"})

Scope = Literal["all", "tmp", "repo"]
TargetScope = Literal["tmp", "repo"]


@dataclass(frozen=True)
class CleanupCandidate:
    """A path that matched an allow-listed cleanup pattern."""

    path: Path
    scope: TargetScope
    reason: str
    size_bytes: int = 0


@dataclass(frozen=True)
class SkippedTarget:
    """A matched path that was not safe to delete."""

    path: Path
    scope: TargetScope
    reason: str


@dataclass(frozen=True)
class TrackedIndex:
    """Result of the Git-tracked path lookup used by repository cleanup."""

    verified: bool
    paths: frozenset[PurePosixPath]
    error: str | None = None


@dataclass(frozen=True)
class CleanupPlan:
    """Safe deletion candidates and paths intentionally left untouched."""

    candidates: tuple[CleanupCandidate, ...]
    skipped: tuple[SkippedTarget, ...]
    tracked_verified: bool

    @property
    def total_size_bytes(self) -> int:
        """Return the total size of safe candidates."""
        return sum(candidate.size_bytes for candidate in self.candidates)


def _has_path_entry(path: Path) -> bool:
    """Check a path with lstat so broken symlinks remain observable."""
    try:
        path.lstat()
    except OSError:
        return False
    return True


def _normalise_root(path: Path, label: str) -> Path:
    """Return a usable non-root directory or raise a clear safety error."""
    try:
        resolved = path.expanduser().resolve()
    except (OSError, RuntimeError) as error:
        raise ValueError(f"{label} 경로를 확인할 수 없습니다: {path}") from error
    if not resolved.is_dir():
        raise ValueError(f"{label} 디렉토리가 없습니다: {resolved}")
    if resolved.parent == resolved:
        raise ValueError(f"{label}로 filesystem root를 사용할 수 없습니다: {resolved}")
    return resolved


def _tmp_pattern(name: str) -> str | None:
    for pattern in TMP_PATTERNS:
        if fnmatch.fnmatchcase(name, pattern):
            return pattern
    return None


def discover_tmp_targets(tmp_root: Path = TMP_ROOT) -> tuple[CleanupCandidate, ...]:
    """Find matching direct children of the supplied temporary root."""
    root = _normalise_root(tmp_root, "temporary root")
    candidates: list[CleanupCandidate] = []
    try:
        entries = sorted(root.iterdir(), key=lambda entry: entry.name)
    except OSError:
        return ()

    for entry in entries:
        pattern = _tmp_pattern(entry.name)
        if pattern is not None:
            candidates.append(
                CleanupCandidate(
                    path=entry,
                    scope="tmp",
                    reason=f"/tmp pattern {pattern!r}",
                )
            )
    return tuple(candidates)


def _is_testmon_name(name: str) -> bool:
    return name.startswith(".testmondata")


def _is_cache_directory_name(name: str) -> bool:
    return name in CACHE_DIRECTORY_NAMES or _is_testmon_name(name)


def _is_relative_to_any(path: Path, roots: Sequence[Path]) -> bool:
    return any(path == root or root in path.parents for root in roots)


def _relative_path(path: Path, root: Path) -> Path:
    return path.relative_to(root)


def discover_repo_targets(repo_root: Path = REPO_ROOT) -> tuple[CleanupCandidate, ...]:
    """Find only the repository cache and artifact paths in scope."""
    root = _normalise_root(repo_root, "repository root")
    candidates: list[CleanupCandidate] = []

    fixed_targets = tuple(root / relative for relative in REPO_DIRECTORY_TARGETS)
    for relative, path in zip(REPO_DIRECTORY_TARGETS, fixed_targets, strict=True):
        if _has_path_entry(path):
            candidates.append(
                CleanupCandidate(
                    path=path,
                    scope="repo",
                    reason=f"repository directory {relative.as_posix()}/",
                )
            )

    artifact_directory = root / "artifacts"
    if artifact_directory.is_dir():
        try:
            artifact_entries = sorted(
                artifact_directory.iterdir(), key=lambda entry: entry.name
            )
        except OSError:
            artifact_entries = []
        for entry in artifact_entries:
            if entry.suffix.lower() in ARTIFACT_SUFFIXES:
                candidates.append(
                    CleanupCandidate(
                        path=entry,
                        scope="repo",
                        reason=f"artifacts/{entry.name}",
                    )
                )

    protected_paths = tuple(root / relative for relative in PROTECTED_REPO_PATHS)
    fixed_paths = tuple(fixed_targets)
    for current, directory_names, file_names in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        current_path = Path(current)
        kept_directories: list[str] = []
        for name in sorted(directory_names):
            directory = current_path / name
            relative = _relative_path(directory, root)
            if name in PROTECTED_DIRECTORY_NAMES:
                continue
            if _is_relative_to_any(directory, protected_paths):
                continue
            if _is_relative_to_any(directory, fixed_paths):
                continue
            if _is_cache_directory_name(name):
                candidates.append(
                    CleanupCandidate(
                        path=directory,
                        scope="repo",
                        reason=f"cache directory {relative.as_posix()}/",
                    )
                )
                continue
            kept_directories.append(name)
        directory_names[:] = kept_directories

        for name in sorted(file_names):
            if _is_testmon_name(name):
                file_path = current_path / name
                relative = _relative_path(file_path, root)
                candidates.append(
                    CleanupCandidate(
                        path=file_path,
                        scope="repo",
                        reason=f"testmon cache {relative.as_posix()}",
                    )
                )

    return _deduplicate_candidates(candidates)


def _deduplicate_candidates(
    candidates: Sequence[CleanupCandidate],
) -> tuple[CleanupCandidate, ...]:
    """Keep the broadest matching target once, in deterministic order."""
    unique: dict[Path, CleanupCandidate] = {}
    for candidate in candidates:
        unique.setdefault(candidate.path, candidate)

    selected: list[CleanupCandidate] = []
    for candidate in sorted(
        unique.values(),
        key=lambda item: (len(item.path.parts), item.path.as_posix()),
    ):
        if any(
            candidate.path == selected_item.path
            or candidate.path.is_relative_to(selected_item.path)
            for selected_item in selected
        ):
            continue
        selected.append(candidate)
    return tuple(sorted(selected, key=lambda item: item.path.as_posix()))


def _load_tracked_index(repo_root: Path) -> TrackedIndex:
    """Read Git's index, failing closed if tracked state cannot be verified."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "--cached", "--full-name", "-z"],
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="surrogateescape",
            text=True,
        )
    except OSError as error:
        return TrackedIndex(
            verified=False,
            paths=frozenset(),
            error=f"Git tracked state를 확인할 수 없습니다: {error}",
        )

    if result.returncode != 0:
        detail = result.stderr.strip() or f"git exited with {result.returncode}"
        return TrackedIndex(
            verified=False,
            paths=frozenset(),
            error=f"Git tracked state를 확인할 수 없습니다: {detail}",
        )

    paths = frozenset(
        PurePosixPath(raw_path) for raw_path in result.stdout.split("\0") if raw_path
    )
    return TrackedIndex(verified=True, paths=paths)


def _path_size(path: Path) -> int:
    """Calculate regular-file bytes without following symlinks."""
    try:
        path_stat = path.lstat()
    except OSError:
        return 0

    if stat.S_ISREG(path_stat.st_mode):
        return path_stat.st_size
    if not stat.S_ISDIR(path_stat.st_mode):
        return 0

    total = 0
    for current, directory_names, file_names in os.walk(
        path,
        topdown=True,
        followlinks=False,
    ):
        current_path = Path(current)
        directory_names[:] = [
            name for name in directory_names if not (current_path / name).is_symlink()
        ]
        for name in file_names:
            file_path = current_path / name
            try:
                file_stat = file_path.lstat()
            except OSError:
                continue
            if stat.S_ISREG(file_stat.st_mode):
                total += file_stat.st_size
    return total


def _is_protected_relative(relative: Path) -> bool:
    return any(
        relative == protected or protected in relative.parents
        for protected in PROTECTED_REPO_PATHS
    )


def _contains_tracked_path(
    candidate: CleanupCandidate,
    repo_root: Path,
    tracked_index: TrackedIndex,
) -> bool:
    relative = PurePosixPath(candidate.path.relative_to(repo_root).as_posix())
    return any(
        tracked == relative or relative in tracked.parents
        for tracked in tracked_index.paths
    )


def _symlink_ancestor_reason(path: Path, root: Path) -> str | None:
    """Reject symlink components between a trusted root and a candidate."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return "candidate가 trusted root 아래에 lexical하게 있지 않습니다"

    current = root
    for part in relative.parts:
        current /= part
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            return "삭제 직전 path component가 사라졌습니다"
        except OSError as error:
            return f"path component를 확인할 수 없습니다: {error}"
        if stat.S_ISLNK(current_stat.st_mode):
            return f"symlink ancestor는 삭제하지 않습니다: {current}"
    return None


def _safety_reason(
    candidate: CleanupCandidate,
    *,
    repo_root: Path,
    tmp_root: Path,
    tracked_index: TrackedIndex,
) -> str | None:
    """Return why a candidate must be skipped, or None when it is safe."""
    try:
        path_stat = candidate.path.lstat()
    except FileNotFoundError:
        return "경로가 사라졌습니다"
    except OSError as error:
        return f"경로를 확인할 수 없습니다: {error}"

    if stat.S_ISLNK(path_stat.st_mode):
        return "symlink는 삭제하지 않습니다"
    if not (stat.S_ISREG(path_stat.st_mode) or stat.S_ISDIR(path_stat.st_mode)):
        return "regular file 또는 directory가 아닙니다"

    trusted_root = repo_root if candidate.scope == "repo" else tmp_root
    ancestor_reason = _symlink_ancestor_reason(candidate.path, trusted_root)
    if ancestor_reason is not None:
        return ancestor_reason

    try:
        resolved = candidate.path.resolve()
    except (OSError, RuntimeError) as error:
        return f"resolved path를 확인할 수 없습니다: {error}"

    if candidate.scope == "repo":
        if resolved == repo_root or not resolved.is_relative_to(repo_root):
            return "repository root 밖으로 resolve되어 삭제하지 않습니다"
        relative = candidate.path.relative_to(repo_root)
        if _is_protected_relative(relative):
            return "보호된 repository 경로입니다"
        if not tracked_index.verified:
            return tracked_index.error or "Git tracked state를 확인할 수 없습니다"
        if _contains_tracked_path(candidate, repo_root, tracked_index):
            return "Git tracked path를 포함하므로 삭제하지 않습니다"
    else:
        if resolved == tmp_root or not resolved.is_relative_to(tmp_root):
            return "temporary root 밖으로 resolve되어 삭제하지 않습니다"
        if repo_root == resolved or repo_root.is_relative_to(resolved):
            return "repository root를 포함할 수 있어 삭제하지 않습니다"
    return None


def build_cleanup_plan(
    *,
    scope: Scope,
    repo_root: Path = REPO_ROOT,
    tmp_root: Path = TMP_ROOT,
    tracked_index: TrackedIndex | None = None,
) -> CleanupPlan:
    """Discover and safety-filter targets for one requested cleanup scope."""
    if scope not in {"all", "tmp", "repo"}:
        raise ValueError(f"알 수 없는 cleanup scope: {scope}")

    resolved_repo_root = _normalise_root(repo_root, "repository root")
    resolved_tmp_root = _normalise_root(tmp_root, "temporary root")
    if resolved_repo_root == resolved_tmp_root:
        raise ValueError("repository root와 temporary root를 같게 사용할 수 없습니다")

    discovered: list[CleanupCandidate] = []
    if scope in {"all", "tmp"}:
        discovered.extend(discover_tmp_targets(resolved_tmp_root))
    if scope in {"all", "repo"}:
        discovered.extend(discover_repo_targets(resolved_repo_root))

    index = tracked_index
    if index is None:
        index = (
            _load_tracked_index(resolved_repo_root)
            if scope in {"all", "repo"}
            else TrackedIndex(verified=True, paths=frozenset())
        )

    candidates: list[CleanupCandidate] = []
    skipped: list[SkippedTarget] = []
    for candidate in _deduplicate_candidates(discovered):
        reason = _safety_reason(
            candidate,
            repo_root=resolved_repo_root,
            tmp_root=resolved_tmp_root,
            tracked_index=index,
        )
        if reason is not None:
            skipped.append(
                SkippedTarget(
                    path=candidate.path,
                    scope=candidate.scope,
                    reason=reason,
                )
            )
            continue
        candidates.append(replace(candidate, size_bytes=_path_size(candidate.path)))

    return CleanupPlan(
        candidates=tuple(candidates),
        skipped=tuple(skipped),
        tracked_verified=index.verified,
    )


def format_size(size_bytes: int) -> str:
    """Format bytes with decimal MB and GB for operator-facing output."""
    megabytes = size_bytes / 1_000_000
    gigabytes = size_bytes / 1_000_000_000
    return f"{megabytes:,.2f} MB ({gigabytes:,.2f} GB)"


def _print_plan(plan: CleanupPlan, scope: Scope) -> None:
    scope_flag = {
        "all": "--all",
        "tmp": "--tmp-only",
        "repo": "--repo-only",
    }[scope]
    print(f"Cleanup scope: {scope_flag}")
    if plan.candidates:
        print("삭제 대상:")
        for candidate in plan.candidates:
            print(
                f"  [{candidate.scope}] {candidate.path}"
                f" — {candidate.reason} — {format_size(candidate.size_bytes)}"
            )
    else:
        print("삭제 가능한 대상이 없습니다.")
    print(f"Total reclaimable: {format_size(plan.total_size_bytes)}")

    if plan.skipped:
        print("건너뛴 대상:")
        for skipped in plan.skipped:
            print(f"  [{skipped.scope}] {skipped.path} — {skipped.reason}")


def _confirm() -> bool:
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        print(
            "error: non-interactive 실행에서는 --yes가 필요합니다 "
            "(삭제하지 않으려면 --dry-run 사용).",
            file=sys.stderr,
        )
        return False
    try:
        answer = input("계속하려면 DELETE를 입력하세요: ")
    except EOFError:
        return False
    return answer.strip() == "DELETE"


def _delete_candidate(
    candidate: CleanupCandidate,
    *,
    repo_root: Path,
    tmp_root: Path,
    tracked_index: TrackedIndex,
) -> tuple[bool, str | None]:
    """Revalidate and remove one candidate, returning success and an error."""
    reason = _safety_reason(
        candidate,
        repo_root=repo_root,
        tmp_root=tmp_root,
        tracked_index=tracked_index,
    )
    if reason is not None:
        return False, f"삭제 직전 안전성 검증 실패: {reason}"

    try:
        if candidate.path.is_dir():
            shutil.rmtree(candidate.path)
        else:
            candidate.path.unlink()
    except OSError as error:
        return False, str(error)
    return True, None


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean allow-listed repository caches and project /tmp artifacts."
    )
    scope_group = parser.add_mutually_exclusive_group(required=True)
    scope_group.add_argument(
        "--all",
        action="store_true",
        help="system /tmp 잔여물과 repository cache/artifact를 모두 정리",
    )
    scope_group.add_argument(
        "--tmp-only",
        action="store_true",
        help="system /tmp의 project pattern만 정리",
    )
    scope_group.add_argument(
        "--repo-only",
        action="store_true",
        help="repository 내부 cache/artifact만 정리",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="삭제하지 않고 대상과 예상 확보 용량만 출력",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="interactive confirmation을 건너뛰는 명시적 삭제 승인",
    )
    return parser.parse_args(argv)


def _scope_from_args(args: argparse.Namespace) -> Scope:
    if args.all:
        return "all"
    if args.tmp_only:
        return "tmp"
    return "repo"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the cleanup CLI and return a process status code."""
    args = _parse_args(argv)
    scope = _scope_from_args(args)
    try:
        repo_root = _normalise_root(REPO_ROOT, "repository root")
        tmp_root = _normalise_root(TMP_ROOT, "temporary root")
        tracked_index = (
            _load_tracked_index(repo_root)
            if scope in {"all", "repo"}
            else TrackedIndex(verified=True, paths=frozenset())
        )
        plan = build_cleanup_plan(
            scope=scope,
            repo_root=repo_root,
            tmp_root=tmp_root,
            tracked_index=tracked_index,
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    _print_plan(plan, scope)
    if args.dry_run:
        print("DRY RUN: 실제 삭제를 수행하지 않았습니다.")
        return 0
    if not plan.candidates:
        return 2 if scope in {"all", "repo"} and not plan.tracked_verified else 0
    if not args.yes and not _confirm():
        print("취소했습니다. 삭제된 파일은 없습니다.")
        return 2

    deleted_bytes = 0
    failures = 0
    for candidate in plan.candidates:
        deleted, error = _delete_candidate(
            candidate,
            repo_root=repo_root,
            tmp_root=tmp_root,
            tracked_index=tracked_index,
        )
        if deleted:
            deleted_bytes += candidate.size_bytes
            print(f"deleted: {candidate.path}")
        else:
            failures += 1
            print(f"skipped: {candidate.path} — {error}", file=sys.stderr)

    print(f"Total reclaimed: {format_size(deleted_bytes)}")
    if failures:
        print(f"error: {failures}개 대상은 삭제하지 못했습니다.", file=sys.stderr)
        return 1
    if scope in {"all", "repo"} and not plan.tracked_verified:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Tests for changed Inbox artifact contract validation."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

REPOSITORY_ROOT = Path(__file__).parents[2]


def load_validator_module() -> ModuleType:
    """Load the repository script without relying on repo-root importability."""
    script_path = REPOSITORY_ROOT / "scripts" / "validate_inbox_artifacts.py"
    spec = importlib.util.spec_from_file_location("validate_inbox_artifacts", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator_module()
validate_changed_paths = validator.validate_changed_paths


def write_artifact(
    path: Path,
    *,
    artifact_type: str = "review",
    description: str = "설명",
) -> None:
    """Write a minimal valid Inbox artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                f"type: {artifact_type}",
                'title: "Review"',
                f'description: "{description}"',
                "---",
                "",
                "# Review",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_bundle(repo_root: Path, relative: Path, *, description: str = "설명") -> None:
    """Write a minimal Inbox bundle with a README root and one member."""
    write_artifact(
        repo_root / relative / "README.md",
        artifact_type="discuss",
        description=description,
    )
    member = repo_root / relative / "turns/001-a.md"
    member.parent.mkdir(parents=True, exist_ok=True)
    member.write_text("# Turn\n", encoding="utf-8")


@pytest.mark.unit
def test_changed_standalone_artifact_passes(tmp_path: Path) -> None:
    """현재 변경된 standalone artifact의 common contract를 검증한다."""
    relative = Path("inbox/2026-09-07/09-30-review-ci-check.md")
    write_artifact(tmp_path / relative)

    assert validate_changed_paths([relative.as_posix()], repo_root=tmp_path) == []


@pytest.mark.unit
def test_github_work_artifact_with_type_passes(tmp_path: Path) -> None:
    """GitHub work filename은 frontmatter type을 naming core에 포함할 수 있다."""
    relative = Path(
        "inbox/github-226-document-consistency-polish/00-review-consistency.md"
    )
    write_artifact(tmp_path / relative)

    assert validate_changed_paths([relative.as_posix()], repo_root=tmp_path) == []


@pytest.mark.unit
def test_github_work_artifact_without_type_passes(tmp_path: Path) -> None:
    """GitHub work filename은 type component를 생략할 수 있다."""
    relative = Path(
        "inbox/github-226-document-consistency-polish/00-document-consistency.md"
    )
    write_artifact(tmp_path / relative, artifact_type="plan")

    assert validate_changed_paths([relative.as_posix()], repo_root=tmp_path) == []


@pytest.mark.unit
def test_branch_work_artifact_passes(tmp_path: Path) -> None:
    """PR 전 branch work unit은 date와 branch-name slug를 container로 사용한다."""
    relative = Path(
        "inbox/2026-09-09-agent-docs-inbox-policy/00-plan-directory-policy.md"
    )
    write_artifact(tmp_path / relative, artifact_type="plan")

    assert validate_changed_paths([relative.as_posix()], repo_root=tmp_path) == []


@pytest.mark.unit
def test_github_work_artifact_requires_two_digit_sequence(tmp_path: Path) -> None:
    """GitHub work artifact는 two-digit sequence prefix를 사용해야 한다."""
    relative = Path(
        "inbox/github-226-document-consistency-polish/0-review-consistency.md"
    )
    write_artifact(tmp_path / relative)

    errors = validate_changed_paths([relative.as_posix()], repo_root=tmp_path)

    assert errors == [f"{tmp_path / relative}: artifact name must start with NN-"]


@pytest.mark.unit
def test_missing_required_frontmatter_fails(tmp_path: Path) -> None:
    """Required frontmatter 누락은 changed artifact에서 실패한다."""
    relative = Path("inbox/2026-09-07/09-30-review-ci-check.md")
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\ntype: review\ntitle: Review\n---\n\n# Review\n",
        encoding="utf-8",
    )

    errors = validate_changed_paths([relative.as_posix()], repo_root=tmp_path)

    assert errors == [
        f"{path}: required frontmatter field 'description' is missing or empty"
    ]


@pytest.mark.unit
def test_date_filename_type_mismatch_fails(tmp_path: Path) -> None:
    """날짜 기반 artifact는 filename type과 frontmatter type을 일치시킨다."""
    relative = Path("inbox/2026-09-07/09-30-review-ci-check.md")
    write_artifact(tmp_path / relative, artifact_type="research")

    errors = validate_changed_paths([relative.as_posix()], repo_root=tmp_path)

    expected = (
        f"{tmp_path / relative}: artifact name must start with '09-30-research-' "
        "to match frontmatter type"
    )
    assert errors == [expected]


@pytest.mark.unit
def test_changed_bundle_member_validates_bundle_readme(tmp_path: Path) -> None:
    """Bundle 내부 변경은 해당 active bundle의 README root만 검증한다."""
    bundle = Path("inbox/2026-09-07/09-30-discuss-ci-policy")
    write_bundle(tmp_path, bundle, description="")

    changed = (bundle / "turns/001-a.md").as_posix()
    errors = validate_changed_paths([changed], repo_root=tmp_path)

    assert errors == [
        f"{tmp_path / bundle / 'README.md'}: required frontmatter field "
        "'description' is missing or empty"
    ]


@pytest.mark.unit
def test_github_work_bundle_passes(tmp_path: Path) -> None:
    """GitHub work bundle도 common artifact contract를 검증한다."""
    bundle = Path("inbox/github-226-document-consistency-polish/02-discuss-follow-up")
    write_bundle(tmp_path, bundle)

    changed = (bundle / "turns/001-a.md").as_posix()
    assert validate_changed_paths([changed], repo_root=tmp_path) == []


@pytest.mark.unit
def test_github_work_bundle_requires_two_digit_sequence(tmp_path: Path) -> None:
    """GitHub work bundle에도 같은 two-digit sequence contract를 적용한다."""
    bundle = Path("inbox/github-226-document-consistency-polish/3-discuss-ci-policy")
    write_bundle(tmp_path, bundle)

    changed = (bundle / "turns/001-a.md").as_posix()
    errors = validate_changed_paths([changed], repo_root=tmp_path)

    assert errors == [
        f"{tmp_path / bundle / 'README.md'}: artifact name must start with NN-"
    ]


@pytest.mark.unit
def test_unrelated_historical_artifact_is_not_scanned(tmp_path: Path) -> None:
    """Changed path로 전달되지 않은 과거 Inbox artifact는 검사하지 않는다."""
    old = Path("inbox/2026-08-01/08-00-review-old.md")
    old_path = tmp_path / old
    old_path.parent.mkdir(parents=True)
    old_path.write_text("# Historical\n", encoding="utf-8")

    current = Path("inbox/2026-09-07/09-30-review-current.md")
    write_artifact(tmp_path / current)

    assert validate_changed_paths([current.as_posix()], repo_root=tmp_path) == []


@pytest.mark.unit
def test_inbox_infrastructure_is_not_artifact_validated(tmp_path: Path) -> None:
    """Inbox guideline/template 같은 infrastructure는 artifact schema 대상이 아니다."""
    guideline = tmp_path / "inbox/_guidelines/review.md"
    guideline.parent.mkdir(parents=True)
    guideline.write_text("# Review\n", encoding="utf-8")

    errors = validate_changed_paths(
        ["inbox/_guidelines/review.md"],
        repo_root=tmp_path,
    )
    assert errors == []

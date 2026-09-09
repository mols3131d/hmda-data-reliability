"""Tests for changed Inbox artifact contract validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.validate_inbox_artifacts import validate_changed_paths


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

    assert validate_changed_paths(
        [relative.as_posix()],
        repo_root=tmp_path,
        added_paths=[relative.as_posix()],
    ) == []


@pytest.mark.unit
def test_github_work_artifact_without_type_passes(tmp_path: Path) -> None:
    """GitHub work filename은 type component를 생략할 수 있다."""
    relative = Path(
        "inbox/github-226-document-consistency-polish/00-document-consistency.md"
    )
    write_artifact(tmp_path / relative, artifact_type="plan")

    assert validate_changed_paths(
        [relative.as_posix()],
        repo_root=tmp_path,
        added_paths=[relative.as_posix()],
    ) == []


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
def test_new_github_sequence_must_append_after_maximum(tmp_path: Path) -> None:
    """Sequence gap을 backfill하지 않고 현재 최대값 다음 번호만 추가한다."""
    container = Path("inbox/github-226-document-consistency-polish")
    write_artifact(tmp_path / container / "01-review-first.md")
    write_bundle(tmp_path, container / "03-discuss-later")
    added = container / "02-plan-backfill.md"
    write_artifact(tmp_path / added, artifact_type="plan")

    errors = validate_changed_paths(
        [added.as_posix()],
        repo_root=tmp_path,
        added_paths=[added.as_posix()],
    )

    assert errors == [
        f"{tmp_path / container}: new top-level sequence must append after the "
        "current maximum; expected [04], got [02]"
    ]


@pytest.mark.unit
def test_new_github_sequence_maximum_plus_one_passes(tmp_path: Path) -> None:
    """01, 03이 존재하면 신규 top-level root는 04를 사용한다."""
    container = Path("inbox/github-226-document-consistency-polish")
    write_artifact(tmp_path / container / "01-review-first.md")
    write_bundle(tmp_path, container / "03-discuss-later")
    added = container / "04-plan-next.md"
    write_artifact(tmp_path / added, artifact_type="plan")

    assert validate_changed_paths(
        [added.as_posix()],
        repo_root=tmp_path,
        added_paths=[added.as_posix()],
    ) == []


@pytest.mark.unit
def test_multiple_new_github_sequences_are_consecutive(tmp_path: Path) -> None:
    """한 change에서 여러 root를 추가하면 max + 1부터 연속해서 append한다."""
    container = Path("inbox/github-226-document-consistency-polish")
    write_artifact(tmp_path / container / "03-review-existing.md")
    first = container / "04-plan-next.md"
    second = container / "05-report-result.md"
    write_artifact(tmp_path / first, artifact_type="plan")
    write_artifact(tmp_path / second, artifact_type="report")

    paths = [first.as_posix(), second.as_posix()]
    assert validate_changed_paths(
        paths,
        repo_root=tmp_path,
        added_paths=paths,
    ) == []


@pytest.mark.unit
def test_existing_github_artifact_keeps_sequence_when_modified(tmp_path: Path) -> None:
    """기존 artifact 수정은 현재 최대 sequence와 무관하게 기존 번호를 유지한다."""
    container = Path("inbox/github-226-document-consistency-polish")
    changed = container / "01-review-existing.md"
    write_artifact(tmp_path / changed)
    write_artifact(tmp_path / container / "03-report-later.md", artifact_type="report")

    assert validate_changed_paths([changed.as_posix()], repo_root=tmp_path) == []


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
def test_new_github_bundle_shares_top_level_sequence(tmp_path: Path) -> None:
    """File과 bundle은 같은 append-only top-level sequence를 공유한다."""
    container = Path("inbox/github-226-document-consistency-polish")
    write_artifact(tmp_path / container / "01-review-first.md")
    added_bundle = container / "02-discuss-follow-up"
    write_bundle(tmp_path, added_bundle)
    readme = added_bundle / "README.md"

    assert validate_changed_paths(
        [readme.as_posix()],
        repo_root=tmp_path,
        added_paths=[readme.as_posix()],
    ) == []


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

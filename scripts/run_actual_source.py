"""Generate portable actual-source HMDA EDA evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from project_pivot.hmda_data.eda import analyze_hmda_csv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = PROJECT_ROOT / "data/raw/hmda/year_2025.csv"
JSON_PATH = PROJECT_ROOT / "docs/references/hmda_eda_reference.json"
MARKDOWN_PATH = PROJECT_ROOT / "docs/references/hmda_eda.md"


class EvidenceProvenanceError(RuntimeError):
    """Raised when repository state is dirty during evidence generation."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repository_revision(project_root: Path) -> str:
    status_proc = subprocess.run(
        ["git", "status", "--porcelain", ":(exclude)inbox"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    if status_proc.stdout.strip():
        msg = (
            "Repository dirty (staged/unstaged/untracked files exist in "
            f"{project_root})"
        )
        raise EvidenceProvenanceError(msg)

    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    return revision


def _markdown_summary(observation: dict[str, Any]) -> str:
    evidence = observation["evidence"]
    return "\n".join(
        [
            "# HMDA EDA Reference",
            "",
            "> [!WARNING]",
            "> 이 artifact는 controlled actual-source run으로 생성된다."
            " 생성 전에는 EDA readiness를 `blocked`로 유지한다.",
            "",
            "## Observation",
            "",
            f"- Source ID: `{observation['source_id']}`",
            f"- Source SHA-256: `{observation['source_sha256']}`",
            f"- Repository Revision: `{observation['repository_revision']}`",
            f"- Observed At: `{observation['observed_at']}`",
            f"- Total Duration Seconds: {evidence['duration_seconds']:.3f}",
            "",
            "## Key Metrics",
            "",
            f"- Total Row Count: {evidence['row_count']:,}",
            f"- Income Null Count: {evidence['null_counts']['income']:,}",
            "- Mart Grain Distinct Group Count: "
            f"{evidence['grain']['distinct_group_count']:,}",
            "",
        ]
    )


def write_evidence(
    evidence: dict[str, Any],
    *,
    json_path: Path,
    markdown_path: Path,
    source_id: str,
    source_sha256: str,
    repository_revision: str,
    observed_at: str,
) -> None:
    """Write canonical JSON and its derived Markdown summary atomically."""
    source = evidence.get("source", {})
    portable_evidence = {
        **evidence,
        "source": {
            "id": source_id,
            "scope": source.get("scope", "full_file"),
            "csv_options": source.get("csv_options", {}),
        },
    }
    observation = {
        "source_id": source_id,
        "source_sha256": source_sha256,
        "repository_revision": repository_revision,
        "observed_at": observed_at,
        "evidence": portable_evidence,
    }

    json_tmp = json_path.with_suffix(".json.tmp")
    md_tmp = markdown_path.with_suffix(".md.tmp")

    json_backup = json_path.with_suffix(".json.bak")

    try:
        json_tmp.write_text(
            json.dumps(observation, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        md_tmp.write_text(_markdown_summary(observation), encoding="utf-8")

        if json_path.exists():
            import shutil

            shutil.copy2(json_path, json_backup)

        json_tmp.replace(json_path)
        try:
            md_tmp.replace(markdown_path)
            if json_backup.exists():
                json_backup.unlink()
        except Exception:
            if json_backup.exists():
                json_backup.replace(json_path)
            else:
                json_path.unlink(missing_ok=True)
            raise
    finally:
        if json_tmp.exists():
            json_tmp.unlink()
        if md_tmp.exists():
            md_tmp.unlink()


def main() -> None:
    evidence = analyze_hmda_csv(
        source_path=SOURCE_PATH,
        memory_limit="2GB",
        threads=2,
        temp_directory=PROJECT_ROOT / ".tmp",
    )
    evidence["source"] = {
        "id": SOURCE_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "scope": evidence["source"]["scope"],
        "csv_options": evidence["source"]["csv_options"],
    }
    write_evidence(
        evidence,
        json_path=JSON_PATH,
        markdown_path=MARKDOWN_PATH,
        source_id=SOURCE_PATH.relative_to(PROJECT_ROOT).as_posix(),
        source_sha256=_sha256(SOURCE_PATH),
        repository_revision=_repository_revision(PROJECT_ROOT),
        observed_at=datetime.now(UTC).isoformat(),
    )
    print(
        "Wrote "
        f"{JSON_PATH.relative_to(PROJECT_ROOT)} and "
        f"{MARKDOWN_PATH.relative_to(PROJECT_ROOT)}"
    )


if __name__ == "__main__":
    main()

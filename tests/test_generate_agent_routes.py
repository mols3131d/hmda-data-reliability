"""Behavioral tests for chatbot Agent Asset route generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.generate_agent_routes as routes


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("owner/repo", "owner/repo"),
        ("owner/repo.git", "owner/repo"),
        ("https://github.com/owner/repo", "owner/repo"),
        ("https://github.com/owner/repo.git", "owner/repo"),
    ],
)
def test_normalize_github_source_accepts_supported_forms(
    source: str, expected: str
) -> None:
    assert routes.normalize_github_source(source) == expected


@pytest.mark.unit
def test_strip_jsonc_comments_preserves_markers_inside_strings() -> None:
    text = """
    {
      "url": "https://github.com/owner/repo", // line comment
      "literal": "/* keep this */",
      /* block comment */
      "enabled": true
    }
    """

    assert json.loads(routes.strip_jsonc_comments(text)) == {
        "url": "https://github.com/owner/repo",
        "literal": "/* keep this */",
        "enabled": True,
    }


@pytest.mark.component
def test_rulesync_dependency_sources_use_locked_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "rulesync.jsonc"
    lock_path = tmp_path / "rulesync.lock"
    config_path.write_text(
        """
        {
          "sources": [
            {
              "source": "owner/assets",
              "path": "src/rulesync/.rulesync/skills" // canonical skill root
            }
          ]
        }
        """,
        encoding="utf-8",
    )
    _write_json(
        lock_path,
        {
            "sources": {
                "owner/assets": {
                    "resolvedRef": "abc123",
                    "skills": {"alpha": {}, "beta": {}},
                }
            }
        },
    )
    monkeypatch.setattr(routes, "RULESYNC_CONFIG", config_path)
    monkeypatch.setattr(routes, "RULESYNC_LOCK", lock_path)

    assert routes.rulesync_dependency_sources() == {
        "alpha": (
            "https://raw.githubusercontent.com/owner/assets/abc123/"
            "src/rulesync/.rulesync/skills/alpha/SKILL.md"
        ),
        "beta": (
            "https://raw.githubusercontent.com/owner/assets/abc123/"
            "src/rulesync/.rulesync/skills/beta/SKILL.md"
        ),
    }


@pytest.mark.component
def test_skills_cli_dependency_sources_use_locked_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lock_path = tmp_path / "skills-lock.json"
    _write_json(
        lock_path,
        {
            "skills": {
                "alpha": {
                    "sourceType": "github",
                    "sourceUrl": "https://github.com/owner/assets.git",
                    "ref": "deadbeef",
                    "skillPath": "skills/alpha/SKILL.md",
                }
            }
        },
    )
    monkeypatch.setattr(routes, "SKILLS_LOCK", lock_path)

    assert routes.skills_cli_dependency_sources() == {
        "alpha": (
            "https://raw.githubusercontent.com/owner/assets/deadbeef/"
            "skills/alpha/SKILL.md"
        )
    }


@pytest.mark.unit
def test_dependency_skill_entry_reads_frontmatter_without_real_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = (
        "https://raw.githubusercontent.com/owner/assets/abc123/"
        "skills/alpha/SKILL.md"
    )
    payload = b"---\nname: alpha\ndescription:  Useful   skill.\n---\n# Alpha\n"

    class Response:
        def __enter__(self) -> Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return payload

    def fake_urlopen(actual_source: str, timeout: int) -> Response:
        assert actual_source == source
        assert timeout == 30
        return Response()

    monkeypatch.setattr(routes, "urlopen", fake_urlopen)

    assert routes.dependency_skill_entry("alpha", source) == {
        "name": "alpha",
        "description": "Useful skill.",
        "source": source,
    }


@pytest.mark.unit
def test_skill_entries_reject_dependency_name_collision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(routes, "find_local_skill_files", lambda: [])
    monkeypatch.setattr(
        routes,
        "rulesync_dependency_sources",
        lambda: {"shared": "https://example.test/rulesync"},
    )
    monkeypatch.setattr(
        routes,
        "skills_cli_dependency_sources",
        lambda: {"shared": "https://example.test/skills-cli"},
    )

    with pytest.raises(
        SystemExit, match="Skill dependency exists in both locks: shared"
    ):
        routes.skill_entries()

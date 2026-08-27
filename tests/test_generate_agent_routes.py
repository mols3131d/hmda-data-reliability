"""Behavioral tests for chatbot Agent Asset route generation."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import scripts.generate_agent_routes as routes


class _TextFile:
    def __init__(self, content: str) -> None:
        self.content = content

    def is_file(self) -> bool:
        return True

    def read_text(self, *, encoding: str) -> str:
        assert encoding == "utf-8"
        return self.content


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


@pytest.mark.unit
def test_rulesync_dependency_sources_use_locked_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = """
    {
      "sources": [
        {
          "source": "owner/assets",
          "path": "src/rulesync/.rulesync/skills" // canonical skill root
        }
      ]
    }
    """
    lock = {
        "sources": {
            "owner/assets": {
                "resolvedRef": "abc123",
                "skills": {"alpha": {}, "beta": {}},
            }
        }
    }
    monkeypatch.setattr(routes, "RULESYNC_CONFIG", _TextFile(config))
    monkeypatch.setattr(routes, "RULESYNC_LOCK", _TextFile(json.dumps(lock)))

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


@pytest.mark.unit
def test_skills_cli_dependency_sources_use_locked_ref(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = {
        "skills": {
            "alpha": {
                "sourceType": "github",
                "sourceUrl": "https://github.com/owner/assets.git",
                "ref": "deadbeef",
                "skillPath": "skills/alpha/SKILL.md",
            }
        }
    }
    monkeypatch.setattr(routes, "SKILLS_LOCK", _TextFile(json.dumps(lock)))

    assert routes.skills_cli_dependency_sources() == {
        "alpha": (
            "https://raw.githubusercontent.com/owner/assets/deadbeef/"
            "skills/alpha/SKILL.md"
        )
    }


@pytest.mark.unit
def test_find_local_skill_files_keeps_empty_tracked_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        routes.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout=""),
    )

    assert routes.find_local_skill_files() == []


@pytest.mark.unit
def test_dependency_skill_entry_uses_injected_loader() -> None:
    source = (
        "https://raw.githubusercontent.com/owner/assets/abc123/skills/alpha/SKILL.md"
    )
    text = "---\nname: alpha\ndescription:  Useful   skill.\n---\n# Alpha\n"

    assert routes.dependency_skill_entry("alpha", source, lambda _source: text) == {
        "name": "alpha",
        "description": "Useful skill.",
        "source": source,
    }


@pytest.mark.unit
def test_dependency_skill_entry_rejects_locked_name_mismatch() -> None:
    source = (
        "https://raw.githubusercontent.com/owner/assets/abc123/skills/alpha/SKILL.md"
    )
    text = "---\nname: beta\ndescription: Different skill.\n---\n# Beta\n"

    with pytest.raises(
        routes.RouteGenerationError,
        match="locked Skill name mismatch: alpha != beta",
    ):
        routes.dependency_skill_entry("alpha", source, lambda _source: text)


@pytest.mark.unit
def test_skill_entries_include_external_dependency_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rulesync_source = "https://example.test/rulesync/zeta"
    skills_cli_source = "https://example.test/skills-cli/alpha"
    monkeypatch.setattr(routes, "find_local_skill_files", lambda: [])
    monkeypatch.setattr(
        routes,
        "rulesync_dependency_sources",
        lambda: {"zeta": rulesync_source},
    )
    monkeypatch.setattr(
        routes,
        "skills_cli_dependency_sources",
        lambda: {"alpha": skills_cli_source},
    )

    def loader(source: str) -> str:
        name = "zeta" if source == rulesync_source else "alpha"
        return f"---\nname: {name}\ndescription: {name} skill\n---\n"

    assert routes.skill_entries(loader) == [
        {
            "name": "alpha",
            "description": "alpha skill",
            "source": skills_cli_source,
        },
        {
            "name": "zeta",
            "description": "zeta skill",
            "source": rulesync_source,
        },
    ]


@pytest.mark.unit
def test_skill_entries_reject_local_external_name_collision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    local_path = object()
    monkeypatch.setattr(routes, "find_local_skill_files", lambda: [local_path])
    monkeypatch.setattr(
        routes,
        "load_frontmatter",
        lambda _path: {"name": "shared", "description": "Local skill"},
    )
    monkeypatch.setattr(
        routes,
        "relative",
        lambda _path: ".rulesync/skills/shared/SKILL.md",
    )
    monkeypatch.setattr(
        routes,
        "rulesync_dependency_sources",
        lambda: {"shared": "https://example.test/external"},
    )
    monkeypatch.setattr(routes, "skills_cli_dependency_sources", lambda: {})

    with pytest.raises(
        routes.RouteGenerationError,
        match="local and external Skill names overlap: shared",
    ):
        routes.skill_entries()


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
        routes.RouteGenerationError,
        match="Skill dependency exists in both locks: shared",
    ):
        routes.skill_entries()

"""Behavioral tests for chatbot Agent Asset route generation."""

from __future__ import annotations

import json
from types import SimpleNamespace
from urllib.request import Request

import pytest

import scripts.generate_agent_routes as routes


class _TextFile:
    """테스트용 가상 텍스트 파일 래퍼.

    `is_file() -> True`와 `read_text(encoding='utf-8')` 인터페이스를 제공하여
    디스크 I/O 없이 모킹된 설정 파일 내용을 반환한다.
    """

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
    """GitHub 소스 경로의 다양한 형태가 단일 규격으로 정규화되는지 검증한다."""
    assert routes.normalize_github_source(source) == expected


@pytest.mark.unit
def test_strip_jsonc_comments_preserves_markers_inside_strings() -> None:
    """JSONC 주석 제거 시 문자열 리터럴 내부의 마커는 보존되는지 검증한다."""
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
    """lockfile의 resolvedRef 커밋 해시가 GitHub raw URL에 바인딩되는지 검증한다."""
    config = """
    {
      "sources": [
        {
          "source": "owner/assets",
          "path": "src/rulesync/.rulesync/skills", // canonical skill root
          "skills": ["alpha", "beta"]
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
def test_rulesync_dependency_sources_reject_missing_configured_skill(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """설정된 외부 Skill이 lock에서 빠지면 route 생성을 중단한다."""

    config = """
    {
      "sources": [
        {
          "source": "owner/assets",
          "path": "src/rulesync/.rulesync/skills",
          "skills": ["alpha", "beta"]
        }
      ]
    }
    """
    lock = {
        "sources": {
            "owner/assets": {
                "resolvedRef": "abc123",
                "skills": {"alpha": {}},
            }
        }
    }
    monkeypatch.setattr(routes, "RULESYNC_CONFIG", _TextFile(config))
    monkeypatch.setattr(routes, "RULESYNC_LOCK", _TextFile(json.dumps(lock)))

    with pytest.raises(
        routes.RouteGenerationError,
        match="missing configured Skills.*beta",
    ):
        routes.rulesync_dependency_sources()


@pytest.mark.unit
def test_fetch_text_does_not_send_github_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """public metadata fetch는 설정된 GitHub token도 요청에 보내지 않는다."""

    monkeypatch.setenv("GH_TOKEN", "secret-token")
    monkeypatch.setenv("GITHUB_TOKEN", "another-secret-token")
    requests: list[Request] = []

    class _Response:
        def __enter__(self) -> _Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b"metadata"

    def fake_urlopen(request: Request, *, timeout: int) -> _Response:
        assert timeout == 30
        requests.append(request)
        return _Response()

    monkeypatch.setattr(routes, "urlopen", fake_urlopen)

    raw_url = "https://raw.githubusercontent.com/owner/repo/main/SKILL.md"
    assert routes.fetch_text(raw_url) == "metadata"
    assert routes.fetch_text("https://example.test/SKILL.md") == "metadata"
    assert requests[0].get_header("Authorization") is None
    assert requests[1].get_header("Authorization") is None


@pytest.mark.unit
def test_skills_cli_dependency_sources_use_locked_ref(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Skills CLI lockfile에 잠긴 Git ref와 skillPath가 URL로 합성되는지 검증한다."""
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
    """Git 추적 파일 결과가 비어있을 때 빈 목록을 온전히 반환하는지 검증한다."""
    monkeypatch.setattr(
        routes.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout=""),
    )

    assert routes.find_local_skill_files() == []


@pytest.mark.unit
def test_dependency_skill_entry_uses_injected_loader() -> None:
    """주입된 텍스트 로더 콜백을 통해 Skill 메타데이터가 파싱되는지 검증한다."""
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
    """외부 마크다운의 실제 name과 lockfile의 식별자 불일치 시 예외를 검증한다."""
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
    """외부 의존성들이 이름순으로 정렬되어 통합 색인에 포함되는지 검증한다."""
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
    """로컬 Skill과 외부 의존성 Skill 이름 중복 시 생성을 거부하는지 검증한다."""
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
    """양쪽 lockfile에 동일한 Skill 이름이 중복 정의된 경우 거부하는지 검증한다."""
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

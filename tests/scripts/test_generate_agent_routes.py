"""Behavioral tests for chatbot Agent Asset route generation."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
from http.client import HTTPResponse
from pathlib import Path
from types import SimpleNamespace
from urllib.request import Request
from zipfile import ZipFile

import pytest

from scripts.agent_routes import RouteGenerationError, indexes, metadata, sources
from scripts.agent_routes import __main__ as cli


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
    assert sources.normalize_github_source(source) == expected


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

    assert json.loads(metadata.strip_jsonc_comments(text)) == {
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
    monkeypatch.setattr(sources, "RULESYNC_CONFIG", _TextFile(config))
    monkeypatch.setattr(sources, "RULESYNC_LOCK", _TextFile(json.dumps(lock)))

    assert sources.rulesync_dependency_sources() == {
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
    monkeypatch.setattr(sources, "RULESYNC_CONFIG", _TextFile(config))
    monkeypatch.setattr(sources, "RULESYNC_LOCK", _TextFile(json.dumps(lock)))

    with pytest.raises(
        RouteGenerationError,
        match="missing configured Skills.*beta",
    ):
        sources.rulesync_dependency_sources()


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

    monkeypatch.setattr(sources, "urlopen", fake_urlopen)

    raw_url = "https://raw.githubusercontent.com/owner/repo/main/SKILL.md"
    assert sources.fetch_text(raw_url) == "metadata"
    assert sources.fetch_text("https://example.test/SKILL.md") == "metadata"
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
    monkeypatch.setattr(sources, "SKILLS_LOCK", _TextFile(json.dumps(lock)))

    assert sources.skills_cli_dependency_sources() == {
        "alpha": (
            "https://raw.githubusercontent.com/owner/assets/deadbeef/"
            "skills/alpha/SKILL.md"
        )
    }


def _github_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    files: dict[str, bytes],
    *,
    repository: str = "owner/assets",
    ref: str | None = None,
) -> list[str]:
    payload = io.BytesIO()
    with ZipFile(payload, "w") as archive:
        for path, content in files.items():
            archive.writestr(f"assets-{'a' * 40}/{path}", content)
    calls: list[str] = []
    commits_url = f"https://api.github.com/repos/{repository}/commits?per_page=1"
    if ref is not None:
        commits_url += f"&sha={ref}"

    def fake_urlopen(request: Request, *, timeout: int) -> io.BytesIO:
        assert timeout == 30
        assert request.get_header("Authorization") is None
        calls.append(request.full_url)
        if request.full_url == commits_url:
            return io.BytesIO(json.dumps([{"sha": "a" * 40}]).encode())
        if (
            request.full_url
            == f"https://codeload.github.com/{repository}/zip/{'a' * 40}"
        ):
            return io.BytesIO(payload.getvalue())
        pytest.fail(f"unexpected remote request: {request.full_url}")

    monkeypatch.setattr(sources, "urlopen", fake_urlopen)
    return calls


@pytest.mark.unit
def test_skills_cli_version_one_resolves_hash_verified_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = b"---\nname: alpha\ndescription: Alpha skill\n---\n"
    lock = {
        "version": 1,
        "skills": {
            "alpha": {
                "source": "owner/assets",
                "sourceType": "github",
                "computedHash": hashlib.sha256(b"SKILL.md" + text).hexdigest(),
            }
        },
    }
    monkeypatch.setattr(sources, "SKILLS_LOCK", _TextFile(json.dumps(lock)))
    monkeypatch.setenv("GH_TOKEN", "must-not-be-sent")
    calls = _github_snapshot(
        monkeypatch,
        {"unusual/location/SKILL.md": text, "README.md": b"outside the skill"},
    )

    assert sources.skills_cli_dependency_sources() == {
        "alpha": (
            f"https://raw.githubusercontent.com/owner/assets/{'a' * 40}/"
            "unusual/location/SKILL.md"
        )
    }
    assert calls == [
        "https://api.github.com/repos/owner/assets/commits?per_page=1",
        f"https://codeload.github.com/owner/assets/zip/{'a' * 40}",
    ]


@pytest.mark.unit
@pytest.mark.parametrize("repository", ["vercel-labs/assets", "zapier/connectors"])
@pytest.mark.parametrize("skill_path", [None, "SKILL.md"])
def test_skills_cli_version_one_resolves_root_blob_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    repository: str,
    skill_path: str | None,
) -> None:
    text = b"---\nname: alpha\ndescription: Alpha skill\n---\n"
    entry: dict[str, str] = {
        "source": repository,
        "sourceType": "github",
        "computedHash": hashlib.sha256(b"SKILL.md" + text).hexdigest(),
    }
    if skill_path is not None:
        entry["skillPath"] = skill_path
    lock = {
        "version": 1,
        "skills": {"alpha": entry},
    }
    monkeypatch.setattr(sources, "SKILLS_LOCK", _TextFile(json.dumps(lock)))
    _github_snapshot(
        monkeypatch,
        {"SKILL.md": text, "README.md": b"outside the blob snapshot"},
        repository=repository,
    )

    assert sources.skills_cli_dependency_sources() == {
        "alpha": f"https://raw.githubusercontent.com/{repository}/{'a' * 40}/SKILL.md"
    }


@pytest.mark.unit
def test_skills_cli_version_one_rejects_changed_root_blob(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = b"---\nname: alpha\ndescription: Alpha skill\n---\n"
    lock = {
        "version": 1,
        "skills": {
            "alpha": {
                "source": "vercel-labs/assets",
                "sourceType": "github",
                "skillPath": "SKILL.md",
                "computedHash": hashlib.sha256(b"SKILL.md" + text).hexdigest(),
            }
        },
    }
    monkeypatch.setattr(sources, "SKILLS_LOCK", _TextFile(json.dumps(lock)))
    _github_snapshot(
        monkeypatch,
        {
            "SKILL.md": text + b"Changed instructions\n",
            "README.md": b"outside the blob",
        },
        repository="vercel-labs/assets",
    )

    with pytest.raises(RouteGenerationError, match="Skills CLI hash mismatch: alpha"):
        sources.skills_cli_dependency_sources()


@pytest.mark.unit
@pytest.mark.parametrize("repository", ["owner/assets", "vercel-labs/assets"])
def test_skills_cli_version_one_resolves_root_clone_snapshot(
    monkeypatch: pytest.MonkeyPatch, repository: str
) -> None:
    text = b"---\nname: alpha\ndescription: Alpha skill\n---\n"
    readme = b"part of the cloned folder"
    lock = {
        "version": 1,
        "skills": {
            "alpha": {
                "source": repository,
                "sourceType": "github",
                "computedHash": hashlib.sha256(
                    b"README.md" + readme + b"SKILL.md" + text
                ).hexdigest(),
            }
        },
    }
    monkeypatch.setattr(sources, "SKILLS_LOCK", _TextFile(json.dumps(lock)))
    _github_snapshot(
        monkeypatch, {"SKILL.md": text, "README.md": readme}, repository=repository
    )

    assert sources.skills_cli_dependency_sources() == {
        "alpha": f"https://raw.githubusercontent.com/{repository}/{'a' * 40}/SKILL.md"
    }


@pytest.mark.unit
@pytest.mark.parametrize("repository", ["owner/assets", "vercel-labs/assets"])
def test_skills_cli_version_one_rejects_changed_root_clone_folder(
    monkeypatch: pytest.MonkeyPatch, repository: str
) -> None:
    text = b"---\nname: alpha\ndescription: Alpha skill\n---\n"
    lock = {
        "version": 1,
        "skills": {
            "alpha": {
                "source": repository,
                "sourceType": "github",
                "computedHash": hashlib.sha256(
                    b"README.md" + b"original readme" + b"SKILL.md" + text
                ).hexdigest(),
            }
        },
    }
    monkeypatch.setattr(sources, "SKILLS_LOCK", _TextFile(json.dumps(lock)))
    _github_snapshot(
        monkeypatch,
        {"SKILL.md": text, "README.md": b"changed readme"},
        repository=repository,
    )

    with pytest.raises(RouteGenerationError, match="Skills CLI hash mismatch: alpha"):
        sources.skills_cli_dependency_sources()


@pytest.mark.unit
@pytest.mark.parametrize(
    ("repository", "ref"), [("owner/assets", None), ("vercel-labs/assets", "stable")]
)
def test_skills_cli_version_one_rejects_blob_hash_for_clone_only_source(
    monkeypatch: pytest.MonkeyPatch, repository: str, ref: str | None
) -> None:
    text = b"---\nname: alpha\ndescription: Alpha skill\n---\n"
    entry: dict[str, str] = {
        "source": repository,
        "sourceType": "github",
        "skillPath": "SKILL.md",
        "computedHash": hashlib.sha256(b"SKILL.md" + text).hexdigest(),
    }
    if ref is not None:
        entry["ref"] = ref
    monkeypatch.setattr(
        sources,
        "SKILLS_LOCK",
        _TextFile(json.dumps({"version": 1, "skills": {"alpha": entry}})),
    )
    _github_snapshot(
        monkeypatch,
        {"SKILL.md": text, "README.md": b"part of the cloned folder"},
        repository=repository,
        ref=ref,
    )

    with pytest.raises(RouteGenerationError, match="Skills CLI hash mismatch: alpha"):
        sources.skills_cli_dependency_sources()


@pytest.mark.unit
def test_skills_cli_version_one_rejects_unlocked_folder_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = b"---\nname: alpha\ndescription: Alpha skill\n---\n"
    lock = {
        "version": 1,
        "skills": {
            "alpha": {
                "source": "owner/assets",
                "sourceType": "github",
                "computedHash": hashlib.sha256(b"SKILL.md" + text).hexdigest(),
            }
        },
    }
    monkeypatch.setattr(sources, "SKILLS_LOCK", _TextFile(json.dumps(lock)))
    _github_snapshot(
        monkeypatch,
        {"skills/alpha/SKILL.md": text, "skills/alpha/extra.txt": b"unlocked file"},
    )

    with pytest.raises(RouteGenerationError, match="Skills CLI hash mismatch: alpha"):
        sources.skills_cli_dependency_sources()


@pytest.mark.unit
def test_skills_cli_encodes_verified_path_for_metadata_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = b"---\nname: alpha\ndescription: Verified metadata\n---\n"
    path = "alpha#stable ?100%/SKILL.md"
    lock = {
        "version": 1,
        "skills": {
            "alpha": {
                "source": "owner/assets",
                "sourceType": "github",
                "computedHash": hashlib.sha256(b"SKILL.md" + text).hexdigest(),
            }
        },
    }
    monkeypatch.setattr(sources, "SKILLS_LOCK", _TextFile(json.dumps(lock)))
    _github_snapshot(monkeypatch, {path: text})
    resolved = sources.skills_cli_dependency_sources()["alpha"]
    expected_url = (
        f"https://raw.githubusercontent.com/owner/assets/{'a' * 40}/"
        "alpha%23stable%20%3F100%25/SKILL.md"
    )

    def metadata_request(request: Request, *, timeout: int) -> io.BytesIO:
        assert timeout == 30
        assert request.full_url == expected_url
        return io.BytesIO(text)

    monkeypatch.setattr(sources, "urlopen", metadata_request)
    assert indexes.dependency_skill_entry("alpha", resolved, sources.fetch_text) == {
        "name": "alpha",
        "description": "Verified metadata",
        "source": expected_url,
    }


@pytest.mark.unit
def test_skills_cli_explicit_path_does_not_bypass_duplicate_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = b"---\nname: alpha\ndescription: Alpha skill\n---\n"
    lock = {
        "version": 1,
        "skills": {
            "alpha": {
                "source": "owner/assets",
                "sourceType": "github",
                "skillPath": "first/SKILL.md",
                "computedHash": hashlib.sha256(b"SKILL.md" + text).hexdigest(),
            }
        },
    }
    monkeypatch.setattr(sources, "SKILLS_LOCK", _TextFile(json.dumps(lock)))
    _github_snapshot(monkeypatch, {"first/SKILL.md": text, "second/SKILL.md": text})
    with pytest.raises(RouteGenerationError, match="one named Skill: alpha"):
        sources.skills_cli_dependency_sources()


@pytest.mark.unit
@pytest.mark.parametrize(
    "lock",
    [
        [],
        {"version": 2, "skills": {}},
        {"version": True, "skills": {}},
        {"version": 1, "skills": []},
        {
            "version": 1,
            "skills": {"alpha": {"source": "owner/assets", "sourceType": "github"}},
        },
    ],
)
def test_skills_cli_rejects_invalid_lock_without_network(
    monkeypatch: pytest.MonkeyPatch, lock: object
) -> None:
    monkeypatch.setattr(sources, "SKILLS_LOCK", _TextFile(json.dumps(lock)))
    monkeypatch.setattr(
        sources,
        "urlopen",
        lambda *_args, **_kwargs: pytest.fail("invalid lock must not fetch metadata"),
    )

    with pytest.raises(RouteGenerationError):
        sources.skills_cli_dependency_sources()


@pytest.mark.unit
def test_skills_cli_reports_snapshot_network_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = {
        "version": 1,
        "skills": {
            "alpha": {
                "source": "owner/assets",
                "sourceType": "github",
                "computedHash": "a" * 64,
            }
        },
    }
    monkeypatch.setattr(sources, "SKILLS_LOCK", _TextFile(json.dumps(lock)))

    def unavailable(*_args: object, **_kwargs: object) -> None:
        raise OSError("offline")

    monkeypatch.setattr(sources, "urlopen", unavailable)

    with pytest.raises(
        RouteGenerationError, match="failed to load Skills CLI snapshot: alpha.*offline"
    ):
        sources.skills_cli_dependency_sources()


@pytest.mark.component
@pytest.mark.parametrize("phase", ["commits", "archive", "metadata"])
def test_cli_reports_incomplete_http_read_without_writing_routes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    phase: str,
) -> None:
    text = b"---\nname: alpha\ndescription: Alpha skill\n---\n"
    lock = {
        "version": 1,
        "skills": {
            "alpha": {
                "source": "owner/assets",
                "sourceType": "github",
                "computedHash": hashlib.sha256(b"SKILL.md" + text).hexdigest(),
            }
        },
    }
    monkeypatch.setattr(sources, "SKILLS_LOCK", _TextFile(json.dumps(lock)))
    monkeypatch.setattr(sources, "RULESYNC_LOCK", tmp_path / "rulesync.lock")
    monkeypatch.setattr(indexes, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(indexes, "SKILLS_ROOT", tmp_path / ".rulesync/skills")
    monkeypatch.setattr(indexes, "RULES_ROOT", tmp_path / ".rulesync/rules")
    route_root = tmp_path / ".agents/route"
    route_root.mkdir(parents=True)
    for name in ("skills.jsonl", "rules.jsonl"):
        (route_root / name).write_text("stale\n", encoding="utf-8")
    monkeypatch.setattr(indexes, "ROUTE_ROOT", route_root)
    monkeypatch.setattr(cli, "ROUTE_ROOT", route_root)
    _github_snapshot(monkeypatch, {"alpha/SKILL.md": text})
    snapshot_request = sources.urlopen

    def partial_request(request: Request, *, timeout: int) -> object:
        if (
            (phase == "commits" and request.full_url.startswith("https://api."))
            or (phase == "metadata" and request.full_url.startswith("https://raw."))
            or (phase == "archive" and request.full_url.startswith("https://codeload."))
        ):
            payload = (
                b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n14\r\npartial"
                if phase == "archive"
                else b"HTTP/1.1 200 OK\r\nContent-Length: 20\r\n\r\npartial"
            )
            connection, sender = socket.socketpair()
            with connection:
                with sender:
                    sender.sendall(payload)
                response = HTTPResponse(connection)
                response.begin()
                return response
        return snapshot_request(request, timeout=timeout)

    monkeypatch.setattr(sources, "urlopen", partial_request)

    assert cli.main(["--check"]) == 2
    assert "IncompleteRead" in capsys.readouterr().err
    assert {
        path.name: path.read_text(encoding="utf-8") for path in route_root.iterdir()
    } == {
        "skills.jsonl": "stale\n",
        "rules.jsonl": "stale\n",
    }


@pytest.mark.unit
def test_skills_cli_absent_lock_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sources, "SKILLS_LOCK", SimpleNamespace(is_file=lambda: False))
    assert sources.skills_cli_dependency_sources() == {}


@pytest.mark.unit
@pytest.mark.parametrize("names", [["beta"], ["alpha", "alpha"]])
def test_skills_cli_rejects_missing_or_ambiguous_named_skill(
    monkeypatch: pytest.MonkeyPatch, names: list[str]
) -> None:
    lock = {
        "version": 1,
        "skills": {
            "alpha": {
                "source": "owner/assets",
                "sourceType": "github",
                "computedHash": "a" * 64,
            }
        },
    }
    monkeypatch.setattr(sources, "SKILLS_LOCK", _TextFile(json.dumps(lock)))
    _github_snapshot(
        monkeypatch,
        {
            f"folder{index}/SKILL.md": (
                f"---\nname: {name}\ndescription: Skill\n---\n".encode()
            )
            for index, name in enumerate(names)
        },
    )
    with pytest.raises(RouteGenerationError, match="one named Skill: alpha"):
        sources.skills_cli_dependency_sources()


@pytest.mark.component
def test_folder_hash_matches_vendor_path_order_and_exclusions() -> None:
    files = {
        "skill/b.txt": b"b",
        "skill/a.txt": b"a",
        "skill/SKILL.md": b"metadata",
        "skill/.git/config": b"excluded",
        "skill/node_modules/package.txt": b"excluded",
        "outside.txt": b"excluded",
    }
    expected = hashlib.sha256(b"a.txtab.txtbSKILL.mdmetadata").hexdigest()
    assert sources._skill_folder_hash(files, "skill") == expected


@pytest.mark.component
def test_module_cli_preserves_output_and_exit_codes_without_path_injection(
    tmp_path: Path,
) -> None:
    bundle_root = Path(sources.__file__).parent
    shutil.copytree(
        bundle_root,
        tmp_path / "scripts/agent_routes",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    skill = tmp_path / ".rulesync/skills/alpha/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: alpha\ndescription: Alpha   skill\n---\n", encoding="utf-8"
    )
    rule = tmp_path / ".rulesync/rules/python.md"
    rule.parent.mkdir(parents=True)
    rule.write_text(
        "---\ndescription: Python rules\nglobs: '*.py'\n---\n", encoding="utf-8"
    )
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", ".rulesync"], cwd=tmp_path, check=True)
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}

    def invoke(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "scripts.agent_routes", *args],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    assert invoke("--check").returncode == 1
    route_root = tmp_path / ".agents/route"
    assert not route_root.exists()
    assert invoke().returncode == 0
    skills_route = route_root / "skills.jsonl"
    rules_route = route_root / "rules.jsonl"
    assert skills_route.read_text(encoding="utf-8") == (
        '{"name":"alpha","description":"Alpha skill",'
        '"source":".rulesync/skills/alpha/SKILL.md"}\n'
    )
    assert rules_route.read_text(encoding="utf-8") == (
        '{"description":"Python rules","globs":["*.py"],'
        '"source":".rulesync/rules/python.md"}\n'
    )
    assert invoke("--check").returncode == 0
    skills_route.write_text("stale\n", encoding="utf-8")
    assert invoke("--check").returncode == 1
    assert skills_route.read_text(encoding="utf-8") == "stale\n"
    (tmp_path / "skills-lock.json").write_text("[]", encoding="utf-8")
    failed = invoke("--check")
    assert failed.returncode == 2
    assert "invalid skills-lock.json" in failed.stderr
    assert skills_route.read_text(encoding="utf-8") == "stale\n"


@pytest.mark.unit
def test_find_local_skill_files_keeps_empty_tracked_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Git 추적 파일 결과가 비어있을 때 빈 목록을 온전히 반환하는지 검증한다."""
    monkeypatch.setattr(
        indexes.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout=""),
    )

    assert indexes.find_local_skill_files() == []


@pytest.mark.unit
def test_dependency_skill_entry_uses_injected_loader() -> None:
    """주입된 텍스트 로더 콜백을 통해 Skill 메타데이터가 파싱되는지 검증한다."""
    source = (
        "https://raw.githubusercontent.com/owner/assets/abc123/skills/alpha/SKILL.md"
    )
    text = "---\nname: alpha\ndescription:  Useful   skill.\n---\n# Alpha\n"

    assert indexes.dependency_skill_entry("alpha", source, lambda _source: text) == {
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
        RouteGenerationError,
        match="locked Skill name mismatch: alpha != beta",
    ):
        indexes.dependency_skill_entry("alpha", source, lambda _source: text)


@pytest.mark.unit
def test_skill_entries_include_external_dependency_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """외부 의존성들이 이름순으로 정렬되어 통합 색인에 포함되는지 검증한다."""
    rulesync_source = "https://example.test/rulesync/zeta"
    skills_cli_source = "https://example.test/skills-cli/alpha"
    monkeypatch.setattr(indexes, "find_local_skill_files", lambda: [])
    monkeypatch.setattr(
        indexes,
        "rulesync_dependency_sources",
        lambda: {"zeta": rulesync_source},
    )
    monkeypatch.setattr(
        indexes,
        "skills_cli_dependency_sources",
        lambda: {"alpha": skills_cli_source},
    )

    def loader(source: str) -> str:
        name = "zeta" if source == rulesync_source else "alpha"
        return f"---\nname: {name}\ndescription: {name} skill\n---\n"

    assert indexes.skill_entries(loader) == [
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
    monkeypatch.setattr(indexes, "find_local_skill_files", lambda: [local_path])
    monkeypatch.setattr(
        indexes,
        "load_frontmatter",
        lambda _path: {"name": "shared", "description": "Local skill"},
    )
    monkeypatch.setattr(
        indexes,
        "relative",
        lambda _path: ".rulesync/skills/shared/SKILL.md",
    )
    monkeypatch.setattr(
        indexes,
        "rulesync_dependency_sources",
        lambda: {"shared": "https://example.test/external"},
    )
    monkeypatch.setattr(indexes, "skills_cli_dependency_sources", lambda: {})

    with pytest.raises(
        RouteGenerationError,
        match="local and external Skill names overlap: shared",
    ):
        indexes.skill_entries()


@pytest.mark.unit
def test_skill_entries_reject_dependency_name_collision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """양쪽 lockfile에 동일한 Skill 이름이 중복 정의된 경우 거부하는지 검증한다."""
    monkeypatch.setattr(indexes, "find_local_skill_files", lambda: [])
    monkeypatch.setattr(
        indexes,
        "rulesync_dependency_sources",
        lambda: {"shared": "https://example.test/rulesync"},
    )
    monkeypatch.setattr(
        indexes,
        "skills_cli_dependency_sources",
        lambda: {"shared": "https://example.test/skills-cli"},
    )

    with pytest.raises(
        RouteGenerationError,
        match="Skill dependency exists in both locks: shared",
    ):
        indexes.skill_entries()

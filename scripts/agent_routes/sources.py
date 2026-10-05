"""External lock interpretation and public Skill metadata loading."""

from __future__ import annotations

import hashlib
import io
import json
import re
import stat
import subprocess
from http.client import HTTPException
from pathlib import PurePosixPath
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile

from . import RULESYNC_CONFIG, RULESYNC_LOCK, SKILLS_LOCK, RouteGenerationError
from .metadata import parse_frontmatter, strip_jsonc_comments

_MAX_ARCHIVE_BYTES = 32 * 1024 * 1024
_MAX_SNAPSHOT_BYTES = 128 * 1024 * 1024
_BLOB_ALLOWED_OWNERS = frozenset(
    {"vercel", "vercel-labs", "heygen-com", "remotion-dev"}
)


def normalize_github_source(source: str) -> str:
    """GitHub 저장소 원천 표현을 일관된 'owner/repo' 축약 형태로 정규화한다.

    지원하는 형태:
    - 'owner/repo'
    - 'owner/repo.git'
    - 'https://github.com/owner/repo'
    - 'https://github.com/owner/repo.git'

    Args:
        source: 정규화할 원천 문자열.

    Returns:
        정규화된 'owner/repo' 형태의 문자열.

    Raises:
        RouteGenerationError: 지원되지 않는 GitHub URL 형식인 경우.
    """
    shorthand = source.removesuffix(".git")
    if re.fullmatch(r"[^/]+/[^/]+", shorthand):
        return shorthand

    parsed = urlparse(source)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.scheme == "https" and parsed.hostname == "github.com" and len(parts) == 2:
        return f"{parts[0]}/{parts[1].removesuffix('.git')}"
    raise RouteGenerationError(f"unsupported GitHub Skill source: {source}")


def github_raw_url(source: str, ref: str, path: str) -> str:
    """GitHub 저장소 파일의 raw.githubusercontent.com 직접 다운로드 URL을 생성한다."""
    repository = normalize_github_source(source)
    return f"https://raw.githubusercontent.com/{repository}/{ref}/{path.lstrip('/')}"


def fetch_text(url: str) -> str:
    """원격 URL에서 텍스트를 UTF-8로 가져온다.

    보안 불변식:
    퍼블릭 메타데이터 조회이므로 환경 변수의 인증 토큰을 헤더에
    절대 포함하지 않고 식별용 User-Agent만 전송한다.
    """
    request = Request(
        url,
        headers={"User-Agent": "hmda-data-reliability-agent-route"},
    )
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310
            return response.read().decode("utf-8")
    except HTTPException as exc:
        raise RouteGenerationError(
            f"failed to load remote metadata: {url}: {exc}"
        ) from exc


def rulesync_dependency_sources() -> dict[str, str]:
    """`rulesync.jsonc` 및 lock을 읽어 외부 Rulesync Skill의 원격 raw URL을 도출한다.

    검증 불변식:
    1. `rulesync.lock`이 없으면 빈 딕셔너리 반환.
    2. config에 설정된 모든 skills가 lockfile sources 내에 반드시 존재해야 함.
       (하나라도 누락 시 `RouteGenerationError` 발생)
    3. 누락된 skill들은 사전 순서대로 콤마로 묶여 예외 메시지에 표기됨.

    Returns:
        `{스킬_이름: raw_github_url}` 매핑 딕셔너리.
    """
    if not RULESYNC_LOCK.is_file():
        return {}

    lock = json.loads(RULESYNC_LOCK.read_text(encoding="utf-8"))
    config = json.loads(
        strip_jsonc_comments(RULESYNC_CONFIG.read_text(encoding="utf-8"))
    )
    config_sources: dict[str, dict[str, object]] = {}
    for entry in config.get("sources", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("source"), str):
            continue
        config_sources[entry["source"]] = entry

    lock_sources = lock.get("sources")
    if not isinstance(lock_sources, dict):
        raise RouteGenerationError("invalid Rulesync lock: sources must be an object")

    result: dict[str, str] = {}
    for source, config_source in config_sources.items():
        raw_configured_skills = config_source.get("skills")
        if raw_configured_skills is None:
            continue
        if not isinstance(raw_configured_skills, list):
            raise RouteGenerationError(
                f"incomplete configured Rulesync Skills: {source}"
            )

        locked = lock_sources.get(source)
        if not isinstance(locked, dict):
            raise RouteGenerationError(f"Rulesync lock is missing source: {source}")

        path_value = config_source.get("path")
        resolved_ref = locked.get("resolvedRef")
        skills = locked.get("skills")
        if (
            not isinstance(path_value, str)
            or not isinstance(resolved_ref, str)
            or not isinstance(skills, dict)
        ):
            raise RouteGenerationError(f"incomplete Rulesync Skill source: {source}")

        configured_skills: list[str] = []
        for skill_name in raw_configured_skills:
            if not isinstance(skill_name, str) or not skill_name:
                raise RouteGenerationError(
                    f"invalid configured Rulesync Skill name: {skill_name!r}"
                )
            configured_skills.append(skill_name)

        missing_skills = [
            skill_name for skill_name in configured_skills if skill_name not in skills
        ]
        if missing_skills:
            missing = ", ".join(missing_skills)
            raise RouteGenerationError(
                f"Rulesync lock is missing configured Skills for {source}: {missing}"
            )

        base_path = path_value.rstrip("/")
        for skill_name in configured_skills:
            result[skill_name] = github_raw_url(
                source,
                resolved_ref,
                f"{base_path}/{skill_name}/SKILL.md",
            )
    return result


def _github_snapshot(repository: str, ref: str | None) -> tuple[str, dict[str, bytes]]:
    query = {"per_page": "1"}
    if ref is not None:
        query["sha"] = ref
    commits_url = (
        f"https://api.github.com/repos/{repository}/commits?{urlencode(query)}"
    )
    commits = json.loads(fetch_text(commits_url))
    if (
        not isinstance(commits, list)
        or not commits
        or not isinstance(commits[0], dict)
        or not isinstance(commits[0].get("sha"), str)
        or not re.fullmatch(r"[0-9a-f]{40}", commits[0]["sha"])
    ):
        raise RouteGenerationError(f"cannot resolve Skills CLI revision: {repository}")
    revision = commits[0]["sha"]
    url = f"https://codeload.github.com/{repository}/zip/{revision}"
    request = Request(url, headers={"User-Agent": "hmda-data-reliability-agent-route"})
    with urlopen(request, timeout=30) as response:  # noqa: S310
        content = response.read(_MAX_ARCHIVE_BYTES + 1)
    if len(content) > _MAX_ARCHIVE_BYTES:
        raise RouteGenerationError(
            f"Skills CLI archive exceeds size limit: {repository}"
        )

    files: dict[str, bytes] = {}
    try:
        with ZipFile(io.BytesIO(content)) as archive:
            if sum(info.file_size for info in archive.infolist()) > _MAX_SNAPSHOT_BYTES:
                raise RouteGenerationError(
                    f"Skills CLI snapshot exceeds size limit: {repository}"
                )
            for info in archive.infolist():
                if info.is_dir() or stat.S_ISLNK(info.external_attr >> 16):
                    continue
                path = PurePosixPath(info.filename)
                if path.is_absolute() or ".." in path.parts or len(path.parts) < 2:
                    raise RouteGenerationError(
                        f"invalid Skills CLI archive path: {path}"
                    )
                relative_path = PurePosixPath(*path.parts[1:]).as_posix()
                if relative_path in files:
                    raise RouteGenerationError(
                        f"duplicate Skills CLI archive path: {relative_path}"
                    )
                files[relative_path] = archive.read(info)
    except BadZipFile as exc:
        raise RouteGenerationError(f"invalid Skills CLI archive: {repository}") from exc
    return revision, files


def _skill_folder_hash(files: dict[str, bytes], folder: str) -> str:
    prefix = f"{folder}/" if folder else ""
    contents = {
        path.removeprefix(prefix): content
        for path, content in files.items()
        if path.startswith(prefix)
        and not {".git", "node_modules"}.intersection(
            PurePosixPath(path.removeprefix(prefix)).parts[:-1]
        )
    }
    try:
        ordered = subprocess.run(
            [
                "node",
                "-e",
                "const fs = require('node:fs'); "
                "const paths = JSON.parse(fs.readFileSync(0, 'utf8')); "
                "paths.sort((a, b) => a.localeCompare(b)); "
                "console.log(JSON.stringify(paths));",
            ],
            input=json.dumps(list(contents)),
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RouteGenerationError(
            "Skills CLI hash verification requires the Node.js runtime"
        ) from exc
    digest = hashlib.sha256()
    for path in json.loads(ordered.stdout):
        digest.update(path.encode("utf-8"))
        digest.update(contents[path])
    return digest.hexdigest()


def _snapshot_skill_path(
    name: str,
    path: str | None,
    expected_hash: str,
    files: dict[str, bytes],
    *,
    allow_root_blob: bool,
) -> str:
    if path is not None and path not in files:
        raise RouteGenerationError(f"missing Skills CLI skillPath: {name}: {path}")
    candidates = [
        candidate
        for candidate in files
        if PurePosixPath(candidate).name == "SKILL.md"
        and not {".git", "node_modules"}.intersection(
            PurePosixPath(candidate).parts[:-1]
        )
    ]
    matching: list[str] = []
    for candidate in candidates:
        meta = parse_frontmatter(files[candidate].decode("utf-8"), candidate)
        if meta.get("name") == name:
            matching.append(candidate)
    if len(matching) != 1:
        raise RouteGenerationError(
            f"Skills CLI snapshot must contain one named Skill: {name}"
        )
    skill_path = matching[0]
    if path is not None and path != skill_path:
        raise RouteGenerationError(
            f"Skills CLI skillPath name mismatch: {name}: {path}"
        )
    folder = PurePosixPath(skill_path).parent.as_posix()
    actual_hash = _skill_folder_hash(files, "" if folder == "." else folder)
    if actual_hash != expected_hash and allow_root_blob and skill_path == "SKILL.md":
        actual_hash = hashlib.sha256(b"SKILL.md" + files[skill_path]).hexdigest()
    if actual_hash != expected_hash:
        raise RouteGenerationError(
            f"Skills CLI hash mismatch: {name}; upstream snapshot differs from lock"
        )
    return skill_path


def skills_cli_dependency_sources() -> dict[str, str]:
    """version 1 lock의 내용 hash를 검증한 immutable raw URL을 반환한다.

    ref와 skillPath는 vendor의 optional 필드다. 누락 시 실제 default revision과
    Skill 이름으로 source를 찾되 computedHash와 내용이 같을 때만 채택한다.
    Skills CLI 1.7.0의 ref 없는 허용 source는 root blob의 SKILL.md hash도 지원한다.
    그 외 입력은 전체 폴더 hash를 요구한다. Lock에는 설치 방식 구분이 없다.
    version과 computedHash가 없는 기존 explicit ref/path 입력도 계속 지원한다.
    """
    if not SKILLS_LOCK.is_file():
        return {}

    lock = json.loads(SKILLS_LOCK.read_text(encoding="utf-8"))
    if not isinstance(lock, dict):
        raise RouteGenerationError("invalid skills-lock.json: expected an object")
    version = lock.get("version")
    if "version" in lock and (type(version) is not int or version != 1):
        raise RouteGenerationError(f"unsupported skills-lock.json version: {version!r}")
    skills = lock.get("skills")
    if not isinstance(skills, dict):
        raise RouteGenerationError("invalid skills-lock.json: skills must be an object")

    result: dict[str, str] = {}
    snapshots: dict[tuple[str, str | None], tuple[str, dict[str, bytes]]] = {}
    for skill_name, entry in skills.items():
        if (
            not isinstance(skill_name, str)
            or not skill_name
            or not isinstance(entry, dict)
        ):
            raise RouteGenerationError("invalid Skills CLI lock entry")
        if entry.get("sourceType") != "github":
            raise RouteGenerationError(
                f"chatbot route supports GitHub Skills CLI sources only: {skill_name}"
            )

        source = entry.get("sourceUrl") or entry.get("source")
        ref = entry.get("ref")
        path = entry.get("skillPath")
        if not isinstance(source, str) or not source:
            raise RouteGenerationError(
                f"incomplete Skills CLI lock entry: {skill_name}"
            )
        for field in ("ref", "skillPath"):
            if field in entry and (
                not isinstance(entry[field], str) or not entry[field].strip()
            ):
                raise RouteGenerationError(f"invalid Skills CLI {field}: {skill_name}")
        repository = normalize_github_source(source)
        expected_hash = entry.get("computedHash")
        if version is None and "computedHash" not in entry:
            if not isinstance(ref, str) or not isinstance(path, str):
                raise RouteGenerationError(
                    f"incomplete Skills CLI lock entry: {skill_name}"
                )
            result[skill_name] = github_raw_url(repository, ref, path)
            continue
        if not isinstance(expected_hash, str) or not re.fullmatch(
            r"[0-9a-f]{64}", expected_hash
        ):
            raise RouteGenerationError(f"invalid Skills CLI computedHash: {skill_name}")
        key = (repository, ref)
        try:
            if key not in snapshots:
                snapshots[key] = _github_snapshot(repository, ref)
            revision, files = snapshots[key]
            resolved_path = _snapshot_skill_path(
                skill_name,
                path,
                expected_hash,
                files,
                allow_root_blob=ref is None
                and (
                    repository.lower().split("/", 1)[0] in _BLOB_ALLOWED_OWNERS
                    or repository.lower() == "zapier/connectors"
                ),
            )
        except (OSError, HTTPException) as exc:
            raise RouteGenerationError(
                f"failed to load Skills CLI snapshot: {skill_name}: {exc}"
            ) from exc
        result[skill_name] = github_raw_url(
            repository, revision, quote(resolved_path, safe="/")
        )
    return result

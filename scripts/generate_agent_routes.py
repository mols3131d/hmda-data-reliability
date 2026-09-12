#!/usr/bin/env python3
"""Generate chatbot routing indexes from repository Agent Asset sources."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / ".rulesync" / "skills"
RULES_ROOT = REPO_ROOT / ".rulesync" / "rules"
ROUTE_ROOT = REPO_ROOT / ".agents" / "route"
RULESYNC_CONFIG = REPO_ROOT / "rulesync.jsonc"
RULESYNC_LOCK = REPO_ROOT / "rulesync.lock"
SKILLS_LOCK = REPO_ROOT / "skills-lock.json"


class RouteGenerationError(RuntimeError):
    """Raised when route source metadata cannot be converted into a valid index."""


def parse_frontmatter(text: str, source: str) -> dict[str, Any]:
    """YAML 프런트매터를 파싱하여 딕셔너리로 반환한다.

    Args:
        text: 파싱할 마크다운 또는 텍스트 문서 내용.
        source: 오류 메시지에 표시할 소스 식별자 (파일 경로 또는 URL).

    Returns:
        파싱된 프런트매터 딕셔너리. 프런트매터가 없으면 빈 딕셔너리 `{}` 반환.

    Raises:
        RouteGenerationError: 프런트매터가 닫히지 않았거나 매핑(dict)이 아닌 경우.
    """
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return {}

    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise RouteGenerationError(f"unterminated frontmatter: {source}") from exc

    data = yaml.safe_load("\n".join(lines[1:end])) or {}
    if not isinstance(data, dict):
        raise RouteGenerationError(f"frontmatter must be a mapping: {source}")
    return data


def load_frontmatter(path: Path) -> dict[str, Any]:
    """로컬 파일에서 UTF-8 인코딩으로 프런트매터를 읽고 파싱한다.

    Args:
        path: 대상 파일 경로.

    Returns:
        파싱된 프런트매터 딕셔너리.
    """
    return parse_frontmatter(path.read_text(encoding="utf-8"), str(path))


def relative(path: Path) -> str:
    """저장소 루트 기준의 POSIX 상대 경로 문자열을 반환한다."""
    return path.relative_to(REPO_ROOT).as_posix()


def normalized_text(value: object, *, field: str, source: str) -> str:
    """텍스트 필드의 유효성을 검증하고 연속 공백을 단일 공백으로 정규화한다.

    Args:
        value: 검증할 대상 값 (반드시 비어있지 않은 문자열이어야 함).
        field: 누락 시 예외 메시지에 표기할 필드명.
        source: 오류 발생 출처 식별자.

    Returns:
        공백이 정규화된 텍스트.

    Raises:
        RouteGenerationError: 문자열이 아니거나 공백만으로 이루어진 경우.
    """
    if not isinstance(value, str) or not value.strip():
        raise RouteGenerationError(f"missing {field}: {source}")
    return " ".join(value.split())


def route_enabled(meta: dict[str, Any], *, path: Path) -> bool:
    """메타데이터의 'route' 불리언 활성화 여부를 반환한다.

    Args:
        meta: 프런트매터 메타데이터 딕셔너리.
        path: 검사 대상 파일 경로.

    Returns:
        라우팅 포함 여부 (기본값: True).

    Raises:
        RouteGenerationError: 'route' 필드가 불리언 타입이 아닌 경우.
    """
    value = meta.get("route", True)
    if not isinstance(value, bool):
        raise RouteGenerationError(f"route must be boolean: {path}")
    return value


def strip_jsonc_comments(text: str) -> str:
    """JSONC 텍스트에서 한 줄 주석(//)과 블록 주석(/* */)을 안전하게 제거한다.

    구현 불변식:
    문자열 리터럴 내부(따옴표 안)에 등장하는 주석 기호나 이스케이프된 따옴표는
    주석으로 오인하여 제거하지 않고 그대로 보존한다.

    Args:
        text: 주석이 포함될 수 있는 JSONC 원문 문자열.

    Returns:
        주석이 제거되어 표준 `json.loads`로 파싱 가능한 JSON 문자열.

    Raises:
        RouteGenerationError: 닫히지 않은 블록 주석(`/*`)이 존재할 때.
    """
    result: list[str] = []
    index = 0
    in_string = False
    escaped = False

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if char == "/" and next_char == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue
        if char == "/" and next_char == "*":
            index += 2
            while index < len(text):
                if text[index : index + 2] == "*/":
                    index += 2
                    break
                if text[index] in "\r\n":
                    result.append(text[index])
                index += 1
            else:
                raise RouteGenerationError(
                    "unterminated JSONC block comment: rulesync.jsonc"
                )
            continue
        result.append(char)
        index += 1

    return "".join(result)


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
    with urlopen(request, timeout=30) as response:  # noqa: S310
        return response.read().decode("utf-8")


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


def skills_cli_dependency_sources() -> dict[str, str]:
    """`skills-lock.json`을 읽어 Skills CLI로 관리되는 외부 Skill의 raw URL을 도출한다.

    검증 불변식:
    1. `skills-lock.json` 미존재 시 빈 딕셔너리 반환.
    2. 오직 `sourceType == "github"`인 에셋만 지원 (기타 소스는 `RouteGenerationError`).
    3. `sourceUrl` 또는 `source`, `ref`, `skillPath`가 누락되지 않아야 함.

    Returns:
        `{스킬_이름: raw_github_url}` 매핑 딕셔너리.
    """
    if not SKILLS_LOCK.is_file():
        return {}

    lock = json.loads(SKILLS_LOCK.read_text(encoding="utf-8"))
    skills = lock.get("skills")
    if not isinstance(skills, dict):
        raise RouteGenerationError("invalid skills-lock.json: skills must be an object")

    result: dict[str, str] = {}
    for skill_name, entry in skills.items():
        if not isinstance(skill_name, str) or not isinstance(entry, dict):
            raise RouteGenerationError("invalid Skills CLI lock entry")
        if entry.get("sourceType") != "github":
            raise RouteGenerationError(
                f"chatbot route supports GitHub Skills CLI sources only: {skill_name}"
            )

        source = entry.get("sourceUrl") or entry.get("source")
        ref = entry.get("ref")
        path = entry.get("skillPath")
        if not all(isinstance(value, str) and value for value in (source, ref, path)):
            raise RouteGenerationError(
                f"incomplete Skills CLI lock entry: {skill_name}"
            )
        result[skill_name] = github_raw_url(source, ref, path)
    return result


def find_local_skill_files() -> list[Path]:
    """저장소 내의 로컬 Skill 마크다운(`SKILL.md`) 파일들을 탐색한다.

    Git 추적 파일(`.rulesync/skills/*/SKILL.md`)을 우선 탐색하고,
    git 명령 실패 또는 git 미설치 환경에서는 디렉토리 글로브로 폴백한다.

    Returns:
        정렬된 `SKILL.md` 절대/상대 `Path` 목록.
    """
    try:
        proc = subprocess.run(
            ["git", "ls-files", ".rulesync/skills/*/SKILL.md"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return sorted(SKILLS_ROOT.glob("*/SKILL.md"))

    return sorted(
        REPO_ROOT / line.strip() for line in proc.stdout.splitlines() if line.strip()
    )


def dependency_skill_entry(
    name: str,
    source: str,
    loader: Callable[[str], str] = fetch_text,
) -> dict[str, object]:
    """원격 또는 외부 의존성 Skill의 메타데이터를 로드하여 색인 엔트리를 구성한다.

    검증 불변식:
    다운로드한 Skill 문서의 프런트매터 `name`과 lockfile에 선언된 `name`이 일치해야 함.

    Args:
        name: 기대하는 Skill 식별자 이름.
        source: Skill 파일의 원격 URL.
        loader: 텍스트 취득 함수 (기본값: HTTP `fetch_text`, 테스트 시 모킹 주입 가능).

    Returns:
        `{"name": ..., "description": ..., "source": ...}` 딕셔너리.
    """
    try:
        meta = parse_frontmatter(loader(source), source)
    except OSError as exc:
        raise RouteGenerationError(
            f"failed to load dependency Skill: {source}: {exc}"
        ) from exc

    actual_name = normalized_text(meta.get("name"), field="name", source=source)
    if actual_name != name:
        raise RouteGenerationError(
            f"locked Skill name mismatch: {name} != {actual_name}"
        )
    return {
        "name": name,
        "description": normalized_text(
            meta.get("description"), field="description", source=source
        ),
        "source": source,
    }


def skill_entries(
    loader: Callable[[str], str] = fetch_text,
) -> list[dict[str, object]]:
    """로컬 및 외부 의존성 Skill 전체를 취합하고 정렬된 엔트리 목록을 반환한다.

    충돌 방지 불변식:
    1. Rulesync 의존성과 Skills CLI 간에 동일한 이름이 선언되면 충돌 예외.
    2. 로컬 Skill과 외부 의존성 Skill 간에 동일한 이름이 겹치면 충돌 예외.

    Args:
        loader: 의존성 Skill 로드 콜백.

    Returns:
        정렬된 Skill 메타데이터 엔트리 목록.
    """
    entries: dict[str, dict[str, object]] = {}
    for path in find_local_skill_files():
        meta = load_frontmatter(path)
        source = relative(path)
        name = normalized_text(meta.get("name"), field="name", source=source)
        entries[name] = {
            "name": name,
            "description": normalized_text(
                meta.get("description"), field="description", source=source
            ),
            "source": source,
        }

    dependency_sources = rulesync_dependency_sources()
    for name, source in skills_cli_dependency_sources().items():
        if name in dependency_sources:
            raise RouteGenerationError(f"Skill dependency exists in both locks: {name}")
        dependency_sources[name] = source

    for name, source in dependency_sources.items():
        if name in entries:
            raise RouteGenerationError(
                f"local and external Skill names overlap: {name}"
            )
        entries[name] = dependency_skill_entry(name, source, loader)

    return [entries[name] for name in sorted(entries)]


def rule_entries() -> list[dict[str, object]]:
    """`.rulesync/rules/*.md`에서 활성화된 Rule 메타데이터 엔트리들을 취합하여 반환한다.

    필터링 및 검증 규칙:
    - `root: true`인 루트 지침이나 `route: false`로 비활성화된 규칙은 색인에서 제외.
    - `globs`는 필수이며, 유효한 문자열 또는 비어있지 않은 문자열 리스트여야 함.

    Returns:
        Rule 엔트리 목록 (`{"description": ..., "globs": [...], "source": ...}`).
    """
    entries: list[dict[str, object]] = []
    for path in sorted(RULES_ROOT.glob("*.md")):
        meta = load_frontmatter(path)
        if meta.get("root") is True or not route_enabled(meta, path=path):
            continue

        globs = meta.get("globs")
        if globs is None:
            continue
        if isinstance(globs, str):
            globs = [globs]
        if (
            not isinstance(globs, list)
            or not globs
            or not all(isinstance(item, str) and item for item in globs)
        ):
            raise RouteGenerationError(f"invalid globs: {path}")

        source = relative(path)
        entries.append(
            {
                "description": normalized_text(
                    meta.get("description"), field="description", source=source
                ),
                "globs": globs,
                "source": source,
            }
        )
    return entries


def render(entries: list[dict[str, object]]) -> str:
    """엔트리 리스트를 JSONL(JSON Lines) 포맷의 텍스트로 렌더링한다.

    각 엔트리는 공백 없이 컴팩트하게 직렬화되며,
    `ensure_ascii=False`로 유니코드(한국어 등)를 그대로 유지한다.

    Args:
        entries: 직렬화할 딕셔너리 객체 목록.

    Returns:
        개행 문자로 구분된 JSONL 문자열 (마지막 줄 개행 포함).
    """
    return (
        "\n".join(
            json.dumps(entry, ensure_ascii=False, separators=(",", ":"))
            for entry in entries
        )
        + "\n"
    )


def generated_routes(
    loader: Callable[[str], str] = fetch_text,
) -> dict[Path, str]:
    """Chatbot 라우팅 인덱스 파일 경로와 기대 렌더링 콘텐츠의 매핑을 반환한다.

    생성 대상:
    - `.agents/route/skills.jsonl`: 전체 로컬 및 외부 스킬 목록
    - `.agents/route/rules.jsonl`: 활성화된 저장소 규칙 목록

    Args:
        loader: 외부 의존성 Skill 로드 함수.

    Returns:
        `{절대_경로: jsonl_문자열}` 딕셔너리.
    """
    return {
        ROUTE_ROOT / "skills.jsonl": render(skill_entries(loader)),
        ROUTE_ROOT / "rules.jsonl": render(rule_entries()),
    }


def check_routes(routes: dict[Path, str]) -> int:
    """디스크 상의 라우팅 인덱스 파일들이 생성 기대치와 일치하는지 드리프트를 검사한다.

    Returns:
        드리프트(누락 또는 불일치)가 있는 파일이 존재하면 1, 완전히 일치하면 0.
    """
    stale = [
        path
        for path, expected in routes.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != expected
    ]
    for path in stale:
        print(f"stale route: {relative(path)}")
    return 1 if stale else 0


def write_routes(routes: dict[Path, str]) -> None:
    """기대 라우팅 인덱스를 디스크에 기록하고 생성된 파일 경로를 출력한다.

    Args:
        routes: `{경로: 콘텐츠}` 매핑.
    """
    ROUTE_ROOT.mkdir(parents=True, exist_ok=True)
    for path, content in routes.items():
        path.write_text(content, encoding="utf-8")
        print(f"generated {relative(path)}")


def main(argv: list[str] | None = None) -> int:
    """Chatbot 라우팅 인덱스 생성 CLI 진입점.

    Args:
        argv: 커맨드라인 인자 리스트 (기본값: `sys.argv[1:]`).

    Returns:
        0 (성공), 1 (체크 모드에서 드리프트 발견), 2 (파싱/파일/생성 오류).
    """
    parser = argparse.ArgumentParser(
        description="Generate .agents/route Skill and Rule indexes."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when generated routes differ from committed files",
    )
    args = parser.parse_args(argv)

    try:
        routes = generated_routes()
        if args.check:
            return check_routes(routes)
        write_routes(routes)
    except (OSError, RouteGenerationError, ValueError, yaml.YAMLError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Local assets, dependency composition and deterministic JSONL indexes."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path

from . import REPO_ROOT, ROUTE_ROOT, RULES_ROOT, SKILLS_ROOT, RouteGenerationError
from .metadata import (
    load_frontmatter,
    normalized_text,
    parse_frontmatter,
    route_enabled,
)
from .sources import (
    fetch_text,
    rulesync_dependency_sources,
    skills_cli_dependency_sources,
)


def relative(path: Path) -> str:
    """저장소 루트 기준의 POSIX 상대 경로 문자열을 반환한다."""
    return path.relative_to(REPO_ROOT).as_posix()


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

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
from urllib.request import urlopen

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / ".rulesync" / "skills"
RULES_ROOT = REPO_ROOT / ".rulesync" / "rules"
ROUTE_ROOT = REPO_ROOT / ".agents" / "route"
RULESYNC_CONFIG = REPO_ROOT / "rulesync.jsonc"
RULESYNC_LOCK = REPO_ROOT / "rulesync.lock"
SKILLS_LOCK = REPO_ROOT / "skills-lock.json"

SKILLS_META = {"kind": "skills"}
RULES_META = {"kind": "rules"}


class RouteGenerationError(RuntimeError):
    """Raised when route source metadata cannot be converted into a valid index."""


def parse_frontmatter(text: str, source: str) -> dict[str, Any]:
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
    return parse_frontmatter(path.read_text(encoding="utf-8"), str(path))


def relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def normalized_text(value: object, *, field: str, source: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RouteGenerationError(f"missing {field}: {source}")
    return " ".join(value.split())


def route_enabled(meta: dict[str, Any], *, path: Path) -> bool:
    value = meta.get("route", True)
    if not isinstance(value, bool):
        raise RouteGenerationError(f"route must be boolean: {path}")
    return value


def strip_jsonc_comments(text: str) -> str:
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
    shorthand = source.removesuffix(".git")
    if re.fullmatch(r"[^/]+/[^/]+", shorthand):
        return shorthand

    parsed = urlparse(source)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.scheme == "https" and parsed.hostname == "github.com" and len(parts) == 2:
        return f"{parts[0]}/{parts[1].removesuffix('.git')}"
    raise RouteGenerationError(f"unsupported GitHub Skill source: {source}")


def github_raw_url(source: str, ref: str, path: str) -> str:
    repository = normalize_github_source(source)
    return f"https://raw.githubusercontent.com/{repository}/{ref}/{path.lstrip('/')}"


def fetch_text(url: str) -> str:
    with urlopen(url, timeout=30) as response:  # noqa: S310
        return response.read().decode("utf-8")


def rulesync_dependency_sources() -> dict[str, str]:
    if not RULESYNC_LOCK.is_file():
        return {}

    lock = json.loads(RULESYNC_LOCK.read_text(encoding="utf-8"))
    config = json.loads(
        strip_jsonc_comments(RULESYNC_CONFIG.read_text(encoding="utf-8"))
    )
    config_sources = {
        entry["source"]: entry
        for entry in config.get("sources", [])
        if isinstance(entry, dict) and isinstance(entry.get("source"), str)
    }

    result: dict[str, str] = {}
    for source, locked in lock.get("sources", {}).items():
        if not isinstance(locked, dict):
            raise RouteGenerationError(f"invalid Rulesync lock source: {source}")
        config_source = config_sources.get(source)
        resolved_ref = locked.get("resolvedRef")
        skills = locked.get("skills")
        if (
            not isinstance(config_source, dict)
            or not isinstance(config_source.get("path"), str)
            or not isinstance(resolved_ref, str)
            or not isinstance(skills, dict)
        ):
            raise RouteGenerationError(f"incomplete Rulesync Skill source: {source}")

        base_path = config_source["path"].rstrip("/")
        for skill_name in skills:
            if not isinstance(skill_name, str):
                raise RouteGenerationError(
                    f"invalid Rulesync Skill name: {skill_name!r}"
                )
            result[skill_name] = github_raw_url(
                source,
                resolved_ref,
                f"{base_path}/{skill_name}/SKILL.md",
            )
    return result


def skills_cli_dependency_sources() -> dict[str, str]:
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
        REPO_ROOT / line.strip()
        for line in proc.stdout.splitlines()
        if line.strip()
    )


def dependency_skill_entry(
    name: str,
    source: str,
    loader: Callable[[str], str] = fetch_text,
) -> dict[str, object]:
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
            raise RouteGenerationError(
                f"Skill dependency exists in both locks: {name}"
            )
        dependency_sources[name] = source

    for name, source in dependency_sources.items():
        if name in entries:
            raise RouteGenerationError(
                f"local and external Skill names overlap: {name}"
            )
        entries[name] = dependency_skill_entry(name, source, loader)

    return [entries[name] for name in sorted(entries)]


def rule_entries() -> list[dict[str, object]]:
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


def render(meta: dict[str, object], entries: list[dict[str, object]]) -> str:
    rows: list[dict[str, object]] = [{"_meta": meta}, *entries]
    return (
        "\n".join(
            json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows
        )
        + "\n"
    )


def generated_routes(
    loader: Callable[[str], str] = fetch_text,
) -> dict[Path, str]:
    return {
        ROUTE_ROOT / "skills.jsonl": render(SKILLS_META, skill_entries(loader)),
        ROUTE_ROOT / "rules.jsonl": render(RULES_META, rule_entries()),
    }


def check_routes(routes: dict[Path, str]) -> int:
    stale = [
        path
        for path, expected in routes.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != expected
    ]
    for path in stale:
        print(f"stale route: {relative(path)}")
    return 1 if stale else 0


def write_routes(routes: dict[Path, str]) -> None:
    ROUTE_ROOT.mkdir(parents=True, exist_ok=True)
    for path, content in routes.items():
        path.write_text(content, encoding="utf-8")
        print(f"generated {relative(path)}")


def main(argv: list[str] | None = None) -> int:
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

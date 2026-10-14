"""Frontmatter, JSONC and route field validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from . import RouteGenerationError


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

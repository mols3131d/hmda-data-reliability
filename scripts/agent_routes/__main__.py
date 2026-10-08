"""Single module entrypoint for chatbot route generation and checking."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from . import ROUTE_ROOT, RouteGenerationError
from .indexes import generated_routes, relative


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

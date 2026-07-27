# DEVELOPMENT

> [!TIP]
> 의존성 설치: `uv sync` · 테스트: `uv run pytest`

| Index | Description |
| --- | --- |
| [Development Environment](#development-environment) | 개발 환경 |
| [Directory Structure](#directory-structure) | 주요 디렉토리 |
| [Testing](#testing) | 테스트 실행 |
| [Formatting](#formatting) | 코드·문서 포맷 |
| [VCS](#vcs) | 버전 관리 |

| When indexing | Read elsewhere |
| --- | --- |
| 데이터 계약·시스템 경계 | [`ARCHITECTURE`](ARCHITECTURE.md) |

## Development Environment

| Item | Requirement |
| --- | --- |
| Python | `>=3.13` |
| Package manager | `uv` · [`pyproject.toml`](../pyproject.toml) |

## Directory Structure

| Directory | Purpose |
| --- | --- |
| `src/` | 애플리케이션 패키지 |
| `tests/` | 도메인별 테스트 |
| `dbt/` | 모델·매크로·설정 |
| `data/` | DuckDB·원천 데이터·메타데이터 |
| `notebooks/` | Marimo 분석 노트북 |
| `docs/` | 프로젝트 문서 |
| `scripts/` | 설정·유틸리티 스크립트 |

## Testing

```bash
uv run pytest
```

## Formatting

| Target | Tool |
| --- | --- |
| Python | `ruff` |
| Markdown | `rumdl` |

```bash
uv run ruff format .
uv run ruff check src tests
uv run rumdl fmt .
```

## VCS

| Item | Reference |
| --- | --- |
| Git | [`.gitmessage`](../.gitmessage) |

# DEVELOPMENT

> [!TIP]
> 의존성 설치: `uv sync`
> 테스트: `uv run pytest`

## Index

| Section | Description |
| --- | --- |
| [Development Environment](#development-environment) | 개발 환경 |
| [Package Layout](#package-layout) | 패키지·도메인 |
| [Directory Structure](#directory-structure) | 주요 디렉토리 |
| [Testing](#testing) | 테스트 실행 |
| [Formatting](#formatting) | 코드·문서 포맷 |
| [VCS](#vcs) | 버전 관리 |

### Related Documentation

| Topic | Doc |
| --- | --- |
| 데이터 계약·시스템 경계·scope | [`ARCHITECTURE`](ARCHITECTURE.md) |

## Development Environment

|  |  |
| --- | --- |
| Python | `>=3.13` |
| Package manager | `uv`, [`pyproject.toml`](../pyproject.toml) |
| Local stack | DuckDB, dbt, Dagster. |

## Package Layout

| Item | Rule |
| --- | --- |
| Root | `src/project_pivot/` |
| Domains | 새 패키지를 만들기 전에 `data_operations`, `data_platform`, `hmda_data`, `orchestration`, `reliability`, `shared`, `configs` 중 기존 도메인을 우선 사용 |

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

| Tool | Target |
| --- | --- |
| `ruff` | `Python` |
| `rumdl` | `Markdown` |

| Command | Description |
| --- | --- |
| `uv run ruff format .` | `Python` 코드 포매팅 |
| `uv run ruff check src tests` | `src/`·`tests/` 린트 |
| `uv run rumdl fmt .` | `Markdown` 포매팅 |

## VCS

|  |  |
| --- | --- |
| Git | conventional commits; 한글; 상세 내용은 [`.gitmessage`](../.gitmessage)을 참고 |

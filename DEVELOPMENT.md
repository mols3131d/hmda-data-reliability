# DEVELOPMENT

## Related Guides

| Document | Description |
| --- | --- |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | 시스템 경계, 실행 경계, 핵심 domain contract |
| [Testing Guide](docs/development/testing.md) | pytest 실행 command, marker, report, coverage, tracing |
| [Test Design and Implementation](docs/development/test-design-and-implementation.md) | test design, observable contract, scenario, oracle, validation 기준 |

## Quick Commands

| Purpose | Command |
| --- | --- |
| Python format | `uv run ruff format .` |
| Python lint | `uv run ruff check src tests` |
| Markdown format | `uv run rumdl fmt .` |

## Development Environment

| Field | Tools |
| --- | --- |
| Runtime | `Python>=3.13` |
| Package manager | `uv` |
| Data platform | `DuckDB`, `dbt` |
| Orchestration | `Dagster` |
| Analysis | `Marimo`, `Polars` |

## Package And Directory Layout

- 애플리케이션 package root는 `src/project_pivot/`다.
- 새 package를 만들기 전에 `data_operations`, `data_platform`, `hmda_data`, `orchestration`, `reliability`, `shared`, `configs` 중 기존 domain을 우선 사용한다.

| Directory | Purpose |
| --- | --- |
| `src/` | 애플리케이션 package |
| `tests/` | domain별 test |
| `dbt/` | model·macro·설정 |
| `data/` | DuckDB·원천 데이터·metadata |
| `notebooks/` | Marimo 분석 notebook |
| `docs/` | 프로젝트 문서 |
| `scripts/` | 설정·utility script |

## Git Convention

커밋 메시지는 한글 `Conventional Commits` 형식을 따른다. 형식과 타입을 포함한 상세 규칙은 [`.gitmessage`](.gitmessage)를 참고한다.

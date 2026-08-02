# Development Guide

이 문서는 로컬 개발, test, formatting에 필요한 표준 command와 package 배치 규칙을 설명한다. 시스템 경계와 데이터 계약은 [`ARCHITECTURE`](ARCHITECTURE.md)를 기준으로 한다.

## Quick Start

| Goal | Command |
| --- | --- |
| Testing guide | [`docs/TESTING.md`](TESTING.md) |
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

애플리케이션 package root는 `src/project_pivot/`다. 새 package를 만들기 전에 `data_operations`, `data_platform`, `hmda_data`, `orchestration`, `reliability`, `shared`, `configs` 중 기존 domain을 우선 사용한다.

| Directory | Purpose |
| --- | --- |
| `src/` | 애플리케이션 package |
| `tests/` | domain별 test |
| `dbt/` | model·macro·설정 |
| `data/` | DuckDB·원천 데이터·metadata |
| `notebooks/` | Marimo 분석 notebook |
| `docs/` | 프로젝트 문서 |
| `scripts/` | 설정·utility script |

## Testing

테스트 실행 정책과 command는 [`docs/TESTING.md`](TESTING.md)에서 관리한다. 이 문서는 사람용 local command와 Agent용 machine-readable report command를 분리해 설명한다.

## Formatting Commands

Python:

```bash
uv run ruff format .
uv run ruff check src tests
```

Markdown:

```bash
uv run rumdl fmt .
```

## Git Convention

커밋 메시지는 한글 `Conventional Commits` 형식을 따른다. 형식과 타입을 포함한 상세 규칙은 [`.gitmessage`](../.gitmessage)를 참고한다.

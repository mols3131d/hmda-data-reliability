# DEVELOPMENT

이 문서는 repository-wide **개발 환경, active tool choice, package layout과 code convention**을 소유한다. Test와 Git/GitHub처럼 별도 workflow가 있는 영역의 상세 규칙은 `docs/development/**`의 owning guide가 소유한다.

## Related Guides

| Document | Description |
| --- | --- |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | 시스템 경계, 실행 경계, domain ownership guidance |
| [Testing Guide](docs/development/testing.md) | pytest 실행 command, marker, report, coverage, tracing |
| [Test Design and Implementation](docs/development/test-design-and-implementation.md) | test design, observable contract, scenario, oracle, validation 기준 |
| [Version Control and GitHub](docs/development/vcs-git/README.md) | branch, commit, Pull Request와 review workflow |

## Quick Commands

| Purpose | Command |
| --- | --- |
| Repository setup | `python scripts/bootstrap.py setup` |
| Session bootstrap | `python scripts/bootstrap.py session` |
| Agent Asset update | `python scripts/agent_assets.py update` |
| Python format | `uv run ruff format .` |
| Python lint | `uv run ruff check src tests` |
| Markdown format | `uv run rumdl fmt .` |

`setup`은 clone 후 처음 한 번 실행해 locked dependency와 Agent Asset을 복원하고 Git hook을 설치한다. 이후 작업 시작 시에는 `session`으로 dependency와 Agent Asset만 현재 lock 상태에 맞춘다. 최신 Agent Asset을 가져오는 작업은 bootstrap과 분리해 명시적으로 `update`한다.

## Development Environment

| Field | Tools |
| --- | --- |
| Runtime | `Python>=3.13` |
| Package manager | `uv` |
| Data platform | `DuckDB`, `dbt` |
| Orchestration | `Apache Airflow 3.3.0` |
| Analysis | `Polars` |

## Layer Tool Choices

| Layer | Tools | Responsibility |
| --- | --- | --- |
| Bronze | `DuckDB`, `PyArrow` | raw query와 full/partition ingestion |
| Silver / Gold | `dbt Core`, `dbt-duckdb` | staging, mart, test와 `manifest.json` |
| Contracts | `Pydantic` | reliability structured models |
| Control quality | custom profiler/detector | profile snapshot과 detection rules |
| Remediation | `LangGraph` | remediation draft 경로만 |
| Orchestration | `Apache Airflow` | DAG dependency와 task/data-update evidence |

`PyIceberg`는 dependency로 존재하지만 active table engine으로 사용하지 않는다. Spark, cloud warehouse, FastAPI 기반 통합 pipeline CLI, OpenTelemetry, 외부 catalog와 approval UI는 현재 active toolchain에 포함하지 않는다.

## Package And Directory Layout

- 애플리케이션 package root는 `src/hmda_reliability/`다.
- 새 package를 만들기 전에 `data_operations`, `data_platform`, `hmda_data`, `orchestration`, `reliability`, `shared`, `configs` 중 기존 domain을 우선 사용한다.

| Directory | Purpose |
| --- | --- |
| `src/` | 애플리케이션 package |
| `tests/` | domain별 test |
| `dbt/` | model·macro·설정 |
| `data/` | DuckDB·원천 데이터·metadata |
| `docs/` | 프로젝트 문서 |
| `scripts/` | bootstrap·maintenance·utility script |

## Code Conventions

- SRP는 실용적으로 적용한다. Helper 추출은 complexity나 duplication을 실제로 줄일 때만 한다.
- One-class-per-file은 주요 type이나 model에만 적용하고 speculative file splitting을 피한다.

## Git Convention

Git/GitHub workflow는 [`docs/development/vcs-git/`](docs/development/vcs-git/README.md)가 소유한다. Commit message의 실제 형식과 type은 [`.gitmessage`](.gitmessage)를 따른다.

# DEVELOPMENT

이 문서는 repository-wide **개발 환경, active tool choice, package layout과 code convention**을 소유한다. Test와 Git/GitHub처럼 별도 workflow가 있는 영역의 상세 규칙은 `docs/development/**`의 owning guide가 소유한다.

## Related Guides

| Document | Description |
| --- | --- |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | 시스템 경계, 실행 경계, domain ownership guidance |
| [Testing Guide](docs/development/testing.md) | pytest 실행 command, marker, report, coverage, tracing |
| [Test Design](docs/development/test-design.md) | test design, observable contract, scenario, oracle, validation 기준 |
| [Version Control and GitHub](docs/development/vcs-git/README.md) | branch, commit, Pull Request와 review workflow |

## Quick Commands

| Purpose | Command |
| --- | --- |
| Docs index | `uv run python scripts/generate_docs_indexes.py` |
| Repository setup | `python scripts/bootstrap.py setup` |
| Session bootstrap | `python scripts/bootstrap.py session` |
| Tooling update | `python scripts/bootstrap.py update` |
| Python format | `uv run ruff format .` |
| Python lint | `uv run ruff check src tests` |
| Markdown format | `uv run rumdl fmt .` |
| JSON / JSONC format | `python scripts/biome.py format --write --files-ignore-unknown=true .` |

`setup`은 clone 후 처음 한 번 실행해 locked dependency와 Agent Asset을 복원하고 Git hook을 설치하며 OpenSpec과 Biome 사용 상태를 준비한다. 이후 작업 시작 시에는 `session`으로 dependency와 Agent Asset만 현재 lock 상태에 맞춘다.

`update`는 외부에서 관리되는 Agent Asset source와 OpenSpec integration을 명시적으로 갱신한다. `npx` 기반 repository tooling은 기본적으로 upstream의 stable `latest` channel을 따르고, upstream이 명시적인 LTS channel을 제공하면 필요에 따라 그 channel을 우선할 수 있다. Python dependency lock은 자동으로 올리지 않으며 별도 dependency change로 검토한다.

## Development Environment

| Field | Tools |
| --- | --- |
| Runtime | `Python>=3.13`, `Node.js` |
| Package manager | `uv`, `npx` |
| Repository tooling | `OpenSpec`, `RuleSync`, `Skills CLI`, `Biome`, `Lefthook` |
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
| AI runtime | `OpenAI` Python SDK | OpenAI-compatible bounded provider invocation |
| Orchestration | `Apache Airflow` | DAG dependency와 task/data-update evidence |

`PyIceberg`는 dependency로 존재하지만 active table engine으로 사용하지 않는다. Spark, cloud warehouse, FastAPI 기반 통합 pipeline CLI, OpenTelemetry, 외부 catalog와 approval UI는 현재 active toolchain에 포함하지 않는다.

## Package And Directory Layout

- 애플리케이션 package root는 `src/hmda_reliability/`다.
- 새 package를 만들기 전에 `configs`, `data_operations`, `data_platform`, `hmda_data`, `orchestration`, `reliability`, `review_ai`, `runtime_ai`, `shared` 중 기존 domain을 우선 사용한다.

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

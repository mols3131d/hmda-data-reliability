# DEVELOPMENT

이 문서는 repository-wide **개발 환경, active tool choice, package layout과 code convention**을 소유한다. Test와 Git/GitHub처럼 별도 workflow가 있는 영역의 상세 규칙은 `docs/development/**`의 owning guide가 소유한다.

## Related Guides

| Document | Description |
| --- | --- |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | 시스템 경계, 실행 경계, domain ownership guidance |
| [Tooling](docs/development/tooling/README.md) | repository 개발·검증·유지보수 도구의 project-specific usage와 entrypoint |
| [Testing Guide](docs/development/testing.md) | pytest 실행 command, marker, report, coverage, tracing |
| [Test Design](docs/development/test-design.md) | test design, observable contract, scenario, oracle, validation 기준 |
| [Review AI Prompts](docs/development/review-ai-prompts.md) | 프롬프트 조립, 단계별 실행과 HTTP timeout·실행 예산·환경 설정 |
| [Version Control and GitHub](docs/development/vcs-git/README.md) | branch, commit, Pull Request와 review workflow |

## Quick Commands

| Purpose | Command |
| --- | --- |
| Docs index | `uv run python scripts/generate_docs_indexes.py` |
| Tach dependency check | `uv run --no-sync tach check` |
| Repository setup | `uv run --no-sync python scripts/bootstrap.py setup` |
| Session bootstrap | `uv run --no-sync python scripts/bootstrap.py session` |
| Tooling update | `uv run --no-sync python scripts/bootstrap.py update` |
| External Skill 실행 | `uv run python scripts/agent_assets.py run <source> --skill <name> --agent <id>` |
| Python format | `uv run ruff format .` |
| Python lint | `uv run ruff check src tests` |
| Markdown format | `uv run rumdl fmt .` |
| JSON / JSONC format | `uv run python scripts/biome.py format --write --files-ignore-unknown=true .` |
| TOML format | `uv run python scripts/tombi.py format .` |
| TOML lint | `uv run python scripts/tombi.py lint .` |

`setup`, `session`, `update`의 선택 기준과 external tooling refresh 경계는 [Bootstrap](docs/development/tooling/bootstrap.md)이 소유한다. 개별 tool의 repository-specific configuration, wrapper와 검증 경로는 [Tooling](docs/development/tooling/README.md)에서 해당 guide를 확인한다.

## Development Environment

| Field | Tools |
| --- | --- |
| Runtime | `Python>=3.13`, `Node.js` |
| Package manager | `uv`, `npm` |
| Repository tooling | `OpenSpec`, `Rulesync`, `Skills CLI`, `Lefthook`, `Ruff`, `rumdl`, `Biome`, `Tombi`, `Tach`, `zizmor`, `actionlint` |
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

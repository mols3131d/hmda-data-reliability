---
type: plan
title: Development Dependency Cleanup and pytest-env Adoption
description: Marimo 잔재 제거, 개발 의존성 재분류, pytest-env 도입 범위와 검증 기준을 정리한다.
tags:
  - "domain:development"
  - dependencies
  - pytest
---

> [!NOTE]
> 이 문서는 current `main` 정적 검토와 upstream `pytest-env` 확인을 바탕으로 한 적용 계획이다. Dependency 변경과 test 실행은 아직 수행하지 않았다.

## Decision

| Item | Action | Rationale |
| --- | --- | --- |
| `marimo` | remove | active EDA runtime/notebook이 제거됨 |
| `mypy` | remove | 현재 active hook과 개발 경로는 `ty`를 사용함 |
| `pytest-asyncio` | remove | async test가 없고 plugin 설정만 남아 있음 |
| `pyromark` | move to `dev` | agent skill script가 사용하는 development tooling |
| `python-dotenv` | keep in `dev` | `scripts/log_agent_event.py`가 `.env`를 읽기 위해 직접 import함 |
| `pytest-env` | add to `dev` | pytest-owned test environment를 declarative configuration으로 관리 |

Current upstream의 latest release는 `pytest-env 1.7.0`이며 `pytest>=9.0.2`와 `python-dotenv>=1.2.2`를 dependency로 가진다. Project Pivot의 `pytest>=9.1.1`과 호환된다.

`pytest-env`는 `python-dotenv`의 범용 대체재가 아니다. 이 프로젝트에서는 application/agent tooling의 `.env` loading은 `python-dotenv`, pytest process의 deterministic environment는 `pytest-env`가 각각 소유한다.

`python-dotenv`의 유지보수 상태는 이번 dependency 결정의 근거로 사용하지 않는다. 현재 repo-local direct import가 있으므로 직접 dev dependency로 유지한다.

## Ownership

```text
local .env
   |
   +--> scripts/log_agent_event.py --> python-dotenv

pyproject.toml [tool.pytest_env]
   |
   +--> pytest process environment --> pytest-env
                                  |
                                  +--> test subprocess inheritance
```

- Application runtime은 계속 `os.environ`/typed configuration boundary를 사용한다.
- `pytest-env`를 application runtime configuration loader로 사용하지 않는다.
- Repository-local `.env`를 pytest가 자동 load하도록 `env_files`를 설정하지 않는다.
- Secret, machine-specific path, temporary path는 `[tool.pytest_env]`에 넣지 않는다.

## Marimo Cleanup

Active asset에서 다음을 제거하거나 갱신한다.

- `pyproject.toml`: `marimo`, `[tool.marimo.runtime]`
- `scripts/stop_marimo_kernels.py`
- `.vscode/tasks.json`: `Stop Marimo Kernels`
- `.vscode/settings.json`: Marimo notebook editor association
- `skills-lock.json`: `marimo-notebook`, `marimo-pair`, `retro-marimo-pair`
- `DEVELOPMENT.md`: Marimo analysis/notebook 설명과 존재하지 않는 `notebooks/` entry
- `docs/development/foundation/readiness.md`: 해결된 Marimo documentation drift 제거
- `docs/development/foundation/readiness.yml`: 동일 risk 제거

`DEVELOPMENT.md`의 active EDA 설명은 실제 구현에 맞춰 `Polars`와 `Altair` 중심으로 정리한다. `inbox/**`와 `openspec/changes/archive/**`의 역사적 Marimo 언급은 보존한다.

## pyproject Cleanup

`[dependency-groups].dev`:

- remove: `marimo`, `mypy`, `pytest-asyncio`
- keep: `python-dotenv`
- add: `pyromark` — project runtime dependencies에서 이동
- add: `pytest-env>=1.7.0`

Configuration:

- `[tool.marimo.runtime]` 제거
- `[tool.mypy]` 제거
- `[tool.pytest.ini_options]`의 `asyncio_mode`, `asyncio_default_fixture_loop_scope` 제거
- `[tool.pytest_env]` 추가

```toml
[tool.pytest_env]
DBT_SEND_ANONYMOUS_USAGE_STATS = "false"
```

Dependency 변경 후 `uv.lock`을 재생성한다.

## pytest-env Boundary

`DBT_SEND_ANONYMOUS_USAGE_STATS=false`는 test suite 전체에 적용되는 deterministic policy이므로 `[tool.pytest_env]`가 소유한다.

현재 `tests/dbt/test_analytics_foundation.py`의 `_run_dbt()`는 같은 값을 subprocess environment에 다시 기록한다. `pytest-env` 적용 후 이 중복 assignment를 제거하고, subprocess는 pytest process environment를 복사해 상속한다.

반대로 `PROJECT_PIVOT_DUCKDB_PATH`처럼 test마다 달라지는 temporary value는 `_run_dbt()`가 계속 명시적으로 설정한다. `OTEL_TRACES_EXPORTER`처럼 특정 test가 behavior를 검증하기 위해 설정하는 값도 `monkeypatch`에 남긴다.

## Validation

적용 후 좁은 범위부터 확인한다.

1. `uv lock` 후 `uv sync`가 성공한다.
2. `uv run pytest --help`에서 `pytest-env` CLI option이 등록됐는지 확인한다.
3. `uv run pytest --pytest-env-verbose --collect-only tests/dbt/test_analytics_foundation.py`에서 `DBT_SEND_ANONYMOUS_USAGE_STATS=false`가 `SET`으로 보고되는지 확인한다.
4. `mkdir -p artifacts && uv run pytest tests/test_log_agent_event.py`가 통과해 `python-dotenv` 기반 hook contract를 보존한다.
5. `mkdir -p artifacts && uv run pytest tests/dbt/test_analytics_foundation.py`가 통과해 pytest-owned dbt environment가 subprocess까지 전달됨을 확인한다.
6. `mkdir -p artifacts && uv run pytest tests/test_pytest_opentelemetry.py`가 통과한다.
7. `mkdir -p artifacts && uv run pytest`가 기존 default suite에서 통과한다.
8. active files에서 Marimo dependency/config/task/editor association과 `[tool.mypy]`, pytest asyncio settings가 사라졌는지 검색한다.
9. `python-dotenv`가 dev direct dependency로 남고 `scripts/log_agent_event.py` import가 해결되는지 확인한다.
10. `pyromark`가 dev dependency로 resolve되는지 확인하고, 가능한 경우 실제 pyromark-consuming agent skill script 하나로 smoke validation한다.

실행하지 않은 검증은 통과로 기록하지 않는다.

## Deferred Dependency Audit

`pyarrow`, `pydantic-settings`, `pyiceberg`, `sqlalchemy`, `sqlglot`, `pytest-testmon`은 이번 변경 범위에서 제거하지 않는다. 별도 사용성 검증 후 결정한다.

## Review Loop

| Loop | Findings | Resolution |
| --- | --- | --- |
| 1 — Review | `python-dotenv` direct 사용 누락 | `scripts/log_agent_event.py` 근거로 dev dependency 유지 |
| 2 — Adversarial | readiness drift 정리와 pytest validation command 불완전 | readiness 두 파일 포함, testing guide와 command 정렬 |
| 3 — Consistency | upstream version 근거와 pytest-env config 관찰 방법을 더 명확히 할 필요 | latest `1.7.0` 확인, `--collect-only` verbose validation 분리 |
| 4 — Final | material finding 없음 | scope와 ownership 확정 |

## References

- `pyproject.toml`
- `scripts/log_agent_event.py`
- `tests/test_log_agent_event.py`
- `tests/dbt/test_analytics_foundation.py`
- `tests/test_pytest_opentelemetry.py`
- `DEVELOPMENT.md`
- `docs/development/testing.md`
- `docs/development/foundation/readiness.md`
- `docs/development/foundation/readiness.yml`
- `https://github.com/pytest-dev/pytest-env`
- `https://github.com/pytest-dev/pytest-env/blob/main/pyproject.toml`

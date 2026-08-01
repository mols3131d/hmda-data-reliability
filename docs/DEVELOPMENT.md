# Development Guide

이 문서는 로컬 개발, test, formatting에 필요한 표준 command와 package 배치 규칙을 설명한다. 시스템 경계와 데이터 계약은 [`ARCHITECTURE`](ARCHITECTURE.md)를 기준으로 한다.

## Quick Start

| Goal | Command |
| --- | --- |
| 전체 test | `uv run pytest` |
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

### Pytest Plugins

| Package | Description |
| --- | --- |
| `pytest` | 테스트 실행 프레임워크 |
| `pytest-asyncio` | 비동기 테스트·fixture 지원 |
| `pytest-cov` | 테스트 커버리지 측정 |
| `pytest-html` | HTML 테스트 결과 리포트 생성 |
| `pytest-sugar` | 진행 상황 표시 개선 |
| `pytest-timeout` | 테스트 실행 시간 제한 |
| `pytest-xdist` | 테스트 병렬 실행 |
| `hypothesis` | 순수 helper의 property-based testing |
| `opentelemetry-api` | test trace API |
| `opentelemetry-sdk` | opt-in pytest span 생성·export |

`pytest-opentelemetry`는 공식 OpenTelemetry 또는 pytest project가 관리하는 plugin으로 확인되지 않아 사용하지 않는다. Python 3.13과 `pytest-xdist` 지원 계약이 검증되기 전까지 공식 SDK와 local pytest hook을 유지한다.

### Default Pytest Options

`pyproject.toml`의 `addopts`로 다음 옵션을 모든 테스트 실행에 자동 적용한다.

| Option | Description |
| --- | --- |
| `-n auto` | CPU 수에 맞춰 테스트 병렬 실행 |
| `--timeout=60` | 테스트별 최대 실행 시간 60초 |
| `--html=pytest_report.html --self-contained-html` | HTML 리포트 생성 |
| `--strict-markers` | 등록되지 않은 marker 사용 금지 |
| `-m 'not memory and not stress'` | 대형 resource workload 기본 제외 |

기본 옵션을 일시적으로 덮어쓰거나 디버깅할 때만 명령에 직접 지정한다.

### Test Markers

| Marker | Description |
| --- | --- |
| `unit` | 순수 함수·격리된 도메인 테스트 |
| `component` | 로컬 파일을 사용하는 패키지 단위 테스트 |
| `integration` | 여러 시스템을 연결하는 워크플로 테스트 |
| `memory` | 대표 fixture의 process-level memory-budget test |
| `stress` | worst-case resource stress test |

### Core Commands

기본 실행:

```bash
uv run pytest
```

특정 범위 실행:

```bash
uv run pytest tests/data_platform
uv run pytest tests/data_platform/test_sql.py
uv run pytest tests/data_platform/test_sql.py::test_name
```

선택 실행:

```bash
uv run pytest -k "loader"
uv run pytest -m unit
uv run pytest -m "not integration"
```

### HMDA EDA Resource Validation

HMDA EDA correctness test와 resource test는 분리한다.

```bash
uv run pytest tests/hmda_data/test_eda.py \
	tests/hmda_data/test_eda_fixture.py \
	tests/hmda_data/test_eda_memory_helpers.py

uv run python scripts/prepare_hmda_eda_fixture.py
uv run python scripts/run_hmda_eda_memory.py
```

> [!IMPORTANT]
> **Memory runner는 cgroup hard limit를 실제 적용할 수 있을 때만 유효하다.** user systemd와 `MemoryMax`, `MemorySwapMax`를 사용할 수 있는 WSL/Linux 환경에서 실행한다. 사전 hard-limit probe 실패는 통과로 기록하지 않는다.

`stress` marker는 별도 worst-case workload가 추가된 뒤 명시적으로 선택한다.

실패·디버깅:

```bash
uv run pytest --lf
uv run pytest -n 0 -vv -s
```

커버리지:

```bash
uv run pytest --cov=src/project_pivot
```

Test span을 console JSON으로 확인할 때만 tracing을 활성화한다.

```bash
OTEL_TEST_TRACING=1 uv run pytest -n 0 tests/data_platform/test_sql.py
```

기본 pytest 실행은 OpenTelemetry provider나 exporter를 초기화하지 않는다.

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

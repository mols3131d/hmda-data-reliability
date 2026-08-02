# Testing Guide

이 문서는 Project Pivot의 pytest 실행 정책과 command를 정의한다. 사람용 local command는 읽기 쉬운 출력을 우선하고, Agent용 command는 재현 가능한 종료 상태와 machine-readable report를 우선한다.

## Quick Choice

| User | Recommended command | Purpose |
| --- | --- | --- |
| Human | `uv run pytest` | `pytest-sugar`와 기본 HTML report를 사용하는 local test |
| Agent | `mkdir -p artifacts && uv run pytest -p no:sugar --color=no --tb=short -ra --junitxml=artifacts/pytest.xml` | 압축된 console output과 JUnit XML report |
| Agent, changed files | `mkdir -p artifacts && uv run pytest -o 'addopts=-n auto --timeout=60 --html=pytest_report.html --self-contained-html --strict-markers' --testmon -p no:sugar --color=no --tb=short -ra --junitxml=artifacts/pytest.xml` | 이전 coverage data를 사용한 영향 범위 test |

> [!IMPORTANT]
> 두 command 모두 `pyproject.toml`의 기본 옵션을 사용한다. `-n auto`, `--timeout=60`, HTML report, `--strict-markers`, 기본 marker filter를 command에 다시 적지 않는다.

## Default Policy

`pyproject.toml`의 `addopts`가 모든 test 실행에 다음 옵션을 적용한다.

| Option | Description |
| --- | --- |
| `-n auto` | CPU 수에 맞춰 test 병렬 실행 |
| `--timeout=60` | test당 최대 실행 시간 60초 |
| `--html=pytest_report.html --self-contained-html` | HTML report 생성 |
| `--strict-markers` | 등록되지 않은 marker 사용 금지 |
| `-m 'not memory and not stress'` | 대형 resource workload 기본 제외 |

## Human Commands

사람이 local terminal에서 결과를 읽을 때는 기본 command를 사용한다.

```bash
uv run pytest
```

가장 좁은 범위부터 실행한다.

```bash
uv run pytest tests/data_platform
uv run pytest tests/data_platform/test_sql.py
uv run pytest tests/data_platform/test_sql.py::test_name
uv run pytest -k "keyword"
uv run pytest -m unit
uv run pytest -m "not integration"
```

실패 원인을 직접 조사할 때만 console output을 확장하고 병렬 실행을 끈다.

```bash
uv run pytest --lf
uv run pytest -n 0 -vv -s
```

## Agent Commands

Agent는 결과를 후속 처리하기 쉽도록 `pytest-sugar`와 ANSI color를 끄고, 짧은 traceback과 JUnit XML을 사용한다.

전체 test:

```bash
mkdir -p artifacts && uv run pytest \
	-p no:sugar \
	--color=no \
	--tb=short \
	-ra \
	--junitxml=artifacts/pytest.xml
```

좁은 범위 test:

```bash
mkdir -p artifacts && uv run pytest tests/data_platform/test_sql.py \
	-p no:sugar \
	--color=no \
	--tb=short \
	-ra \
	--junitxml=artifacts/pytest.xml
```

`artifacts/pytest.xml`은 실행 결과를 읽는 Agent 또는 CI adapter가 사용할 수 있다. 작업이 끝난 뒤 local-only report라면 생성물을 제거한다.

## Markers

| Marker | Description |
| --- | --- |
| `unit` | 순수 함수·격리된 domain test |
| `component` | local file을 사용하는 package-level test |
| `integration` | 여러 system을 연결하는 workflow test |
| `memory` | 대표 fixture의 process-level memory budget test |
| `stress` | worst-case resource stress test |

기본 실행에서는 `memory`와 `stress`가 제외된다.

```bash
uv run pytest -m memory
uv run pytest -m stress
uv run pytest -m "not integration"
```

## Test Tooling

프로젝트에 도입된 test tooling은 기본 실행, 선택 실행, 또는 별도 validation command로 사용한다.

| Tool | Command or behavior | Use |
| --- | --- | --- |
| `pytest-xdist` | `-n auto`가 기본 적용 | test 병렬 실행 |
| `pytest-timeout` | `--timeout=60`이 기본 적용 | test hang 방지 |
| `pytest-html` | `pytest_report.html`이 기본 생성 | 사람용 HTML 결과 확인 |
| `pytest-sugar` | Human command에서 기본 활성화, Agent command에서 `-p no:sugar`로 비활성화 | local console output 개선 |
| `pytest-testmon` | Agent incremental command에서 `-o 'addopts=...'`로 기본 `-m` filter를 덮어쓴 뒤 `--testmon` 사용 | 변경 영향 test만 빠르게 실행 |
| `pytest-cov` | `--cov=src/project_pivot` | coverage 수집 |
| `pytest-opentelemetry` | `--trace-per-test`, `--export-traces` | test trace와 OTLP export |
| `Hypothesis` | test code의 `@given` 및 strategy | pure helper property test |

`--testmon`은 이전 실행에서 수집한 coverage data가 있어야 효과가 있다. 현재 기본 `addopts`의 `-m 'not memory and not stress'`는 testmon selection과 충돌하므로 incremental command에서 `addopts`를 덮어쓴다. 변경된 test가 없으면 `0 tests`가 정상 결과일 수 있다. 초기 실행, release 전 검증, 변경 영향이 불명확한 경우에는 Agent 전체 test command를 사용한다.

```bash
mkdir -p artifacts && uv run pytest \
	-o 'addopts=-n auto --timeout=60 --html=pytest_report.html --self-contained-html --strict-markers' \
	--testmon \
	-p no:sugar \
	--color=no \
	--tb=short \
	-ra \
	--junitxml=artifacts/pytest.xml
```

## HMDA EDA Resource Validation

HMDA EDA correctness test와 resource test는 분리한다.

```bash
uv run pytest tests/hmda_data/test_eda.py \
	tests/hmda_data/test_eda_fixture.py \
	tests/hmda_data/test_eda_memory_helpers.py

uv run python scripts/prepare_hmda_eda_fixture.py
uv run python scripts/run_hmda_eda_memory.py
```

> [!WARNING]
> **Memory runner는 cgroup hard limit를 실제 적용할 수 있을 때만 유효하다.** user systemd와 `MemoryMax`, `MemorySwapMax`를 사용할 수 있는 WSL/Linux 환경에서 실행한다. 사전 hard-limit probe 실패는 통과로 기록하지 않는다.

## Coverage And Tracing

변경 범위가 넓거나 coverage 근거가 필요할 때만 coverage를 수집한다.

```bash
uv run pytest --cov=src/project_pivot
```

각 test를 독립 trace로 기록할 수 있다.

```bash
uv run pytest --trace-per-test tests/data_platform/test_sql.py
```

OTLP/gRPC collector로 export할 때 endpoint와 export option을 명시한다.

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
	uv run pytest --export-traces
```

Agent가 JUnit XML과 OpenTelemetry trace를 함께 수집해야 하면 다음처럼 실행한다.

```bash
mkdir -p artifacts && OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
	uv run pytest \
		-p no:sugar \
		--color=no \
		--tb=short \
		-ra \
		--junitxml=artifacts/pytest.xml \
		--trace-per-test \
		--export-traces
```

## Related Guides

- [`docs/DEVELOPMENT.md`](DEVELOPMENT.md): local development, package layout, formatting
- [`pyproject.toml`](../pyproject.toml): pytest default options and marker registration

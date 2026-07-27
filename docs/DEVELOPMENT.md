# DEVELOPMENT

## Index

| Section | Description |
| --- | --- |
| [Development Environment](#development-environment) | 개발 환경 |
| [Package Layout](#package-layout) | 패키지·도메인 |
| [Directory Structure](#directory-structure) | 주요 디렉토리 |
| [Testing](#testing) | 테스트 실행 |
| [Formatting](#formatting) | 코드·문서 포맷 |
| [VCS Git](#vcs-git) | 버전 관리 시스템 |

### Related Documentation

| Topic | Doc |
| --- | --- |
| 데이터 계약·시스템 경계·scope | [`ARCHITECTURE`](ARCHITECTURE.md) |

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

## Package Layout

| Item | Rule |
| --- | --- |
| Root | `src/project_pivot/` |
| Domains | 새 패키지를 만들기 전에 `data_operations`, `data_platform`, `hmda_data`, `orchestration`, `reliability`, `shared`, `configs` 중 기존 도메인을 우선 사용 |

## Development Environment

### Tech stack

| Field | Tools |
| --- | --- |
| Runtime | `Python>=3.13` |
| Package manager | `uv` |
| Data platform | `DuckDB`, `dbt` |
| Orchestration | `Dagster` |
| Analysis | `Marimo`, `Polars` |

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

### Default Pytest Options

`pyproject.toml`의 `addopts`로 다음 옵션을 모든 테스트 실행에 자동 적용한다.

| Option | Description |
| --- | --- |
| `-n auto` | CPU 수에 맞춰 테스트 병렬 실행 |
| `--timeout=60` | 테스트별 최대 실행 시간 60초 |
| `--html=pytest_report.html --self-contained-html` | HTML 리포트 생성 |
| `--strict-markers` | 등록되지 않은 marker 사용 금지 |

기본 옵션을 일시적으로 덮어쓰거나 디버깅할 때만 명령에 직접 지정한다.

### Test Markers

| Marker | Description |
| --- | --- |
| `unit` | 순수 함수·격리된 도메인 테스트 |
| `component` | 로컬 파일을 사용하는 패키지 단위 테스트 |
| `integration` | 여러 시스템을 연결하는 워크플로 테스트 |

### Testing Commands

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

실패·디버깅:

```bash
uv run pytest --lf
uv run pytest -n 0 -vv -s
```

커버리지:

```bash
uv run pytest --cov=src/project_pivot
```

## Formatting

Python:

```bash
uv run ruff format .
uv run ruff check src tests
```

Markdown:

```bash
uv run rumdl fmt .
```

## VCS Git

커밋 메시지는 한글 `Conventional Commits` 형식을 따른다. 형식과 타입을 포함한 상세 규칙은 [`.gitmessage`](../.gitmessage)를 참고한다.

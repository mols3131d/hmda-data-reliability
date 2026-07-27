# DEVELOPMENT

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

### Pytest Plugins

| Package | Description |
| --- | --- |
| `pytest` | 테스트 실행 프레임워크 |
| `pytest-asyncio` | 비동기 테스트·fixture 지원 |
| `pytest-cov` | 테스트 커버리지 측정 |
| `pytest-html` | HTML 테스트 결과 리포트 생성 |
| `pytest-sugar` | 진행 상황 표시 개선 |
| `pytest-testmon` | 변경된 코드와 관련된 테스트 선택 실행 |
| `pytest-timeout` | 테스트 실행 시간 제한 |
| `pytest-xdist` | 테스트 병렬 실행 |

### Pytest Options

| Option | Description |
| --- | --- |
| `-n auto` | CPU 수에 맞춰 테스트 병렬 실행 |
| `--timeout=60` | 테스트별 최대 실행 시간 60초 |
| `--html=pytest_report.html --self-contained-html` | HTML 리포트 생성 |
| `--strict-markers` | 등록되지 않은 marker 사용 금지 |

### Test Markers

| Marker | Description |
| --- | --- |
| `unit` | 순수 함수·격리된 도메인 테스트 |
| `component` | 로컬 파일을 사용하는 패키지 단위 테스트 |
| `integration` | 여러 시스템을 연결하는 워크플로 테스트 |

### Testing Commands

| Usage | Example | Description |
| --- | --- | --- |
| `uv run pytest [path]` | `uv run pytest tests/` | 전체 또는 특정 경로 테스트 실행 |
| `uv run pytest [path]::[test]` | `uv run pytest tests/data_platform/test_loader.py::test_load` | 특정 테스트 실행 |
| `uv run pytest -k [keyword]` | `uv run pytest -k "loader"` | 키워드로 테스트 선택 실행 |
| `uv run pytest -m [marker]` | `uv run pytest -m unit` | marker로 테스트 선택 실행 |
| `uv run pytest -m "not [marker]"` | `uv run pytest -m "not integration"` | 특정 marker 테스트 제외 |
| `uv run pytest -n 0 -vv -s` | `uv run pytest -n 0 -vv -s` | 병렬 실행을 끄고 상세 로그 출력 |
| `uv run pytest --lf` | `uv run pytest --lf` | 마지막 실패 테스트 재실행 |
| `uv run pytest --cov=[package]` | `uv run pytest --cov=src/project_pivot --cov-report=term-missing` | 커버리지와 누락된 줄 표시 |

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

- Git
- commit message:
  - conventional commits
  - 한글
  - 상세: [`.gitmessage`](../.gitmessage)

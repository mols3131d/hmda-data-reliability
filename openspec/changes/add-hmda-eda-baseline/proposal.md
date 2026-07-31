## Why

현재 HMDA EDA baseline은 CSV 파싱 오류 행을 조용히 제외할 수 있었고, 약
4.76 GiB의 기본 CSV를 직접 분석하면서 DuckDB 내부 메모리만 제한하므로
결과 무결성과 process 전체 메모리 예산 준수를 함께 증명하지 못한다.
신뢰할 수 있는 reliability 기준선을 만들려면 fail-fast reader, 재사용 가능한
계산 경계와 대표 workload의 memory-budget 검증이 하나의 계약으로 필요하다.

## What Changes

- 원천 HMDA CSV의 required columns 존재와 타입 기준을 표시한다.
- 전체 및 `activity_year`별 row count, required column별 null count와 null
  rate를 표시한다.
- EDA 출력과 `ProfileSnapshot` evidence 필드의 대응 및 baseline/current
  역할을 표시한다.
- 원천 관측 시각이 없으면 freshness를 `미측정`으로 표시하고, 파일 수정
  시각과 Bronze `ingested_at`을 data freshness와 구분한다.
- CSV reader를 fail-fast로 구성한다. 파싱 오류 또는 입력 파일 부재 시
  baseline metric과 `eda_evidence`를 생성하지 않는다.
- EDA 계산과 evidence 생성을 일반 Python entrypoint로 분리하고, Marimo
  노트북과 automated test가 같은 경로를 사용한다.
- correctness test와 대표 fixture의 process-level memory-budget test를
  분리한다.
- memory-budget 실행에 hard memory limit, swap 0, timeout, DuckDB
  memory/thread limit과 전용 temp directory를 적용하고 결과 invariant를
  함께 검증한다.
- 동일한 대표 workload를 반복 실행해 peak RSS, elapsed time, temp disk와
  실행 환경을 기록한다.
- valid sample, malformed CSV와 full/representative source 검증 결과를
  실제 reader 및 resource 계약과 일치시킨다.

## Capabilities

### New Capabilities

- `hmda-eda-baseline`: 원천 HMDA CSV를 fail-fast로 탐색해 reliability
  기준선과 측정 경계를 표시하고, 동일 계산 경로의 correctness와
  process-level memory budget을 검증하는 계약

### Modified Capabilities

- 없음

## Impact

- `notebooks/eda_mo.py`는 공유 EDA entrypoint의 입력 UI와 결과 표시를
  담당한다.
- `src/project_pivot/hmda_data/`에 read-only EDA 계산 entrypoint와 resource
  lifecycle이 추가된다.
- `tests/hmda_data/`, `pyproject.toml`과 memory-budget 실행용 `scripts/`
  command에 correctness·memory test 경로가 추가된다.
- CSV reader의 `ignore_errors=true` 동작이 제거된다. 손상된 입력은 성공한
  baseline 대신 명시적 실행 오류를 반환한다.
- EDA reference와 개발 문서는 실제 input path, fail-fast 동작,
  memory-budget command 및 검증 범위와 일치해야 한다.
- 원천 CSV, Bronze, dbt model, `ProfileSnapshot`, production lifecycle,
  detector와 recovery API의 데이터 계약은 변경하지 않는다.
- 새 dataframe/profiling dependency와 데이터 migration은 없다.

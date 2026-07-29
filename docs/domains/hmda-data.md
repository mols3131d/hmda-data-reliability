# HMDA Data

`hmda_data`는 HMDA 원천 파일을 발견하고 DuckDB Bronze 테이블에 적재하며, reliability 검증용 합성 결함 파일을 만든다. 실행 순서 조합과 결과 모델은 소유하지 않는다.

## Scope

| In scope | Out of scope |
| --- | --- |
| CSV/Parquet 원천 파일 발견 | 원천 데이터 다운로드 |
| `raw.hmda_loans` 전체·파티션 적재 | dbt Silver/Gold 변환 |
| 필수 컬럼 검증과 적재 오류 변환 | 실행 설정, 실행 결과 모델, orchestration |
| 결정론적 합성 결함 Parquet 생성 | incident 탐지·영향 분석·remediation |

상위 application boundary는 [`data-operations.md`](data-operations.md)다. Bronze 이후 데이터 계약은 [`ARCHITECTURE`](../ARCHITECTURE.md)를 따른다.

## Source Contract

입력은 `data/raw/hmda` 아래의 파일이다.

| Item | Contract |
| --- | --- |
| Supported formats | `.csv`, `.parquet` |
| Discovery order | 파일명 오름차순 |
| Unsupported files | 발견 단계에서 제외하고 진단 로그 기록 |
| Missing directory or supported file | `HMDADataLoadError` |
| Required columns | `activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income` |
| Nullable fields | `state_code`, `county_code` 포함 모든 값은 원천 그대로 보존 |

필수 컬럼 누락은 `HMDADataValidationError`다. CSV 파싱 실패와 DuckDB 오류는 `HMDADataLoadError`로 변환한다. 적재는 원천 값의 범위나 코드값을 정규화하거나 제외하지 않는다.

## Bronze Load

대상 테이블은 `raw.hmda_loans`다. 적재 행에는 원천 컬럼과 아래 추적 필드가 함께 저장된다.

| Field | Meaning |
| --- | --- |
| `source_file` | 원천 파일 경로 |
| `source_file_name` | 원천 파일명 |
| `source_year` | 파일명에서 추출한 네 자리 연도 |
| `ingested_at` | 적재 시각 |

| API | Behavior | Return |
| --- | --- | --- |
| `discover_hmda_files(raw_dir)` | 지원 원천 파일 발견 | 정렬된 `list[Path]` |
| `load_hmda_loans(connection, source_paths)` | raw 테이블 전체를 생성 또는 교체 | 전체 행 수 `int` |
| `load_hmda_loans_partition(connection, source_paths, source_year, source_file=None)` | 연도, 선택 파일명 범위만 교체 | 대상 파티션 행 수 `int` |
| `validate_required_columns(connection, table_name=...)` | 필수 컬럼 존재 확인 | `None` 또는 검증 오류 |

전체 적재는 `CREATE OR REPLACE TABLE`을 사용하므로 같은 입력을 다시 적재해도 중복되지 않는다. 파티션 적재는 임시 테이블에서 필수 컬럼과 비어 있지 않은 행을 먼저 검증한 뒤, 기존 범위를 삭제하고 새 행을 하나의 transaction으로 삽입한다. `source_file`가 빈 문자열이거나 대상 행이 없으면 기존 파티션을 변경하지 않고 오류로 끝난다.

공개 API는 [`hmda_data/__init__.py`](../../src/project_pivot/hmda_data/__init__.py), 적재 동작은 [`tests/hmda_data`](../../tests/hmda_data)에서 확인한다.

## Synthetic Defect Cases

합성 API는 원천 파일을 읽어 `output_root` 아래에 Parquet 파일을 만든다. case name은 출력 root 밖을 가리킬 수 없으며, 입력 파일은 수정하지 않는다.

| API | Default | Generated defect |
| --- | --- | --- |
| `row_count_drop(...)` | `sample_fraction=0.1` | `activity_year`별 분포를 유지한 행 수 감소 |
| `null_spike(...)` | `target_column="income"`, `null_fraction=0.2` | 대상 컬럼 Null 비율 급증 |
| `schema_drift(...)` | `target_column="loan_amount"` | 대상 컬럼을 `VARCHAR`로 변환 |
| `freshness_delay(...)` | `delay_days=30` | 오래된 `observed_at` 열 추가 |

`sample_fraction`과 `null_fraction`은 $0 < value \leq 1$이어야 한다. 대상 컬럼이 없거나 출력 경로가 유효하지 않으면 `SyntheticCaseError`를 반환한다. 샘플은 연도별 최소 한 행을 유지하고 안정적인 컬럼 순서로 선택한다.

## Ownership Boundaries

`hmda_data`는 파일 발견, 원천 검증, Bronze 적재, 결함 입력 생성을 책임진다. `data_operations`가 이 API를 호출해 실행 설정·순서·결과를 조합한다. dbt 모델과 Bronze 이후의 grain은 `data_platform` 소유이며, 합성 파일을 활용한 품질 판단은 `reliability` 소유다.

## Reading Order

1. [`__init__.py`](../../src/project_pivot/hmda_data/__init__.py)
1. [`ingestion/__init__.py`](../../src/project_pivot/hmda_data/ingestion/__init__.py)
1. [`synthetic/__init__.py`](../../src/project_pivot/hmda_data/synthetic/__init__.py)
1. [`tests/hmda_data`](../../tests/hmda_data)

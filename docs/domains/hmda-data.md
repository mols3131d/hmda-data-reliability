# HMDA Data: Source to Bronze

**`hmda_data`는 HMDA 원천을 DuckDB Bronze로 적재하고, read-only descriptive EDA와 합성 결함 입력을 제공한다.** 원천 파일 발견·검증, descriptive evidence와 결정론적 Parquet 생성까지 소유한다.

> [!IMPORTANT]
> **Boundary:** 실행 설정·순서·결과 조합은 `data_operations`가 소유한다. `hmda_data`는 dbt 변환이나 incident 판단을 수행하지 않는다.

| In scope | Out of scope |
| --- | --- |
| CSV/Parquet 원천 파일 발견 | 원천 데이터 다운로드 |
| `raw.hmda_loans` 전체·파티션 적재 | dbt Silver/Gold 변환 |
| 필수 컬럼 검증과 적재 오류 변환 | 실행 설정, 실행 결과 모델, orchestration |
| read-only descriptive EDA evidence | incident 탐지·영향 분석·remediation |
| 결정론적 합성 결함 Parquet 생성 | reliability recovery와 evaluation |

상위 application boundary는 [`data-operations.md`](data-operations.md)다. Bronze 이후 데이터 계약은 [`ARCHITECTURE`](../ARCHITECTURE.md)를 따른다.

## Source Contract

**Input**: `data/raw/hmda` 아래의 `.csv` 또는 `.parquet` 파일을 파일명 오름차순으로 처리한다.

| Item | Contract |
| --- | --- |
| Supported formats | `.csv`, `.parquet` |
| Unsupported files | 발견 단계에서 제외하고 진단 로그 기록 |
| Required columns | `activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income` |
| Nullable fields | `state_code`, `county_code` 포함 모든 값은 원천 그대로 보존 |

| Condition | Result |
| --- | --- |
| 원천 directory가 없거나 지원 파일이 없음 | `HMDADataLoadError` |
| 필수 컬럼 누락 | `HMDADataValidationError` |
| CSV 파싱 실패 또는 DuckDB 오류 | `HMDADataLoadError` |

원천 값의 범위나 코드값은 정규화하거나 제외하지 않는다.

## Bronze Load

**Destination**: `raw.hmda_loans`에 원천 컬럼과 추적 필드를 함께 저장한다.

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
| `load_hmda_loans_partition(..., expected_identity=None, expected_max_ingested_at=None, preserve_source_metadata=False)` | 연도, 선택 파일명 범위를 content/temporal expected state로 atomic compare-and-replace | 대상 파티션 행 수 `int` |
| `partition_content_identity(connection, source_year=..., source_file=None, table_name=...)` | Partition logical row multiset의 stable identity 계산 | `PartitionContentIdentity` |
| `partition_max_ingested_at(connection, source_year=..., source_file=None, table_name=...)` | Scoped Bronze ingestion timestamp 측정 | `datetime | None` |
| `validate_required_columns(connection, table_name=...)` | 필수 컬럼 존재 확인 | `None` 또는 검증 오류 |

### Replacement Guarantees

| Load | Guarantee |
| --- | --- |
| 전체 적재 | `CREATE OR REPLACE TABLE`을 사용하므로 같은 입력을 다시 적재해도 중복되지 않는다. |
| 파티션 적재 | 임시 테이블에서 필수 컬럼과 비어 있지 않은 행을 검증한 뒤, 기존 범위를 삭제하고 새 행을 하나의 transaction으로 삽입한다. |
| Expected-state replacement | `expected_identity`가 있으면 같은 transaction 안에서 actual identity와 비교하고 다를 때 `HMDAStalePartitionError`로 zero mutation을 보장한다. |
| Temporal expected state | `expected_max_ingested_at`이 있으면 같은 transaction에서 actual `max(ingested_at)`을 비교하며 timestamp-only drift도 zero mutation으로 차단한다. |
| Metadata-preserving candidate | 명시적으로 요청된 candidate는 `source_file`, `source_file_name`, `source_year`, `ingested_at`과 target-compatible schema를 mutation 전에 검증하고 값을 재계산하지 않는다. |
| Managed writer serialization | File database의 전체·파티션 적재는 공통 database mutation lock을 획득한 뒤 target을 확인·변경한다. 파티션 actual identity와 temporal state는 lock 획득 후 transaction 안에서 다시 계산한다. |
| 빈 대상 파티션 | `source_file`가 빈 문자열이거나 대상 행이 없으면 기존 파티션을 변경하지 않고 오류로 끝난다. |

`PartitionContentIdentity`는 `table + source_year + optional source_file` scope를 포함한다. Row order와 `ingested_at`은 identity에 영향을 주지 않지만 logical value와 duplicate multiplicity는 보존한다.

Database-level lock은 서로 다른 partition을 다루는 Project Pivot managed writer도 직렬화한다. 전체 적재는 기존 validation-after-replacement failure semantics를 유지하고, 파티션 적재는 transaction commit 또는 rollback까지 lock을 유지한다. 같은 sidecar lock을 사용하지 않는 external writer와 multi-host writer는 이 serialization contract 밖이다.

공개 API는 [`hmda_data/__init__.py`](../../src/project_pivot/hmda_data/__init__.py), 적재 동작은 [`tests/hmda_data`](../../tests/hmda_data)에서 확인한다.

## Descriptive EDA

EDA는 HMDA 원천을 변경하지 않고 six-core schema compatibility, volume, null, categorical distribution, numeric summary와 complete-key grain coverage를 구조화된 evidence로 계산한다. 품질 이상을 incident로 판정하거나 원천 값을 정제하지 않는다.

상세 행동 계약은 [`hmda-data-eda-descriptive-evidence`](../../openspec/specs/hmda-data-eda-descriptive-evidence/spec.md), 동작 검증은 [`tests/hmda_data/eda`](../../tests/hmda_data/eda)에서 확인한다.

## Synthetic Defect Cases

**Output**: 합성 API는 원천 파일을 읽어 `output_root` 아래에 Parquet 파일을 만든다. case name은 출력 root 밖을 가리킬 수 없고, 입력 파일은 수정하지 않는다.

| API | Default | Generated defect |
| --- | --- | --- |
| `row_count_drop(...)` | `sample_fraction=0.1` | `activity_year`별 분포를 유지한 행 수 감소 |
| `null_spike(...)` | `target_column="income"`, `null_fraction=0.2` | 대상 컬럼 Null 비율 급증 |
| `schema_drift(...)` | `target_column="loan_amount"` | 대상 컬럼을 `VARCHAR`로 변환 |

`sample_fraction`과 `null_fraction`은 $0 < value \leq 1$이어야 한다. 대상 컬럼이 없거나 출력 경로가 유효하지 않으면 `SyntheticCaseError`를 반환한다. 샘플은 연도별 최소 한 행을 유지하고 안정적인 컬럼 순서로 선택한다.

Bronze freshness defect는 source schema에 `observed_at`을 추가하지 않는다.
[`evaluate_freshness_delay_vertical_slice`](reliability.md)는 isolated database의 existing
`ingested_at`만 변경해 측정, recovery와 replay를 검증한다. Upstream HMDA publication
timestamp와 download cadence는 여전히 이 domain의 범위 밖이다.

## Ownership And Reading Path

| Owner | Responsibility |
| --- | --- |
| `hmda_data` | 파일 발견, 원천 검증, Bronze 적재, descriptive EDA, 결함 입력 생성 |
| `data_operations` | 실행 설정·순서·결과 조합 |
| `data_platform` | dbt 모델과 Bronze 이후의 grain |
| `reliability` | profile, incident 판단과 recovery/evaluation |

구현을 따라갈 때는 [`__init__.py`](../../src/project_pivot/hmda_data/__init__.py)에서 공개 API를 확인한 뒤 [`ingestion/__init__.py`](../../src/project_pivot/hmda_data/ingestion/__init__.py), [`eda/__init__.py`](../../src/project_pivot/hmda_data/eda/__init__.py), [`synthetic/__init__.py`](../../src/project_pivot/hmda_data/synthetic/__init__.py), [`tests/hmda_data`](../../tests/hmda_data) 순으로 읽는다.

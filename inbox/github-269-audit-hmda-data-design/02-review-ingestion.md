---
type: review
title: HMDA Ingestion Current Test Design Review
description: 현행 ingestion 테스트 2개 모듈을 계약·시나리오·독립 oracle과 대조하고 역사적 finding의 처분 및 회귀 보호 근거를 기록합니다.
---

# HMDA Ingestion Current Test Design Review

현행 ingestion의 2개 테스트 모듈, 33개 test function을 전수 검토했다. 역사적 H2는 현행 파일별 검증과 회귀 테스트로 이미 해결되어 `obsolete`로 판정했다. H3·H4·H7은 현행 production defect가 아닌 test design gap으로 수용하고 회귀 보호를 추가했다. 실제 DuckDB를 사용한 focused suite는 49개 case가 통과했다.

- **Target:** HMDA ingestion의 discovery/full load 및 partition/identity/freshness 테스트.
- **Revision:** `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`을 반영한 audit merge `150d565a6be06bc71ca0c446ad26e8143523d780`과 이 문서가 설명하는 테스트 변경. 최종 commit·CI 결과는 [최종 보고서](05-report-hmda-data-audit.md)에서 별도로 고정한다.
- **Scope:** 아래 두 테스트 모듈 전수 검토와 허용된 회귀 보호. Production source, Spec, configuration과 다른 도메인 테스트는 수정하지 않았다.

## Coverage And Evidence

| Surface | Reviewed Files | Assessment |
| --- | --- | --- |
| Authored tests | [Full/discovery](../../tests/hmda_data/test_ingestion.py), [partition/identity/freshness](../../tests/hmda_data/test_ingestion_partition.py) | 모든 33개 test function의 setup, assertion, failure path와 parameterization을 대조했다. 아래 inventory에 제외 없이 연결했다. |
| Source discovery/full load | [discovery.py](../../src/hmda_reliability/hmda_data/ingestion/discovery.py), [full_load.py](../../src/hmda_reliability/hmda_data/ingestion/full_load.py), [_source_query.py](../../src/hmda_reliability/hmda_data/ingestion/_source_query.py), [_common.py](../../src/hmda_reliability/hmda_data/ingestion/_common.py) | reader, 파일별 필수 컬럼 검사, validation-after-replacement와 lock 획득 위치를 확인했다. |
| Partition/public state API | [partition.py](../../src/hmda_reliability/hmda_data/ingestion/partition.py), [identity.py](../../src/hmda_reliability/hmda_data/ingestion/identity.py), [exports](../../src/hmda_reliability/hmda_data/ingestion/__init__.py), [errors.py](../../src/hmda_reliability/hmda_data/errors.py) | staging → validation → expected-state 검사 → DELETE/INSERT → commit/rollback → cleanup을 추적했다. |
| Contract | [Ingestion Spec](../../openspec/specs/hmda-data-ingestion/spec.md) | discovery, source validation, provenance, scoped replacement, identity, outlier preservation, mutation serialization, freshness와 metadata-preserving candidate를 대조했다. |
| Read-only support | [fixtures](../../tests/hmda_data/conftest.py), [DuckDB primitive](../../src/hmda_reliability/data_platform/duckdb.py), [primitive tests](../../tests/data_platform/test_duckdb.py) | 고정 작은 입력의 독립 기대값과 canonical lock semantics를 확인했다. 공유 primitive 테스트는 수정하거나 이 focused 실행의 통과로 계산하지 않았다. |
| Historical evidence | [H2/H3/H4/H7 mapping](01-review-historical/hmda-data/README.md), [Ingestion F1–F4](01-review-historical/hmda-data/ingestion.md) | 과거 재현 결과를 현행 defect로 전용하지 않고 다음 처분으로 갱신했다. |

## Historical Finding Disposition

| ID | Historical Finding | Disposition | Current Evidence And Action |
| --- | --- | --- | --- |
| H2 / F1 | 여러 파일의 필수 컬럼 누락을 `UNION ALL BY NAME`이 가린다. | `obsolete` | [_common.py](../../src/hmda_reliability/hmda_data/ingestion/_common.py)의 `validate_source_required_columns`가 각 파일을 동일 reader로 검사한다. full·partition의 `test_*rejects_missing_source_columns*`는 CSV/CSV, Parquet/Parquet, CSV/Parquet, Parquet/CSV × 두 입력 순서의 16개 case에서 정확한 누락 컬럼과 경로를 검사한다. Full의 교체 후 실패와 partition의 전체 행 보존도 각각 검증한다. 중복 테스트를 추가하지 않았다. |
| H3 / F2 | DELETE 뒤 INSERT 실패의 rollback 검출력이 없다. | `accepted` | [Partition replacement / Failed partition replacement](../../openspec/specs/hmda-data-ingestion/spec.md#requirement-partition-replacement)에 연결한다. `test_partition_insert_failure_rolls_back_deleted_rows`는 두 연도의 3행을 적재한 실제 DuckDB에 UNIQUE index를 만들고, 새 입력 내부의 중복 금액으로 실제 INSERT를 실패시킨다. `ConstraintException` cause, 두 연도의 값·provenance 전체 보존, staging 제거를 검사한다. Domain 함수를 mock하지 않았다. Transaction 제거 negative control은 전체 행 보존 assertion에서 실패했다. |
| H4 / F3 | 파일 하나를 교체할 때 같은 연도 sibling 손실을 놓친다. | `accepted` | [File-scoped reload](../../openspec/specs/hmda-data-ingestion/spec.md#requirement-partition-replacement)에 연결한다. `test_file_scoped_reload_preserves_same_year_sibling`는 같은 연도 A/B를 먼저 저장한 뒤 A만 변경한다. A의 정확한 새 값과 B의 모든 행·provenance를 비교한다. DELETE에서 file predicate를 제거한 negative control은 sibling 보존 assertion에서 실패했다. |
| H7 / F4 | fake lock이 실제 DB path 전달 오류를 가린다. | `accepted` | [Serialized managed Bronze mutation](../../openspec/specs/hmda-data-ingestion/spec.md#requirement-serialized-managed-bronze-mutation)에 연결한다. `test_loaders_use_canonical_database_lock_before_mutation[full/partition]`는 실제 file DB를 symlink로 열고 canonical lock file 위치를 directory로 막는다. 실제 획득 실패의 domain error와 전체 행 보존을 확인한다. 각 loader가 DB path 대신 `None`을 넘기는 negative control은 기대 domain error를 발생시키지 않아 실패했다. |

이 네 historical finding 중 `rejected` 또는 `deferred` 판정은 없다. H3·H4·H7의 원래 지적은 production 구현 오류를 입증하지 않았다. 이번 테스트와 negative control도 현행 구현의 결함을 주장하는 근거로 사용하지 않는다.

## Scenario And Oracle Inventory

모든 테스트의 primary level은 `component`다. 임시 source 파일과 실제 local DuckDB가 source-to-Bronze 계약을 입증한다. 아래 이름은 해당 [full/discovery 모듈](../../tests/hmda_data/test_ingestion.py) 또는 [partition 모듈](../../tests/hmda_data/test_ingestion_partition.py)의 실제 function 이름이다.

### Discovery And Full Load

| Test | Scenario / Risk | Independent Oracle / Assessment |
| --- | --- | --- |
| `test_discover_hmda_files_filters_supported_files` | Normal: CSV·Parquet·unsupported 혼합과 순서 비결정성 | 정확한 두 Path의 정렬 목록. 정상이다. |
| `test_discover_hmda_files_rejects_missing_directory` | Failure: 없는 root가 빈 성공으로 변환됨 | `HMDADataLoadError`와 원천 디렉터리 메시지. 정상이다. |
| `test_load_hmda_loans_loads_csv_and_parquet_idempotently` | Normal/regression: 두 format 혼합과 재실행 누적 | 고정 3행·2파일·2024/2025·non-null timestamp SQL tuple. 정상이다. |
| `test_load_hmda_loans_creates_custom_target_schema` | Boundary: 새 DB의 configured schema | 반환 2행과 information schema의 정확한 target. 정상이다. |
| `test_load_hmda_loans_rejects_multipart_target_table` | Failure: 지원 범위 밖 target name | 구체적인 domain error. Source에 명시된 지원 범위를 보호한다. |
| `test_load_hmda_loans_partition_after_full_load` | Integration within component: full 뒤 partition의 공통 Bronze schema | 정확한 3행·2파일·연도 범위. 값 순서 회귀는 partition의 재정렬 사례가 보완한다. |
| `test_load_hmda_loans_wraps_duckdb_errors` | Failure: missing CSV의 외부 reader 오류 | 실제 missing file의 `HMDADataLoadError`. Mock하지 않는다. |
| `test_load_hmda_loans_validates_required_columns` | Failure: 단일 source의 필수 컬럼 누락 | validation exception과 교체 후 target에서 `income` 부재. Full의 기존 failure semantics를 유지한다. |
| `test_full_load_rejects_missing_source_columns_after_replacing_target` | Regression: format·순서에 따라 누락 schema가 가려짐 | 8개 case의 정확한 누락 컬럼·경로와 교체 후 2행의 고정 값·provenance. H2가 기해결임을 증명한다. |
| `test_full_load_accepts_null_values_in_valid_csv_parquet_sources` | Boundary: 구조상 존재하는 nullable 값 | 구조 누락과 구별하여 두 행의 `None`, 코드와 provenance를 정확히 비교한다. |
| `test_load_hmda_loans_translates_mutation_lock_failure` | Failure: lock 획득 전 최초 target 생성 | 외부 lock error만 주입하여 domain error와 target 부재를 검사한다. 기존 경계 검사로 유지한다. |
| `test_loaders_use_canonical_database_lock_before_mutation` | Regression/failure: symlink DB와 실제 canonical lock 위치 연결 | full·partition 각 case에서 실제 lock 획득 실패와 모든 기존 행·timestamp 보존. H7을 보강했다. |
| `test_load_hmda_loans_rejects_malformed_csv_rows` | Failure: 열 개수가 다른 CSV 행이 조용히 버려짐 | 실제 malformed CSV가 load 또는 validation error로 실패. Spec이 허용하는 두 domain error만 받는다. |

### Partition, Identity And Freshness

| Test | Scenario / Risk | Independent Oracle / Assessment |
| --- | --- | --- |
| `test_load_hmda_loans_partition_filters_by_source_year` | Normal: 여러 연도 중 요청 범위만 선택 | 반환 2행과 정확한 연도 통계. 정상이다. |
| `test_load_hmda_loans_partition_is_idempotent` | Regression: 재적재가 append로 변함 | 두 번의 반환값 2와 최종 정확한 2행. 정상이다. |
| `test_partition_load_rejects_missing_source_columns_without_changing_rows` | Failure/regression: 파일별 누락을 다른 원천이 가림 | 8개 case에서 정확한 validation context와 대상·다른 연도의 모든 기존 행 보존. H2는 기해결이다. |
| `test_partition_load_accepts_null_values_in_valid_csv_parquet_sources` | Boundary: 실제 null과 구조 누락의 혼동 | 두 format의 고정 값·null·provenance tuple. 정상이다. |
| `test_partition_load_validates_empty_requested_year_source_before_row_count` | Boundary/failure: 빈 요청 연도 파일의 누락이 다른 연도 schema에 가림 | 실제 empty Parquet의 정확한 누락 컬럼·경로와 전체 target 불변. 정상이다. |
| `test_partition_load_rejects_empty_requested_year_with_valid_source_columns` | Boundary/failure: 정상 schema지만 요청 연도가 0행 | 정확한 non-empty domain error와 두 연도 전체 행 보존. 앞 사례와 다른 validation 경계를 검사한다. |
| `test_partition_reload_preserves_values_after_source_columns_are_reordered` | Regression: positional INSERT가 같은 type의 값을 뒤바꿈 | `(350000,120)`, `(420000,95)` 고정 값과 다른 연도 전체 행 보존. 정상이다. |
| `test_partition_insert_failure_rolls_back_deleted_rows` | Failure/regression: 파괴적 DELETE 뒤 storage INSERT 실패 | 실제 UNIQUE constraint failure cause, 3행 전체 상태와 staging 부재. H3을 보강했다. |
| `test_file_scoped_reload_preserves_same_year_sibling` | Regression: file predicate 누락으로 sibling 삭제 | 요청 파일의 정확한 새 값과 sibling 2행 전체 상태. H4를 보강했다. |
| `test_partition_content_identity_tracks_logical_row_multiset` | Invariant: row order·volatile time 독립성, value·duplicate 구별 | 재정렬/시각 변경 identity는 같고 단일 값 변경·중복 추가는 다름. Production digest를 재구현하지 않는 metamorphic oracle이다. |
| `test_partition_load_compares_expected_identity_before_replacement` | Normal/failure: matching content-only 교체와 stale 거부 | matching 교체 후 identity 변화, 같은 old identity의 재사용 거부와 새 identity 보존. Content-only compatibility도 보호한다. |
| `test_partition_load_rechecks_identity_after_waiting_for_writer` | Concurrency: 같은 before identity의 후행 writer | 두 연결·thread와 제어된 외부 lock 아래 후행 요청 하나만 stale. 실제 primitive/path composition의 증거는 H7 테스트와 분리한다. |
| `test_partition_load_compares_expected_freshness_before_replacement` | Failure: content가 같아도 timestamp만 drift | 정확한 고정 timestamp와 rejection 전후 모든 값·provenance 보존. 이번 변경에서 전체 행 oracle을 강화했다. |
| `test_partition_load_preserves_approved_bronze_metadata` | Normal: content와 temporal state가 모두 matching인 approved candidate | 승인된 시각·원래 filename에 더해 모든 원본 행·4개 provenance의 exact equality를 추가했다. `source_file` 변경과 일부 행 timestamp 손실도 검출한다. |
| `test_partition_load_rejects_invalid_preserved_candidate_before_mutation` | Failure: missing provenance 또는 target와 incompatible schema | 기존 missing-time case를 유지하고 amount type이 VARCHAR인 candidate를 추가했다. Domain rejection, content identity 및 timestamp를 포함한 전체 행 불변을 검사한다. |
| `test_partition_load_creates_custom_target_schema` | Boundary: 새 DB의 configured schema | 정확한 반환 2행과 `bronze.hmda_loans` 존재. 정상이다. |
| `test_partition_load_rejects_multipart_target_table` | Failure: 지원 범위 밖 target name | 구체적인 domain error. Source의 지원 범위와 일치한다. |
| `test_load_hmda_loans_partition_filters_by_source_file` | Normal: 빈 target에서 file-scoped 선택 | 반환 1행과 정확한 단일 filename. Persisted sibling 보존은 H4의 별도 회귀 사례가 맡는다. |
| `test_load_hmda_loans_partition_preserves_outlier_rows` | Boundary: unknown code·큰 금액·음수 소득의 품질 정규화 | 사람이 계산 가능한 정확한 `(99,999999999999,-10,"ZZ",99999)`을 보존한다. |
| `test_load_hmda_loans_partition_handles_empty_source_file` | Boundary/failure: empty string scope가 SQL binding 오류가 됨 | empty scope를 non-empty check의 명시적 domain error로 처리한다. 정상이다. |

## New Oracle Hardening

Historical gap 외에 metadata-preserving candidate의 schema compatibility에는 requirement가 있지만 직접 거부 사례가 없었다. 기존 missing-provenance test를 2개 case로 확장해 `loan_amount` type이 다른 Parquet를 target mutation 전에 거부하도록 검증했다. 실제 source 값의 type 추론을 mock하지 않고 고정 SQL projection으로 candidate만 만든다.

Identity는 의도적으로 `ingested_at`을 제외한다. 따라서 identity equality만으로 zero mutation을 선언하면 timestamp 손실을 놓친다. Temporal-only stale rejection과 invalid candidate rejection은 전체 행 비교를 보완했고, 정상 approved candidate도 모든 값·provenance가 보존되는지 확인했다. 기대 상태는 사전 저장된 실제 행이며 loader 알고리즘을 복제하지 않는다.

## Validation

아래 검사는 audit merge `150d565a` 위의 본 문서 테스트 변경에 대해 worktree 전용 locked environment에서 수행했다. 기존 154개 도메인 baseline 결과는 coordinator가 소유하며 이 문서의 focused 결과에 합산하지 않는다. 개별 모듈의 변경 전 case 수는 별도로 실행하지 않아 추정하지 않는다.

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Focused suite | `uv run --no-sync pytest tests/hmda_data/test_ingestion.py tests/hmda_data/test_ingestion_partition.py` — **49 passed in 6.24s**. Full/discovery 21개, partition 28개 case. |
| ✅ Pass | Lint | `uv run --no-sync ruff check tests/hmda_data/test_ingestion.py tests/hmda_data/test_ingestion_partition.py` — Pass. |
| ✅ Pass | Format | `uv run --no-sync ruff format --check tests/hmda_data/test_ingestion.py tests/hmda_data/test_ingestion_partition.py` — Pass, 2 files already formatted. |
| ✅ Pass | Type | `uv run --no-sync ty check tests/hmda_data/test_ingestion.py tests/hmda_data/test_ingestion_partition.py` — Pass. |
| ✅ Pass | Whitespace | `git diff --check -- tests/hmda_data/test_ingestion.py tests/hmda_data/test_ingestion_partition.py` — Pass. |
| ✅ Pass | Review Markdown | `uv run --no-sync rumdl check inbox/github-269-audit-hmda-data-design/02-review-ingestion.md` — Pass. |

### Bounded Negative Controls

실제 production 파일은 수정하지 않았다. `uv run --no-sync python -`으로 테스트 모듈과 fixture를 import하고, control마다 별도 `TemporaryDirectory`에서 `unittest.mock.patch.object`로 process 안에서만 다음 회귀를 만들었다. 현재 test function을 직접 호출하고 의도한 exception 또는 상태 assertion 실패를 확인했다. 이 control은 test의 검출력을 확인한 실험이며 정상 suite의 실패나 현행 production defect가 아니다.

| Control | Exact Temporary Mutation | Test Invocation | Observed Detection |
| --- | --- | --- | --- |
| Transaction removed | `partition._replace_partition_in_transaction`을 `connection`, `table_name`, `source_year`, `source_file`만 `_replace_partition_rows`에 전달하는 함수로 대체한다. BEGIN/COMMIT/ROLLBACK만 생략한다. | `test_partition_insert_failure_rolls_back_deleted_rows(csv_path, parquet_path)` | `AssertionError`: 기존 연도 2025 행이 사라져 `after == before`가 실패한다. |
| File predicate removed | `partition._replace_partition_rows`를 `DELETE FROM raw.hmda_loans WHERE source_year = ?` 뒤 `INSERT INTO raw.hmda_loans BY NAME SELECT * FROM __hmda_loans_partition_stage`를 실행하는 함수로 대체한다. | `test_file_scoped_reload_preserves_same_year_sibling(csv_path, tmp_path)` | `AssertionError`: sibling 2행이 사라져 전체 행 비교가 실패한다. |
| Full-load DB path lost | `full_load.current_database_path = lambda connection: None`으로 대체한다. | `test_loaders_use_canonical_database_lock_before_mutation(csv_path, tmp_path, False)` | `Failed: DID NOT RAISE HMDADataLoadError`. |
| Partition DB path lost | `partition.current_database_path = lambda connection: None`으로 대체한다. | `test_loaders_use_canonical_database_lock_before_mutation(csv_path, tmp_path, True)` | `Failed: DID NOT RAISE HMDADataLoadError`. |
| Candidate schema check bypassed | `partition._validate_preserved_metadata = lambda connection, table_name: None`으로 대체한다. | `test_partition_load_rejects_invalid_preserved_candidate_before_mutation(csv_path, tmp_path, '* REPLACE (CAST(loan_amount AS VARCHAR) AS loan_amount)')` | `Failed: DID NOT RAISE HMDADataLoadError`: DuckDB의 정상 cast로 INSERT가 성공하는 것을 test가 잡는다. |

`csv_path`와 `parquet_path`는 각 control의 임시 directory에서 [기존 fixture](../../tests/hmda_data/conftest.py)의 `hmda_csv_path.__wrapped__`와 `hmda_parquet_path.__wrapped__`로 생성했다. 모든 patch는 control 종료 시 복원했다. Committed 테스트에는 domain 함수 대체를 추가하지 않았다.

## Remaining Boundaries And Handoff

현행 production defect 또는 Spec 충돌을 재현한 항목은 없다. Full-load의 validation-after-replacement는 명시된 현행 계약이므로 partition과 같은 rollback으로 바꾸지 않았다.

| Item | Disposition | Evidence / Next Owner |
| --- | --- | --- |
| Managed writers의 실제 공통 lock lifetime | `deferred` to [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277) | 현행 partition의 fake-lock stale 재검사, 실제 canonical lock 경로 거부, 별도 Data Platform primitive의 alias 직렬화는 각각 보호한다. 실제 full-load·다른 partition·dbt/recovery writer를 조합해 commit/rollback 또는 validation failure까지 공통 lock을 유지하는 실행은 이 focused suite에서 입증하지 않는다. [Serialized managed Bronze mutation](../../openspec/specs/hmda-data-ingestion/spec.md#requirement-serialized-managed-bronze-mutation) 및 [DuckDB primitive tests](../../tests/data_platform/test_duckdb.py)를 기초로 마지막 cross-domain PR에서 실제 writer의 임계구역이 겹치지 않는 oracle을 추가한다. Production defect를 주장하는 handoff는 아니다. |
| 지원 파일이 없는 root, unsupported/empty explicit source set, 없는 target의 empty identity | `excluded` from new hardening | 관련 [discovery](../../src/hmda_reliability/hmda_data/ingestion/discovery.py), [path validation](../../src/hmda_reliability/hmda_data/ingestion/_source_query.py), [identity](../../src/hmda_reliability/hmda_data/ingestion/identity.py)의 source 경로를 읽었다. 현재 두 모듈에는 각각의 독립 case가 없으므로 실행 검증 완료로 선언하지 않는다. Historical high-impact gap을 해결하는 본 변경에서 새로운 API나 model test matrix를 만들지 않았다. |
| Identity hash 충돌·자원 상한·분산 writer | `excluded` | 현행 계약의 local correctness 검토 범위를 벗어난다. 이번 검사는 성능·OOM·분산 환경·실제 HMDA 전체 원천에 대한 증거가 아니다. |

독립 최종 review와 도메인 전체 실행, PR head·prospective merge CI 확인은 coordinator가 이어서 수행한다. 이 문서의 local pass는 Draft 해제, 승인 또는 merge 권한을 의미하지 않는다.

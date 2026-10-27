---
type: review
title: HMDA Synthetic Contract and Test Audit
description: 현재 synthetic 원본 보존·희소 연도 sampling·null 주입·schema drift 계약과 모든 기존 테스트를 대조하고 후속 구현 문제를 구분합니다.
---

# HMDA Synthetic Contract and Test Audit

> [!NOTE]
> H1의 원본 삭제 문제는 현재 구현과 회귀 테스트에서 해소됐다. H8은 독립적인 희소 연도 oracle과 negative control로 보강했다. 기존 source의 physical-type 미변경 문제와 `activity_year` target의 Spec 해석 문제는 [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277) 후속 범위로 남긴다.

- **Target:** PR [#269](https://github.com/mols3131d/hmda-data-reliability/pull/269)의 synthetic test audit.
- **Revision:** `150d565a6be06bc71ca0c446ad26e8143523d780`에 아래 test 보강을 적용한 working tree. 이 head에는 main `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`이 merge되어 있다.
- **Scope:** [test_synthetic.py](../../tests/hmda_data/test_synthetic.py)의 26개 test function, [synthetic source](../../src/hmda_reliability/hmda_data/synthetic/), [canonical Spec](../../openspec/specs/hmda-data-synthetic-defects/spec.md), [historical synthetic review](01-review-historical/hmda-data/synthetic.md). Production·Spec·configuration은 수정하지 않았다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Major | `schema_drift`가 기존 `VARCHAR` target을 같은 type으로 출력하고 성공한다 | #277에서 실제 physical-type 변경 또는 명시적 거부 정책을 정하고 회귀 검증 |
| F2 | Note | `activity_year` target의 거부 조건은 Spec 문장과 scenario의 범위가 다르다 | #277에서 override 미지정 요청의 계약을 먼저 확정 |

두 항목 모두 이번 test 보강이 만든 regression이 아니다. 성공하는 현재 동작을 정답으로 고정하거나 알려진 실패 test를 추가하지 않고 임시 데이터 probe로 관측했다.

## Historical Disposition

| ID | Disposition | Current Evidence | Resolution |
| --- | --- | --- | --- |
| H1 | `obsolete` | 삭제 전 실제 reader glob과 resolved path·중간 symlink entry를 확인한다. 기존 overlap 45개, Parquet 재사용 3개, 정상 sibling 교체 9개가 source bytes와 기존 output 보존을 확인한다 | 과거 결함은 유효했지만 현재 source에서 해결됐다. 기존 회귀 57개를 유지했다 |
| H8 | `accepted` | 과거 row-drop oracle에 한 행짜리 연도와 dense 연도를 함께 검증하는 직접 assertion이 없었다 | 1행·4행의 두 연도에 fraction `0.01`, `0.5`, `1.0`을 적용해 exact output 3개를 추가했다. 연도 partition 제거 mutation을 탐지했다 |

H1의 active Change는 이미 완료된 별도 구현 근거이며 이 audit의 수정 대상이 아니다. 역사 문서를 현재 결함 목록으로 덮어쓰지 않았다.

## Contract and Source Coverage

| File | Contract and Source Assessment | Executable Evidence or Limit |
| --- | --- | --- |
| [Spec](../../openspec/specs/hmda-data-synthetic-defects/spec.md) | 격리·원본 불변, 연도별 최소 한 행, strict null 증가, target-year·filename 일치, physical-type 변경을 각각 대조했다 | 아래 test matrix와 F1·F2로 각 requirement의 근거와 한계를 분리했다 |
| [cases.py](../../src/hmda_reliability/hmda_data/synthetic/cases.py) | 실제 연도별 ranking·sampling, non-null 우선 sampling, 정수 기반 strict-increase 계산, target-year·ASCII filename 검증, `VARCHAR` cast를 확인했다 | 정상·최소/최대 비율·희소 연도·높은 null baseline·invalid fraction·연도 경계가 실행된다. 기존 target이 이미 `VARCHAR`인 경우는 F1 |
| [_writer.py](../../src/hmda_reliability/hmda_data/synthetic/_writer.py) | 단일 case name, 삭제 전 source path 검증, 기존 case 교체, 실제 `COPY`, domain exception과 원인 보존을 확인했다 | 직접/상대/glob/다중 symlink overlap, sibling 정상 교체, traversal 거부, 실제 query failure의 source bytes 보존을 실행했다 |
| [_source.py](../../src/hmda_reliability/hmda_data/synthetic/_source.py) | CSV·Parquet reader, `UNION ALL BY NAME`, required-column·빈 source·확장자 guard와 schema-error wrapping을 확인했다 | CSV 정상·재사용 Parquet·missing-column·실제 missing-file은 실행된다. 빈 source/unsupported format과 모든 DuckDB error branch의 별도 fault injection은 이번 보강에 포함하지 않았다 |
| [__init__.py](../../src/hmda_reliability/hmda_data/synthetic/__init__.py) | 세 public generator export를 확인했다 | 테스트는 public HMDA Data export로 generator를 호출한다 |

## Test Matrix

아래 표는 현재 [test_synthetic.py](../../tests/hmda_data/test_synthetic.py)의 모든 test function을 포함한다. `Cases`는 parameter expansion 후 개수이며 합계는 114다. 실제 로컬 DuckDB·CSV·Parquet 경계를 사용하므로 기본 `component` marker를 유지했다.

| Test | Cases | Scenario and Independent Oracle | Change |
| --- | ---: | --- | --- |
| `test_synthetic_case_preserves_sources_inside_case_directory` | 45 | 5종 generator/name × 9종 경로에서 요청 거부 후 입력·외부 실제 source·이전 output의 bytes 보존 | 유지 |
| `test_synthetic_case_preserves_source_when_reusing_its_parquet_output` | 3 | 각 generator의 기존 Parquet을 동일 case 입력으로 재사용하면 거부하고 bytes 보존 | 유지 |
| `test_synthetic_case_replaces_output_without_changing_sibling_source` | 9 | sibling·glob·symlink-parent 입력은 허용하고 이전 case의 stale 파일만 제거하며 rows·source bytes 보존 | 유지 |
| `test_synthetic_cases_expose_expected_defect_statistics` | 1 | 2행 fixture의 row drop 1행, 원본보다 높은 null ratio, output `VARCHAR`를 실제 Parquet에서 조회 | 유지. 모든 source type의 drift를 보장하지는 않음 |
| `test_row_count_drop_preserves_sparse_year_with_exact_rows` | 3 | 2024년 1행·2025년 동일한 4행에서 최소 sampling, 절반, 전체의 exact rows를 수동 기대값으로 비교 | 추가 |
| `test_null_spike_full_fraction_preserves_rows_and_other_columns` | 1 | 기존 null 1행과 non-null 2행을 포함한 두 연도에 fraction 1을 적용하고 모든 target만 null인 exact rows 확인 | 추가 |
| `test_null_spike_increases_high_baseline_null_rate` | 1 | baseline 9/10 null에서 마지막 non-null도 null로 바뀌어 strict increase | 유지 |
| `test_null_spike_partial_sample_exceeds_original_null_rate` | 1 | baseline 1/2와 2행 sample을 직접 비교해 원본 대비 strict increase | 유지 |
| `test_null_spike_partial_sample_strict_increase_with_non_binary_exact_ratio` | 1 | baseline 70/100·sample 90행에서 정수 cross-product로 strict inequality 확인 | 유지 |
| `test_null_spike_rejects_all_null_target_without_output` | 1 | 증가 불가능한 입력을 거부하고 case directory 부재 | 유지 |
| `test_null_spike_distributes_mutations_across_years` | 1 | 두 연도 각각 최소 요청 개수의 null이 존재 | 유지 |
| `test_null_spike_requested_fraction_magnitude` | 1 | 10행·20행 연도에서 fraction 0.3의 최소 null 수 확인 | 유지 |
| `test_synthetic_case_rejects_missing_columns` | 2 | 존재하지 않는 target을 null spike와 schema drift 모두 domain error로 거부 | schema drift 추가 |
| `test_synthetic_case_rejects_invalid_fraction_without_output` | 20 | 4종 fraction 인자 × 0·음수·1 초과·NaN·무한대를 거부하고 output 부재·source bytes 보존 | 추가 |
| `test_row_count_drop_is_invariant_to_input_order_for_partial_key_ties` | 1 | partial key가 같은 distinct rows의 행·컬럼 순서를 뒤집어도 선택한 `loan_type` 일치 | 유지 |
| `test_row_count_drop_wraps_source_schema_failure` | 1 | 실제 존재하지 않는 CSV의 schema 조회를 domain error로 노출 | 유지 |
| `test_write_case_file_rejects_unsafe_case_name` | 6 | 빈 이름·`.`·`..`·상위 경로·중첩 경로·절대 경로를 거부하고 외부 sentinel bytes와 output 부재 확인 | 기존 parent-only test 확장 |
| `test_write_case_file_wraps_query_failure_without_changing_source` | 1 | 실제 invalid SQL의 `COPY` 실패를 domain error로 노출하고 원래 DuckDB 원인·source bytes 보존 | 추가 |
| `test_null_spike_supports_target_year_override` | 3 | 2000·2026·2100의 허용 연도에서 output filename·실제 연도·null 비율 확인 | 양 끝 연도 추가 |
| `test_null_spike_rejects_activity_year_target_column_with_target_year` | 1 | override와 key null 주입의 상호 모순을 거부 | 유지. override 미지정은 F2 |
| `test_null_spike_rejects_case_name_without_target_year_when_target_year_is_set` | 1 | ASCII 연도 부재와 다른 첫 연도를 각각 거부 | 유지 |
| `test_null_spike_rejects_case_name_with_conflicting_first_year` | 1 | 첫 연도가 target과 다르면 거부하고 output root 부재 | output 부재 assertion 추가 |
| `test_null_spike_rejects_case_name_with_non_ascii_year` | 1 | ingestion이 읽지 못하는 전각 숫자 연도를 거부하고 output root 부재 | output 부재 assertion 추가 |
| `test_null_spike_allows_case_name_with_matching_first_year` | 1 | 첫 연도만 일치하는 custom name을 실제 partition ingestion에 연결하고 `source_year` 확인 | 유지 |
| `test_null_spike_rejects_invalid_target_year` | 6 | 범위 밖·bool·문자열 연도를 거부 | 유지 |
| `test_null_spike_rejects_multi_year_source_with_target_year` | 1 | 다중 연도 collapse 요청을 거부 | 유지 |

희소 연도 test는 dense 연도에 동일한 행을 사용해 구현의 MD5 정렬을 oracle에 복제하지 않는다. 임의 hash 선택과 무관하게 값과 multiplicity를 직접 비교하며 distinct-row 선택 결정성은 기존 input-order regression이 별도로 담당한다. Null 증가의 cross-product와 비율 최소값은 observable 계약만 계산하며 production의 SQL threshold식을 복사하지 않는다.

## Details

### F1 — Major: Unchanged Physical Type

#### Locations: F1

- [cases.py](../../src/hmda_reliability/hmda_data/synthetic/cases.py)
  - `schema_drift`는 target을 항상 `VARCHAR`로 cast한다.
- [Spec](../../openspec/specs/hmda-data-synthetic-defects/spec.md)
  - `Schema drift case`와 `Loan amount type drift`는 원본과 다른 physical type을 요구한다.
- [test_synthetic.py](../../tests/hmda_data/test_synthetic.py)
  - 기존 통계 test는 output이 `VARCHAR`인지만 확인하여 원본도 `VARCHAR`인 경우를 보호하지 못한다.

#### Evidence: F1

아래 공통 재현의 숫자 문자열을 가진 Parquet source에서 `schema_drift`는 예외 없이 결과를 반환했다. 조회한 source와 output type은 모두 `VARCHAR`였다. Malformed CSV나 mocked reader에 의존하지 않는다.

#### Impact: F1

생성 성공이 실제 schema incompatibility를 의미하지 않아 synthetic 결함을 사용한 후속 검증에서 false green이 생길 수 있다. 이 입력을 거부할지 다른 physical type으로 변환할지 정하는 source 변경은 현재 test-only write 범위 밖이다.

#### Action: F1

[#277](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 이미 `VARCHAR`인 target의 계약을 정하고 원본/output type을 직접 대조하는 회귀를 구현과 함께 추가한다. 이번 PR은 실패를 정상으로 고정하는 test나 source 수정을 포함하지 않는다.

### F2 — Note: Activity-Year Target Scope

#### Locations: F2

- [Spec](../../openspec/specs/hmda-data-synthetic-defects/spec.md)
  - `Null spike case` 문장은 `target_column == "activity_year"` 요청을 거부하도록 서술한다.
  - `Reject target column activity year with target year` scenario는 `target_year` 동시 지정으로 조건을 한정한다.
- [cases.py](../../src/hmda_reliability/hmda_data/synthetic/cases.py)
  - `_validate_target_year_and_case_name`은 `target_year is None`이면 target 검증 전에 반환한다.

#### Evidence: F2

아래 재현에서 override를 생략하고 `activity_year`를 target으로 지정하면 요청이 성공하며 연도 중 하나가 `NULL`이 된다. Source type 문제와 독립적인 관측이다.

#### Impact: F2

상위 requirement 문장에 따르면 거부 대상이지만 scenario와 구현은 동시 지정만 금지한다. 이 관측만으로 override 없는 요청의 최종 정답을 확정하지 않는다.

#### Action: F2

[#277](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 override 없는 `activity_year` null 주입을 허용할지 결정하고 Spec·source·test를 함께 정합화한다. 이번 audit에서는 모호한 계약을 추측해 red test나 현 동작 승인 test를 남기지 않았다.

### Reproduction

Repository root의 준비된 환경에서 실행한다. 모든 데이터와 output은 자동 정리되는 임시 directory 안에 있다.

```bash
uv run --no-sync python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.hmda_data import schema_drift, null_spike

with TemporaryDirectory() as directory:
    root = Path(directory)
    source = root / "source_2025.parquet"
    with DuckDBConnectionManager() as connection:
        connection.execute(
            "COPY (SELECT 2025 AS activity_year, '100000'::VARCHAR AS loan_amount, "
            "80 AS income UNION ALL SELECT 2025, '200000', 90) TO ? (FORMAT PARQUET)",
            [str(source)],
        )
        output = schema_drift(connection, [source], root / "cases")
        for label, path in [("source", source), ("output", output)]:
            row = connection.execute(
                "DESCRIBE SELECT loan_amount FROM read_parquet(?)", [str(path)]
            ).fetchone()
            print(label, row[1])
        output = null_spike(
            connection, [source], root / "year-cases", target_column="activity_year"
        )
        print(connection.execute(
            "SELECT activity_year, loan_amount FROM read_parquet(?) ORDER BY loan_amount",
            [str(output)],
        ).fetchall())
PY
```

관측값은 `source VARCHAR`, `output VARCHAR`, `[(2025, '100000'), (None, '200000')]`였다.

### Negative Control

별도 Python process에서 `_ranked_sample_query`의 반환 SQL에 한해 `PARTITION BY activity_year`를 제거한 뒤 새 희소 연도 test 3개를 실행했다. Production 파일이나 committed test에 mutation을 적용하지 않았다.

```python
import pytest
from hmda_reliability.hmda_data.synthetic import cases

class GlobalSamplingMutation:
    def pytest_sessionstart(self, session):
        original = cases._ranked_sample_query
        def global_ranks(connection, source_paths):
            return original(connection, source_paths).replace(
                "PARTITION BY activity_year", ""
            )
        cases._ranked_sample_query = global_ranks

status = pytest.main([
    "tests/hmda_data/test_synthetic.py::test_row_count_drop_preserves_sparse_year_with_exact_rows",
    "-q", "-p", "no:tach",
], plugins=[GlobalSamplingMutation()])
assert status == 1
```

결과는 **2 failed, 1 passed in 0.58s**, pytest exit 1이었다. Fraction `0.01`과 `0.5`에서 singleton 연도가 사라져 exact-row assertion이 실패했고 fraction `1.0`은 전체 행을 보존해 통과했다. Mutation 탐지 성공이며 정상 source의 test 실패가 아니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 변경 전 owned module | `uv run --no-sync pytest tests/hmda_data/test_synthetic.py -q`: **81 passed in 5.71s** |
| ✅ Pass | 보강 후 owned module | 같은 command: **114 passed in 6.24s** |
| ✅ Pass | 마지막 output 부재 assertion | conflicting-first-year·non-ASCII filename의 두 node ID를 별도로 재실행해 **2 passed in 1.01s**. 최종 working tree의 전체 domain 실행은 최종 PR 검증 보고서가 소유한다 |
| ✅ Pass | 희소 연도 negative control | 연도 partition 제거 시 **2 failed, 1 passed in 0.58s**, exit 1을 확인 |
| ✅ Pass | Python 정적 검증 | owned file의 `ruff check`, `ruff format --check`, `ty check` 및 `git diff --check` exit 0 |
| ❌ Fail | F1의 physical-type 변경 계약 | 임시 Parquet probe에서 source/output 모두 `VARCHAR`, 생성 호출은 성공 |
| ✅ Pass | F2의 현재 동작 재현 | 임시 probe에서 override 없는 `activity_year` target이 성공하며 연도 `NULL`을 생성함을 확인. 계약 충족 판정은 아님 |
| ⚪ Not Verified | #277 수정·새 계약 및 원격 CI | 이 audit은 구현 수정이나 원격 CI 결과를 생성하지 않는다 |

## Risks and Limits

이 보고서는 source·Spec와 26개 test function의 대응 및 bounded runtime probe를 다룬다. 생성 데이터가 실제 운영 결함·review utility를 대표하는지, 대용량 메모리·성능 또는 외부 provider 품질을 입증하지 않는다. Writer는 새 write 실패 후 이전 case output을 복구하지 않는다고 명시하므로 rollback을 이번 test의 암묵적 계약으로 추가하지 않았다.

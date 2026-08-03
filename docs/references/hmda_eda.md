# HMDA Raw EDA: Evidence And Resource Baseline

**이 EDA는 HMDA 원천 CSV의 schema, volume, required-column null과 freshness boundary를 read-only evidence로 만든다.** 계산은 `project_pivot.hmda_data.analyze_hmda_csv`가 담당하며 [`notebooks/eda_mo.py`](../../notebooks/eda_mo.py)와 automated test가 같은 경로를 사용한다.

> [!IMPORTANT]
> **EDA evidence는 incident 판정이나 저장된 `ProfileSnapshot`이 아니다.** Production detector와 lifecycle을 실행하지 않는다.

## Scope

| Included | Excluded |
| --- | --- |
| CSV schema, 전체·`activity_year`별 row count | 원천 다운로드, Bronze 적재, dbt 실행 |
| Required-column null count와 rate | incident 판정, remediation, recovery |
| `observed_at` 기반 source freshness | 파일 mtime 또는 Bronze ingestion time을 source freshness로 해석 |
| JSON-serializable EDA evidence | `ProfileSnapshot` 저장 또는 lifecycle 실행 |

Bronze 적재 계약은 [`HMDA Data`](../domains/hmda-data.md), profile과 incident
lifecycle은 [`Reliability`](../domains/reliability.md)를 따른다.

## Input And Reader

기본 입력은 `data/raw/hmda/year_2025.csv`다. `HMDA_EDA_DATA_PATH`로 다른
CSV를 지정할 수 있다.

`notebooks/eda_mo.py`는 VS Code notebook editor가 관리하는 셀 기반 파일이다.
VS Code에서 해당 file을 열고 `HMDA_EDA_DATA_PATH`를 설정한 terminal에서 실행한다.
일반 Marimo Python script 형식이 아니므로 `marimo edit` 또는 `marimo check` CLI를
이 notebook의 검증 command로 사용하지 않는다.

| Item | Value |
| --- | --- |
| Read scope | 파일 전체 |
| CSV header | 사용 |
| Type inference sample | 200,000 rows |
| Null strings | `NA`, 빈 문자열 |
| Parse error handling | fail-fast, `ignore_errors` 미사용 |
| DuckDB default | memory `2GB`, threads `2`, 호출자 지정 temp directory |
| Grouped result | `activity_year` cardinality 기본 32개로 제한 |

입력 파일은 DuckDB connection 생성 전에 확인한다. CSV parse 또는 aggregate
query가 실패하면 exception을 호출자에게 전달하고 partial `eda_evidence`를
반환하지 않는다. 성공과 실패 모두 entrypoint가 자신이 연 connection을 닫고
원천 파일을 수정하지 않는다.

## Evidence

`analyze_hmda_csv`는 다음 key를 갖는 JSON-serializable `dict`를 반환한다.

| Key | Meaning |
| --- | --- |
| `source` | resolved path, reader options, DuckDB resource 설정 |
| `duration_seconds` | aggregate query 측정 시간 |
| `row_count` | 읽은 전체 row 수 |
| `activity_year_counts` | bounded grouping 결과 |
| `null_counts`, `null_rates` | 존재하는 required column별 null baseline |
| `schema` | 전체 inferred schema, required-column 상태, `schema_hash` |
| `freshness` | 최대 `observed_at` 또는 `unmeasured` 경계 |

`freshness.status=unmeasured`이면 파일 수정 시각은 filesystem metadata이고
Bronze `ingested_at`은 별도 raw-table ingestion time이다.

## Visualizations

노트북([`notebooks/eda_mo.py`](../../notebooks/eda_mo.py))은 `eda_evidence` 데이터를 바탕으로 Altair 대화형 시각화 차트를 제공한다.

- **Activity Year별 Volume 분포**: `activity_year_counts` 데이터를 사용한 수직 막대 차트
- **Required Column Null 비율 Baseline**: `null_baseline` 데이터를 사용한 가로 막대 차트 (Null Rate 비율 표기)

## Profile Mapping

| EDA evidence | `ProfileSnapshot` field | Note |
| --- | --- | --- |
| `row_count` | `row_count` | baseline/current 입력 역할 값 |
| `null_rates` | `null_rates` | baseline/current 입력 역할 값 |
| `schema.schema_hash` | `schema_hash` | display-only mapping |
| `freshness.freshness_at` | `freshness_at` | `unmeasured`이면 `None` |

## Correctness

```bash
uv run pytest tests/hmda_data/eda/test_eda.py \
  tests/hmda_data/eda/test_eda_fixture.py \
  tests/hmda_data/eda/test_eda_memory_helpers.py
```

작은 valid fixture는 schema, row count, null, activity-year count와 freshness를
고정한다. Invalid UTF-8 fixture는 DuckDB parse exception과 partial evidence
미생성을 검증한다. [`test_eda_notebook.py`](../../tests/hmda_data/eda/test_eda_notebook.py)는
향후 runtime smoke의 contract와 수동 확인 대상을 기록한 계획 file이며, 현재 pytest에
수집되는 notebook runtime 검증은 없다. 변경 시 VS Code notebook editor에서 valid fixture와
malformed fixture를 각각 실행해 UI 결과와 명시적 exception 상태를 확인한다.

## Representative Memory Workload

Fixture 생성 비용은 측정 process에 포함하지 않는다.

```bash
uv run python scripts/prepare_hmda_eda_fixture.py \
  --output-directory data/samples/hmda/eda-memory-v1 \
  --row-count 5000000

uv run python scripts/run_hmda_eda_memory.py \
  --fixture-directory data/samples/hmda/eda-memory-v1 \
  --report-path notes/artifacts/hmda_eda_memory_report.json
```

Manifest `hmda-eda-memory-v1`은 seed `20250731`, 5,000,000 rows, 평균 row width
145.7 bytes, null rate `loan_amount=2%`, `income=5%`, 연도 skew
`2023=10%`, `2024=20%`, `2025=70%`, 단일 CSV와 SHA-256을 기록한다.

| Resource | Value |
| --- | ---: |
| Process hard limit | 3 GiB |
| Swap | 0 |
| DuckDB memory | 1600 MB |
| DuckDB threads | 2 |
| Timeout | 15분 |
| Temp disk budget | 10 GiB |
| Repetitions | 3 |

> [!IMPORTANT]
> **Hard limit probe가 실패하면 memory-budget 결과로 인정하지 않는다.** `systemd-run --user` memory control을 사전 확인하고 128 MiB probe가 실제 OOM kill되는지 검증한다.

기본 `pytest`는 `memory`와 `stress` marker를 제외한다.

2026-07-31 WSL2 baseline에서 세 실행은 모두 invariant를 통과했다. 최대 peak RSS는 1,261,285,376 bytes로 3 GiB limit의 39.2%였고 elapsed는 4.80~5.42초였다.

> [!WARNING]
> **이 결과는 해당 fixture와 WSL2 환경에만 적용된다.** 모든 HMDA 입력의 OOM 안전성을 의미하지 않는다.

## Full Source Observation

2026-07-31 `data/raw/hmda/year_2025.csv` 4.8 GiB를 공유 entrypoint로 한 번
전체 scan했다.

| Measurement | Observation |
| --- | ---: |
| Rows | 13,543,606 |
| `activity_year=2025` | 13,543,606 |
| `state_code` null | 170,769, 1.261% |
| `county_code` null | 301,923, 2.229% |
| `income` null | 2,189,834, 16.169% |
| Source freshness | `observed_at` 부재로 `unmeasured` |
| Aggregate query | 0.83초 |
| Process wall time | 66.40초 |
| Peak RSS | 13,041,572 KiB |

> [!WARNING]
> **Full-source 관측은 memory-budget test가 아니다.** Process hard limit 없이 DuckDB `2GB`, 2 threads로 실행했으므로 높은 process RSS를 대표 fixture의 제한 실행 결과와 분리해 해석해야 한다.

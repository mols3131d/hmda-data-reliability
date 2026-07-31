# HMDA Raw EDA

[`notebooks/eda_mo.py`](../../notebooks/eda_mo.py)는 HMDA 원천 CSV의 schema,
volume, required-column null과 freshness boundary를 표시한다. 계산은
`project_pivot.hmda_data.analyze_hmda_csv`가 담당하며 notebook과 automated
test가 같은 read-only 경로를 사용한다.

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

```bash
HMDA_EDA_DATA_PATH=data/raw/hmda/year_2025.csv uv run marimo edit notebooks/eda_mo.py
```

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

## Profile Mapping

| EDA evidence | `ProfileSnapshot` field | Note |
| --- | --- | --- |
| `row_count` | `row_count` | baseline/current 입력 역할 값 |
| `null_rates` | `null_rates` | baseline/current 입력 역할 값 |
| `schema.schema_hash` | `schema_hash` | display-only mapping |
| `freshness.freshness_at` | `freshness_at` | `unmeasured`이면 `None` |

EDA evidence 자체는 저장된 profile이 아니며 production detector를 실행하지
않는다.

## Correctness

```bash
uv run pytest tests/hmda_data/test_eda.py \
  tests/hmda_data/test_eda_fixture.py \
  tests/hmda_data/test_eda_memory_helpers.py
uv run marimo check notebooks/eda_mo.py
```

작은 valid fixture는 schema, row count, null, activity-year count와 freshness를
고정한다. Invalid UTF-8 fixture는 DuckDB parse exception과 partial evidence
미생성을 검증한다. Notebook smoke는 새 kernel에서 valid fixture의 UI 변수와
malformed fixture의 `exception` 상태를 확인한다.

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

`systemd-run --user` memory control을 사전 확인하고, 128 MiB probe가 실제
OOM kill되지 않으면 실행을 유효한 memory-budget 결과로 인정하지 않는다.
기본 `pytest`는 `memory`와 `stress` marker를 제외한다.

2026-07-31 WSL2 baseline에서 세 실행은 모두 invariant를 통과했다. 최대 peak
RSS는 1,261,285,376 bytes로 3 GiB limit의 39.2%였고 elapsed는 4.80~5.42초였다.
이 결과는 위 fixture와 환경의 관측값이며 모든 HMDA 입력의 OOM 안전성을
의미하지 않는다.

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

Full-source 실행은 process hard limit 없이 DuckDB `2GB`, 2 threads로 수행한
관측이다. 높은 process RSS는 대표 memory-budget 결과와 분리해 해석해야 한다.

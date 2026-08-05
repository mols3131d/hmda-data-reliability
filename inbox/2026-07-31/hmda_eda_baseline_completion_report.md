---
title: "HMDA EDA Baseline 완료 보고서"
description: "HMDA EDA baseline의 구현 범위, validation evidence, memory-budget 결과와 OpenSpec 완료 상태를 기록한 보고서"
date: 2026-07-31
---

# HMDA EDA Baseline Completion Report

## Executive Summary

> [!IMPORTANT]
> HMDA EDA baseline은 fail-fast reader, 공유 계산 entrypoint, deterministic
> fixture와 process-level memory runner까지 구현·검증·문서화되었다. 다만
> 3 GiB memory-budget 통과는 5,000,000-row representative fixture에 한정되며,
> 4.8 GiB full source의 process peak RSS 관측값은 약 12.44 GiB였다.

| Field | Value |
| --- | --- |
| Completion date | 2026-07-31 |
| OpenSpec capability | `hmda-eda-baseline` |
| OpenSpec state | Main spec sync 및 archive 완료, active change 0개 |
| Commit | `34e264c46afdfbc761c80ffccea8659b776aab53` |
| Commit subject | `feat: HMDA EDA 공유 계산과 메모리 검증 추가` |
| Change size | 21 files, 1,666 insertions, 270 deletions |
| Working tree at completion | Clean |

## Outcome

| Area | Result | Meaning |
| --- | --- | --- |
| Reader integrity | Input existence check와 DuckDB fail-fast parsing 적용 | Missing 또는 malformed input에서 partial baseline을 반환하지 않음 |
| Computation boundary | Notebook 계산을 공유 Python entrypoint로 이동 | Notebook과 automated test가 같은 evidence 계약 사용 |
| Resource lifecycle | Success, parse failure, query failure에서 connection close 검증 | EDA가 연 DuckDB connection의 lifecycle을 직접 소유 |
| Grouping bound | `activity_year` 결과를 bounded materialization 후 검증 | 비정상 cardinality에서 Python heap으로 무제한 적재하지 않음 |
| Notebook integration | 기존 schema, volume, null, freshness, mapping UI 유지 | UI는 계산 세부사항 대신 `eda_evidence`를 소비 |
| Representative workload | Deterministic CSV와 manifest generator 구현 | Fixture 생성 비용과 측정 process를 분리 |
| Memory enforcement | `systemd-run --user` hard limit과 swap 0 적용 | DuckDB 내부 limit만으로 process memory를 판단하지 않음 |
| Specification | Main spec sync 후 completed change archive | 구현 계약이 active planning artifact가 아닌 canonical spec에 반영됨 |

주요 구현 위치:

- [Shared EDA entrypoint](../../src/project_pivot/hmda_data/eda.py)
- [Representative fixture contract](../../src/project_pivot/hmda_data/eda_fixture.py)
- [Memory workload and assessment](../../src/project_pivot/hmda_data/eda_memory.py)
- [Marimo notebook](../../notebooks/eda_mo.py)
- [Fixture preparation command](../../scripts/prepare_hmda_eda_fixture.py)
- [Memory-budget runner](../../scripts/run_hmda_eda_memory.py)
- [Canonical OpenSpec](../../openspec/specs/hmda-eda-baseline/spec.md)
- [Operational reference](hmda_eda.md)

## Validation Evidence

### Automated Checks

| Check | Result |
| --- | ---: |
| HMDA domain pytest | 30 passed, 1 memory test deselected by default |
| Focused EDA lifecycle and fixture tests | Passed |
| Representative memory workload | 3/3 runs passed |
| Marimo DAG check | Passed |
| Ruff lint and format | Passed |
| `ty check` | Passed |
| OpenSpec strict validation | 17 passed, 0 failed |
| Pre-commit hooks | Passed |

기본 pytest에서 `memory`와 `stress` marker는 제외된다. Memory workload는
fixture 준비 후 별도 runner에서 명시적으로 실행한다.

### Notebook Smoke

Valid fixture에서는 다음 값이 생성됐다.

- `row_count=1`
- Required schema 7개 모두 `valid`
- Required-column null rate 모두 `0`
- `observed_at` 부재에 따라 freshness `unmeasured`

Invalid UTF-8 fixture에서는 분석 cell이 `exception` 상태가 되었고 이전
`eda_evidence`는 kernel globals에서 제거됐다. 따라서 parse failure 뒤 stale
baseline이 화면 계산 경로에 남지 않았다.

## Full Source Observation

대상은 `data/raw/hmda/year_2025.csv`이며 파일 크기는 약 4.8 GiB다. 이 실행은
process hard limit 없이 DuckDB memory `2GB`, threads `2` 조건으로 수행했다.

### Structure And Volume

| Measurement | Observation |
| --- | ---: |
| Total rows | 13,543,606 |
| `activity_year=2025` | 13,543,606 |
| `activity_year` type | `BIGINT` |
| `state_code` type | `VARCHAR` |
| `county_code` type | `VARCHAR` |
| `loan_purpose` type | `BIGINT` |
| `action_taken` type | `BIGINT` |
| `loan_amount` type | `DOUBLE` |
| `income` type | `BIGINT` |

필수 7개 컬럼은 존재했고 configured type family와 호환됐다. 관측된 row는
모두 `activity_year=2025`에 속했다.

### Null Baseline

| Column | Null count | Null rate |
| --- | ---: | ---: |
| `activity_year` | 0 | 0.000% |
| `state_code` | 170,769 | 1.261% |
| `county_code` | 301,923 | 2.229% |
| `loan_purpose` | 0 | 0.000% |
| `action_taken` | 0 | 0.000% |
| `loan_amount` | 0 | 0.000% |
| `income` | 2,189,834 | 16.169% |

`income`의 null 비율이 required columns 중 가장 높았다. 이 값은 품질 판정이나
threshold가 아니라 2025 source 실행의 baseline 관찰값이다.

### Freshness And Runtime

| Measurement | Observation |
| --- | ---: |
| Source freshness | `observed_at` 부재로 `unmeasured` |
| Aggregate query timer | 0.83 seconds |
| Process wall time | 66.40 seconds |
| Process peak RSS | 13,041,572 KiB, 약 12.44 GiB |
| Swap | 0 |
| Exit status | 0 |

Aggregate query timer는 entrypoint 내부 metric query 구간만 측정한다. Process
wall time과 peak RSS에는 CSV type inference, relation 준비, schema access와
Python process overhead가 포함된다. 두 시간을 같은 의미로 비교하면 안 된다.

## Representative Memory Baseline

### Fixture Contract

| Field | Value |
| --- | ---: |
| Version | `hmda-eda-memory-v1` |
| Seed | `20250731` |
| Rows | 5,000,000 |
| CSV size | 728,668,633 bytes |
| Average row width | 145.7 bytes |
| `loan_amount` null rate | 2% |
| `income` null rate | 5% |
| `activity_year` skew | 2023: 10%, 2024: 20%, 2025: 70% |
| File count | 1 |

### Resource Conditions

| Resource | Value |
| --- | ---: |
| Process hard limit | 3 GiB |
| Swap limit | 0 |
| DuckDB memory limit | 1600 MB |
| DuckDB threads | 2 |
| Timeout | 15 minutes |
| Temp disk budget | 10 GiB |
| Repetitions | 3 |

128 MiB hard-limit probe는 실제 `oom-kill` evidence를 생성했다. 따라서 세
baseline run은 memory control이 적용된 동일한 runner에서 실행됐다.

### Run Results

| Run | Exit | Output validation | Peak RSS | Elapsed | Run directory size |
| ---: | ---: | --- | ---: | ---: | ---: |
| 1 | 0 | Passed | 1,231,724 KiB | 4.91 s | 4,760 bytes |
| 2 | 0 | Passed | 1,209,760 KiB | 5.42 s | 4,759 bytes |
| 3 | 0 | Passed | 1,214,308 KiB | 4.80 s | 4,759 bytes |

최대 peak RSS는 1,261,285,376 bytes로 3 GiB hard limit의 39.2%였다. 세
실행에서 schema, row count, null counts, activity-year counts와 freshness
invariant가 모두 manifest와 일치했다.

## Interpretation Boundary

### Confirmed

- Shared EDA entrypoint는 작은 correctness fixture와 5M-row representative
  fixture에서 계약대로 동작했다.
- Missing, parse failure와 aggregate query failure에서 partial evidence를
  반환하지 않고 connection을 닫았다.
- Representative fixture는 지정된 3 GiB process budget 안에서 세 번
  완료됐다.
- Main OpenSpec은 구현된 reader, lifecycle, grouping과 memory 계약을 포함한다.

### Not Confirmed

- Full source가 3 GiB process budget 안에서 완료된다는 것은 확인하지 않았다.
- Representative fixture의 평균 row width 145.7 bytes는 full source의 파일
  크기와 row count로 계산한 평균 physical width보다 작다.
- `income`, `state_code`, `county_code` null baseline의 허용 범위나 anomaly
  threshold는 정의하지 않았다.
- Source freshness는 원천에 `observed_at`이 없어 측정하지 못했다.

> [!WARNING]
> Full-source uncontrolled run의 peak RSS가 약 12.44 GiB였으므로,
> representative fixture의 3 GiB 통과를 full-source memory 보장으로 확대하면
> 안 된다.

## Risks

| Risk | Evidence | Consequence |
| --- | --- | --- |
| Representative mismatch | Fixture row width 145.7 bytes, full source는 더 넓음 | Fixture-level memory margin이 full source를 대표하지 못할 수 있음 |
| Process memory outside DuckDB limit | Full source peak RSS 약 12.44 GiB, DuckDB limit 2GB | DuckDB setting만으로 host memory requirement를 설명할 수 없음 |
| Unmeasured source freshness | Full source에 `observed_at` 부재 | Source recency를 EDA evidence로 비교할 수 없음 |
| Baseline without policy | Null rates는 측정했지만 threshold는 미정 | 관찰값을 incident 판정으로 직접 사용할 수 없음 |
| Platform dependency | Memory runner가 user systemd와 cgroup에 의존 | 지원하지 않는 CI 또는 container에서는 같은 gate를 재현할 수 없음 |

## Recommended Next Actions

1. Full-source 3 GiB 보장이 실제 요구사항인지 먼저 결정한다.
1. 요구된다면 full source 또는 row width가 유사한 fixture를 process hard limit
   안에서 별도 profile하고 eager allocation 위치를 확인한다.
1. `income`, `state_code`, `county_code` null baseline을 여러 source 실행과
   비교한 뒤 threshold 변경을 별도 OpenSpec으로 제안한다.
1. Source observation timestamp의 canonical field가 확보되기 전까지 freshness를
   `unmeasured`로 유지한다.
1. CI memory job을 추가할 경우 user systemd 또는 동등한 container hard limit을
   제공하고 fixture version과 environment version을 함께 고정한다.

현재 capability는 EDA evidence 생성과 representative workload memory gate로는
완료됐다. Full-source memory budget, anomaly threshold와 freshness source
mapping은 별도 변경으로 다루는 것이 경계를 가장 명확하게 유지한다.

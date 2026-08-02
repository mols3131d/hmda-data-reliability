---
type: openspec-rpi
category: design
relatedArtifacts:
  - hmda-eda-foundation-extension
title: "HMDA foundation EDA extension design"
description: "기존 read-only HMDA EDA entrypoint를 MVP 데이터 정보 baseline으로 확장하는 설계"
---

## Context

현재 `analyze_hmda_csv`는 schema, 전체 row count, `activity_year` volume, required-column null rate, freshness boundary를 JSON-serializable evidence로 반환한다. MVP reliability 개발에는 여기에 핵심 code distribution, numeric summary, suspicious value observation, mart grain alignment과 notebook runtime evidence가 필요하다.

설계는 기존 DuckDB 기반 read-only entrypoint와 fixture 구조를 재사용한다. EDA는 `ProfileSnapshot`과 detector 입력을 대체하지 않으며, raw file과 lifecycle에 side effect를 만들지 않는다.

## Goals / Non-Goals

**Goals:**

- 기존 EDA evidence schema를 깨지 않고 descriptive metric을 확장한다.
- 핵심 field의 code/count/share, numeric summary, missingness와 anomaly observation을 제공한다.
- `activity_year + state_code + loan_purpose` grain과 현재 mart aggregation rule을 확인한다.
- deterministic fixture, representative resource check, actual-source observation, notebook runtime smoke를 분리한다.
- raw 값은 보존하고 해석되지 않은 값은 observation flag로만 기록한다.

**Non-Goals:**

- 전체 99개 field의 전수 분석
- ML, fairness, causal analysis
- detector threshold 학습 또는 incident lifecycle 실행
- raw value 정제·삭제
- production monitoring과 dashboard UI

## Decisions

### Reuse the shared DuckDB EDA entrypoint

`analyze_hmda_csv`를 계속 canonical calculation path로 사용한다. 별도 Polars pipeline이나 notebook 전용 query를 만들지 않아 test와 notebook의 결과가 갈라지지 않게 한다.

**Alternative:** Polars 기반 별도 분석 path. 현재 project의 EDA와 memory validation이 DuckDB entrypoint를 중심으로 구성되어 있어 중복 path를 만들지 않는다.

### Return structured descriptive evidence

기존 evidence dict에 다음 namespace를 추가하거나 기존 field를 확장한다.

- `distributions`: `action_taken`, `loan_purpose`, `state_code`, optional `county_code` counts and shares
- `numeric_summaries`: `loan_amount`, `income` non-null count, min, p25, median, p75, max
- `anomalies`: negative income, nonpositive amount, unknown code, cast-to-null counts
- `grain`: configured grouping columns와 raw aggregate count

기존 `row_count`, `null_counts`, `null_rates`, `schema`, `freshness` key는 유지한다.

### Keep semantic interpretation outside automatic cleaning

허용 code와 mart grouping rule은 reference/data contract에 연결하지만, suspicious numeric value를 삭제하거나 null로 치환하지 않는다. 허용 범위가 확정되지 않은 값은 count와 sample context가 있는 observation flag로 기록한다.

### Use fixture invariants for correctness

작은 deterministic fixture에는 exact distribution, numeric summary, anomaly count, grain aggregate expected value를 고정한다. 실제 source의 전체 결과는 immutable unit assertion으로 고정하지 않고 observation command 또는 report로 확인한다.

### Add runtime smoke at the notebook boundary

`marimo check`는 정적/구조 검증으로 유지하고, valid fixture와 malformed fixture를 사용한 notebook runtime smoke를 별도 command 또는 test로 추가한다. 구체적인 실행 방식은 구현 단계에서 현재 marimo test pattern에 맞춰 결정한다.

## Risks / Trade-offs

- [Risk] 전체 source scan 비용이 증가한다. → 핵심 field와 bounded grouping만 대상으로 하고 existing memory/temp 설정을 재사용한다.
- [Risk] 숫자 extreme value를 잘못된 값으로 해석할 수 있다. → 자동 정제하지 않고 `observed anomaly`로만 기록한다.
- [Risk] EDA와 ProfileSnapshot metric이 중복될 수 있다. → EDA는 descriptive distribution과 domain context, ProfileSnapshot은 partition detector metric으로 책임을 분리한다.
- [Risk] 실제 source observation이 source 변경으로 stale해질 수 있다. → 실행일과 source path를 기록하고 fixture invariant와 분리한다.

## Migration Plan

1. EDA structured evidence와 fixture contract를 확장한다.
1. correctness test와 notebook runtime smoke를 추가한다.
1. `docs/references/hmda_eda.md`와 foundation readiness evidence를 갱신한다.
1. 기존 EDA command와 lifecycle API를 실행해 regression을 확인한다.

기존 raw table과 기존 `ProfileSnapshot` contract에는 migration이 필요하지 않다.

## Open Questions

- notebook runtime smoke를 pytest test로 구현할지, dedicated script command로 구현할지는 implementation 환경을 확인한 뒤 결정한다.
- 실제 source에서 관찰된 extreme numeric value의 domain 의미는 별도 semantic research로 남기고 이번 change는 observation contract만 고정한다.

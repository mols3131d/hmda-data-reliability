---
title: Data Platform Test Strategy
description: foundation contract를 빠르고 독립적으로 검증하는 test portfolio와 fixture 원칙을 정의한다.
tags:
  - data-platform
  - testing
  - dbt
  - pytest
---

# Test Strategy

## Objective

좋은 test portfolio는 세 가지를 만족한다.

- **Trustworthy**: 실패가 contract violation을 의미한다.
- **Diagnostic**: 실패한 책임 경계를 빠르게 찾을 수 있다.
- **Economic**: routine 변경에서 full pipeline과 deep review를 반복하지 않는다.

## Layers

| Layer | Owns | Use for |
| --- | --- | --- |
| Python unit | pure validation과 path policy | 입력 규칙, quoting |
| dbt unit | SQL mapping과 계산 | cast, action mapping, denominator |
| Component | real DuckDB lifecycle | connection, cleanup, metadata |
| dbt data | materialized invariant | not-null, uniqueness, rate bounds |
| Integration | real boundary wiring | load → dbt, artifact, lineage, idempotency |
| Memory/stress | resource envelope | 명시적으로 요청된 heavy validation |

가장 싼 계층이 충분한 경우 상위 계층에 같은 exact behavior를 반복하지 않는다.

## Scenario Matrix

| Contract | Scenario | Independent oracle | Level |
| --- | --- | --- | --- |
| DP-R1 | Default request를 다른 CWD에서 실행 | 하나의 absolute DB에 세 schema 존재 | Integration |
| DP-R2 | 기존 DB read-only 연결 후 mutation 시도 | state 불변, mutation 실패 | Component |
| DP-R3 | 기존 DB와 owned temp에 cleanup 요청 | 기존 보존, owned temp 제거 | Component |
| DP-R4 | Context body에서 exception 발생 | 재연결 성공, original exception 유지 | Component |
| DP-S1–S3 | Null과 malformed numeric이 있는 raw fixture | row 보존, field-level Null, mart-only exclusion | dbt unit + Integration |
| DP-S4 | invalid required code | 명시적 build failure | dbt unit 또는 Integration |
| DP-M1 | materialized mart | unique grain | dbt data |
| DP-M2–M3 | action codes 1–8와 zero denominator | 사람이 계산한 literal output | dbt unit |
| DP-E1–E3 | build 2회와 artifact 검사 | identical rows, lineage, current success status | Integration |

## Recommended Layout

```text
tests/data_platform/
├── test_sql.py
├── test_duckdb_connection.py
├── test_duckdb_cleanup.py
└── test_duckdb_metadata.py  # 기존 helper 범위가 커질 때만

tests/dbt/
├── test_analytics_foundation.py
└── test_analytics_foundation.design.md  # 복잡한 matrix가 필요할 때만

dbt/models/{staging,marts}/
├── schema.yml
└── unit_tests.yml
```

파일 수보다 failure ownership을 우선한다. 작은 module은 기존 파일에 유지해도 된다.

## Fixture Policy

두 목적의 fixture만 둔다.

| Fixture | Purpose | Content |
| --- | --- | --- |
| dbt unit | SQL 의미 | 필요한 column과 case만 inline |
| integration CSV | 실제 wiring | source metadata, Null, malformed numeric, 최소 두 grain |

Action code fixture는 `1`부터 `8`까지 포함한다. Expected output은 production SQL을 test helper에서 재구현하지 않고 literal로 기록한다.

Fixture 중복을 제거하려고 범용 abstraction을 먼저 만들지 않는다. 목적과 차이가 길어질 때만 `test_analytics_foundation.design.md`에 연결한다.

## False-Green Controls

금지:

- artifact 존재만 보고 current run status를 확인하지 않음
- 서로 다른 성공 기준을 `or` assertion으로 허용
- broad exception 또는 unconditional skip
- production calculation을 test helper에서 복제
- absolute tmp path만 사용해 default path 계약을 우회
- integration 하나로 모든 risk를 보호

## Validation Gate

| Change | Focused gate | Broader gate |
| --- | --- | --- |
| SQL helper | 해당 unit/component module | `tests/data_platform` |
| Connection or cleanup | 해당 component module | `tests/data_platform` |
| Staging SQL | dbt unit selector | analytics integration |
| Mart metric | dbt unit selector | dbt data + analytics integration |
| Request or runner path | DB identity integration | `tests/data_operations` + analytics integration |
| Profile, artifact, lineage | dbt debug/build integration | relevant full suite |

PR evidence에는 pass count보다 다음을 남긴다.

- 변경한 contract
- scenario와 oracle
- 실제 실행 command와 result
- 실행하지 않은 validation
- 남은 semantic 또는 environment risk

## Portfolio Gate

과거 F1–F4가 가장 낮은 유효 계층의 deterministic check로 보호되고, integration은 실제 wiring만 추가로 증명해야 한다. 전체 exit criteria는 [`README.md`](README.md)가 소유한다.

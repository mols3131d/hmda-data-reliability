---
type: review
title: Reliability Profiling Test Design Review
description: Profile snapshot과 complete-table identity의 범위·시간·변경 민감도 oracle을 검토합니다.
---

# Reliability Profiling Test Design Review

> [!NOTE]
> 실제 SQL과 고정 시간·손계산 값을 사용한다. Builder 단위와 recovery caller의 scope binding을 구분해야 한다.

- **Target**: Reliability profiling와 table-state identity.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [test_profile_snapshots.py](../../../../tests/reliability/test_profile_snapshots.py), [test_table_state_identity.py](../../../../tests/reliability/test_table_state_identity.py) 전체와 관련 builder·모델.

## Findings

이 builder 단위에 추가 material finding은 없다. 정상 profile request가 다른 population을 가리키는 recovery 문제는 [Recovery R2](recovery.md#r2--major-profile-population-binding)에서 추적한다.

## Subview Assessment

| Area | Scenario And Independent Oracle | Boundary And Limit |
| --- | --- | --- |
| Row/null profile | 다른 날짜 sentinel을 포함해 대상 count `2`, null rate `0.5` 비교 | 실제 DuckDB SQL; production aggregate 재구현 아님 |
| Schema change | 별도 schema 변화가 fingerprint 차이를 만드는지 검사 | metadata prefix 검사보다 변화 민감도를 보완 |
| Freshness | exact 최대 timestamp·고정 observed time, 빈 partition·미래 timestamp | clock을 통제하며 unavailable과 measured를 구분 |
| Complete state | 여러 연도의 population·정렬·합계, year/file scope 중복 거부 | 실제 전체 table builder, observation partition만 보는 오류를 구별 |
| Invalid state | NULL year, 누락 partition, 동일 count의 다른 digest | unit digest는 authored 값; 실제 content 민감도는 HMDA ingestion oracle이 보완 |

핵심 근거는 profile 테스트 23·50·84·98·124행과 table-state 테스트 42·85·102·117행이다. 일반 profile builder가 요청된 predicate를 정확히 적용하는 것과, caller가 승인된 population에 맞는 predicate를 요청하는 것은 서로 다른 검증 책임이다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 두 관점 full-body 검토 | Batch B, fixture·assertion과 source targeted 대조 |
| ✅ Pass | 현재 실행 | [전체 suite](../validation.md#test-execution) |
| ⚪ Not Verified | 모든 schema/type·대규모 population 조합 | 대표 계약 사례를 검토했으며 exhaustive 검증은 아님 |

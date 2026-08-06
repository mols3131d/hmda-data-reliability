---
title: Data Platform Foundation Improvement Bundle
description: data_platform의 반복 심층 리뷰 비용을 executable contract와 위험 기반 검토로 전환하기 위한 비정규 작업 번들이다.
tags:
  - data-platform
  - foundation
  - testing
  - review
---

# Data Platform Foundation Improvement

> [!IMPORTANT]
> 이 번들은 `data_platform`을 초안 수준에서 다듬는 문서가 아니다. 향후 변경이 더 싸고 안전해지도록 경로, 소유권, 데이터 의미, 검증과 review gate를 기초 계약으로 정리한 작업 패키지다.

## Summary

현재 도메인은 경계 문서, OpenSpec, dbt 모델과 통합 test를 이미 갖추고 있다. 문제는 기반이 없는 것이 아니라 **핵심 위험이 실행 가능한 invariant로 충분히 고정되지 않은 것**이다.

따라서 개선 방향은 test 수를 무작정 늘리는 것이 아니다.

```text
review finding
    ↓
canonical decision
    ↓
observable invariant
    ↓
independent oracle
    ↓
가장 싼 executable check
    ↓
변경 위험에 맞는 review
```

이 구조가 정착되면 routine 변경은 focused test와 작은 diff review로 처리하고, 의미·소유권·파괴적 동작이 바뀔 때만 심층 review를 수행할 수 있다.

## Bundle

| Artifact | Purpose |
| --- | --- |
| [`01-foundation-assessment.md`](01-foundation-assessment.md) | 현재 기반의 강점, 구조적 결함과 목표 상태 |
| [`02-review-to-invariants.md`](02-review-to-invariants.md) | 기존 review finding을 재현 가능한 계약으로 변환 |
| [`03-test-architecture.md`](03-test-architecture.md) | pytest, dbt unit test, data test와 integration test의 역할 분리 |
| [`04-delivery-roadmap.md`](04-delivery-roadmap.md) | 결정 → red test → 수정 → 검증의 작업 순서와 completion gate |
| [`05-review-policy.md`](05-review-policy.md) | routine review와 deep review의 trigger 및 evidence contract |
| [`06-decisions-and-risks.md`](06-decisions-and-risks.md) | 구현 전에 인간이 확정해야 할 의미·API 결정과 잔여 위험 |

## Core Recommendation

다음 다섯 계약을 foundation gate로 둔다.

1. Python ingestion과 dbt는 동일하게 정규화된 DuckDB resource identity를 사용한다.
1. 파괴적 cleanup은 manager가 명시적으로 소유한 임시 resource에만 적용된다.
1. Staging은 raw row와 허용된 Null을 보존하고 cast 실패를 관찰 가능하게 표현한다.
1. Mart grain과 metric population은 canonical spec으로 정의하고 작은 fixture로 독립 검증한다.
1. Review 깊이는 변경 크기가 아니라 contract risk로 결정한다.

## Scope

이 번들은 다음을 설계한다.

- `data_platform`과 직접 연결되는 `data_operations` 경계
- DuckDB 연결·cleanup·metadata helper 계약
- dbt staging·mart·artifact·lineage 계약
- 관련 pytest와 dbt test portfolio
- review 비용을 낮추는 escalation policy

다음은 의도적으로 제외한다.

- 전체 HMDA 1,350만 행을 매 변경마다 실행하는 부하 검증
- 범용 test DSL 또는 새로운 test framework
- enterprise data observability platform
- 현재 요구사항과 무관한 data domain 재설계
- 이 inbox 문서를 canonical guidance로 직접 승격하는 작업

## Source Revision

- Repository baseline: `f08c2fb7`
- Source review: `reviews/data-platform-domain-contracts.md`
- Review commit: `89c18b2f`
- Validation: repository와 공식 문서 기반 정적 조사만 수행했으며 test command는 실행하지 않았다.

## External References

- [dbt unit tests](https://docs.getdbt.com/docs/build/unit-tests)
- [dbt data tests](https://docs.getdbt.com/docs/build/data-tests)
- [dbt-duckdb profile path behavior](https://github.com/duckdb/dbt-duckdb#configuring-your-profile)
- [DuckDB files created](https://duckdb.org/docs/stable/operations_manual/footprint_of_duckdb/files_created_by_duckdb)
- [CFPB Regulation C data fields](https://www.consumerfinance.gov/rules-policy/regulations/1003/4/)

## Lifecycle

이 번들은 비정규 입력이다. 채택된 내용은 다음 owning artifact로 다시 작성한다.

| Content | Canonical destination |
| --- | --- |
| Database path와 cleanup behavior | OpenSpec change, `docs/domains/data-platform.md` |
| Mart metric 의미 | `openspec/specs/dbt-analytics-foundation/spec.md` |
| Test scenario와 oracle | `tests/`, 필요 시 `test_*.design.md` |
| Review trigger | `reviews/` 또는 development workflow guidance |
| 실행 결과와 잔여 위험 | Draft PR |

Canonical artifact가 이 inbox 경로를 의존하거나 링크해서는 안 된다.

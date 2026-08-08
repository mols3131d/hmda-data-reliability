---
title: Data Platform Foundation Improvement Bundle
description: data_platform의 반복 심층 리뷰를 안정된 계약과 실행 가능한 검증으로 전환하는 작업 번들이다.
tags:
  - data-platform
  - foundation
  - testing
  - review
---

# Data Platform Foundation Improvement

> [!IMPORTANT]
> Foundation은 초안이 아니라 상위 기능이 신뢰할 수 있는 기초 공사다. 이 번들의 목표는 테스트 수를 늘리는 것이 아니라, 반복해서 추론하던 위험을 계약과 검증으로 고정하는 것이다.

## Summary

현재 `data_platform`은 도메인 경계, OpenSpec, dbt 모델과 통합 테스트를 갖추고 있다. 그러나 다음 핵심 계약은 아직 충분히 보호되지 않는다.

| Area | Current state | Required foundation |
| --- | --- | --- |
| DuckDB identity | Python과 dbt의 상대 경로 해석이 다를 수 있음 | 모든 실행 경계가 하나의 resolved path 사용 |
| Resource ownership | `cleanup_on_close`가 기존 DB도 삭제 가능 | 소유한 임시 resource만 삭제 |
| Staging preservation | 문서화됐지만 직접 검증 부족 | row, 허용 Null, tolerant cast 보존 |
| Mart semantics | metric 이름은 있으나 모집단·분모가 불명확 | action mapping과 denominator를 spec에 고정 |
| Review economy | 사람이 같은 위험을 반복 추론 | invariant test와 위험 기반 review gate |

작업 흐름은 다음으로 단순화한다.

```text
decision → contract → scenario → independent oracle → executable check
```

## Bundle

| Artifact | Purpose |
| --- | --- |
| [`01-foundation-contracts.md`](01-foundation-contracts.md) | 완료해야 할 foundation 계약과 현재 gap |
| [`02-test-strategy.md`](02-test-strategy.md) | 계약별 test level, scenario와 oracle |
| [`03-delivery-roadmap.md`](03-delivery-roadmap.md) | 독립적인 변경 단위와 completion gate |
| [`04-review-policy.md`](04-review-policy.md) | focused review와 deep review의 경계 |
| [`05-decisions-and-risks.md`](05-decisions-and-risks.md) | 구현 전 인간 결정과 남은 위험 |

## Exit Criteria

다음이 모두 성립해야 foundation 개선이 완료된다.

1. Default flow가 ingestion과 dbt의 동일 DB 사용을 증명한다.
1. 기존 또는 read-only DB는 cleanup으로 삭제될 수 없다.
1. Staging 보존과 mart 제외 정책을 각각 직접 검증한다.
1. Mart metric은 SQL을 읽지 않고도 spec만으로 계산할 수 있다.
1. 과거 review finding은 deterministic regression check로 이전된다.
1. Routine 변경은 focused test와 focused review로 판정할 수 있다.

## Scope

포함:

- `data_platform`과 직접 연결되는 `data_operations` 실행 경계
- DuckDB lifecycle, dbt staging·mart·artifact·lineage 계약
- pytest와 dbt test portfolio
- review escalation policy

제외:

- 매 변경의 전체 HMDA 부하 검증
- 새로운 test framework 또는 범용 DSL
- enterprise observability 도입
- 현재 요구와 무관한 domain 재설계

## Source And Lifecycle

- Baseline: `f08c2fb7`
- Source review: `reviews/data-platform-domain-contracts.md`
- Runtime validation: 수행하지 않음

이 번들은 비정규 입력이다. 채택된 결정은 OpenSpec과 domain 문서로, scenario는 test로, 실행 결과와 잔여 위험은 PR로 이전한다. Canonical artifact는 이 경로를 의존하지 않는다.

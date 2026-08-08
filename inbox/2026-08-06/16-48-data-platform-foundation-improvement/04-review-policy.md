---
title: Risk-Based Review Policy for Data Platform
description: 반복 심층 review를 자동 검증과 contract risk 기반 escalation으로 전환한다.
tags:
  - data-platform
  - review
  - quality-gate
---

# Review Policy

## Principle

Review 깊이는 diff 크기가 아니라 변경된 contract의 위험으로 결정한다. Test가 이미 보호하는 behavior를 사람이 매번 처음부터 재검증하지 않는다.

인간 review는 다음을 본다.

- contract 선택이 옳은가
- oracle이 implementation과 독립적인가
- 새 위험이 기존 invariant 밖에 있는가
- 책임 경계와 migration 영향이 적절한가

## Gates

### Automated

모든 변경에 적용한다.

- focused test
- 관련 domain suite
- 필요한 dbt parse, build 또는 selector
- 영향 범위의 lint와 type check
- command, failure, omission과 remaining risk 기록

자동 gate 실패를 review로 덮지 않는다.

### Focused Review

다음을 모두 만족하는 routine 변경의 기본 경로다.

- canonical contract 변경 없음
- schema, grain, metric population, ownership 변경 없음
- destructive behavior와 새 boundary 없음
- deterministic test가 변경 behavior를 보호
- 한 가지 변경 목적

검토 범위:

- contract와 diff의 일치
- scenario와 oracle의 타당성
- 불필요한 abstraction 또는 scope 확장
- validation evidence와 remaining risk

### Deep Review

다음 중 하나라도 해당하면 changed contract에 한정해 수행한다.

| Trigger | Example |
| --- | --- |
| Semantic contract | rate denominator 또는 action mapping 변경 |
| Schema or grain | mart grain 변경 |
| Destructive behavior | cleanup, overwrite, backfill |
| Resource identity | DB path와 environment resolution |
| Ownership boundary | domain 책임 이동 |
| New dependency | adapter, storage, execution engine 변경 |
| Weak oracle | expected result를 독립 판정하기 어려움 |
| Resource guarantee | memory, timeout, concurrency policy |
| Repeated regression | 같은 defect가 기존 gate를 통과해 재발 |
| Irreversible migration | downstream 호환성 파괴 |

결정이 모호하면 deep review가 아니라 **Blocked: decision/spec first**다.

## Evidence Package

PR은 reviewer가 repository 전체를 재조사하지 않도록 다음 연결을 제공한다.

```text
changed contract
→ affected scenario
→ independent oracle
→ focused validation
→ broader validation
→ omissions and risks
```

최소 기록:

- 변경한 canonical requirement 또는 “contract 변경 없음”
- regression test 이름과 실패시킬 defect
- 실제 실행 command와 result
- 미수행 heavy validation
- downstream 영향
- deep-review trigger 해당 여부

## Finding Handoff

| Finding | Destination |
| --- | --- |
| Reproducible defect | regression test + owning implementation |
| Missing decision | OpenSpec spec 또는 design |
| Missing invariant | test design + executable check |
| Operational follow-up | PR risk 또는 Issue |
| One-time observation | 삭제 또는 승인된 archive |
| Invalid finding | review에서 제거하고 근거 기록 |

Routine PR은 별도 `reviews/` artifact를 요구하지 않는다. Finding이 spec, test, PR 또는 Issue로 이전되면 review 삭제가 기본이다.

## Prerequisite

F1–F4의 regression gate가 구축되기 전에는 이 정책으로 review를 줄이지 않는다. 적용과 dogfooding 순서는 delivery roadmap이 소유한다.

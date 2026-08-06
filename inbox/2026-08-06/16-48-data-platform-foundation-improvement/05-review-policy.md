---
title: Risk-Based Review Policy for Data Platform
description: 반복 심층 review를 자동 검증과 위험 기반 escalation으로 대체하는 운영 정책 초안이다.
tags:
  - data-platform
  - review
  - quality-gate
---

# Review Policy

## Principle

Review 깊이는 diff 크기나 문서 유형이 아니라 **변경된 계약의 위험**으로 결정한다.

자동 test가 이미 고정한 behavior를 사람이 매번 처음부터 재검증하지 않는다. 인간 review는 다음에 집중한다.

- 올바른 contract를 선택했는가
- test oracle이 그 contract와 독립적인가
- 새 위험이 기존 invariant 밖에 있는가
- 변경 경계와 소유권이 적절한가

## Three Gates

### Automated Gate

모든 변경에 적용한다.

- focused test
- 관련 domain suite
- dbt parse/build 또는 selector
- lint/type check 중 실제 영향 범위
- 실행한 command, failure와 omission 기록

자동 gate 실패를 review로 덮지 않는다.

### Focused Review

다음 조건을 모두 만족하면 사용한다.

- 기존 canonical contract 안의 구현 또는 refactor
- schema, grain, metric population과 ownership 변경 없음
- destructive behavior 추가 없음
- 변경된 behavior를 기존 또는 새 deterministic test가 보호
- cross-domain boundary가 늘어나지 않음
- diff가 한 목적

검토 내용:

- change contract와 diff 일치
- test scenario와 oracle 타당성
- 불필요한 abstraction 또는 scope 확장
- validation evidence와 remaining risk

Routine 변경의 기본 경로다.

### Deep Review

다음 중 하나라도 해당하면 수행한다.

| Trigger | Example |
| --- | --- |
| Semantic contract | `approval_rate` denominator 변경 |
| Schema or grain | mart grain column 변경 |
| Destructive behavior | DB cleanup, overwrite, backfill |
| Resource identity | database path, artifact path, environment resolution |
| Cross-domain ownership | `data_platform`과 `data_operations` 책임 이동 |
| New external dependency | adapter, storage, execution engine 변경 |
| Weak oracle | 실제 result를 독립적으로 판정하기 어려움 |
| Resource guarantee | full-data memory, timeout, concurrency policy |
| Repeated regression | 같은 유형 defect가 test를 통과해 재발 |
| Irreversible migration | 기존 mart/result 호환성이 깨짐 |

Deep review는 “더 오래 읽기”가 아니라 독립 evidence와 adversarial scenario가 필요한 경우다.

## Review Decision Matrix

| Contract change | Tests pass | Review |
| --- | --- | --- |
| 없음 | Yes | Focused |
| 없음 | No | Fix or classify failure before review |
| 있음, behavior fully decided | Yes | Deep but bounded to changed contract |
| 있음, decision ambiguous | N/A | Blocked: decision/spec first |
| destructive or data-loss risk | Yes | Deep |
| test-only oracle improvement | Yes | Focused unless it changes expected behavior |

## Evidence Package

Reviewer가 repository 전체를 다시 조사하지 않도록 PR은 다음을 제공한다.

```text
Changed contract
→ affected invariant
→ scenario and oracle
→ focused validation
→ broader validation
→ omitted validation
→ remaining risk
```

최소 항목:

- 변경한 canonical requirement 또는 “contract 변경 없음”
- regression test 이름
- test가 실패시킬 defect
- 실제 실행 command와 result
- 실행하지 않은 heavy validation
- downstream compatibility 영향
- deep review trigger 해당 여부

## Finding Handoff

Finding은 다음 중 하나로 끝나야 한다.

| Finding type | Destination |
| --- | --- |
| Reproducible defect | regression test + owning implementation |
| Missing behavior decision | OpenSpec/spec/design |
| Missing invariant | test design + executable check |
| Operational follow-up | Issue or PR risk |
| One-time observation | review 삭제 또는 승인된 archive |
| Invalid finding | review에서 제거하고 근거 기록 |

같은 finding을 여러 review 문서에 누적하지 않는다.

## Review Artifact Rule

Routine PR은 별도 `reviews/` artifact를 요구하지 않는다. PR conversation과 test evidence가 충분하면 그것이 review boundary다.

Review artifact는 다음에만 가치가 있다.

- 여러 artifact 사이의 consistency를 장기 조사
- semantic decision 전에 독립 검토가 필요
- adversarial review 결과를 implementation과 분리해 handoff
- 인간이 별도 보고서 형태를 요청

Review 완료 후 accepted finding이 spec, test, PR 또는 issue로 이전되면 삭제가 기본이다.

## Anti-Patterns

- 모든 change에 deep reasoning loop 횟수를 고정
- test가 통과했으므로 contract가 옳다고 가정
- review finding을 test 없이 문서에만 누적
- integration test 하나로 모든 risk를 보호
- snapshot과 coverage percentage를 quality proxy로 사용
- 변경이 작다는 이유로 destructive behavior를 focused review로 처리
- 문서 수정이라는 이유로 metric semantics 변경을 가볍게 처리

## Adoption

이 정책은 A/B foundation workstream의 test gate가 구축된 뒤 적용한다. 먼저 review를 줄이고 나중에 test를 보강하면 risk만 숨는다.

전환 순서:

1. F1–F4 regression obligation을 test와 spec으로 이전한다.
1. focused/deep trigger를 PR workflow에 반영한다.
1. 다음 세 routine 변경에서 focused review를 dogfood한다.
1. 놓친 defect와 불필요한 trigger를 기록해 정책을 조정한다.
1. 반복 가능한 상태가 확인되면 review 문서를 삭제한다.

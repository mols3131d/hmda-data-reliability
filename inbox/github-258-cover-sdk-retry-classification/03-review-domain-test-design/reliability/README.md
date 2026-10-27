---
type: review
title: Reliability Test Design Review
description: Reliability의 contracts·metadata·profiling·detection·impact·remediation·recovery·evaluation 테스트 리뷰를 연결합니다.
---

# Reliability Test Design Review

> [!NOTE]
> 실제 상태·승인·경계값 oracle은 강하다. Recovery evidence·profile 범위·손상된 lineage 처리와 실패 평가의 Action 성공 집계에서 현재 오동작을 확인했다.

- **Target**: Reliability domain의 8개 source 하위 패키지와 quality policy.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: Batch B·C의 test 24개·support 3개·design 1개 전체를 두 관점 독립 검토했다. Source·Spec은 targeted 대조했다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| L1 | Major | commit 후 staging cleanup 실패가 mutation evidence를 잃음 | [Recovery R1](recovery.md#r1--major-staging-cleanup-after-commit) |
| L2 | Major | 다른 population의 profile을 성공 증거로 결합 | [Recovery R2](recovery.md#r2--major-profile-population-binding) |
| L3 | Major | 구조가 손상된 manifest를 영향 없음으로 성공 처리 | [Impact I1](impact.md#i1--major-malformed-graph-shape) |
| L4 | Minor | schema replay의 no-replacement 관측 부족 | [Recovery R3](recovery.md#r3--minor-schema-replay-no-replacement) |
| L5 | Major | schema recovery 실패가 Action PASS로 집계 | [Evaluation E1](evaluation.md#e1--major-failed-recovery-action-pass) |
| L6 | Minor | 모든 요구사항과 일부 충족을 구별하는 집계 반례 부족 | [Evaluation E2](evaluation.md#e2--minor-all-versus-any-oracle) |

L1–L3·L5는 caller의 현재 revision probe로 확인했다. L4·L6는 현재 구현이 정상인 정적 coverage gap이다. 모두 후속 제안이며 이번 보고 작업에서 구현하지 않았다.

## Subdomain Reports

| Subdomain | Main Evidence | Review |
| --- | --- | --- |
| contracts | 실제 validation·immutable approval/actions·evidence 관계 | [Contracts](contracts.md) |
| metadata | 실제 schema/type/nullability·count·timestamp | [Metadata](metadata.md) |
| profiling | 고정 row/null/freshness와 complete-table state | [Profiling](profiling.md) |
| detection / quality policy | exact incident, 경계 equality, 독립 규칙, 5%p policy | [Detection](detection.md) |
| impact | 실제 graph traversal와 affected-assets | [Impact](impact.md) |
| remediation | 실제 workflow의 action·lineage·JSON evidence | [Remediation](remediation.md) |
| recovery | 승인→staging→CAS→mutation→profile→replay의 실제 상태 | [Recovery](recovery.md) |
| evaluation | vertical slice·report·실패 증거 | [Evaluation](evaluation.md) |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Batch B·C 독립 검토 | 28파일 full body·assertion·fixture·design, 두 관점 |
| ✅ Pass | 현재 실행 | [전체 suite와 probe 기록](../validation.md) |
| ❌ Fail | 현재 동작의 계약 반례 | B1 cleanup·B2 profile·B3 malformed manifest·C1 실패 집계 |

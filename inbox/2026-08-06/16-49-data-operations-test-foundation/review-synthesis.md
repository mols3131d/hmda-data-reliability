---
title: Data Operations Review Synthesis
description: domain review finding을 root cause, 우선순위와 testability 기준으로 재평가한다.
tags:
  - data-operations
  - review
  - prioritization
---

# Review Synthesis

## Verdict

**Revise.** Stage API, pipeline ownership과 read-only lifecycle은 유지한다. Configuration, public error, result와 orchestration event의 의미를 runtime contract로 닫아야 한다.

## Root Causes

| Root cause | Findings |
| --- | --- |
| Accepted configuration has no runtime proof | custom artifact path, orchestration flag in shared request |
| Output type is mistaken for domain truth | discovery count, skipped materialization |
| Documented boundary has no regression oracle | error unification, deep immutability |

## Findings

| Priority | Finding | Status | Required decision or action |
| ---: | --- | --- | --- |
| P1 | Custom artifact path is not connected to dbt output | Confirmed defect | output source of truth를 하나로 만들고 end-to-end adapter test를 둔다. |
| P1 | Public stages expose lower-domain error taxonomies | Contract defect | wrapping 대상과 safe context policy를 결정하고 translation test를 둔다. |
| P1 | Skipped dbt build still records materialization | Spec conflict | standard pipeline skip policy를 결정하고 event absence를 검증한다. |
| P2 | `source_file_count` meaning differs from documentation | Decision gap | discovered와 contributing 중 의미를 결정한 뒤 이름과 test를 맞춘다. |
| P2 | Frozen results contain mutable lists | Contract gap | deep immutability를 유지하면 tuple과 mutation test를 사용한다. |

## Finding Notes

### Artifact path

`DataOperationRequest`는 artifact path를 받지만 `dbt build` command는 output location을 제어하지 않는다. 기존 test가 request 경로에 직접 파일을 써서 adapter 연결 defect를 숨긴다.

### Error boundary

문서는 public failure를 `DataOperationError`로 통일한다고 설명한다. Raw와 lifecycle은 예상 가능한 하위 domain error를 그대로 노출할 수 있다. 해결은 broad `except Exception`이 아니라 명시적인 translation policy다.

### Materialization

Standard pipeline spec은 raw 다음 dbt build 실행을 요구한다. 실행하지 않은 Silver/Gold asset에 materialization을 기록하면 event와 실제 data state가 달라진다.

### File count

단순히 filtered path 수로 바꾸면 충분하지 않다. “처리”가 query 참여인지 row contribution인지 먼저 정의해야 한다.

### Immutability

`frozen=True`는 field 재할당만 막는다. Evidence result를 변경 불가로 유지하려면 nested collection도 immutable해야 한다.

## Decision Gaps

다음은 defect로 단정하지 않는다.

- baseline과 current의 profile column set 호환성
- dbt artifact의 최소 usable structure
- 여러 incident 중 하나가 실패할 때 all-or-fail 여부

이 항목은 contract가 결정된 뒤에만 test로 고정한다.

## Scope After Foundation

| Protected contract | Future review focus |
| --- | --- |
| artifact output connection | 새 dbt option과 environment 영향 |
| error translation | 새 exception과 context policy |
| materialization truth | graph 또는 job contract 변경 |
| count semantics | provenance 정의 변경 |
| deep immutability | 새 result field 의미 |

## Assessment

Finding을 하나의 대형 fix로 묶지 않는다. Contract decision, focused test와 production fix를 독립적으로 전달해야 리뷰 범위와 실패 원인이 작게 유지된다.

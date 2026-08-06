---
title: Data Operations Change Gates and Delivery
description: 반복 심층 리뷰를 줄이기 위한 변경 분류, contract decision과 전달 순서를 정의한다.
tags:
  - data-operations
  - change-gate
  - delivery-plan
---

# Change Gates And Delivery

## Principle

먼저 변경이 기존 contract 안에 머무는지 분류한다. Deep review는 새 판단이 필요한 경우에만 사용한다.

## Change Classes

| Class | Meaning | Evidence | Review |
| --- | --- | --- | --- |
| A | Contract-preserving implementation | focused + domain suite | light |
| B | Known boundary risk | relevant matrix scenario + caller suite | targeted |
| C | Contract or architecture change | canonical decision + new scenario + integration | deep |

### Examples

| Area | Default | Escalate when |
| --- | --- | --- |
| private helper | A | state, ordering 또는 public error가 달라짐 |
| result/metadata mapping | B | field meaning 또는 compatibility가 달라짐 |
| request field | C | validation constraint만 보강하면 B |
| dbt command | B | output contract나 ownership이 달라지면 C |
| error mapping | B | public taxonomy policy가 달라지면 C |
| Dagster metadata | B | materialization 의미나 graph가 달라지면 C |
| lifecycle sequence | C | behavior 없는 extraction이면 A |
| docs | A | canonical behavior를 새로 정의하면 C |

## Decisions Before Tests

### D1. dbt artifact source of truth

추천: `dbt_target_path` 하나를 command와 result path의 source of truth로 사용한다. 대안은 project default target만 지원하는 것이다. 독립적인 artifact path는 피한다.

### D2. Standard pipeline skip policy

추천: standard `pipeline_job`은 raw와 dbt를 항상 실행한다. Raw-only는 asset selection 또는 별도 job으로 표현한다. Orchestration control은 shared request에서 분리한다.

### D3. Error boundary policy

추천: 예상 가능한 domain/application failure만 `DataOperationError`로 변환한다. Cause와 필요한 safe context를 보존하고 programming error는 숨기지 않는다.

### D4. Result semantics

추천: evidence collection은 deep immutable하게 유지한다. File count는 discovered 또는 contributing 의미를 이름에 드러내고, 둘 다 필요하면 분리한다.

## Work Units

| Change | Scope |
| --- | --- |
| A — dbt execution contract | D1, fake executable, adapter test, runner fix |
| B — application error boundary | D3, raw/lifecycle matrix, cause/context |
| C — orchestration truthfulness | D2, raw-only path, event absence test |
| D — result and metadata | D4, file provenance, immutability tests |

각 work unit은 별도 branch와 Draft PR로 전달한다. Decision과 mechanical fix를 한 대형 PR에 섞지 않는다.

## Review Retirement

현재 review finding은 다음 durable artifact로 이전한 뒤 review 문서를 삭제할 수 있다.

| Finding | Durable destination |
| --- | --- |
| artifact path | canonical contract + component test |
| error boundary | domain contract + translation tests |
| false materialization | orchestration spec + integration test |
| file count | result contract + component/integration test |
| immutability | result contract + unit test |

Meaning은 canonical contract가 소유하고 test는 그 결정을 실행 가능하게 보호한다.

## Completion Gate

- D1–D4가 명시적으로 해결됐다.
- P1 risk에 red 또는 characterization test가 있다.
- Focused domain suite와 affected integration suite가 실행됐다.
- 실행하지 않은 validation은 통과로 기록하지 않았다.
- 남은 deep review 대상이 새 contract와 architecture decision으로 제한됐다.

```text
contract unchanged + tests pass
→ light review

known boundary changed + contract tests pass
→ targeted review

contract or architecture changed
→ deep review
```

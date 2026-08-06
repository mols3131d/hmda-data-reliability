---
title: Data Operations Test Foundation Research
description: 반복적인 심층 리뷰의 원인과 executable contract로 이전할 판단을 분석한다.
tags:
  - data-operations
  - research
  - executable-specification
---

# Foundation Research

## Question

`data_operations`를 변경할 때마다 전체 domain을 다시 검토하지 않고도 신뢰를 유지하려면 무엇을 먼저 설치해야 하는가?

## Conclusion

문제는 리뷰 횟수가 아니라 **경계의 의미가 실행 가능한 형태로 보존되지 않는 것**이다. 현재 suite가 보호하지 못한 연결은 사람이 코드와 문서를 함께 읽어야 확인할 수 있다.

- configuration이 실제 process 동작에 반영되는가
- 하위 domain failure가 안정적인 public error로 변환되는가
- result와 Dagster event가 실제 실행 상태를 정확히 표현하는가
- 반환된 evidence가 사후 변경되지 않는가

따라서 production refactor보다 contract decision과 boundary test harness가 먼저다.

## Why Cost Repeats

### Contract is distributed

Request, domain guide, OpenSpec, Dagster asset과 test가 각각 일부 의미를 가진다. 한 파일만 보면 변경이 refactor인지 contract 변경인지 판단하기 어렵다.

### Mock replaces the boundary

현재 dbt test는 `subprocess.run`과 artifact 생성을 함께 stub한다. Timeout과 return code는 검증하지만, command와 실제 output location의 연결은 검증하지 못한다.

### Structure is mistaken for meaning

`MaterializeResult`와 `frozen=True`는 각각 실제 갱신과 deep immutability를 보장하지 않는다. 구조 assertion만으로는 semantic regression을 막을 수 없다.

### Known risks remain prose

이미 확인한 artifact path, error leakage, false materialization 같은 위험이 regression test로 이전되지 않아 다음 변경 때 다시 추론한다.

## Foundation Elements

| Element | Role |
| --- | --- |
| Canonical contract | 보존할 의미를 결정한다. |
| Independent oracle | 구현과 별개로 성공·실패를 판정한다. |
| Boundary harness | file, DuckDB, subprocess, Dagster event를 최소 비용으로 연결한다. |
| Focused suite | 변경 직후 빠른 feedback을 제공한다. |
| Review trigger | test로 증명할 수 없는 새 판단을 식별한다. |

## Design Principles

### Protect observable boundaries

가치 있는 assertion은 helper 호출 순서가 아니라 다음 결과다.

- public input, result와 error
- subprocess command와 생성 artifact
- DuckDB persisted state
- Dagster materialization event와 metadata
- result의 사후 변경 가능 여부

### Use the cheapest trustworthy level

| Risk | Level |
| --- | --- |
| validation, deep immutability | unit |
| raw load, error translation | component |
| command-to-artifact connection | component with fake executable |
| materialization semantics | integration |
| pipeline ownership or lifecycle boundary | integration + review |

### Keep oracles independent

- Fake executable이 전달받은 target에 artifact를 생성한다.
- Raw metadata는 persisted rows와 합의된 provenance로 판정한다.
- Error boundary는 public exception type, cause와 safe context로 판정한다.
- Orchestration은 log가 아니라 event 유무로 판정한다.

### Decide before testing

Artifact ownership, skip policy, error policy와 result semantics는 test보다 먼저 canonical contract에서 결정한다. 구체적인 decision은 [`change-gates-and-delivery.md`](change-gates-and-delivery.md)가 소유한다.

Test가 이 결정을 먼저 내리면 architecture가 test에 숨어든다.

## Review Boundary

| Contract tests retire | Deep review remains |
| --- | --- |
| artifact path, stale rejection, known error translation | public contract, stage 또는 dependency 변경 |
| materialization, metadata와 immutability regression | Dagster ownership, lifecycle write boundary 변경 |
| 이미 합의된 observable behavior 재검증 | persistence, transaction, concurrency 또는 oracle 변경 |

## Verdict

`data_operations`의 우선 작업은 architecture rewrite가 아니다. 미결정 contract를 좁게 결정하고, 그 결정을 독립적인 oracle로 보호한 뒤, production fix를 작은 단위로 적용해야 한다.

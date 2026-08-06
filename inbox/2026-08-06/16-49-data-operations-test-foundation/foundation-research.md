---
title: Data Operations Test Foundation Research
description: 반복적인 심층 리뷰가 발생하는 구조적 원인과 이를 executable contract로 이전하는 원칙을 분석한다.
tags:
  - data-operations
  - research
  - executable-specification
  - foundation
---

# Foundation Research

## Question

`data_operations`를 변경할 때마다 전체 domain을 심층 리뷰하지 않고도 충분한 신뢰를 유지하려면 무엇을 기초로 설치해야 하는가?

## Conclusion

문제는 리뷰가 과한 것이 아니라 **경계의 핵심 의미가 실행 가능한 형태로 보존되지 않는 것**이다. 현재 테스트는 주요 happy path와 일부 failure path를 잘 다루지만, configuration-to-runtime 연결, cross-domain error translation, orchestration event semantics처럼 리뷰어가 매번 추론해야 하는 contract가 남아 있다.

Foundation의 목적은 구현을 미리 완성하는 것이 아니라 다음을 안정적으로 만드는 것이다.

| Foundation element | Load-bearing role |
| --- | --- |
| Canonical contract | 무엇을 보존해야 하는지 결정한다. |
| Independent oracle | 구현과 별개로 성공과 실패를 판정한다. |
| Boundary harness | 실제 file, DuckDB, subprocess, Dagster event를 저비용으로 연결한다. |
| Focused suite | 변경 직후 수초 단위 feedback을 제공한다. |
| Review trigger | test로 증명할 수 없는 새 결정만 인간에게 올린다. |

## Why Review Cost Repeats

### Contract가 여러 artifact에 분산된다

`DataOperationRequest`, domain guide, OpenSpec, Dagster asset과 test가 각자 일부 의미를 소유한다. 예를 들어 `run_dbt_build=False`는 request field와 test에는 존재하지만 standard pipeline spec의 “dbt build를 호출한다”는 의미와 충돌한다.

이 상태에서는 한 파일의 변경이 단순 refactor인지 contract 변경인지 자동으로 구분할 수 없다.

### Mock이 연결 오류를 숨긴다

현재 dbt test는 `subprocess.run`을 stub하고 test가 artifact를 request 경로에 직접 쓴다. 이 방식은 timeout과 return code 처리에는 적합하지만, 실제 command가 artifact 생성 위치를 제어하는지는 증명하지 못한다.

즉 mock이 외부 process를 격리하는 동시에 검증해야 할 adapter contract까지 대신 구현한다.

### Result와 event의 의미가 구조보다 강하다

`MaterializeResult`를 반환했다는 사실보다 중요한 것은 “실제로 해당 asset이 새로 만들어졌는가”다. `frozen=True`를 사용했다는 사실보다 중요한 것은 “caller가 결과를 사후 변경할 수 없는가”다.

구조적 assertion만 있으면 semantic regression을 놓친다.

### 리뷰가 known risk와 new risk를 구분하지 않는다

이미 발견한 file-count, error leakage, skip materialization 문제도 다음 변경에서 다시 읽고 추론한다. known risk가 regression test로 이전되지 않았기 때문이다.

## Foundation Principles

### Test the boundary, not every implementation detail

`data_operations`는 application boundary다. 따라서 가장 가치 있는 test 대상은 내부 helper 호출 순서가 아니라 다음 observable behavior다.

- public entry point의 입력과 반환 결과
- 하위 domain failure가 caller에게 보이는 error type과 context
- subprocess command와 실제 artifact state
- DuckDB persisted state
- Dagster materialization event와 metadata
- 반환 결과의 사후 변경 가능 여부

### Use the lowest level that preserves the real risk

| Risk | Cheapest trustworthy level |
| --- | --- |
| Pydantic validation과 nested immutability | unit |
| raw partition 결과와 metadata | component with real DuckDB/files |
| dependency error translation | component with controlled boundary failure |
| dbt command-to-artifact connection | component with fake executable process |
| Dagster materialization semantics | integration with real Dagster event stream |
| full standard pipeline order | integration |

모든 것을 integration test로 만들면 느리고 원인 분리가 어렵다. 반대로 모든 것을 mock unit test로 만들면 연결 오류를 놓친다.

### Prefer independent oracles

- artifact path는 test가 subprocess argument를 재구현하지 않고, fake executable이 받은 target path에 실제 파일을 생성하게 한다.
- raw file count는 loader 내부 call count가 아니라 fixture file과 persisted row의 provenance로 판정한다.
- error translation은 mock call보다 public API에서 관찰된 exception type, cause와 context로 판정한다.
- orchestration skip은 log text보다 materialization event 유무로 판정한다.

### Separate decision gaps from implementation defects

테스트를 쓰기 전에 다음은 인간이 결정해야 한다.

1. `source_file_count`가 discovered file인지 contributing file인지
1. artifact configuration의 source of truth가 target directory인지 개별 path인지
1. raw-only 실행을 asset selection으로만 허용할지
1. public error contract가 모든 dependency failure를 감쌀지 예상 가능한 application failure만 감쌀지
1. immutability가 top-level assignment만 의미하는지 deep immutability인지

결정되지 않은 행동을 test가 먼저 규정하면 test가 architecture를 몰래 소유한다.

## What Tests Can Replace

다음 활동은 contract test가 안정화되면 매 변경마다 반복할 필요가 없다.

- public export에 duplicate pipeline coordinator가 생겼는지 수동 검색
- custom artifact path가 실제 실행에 반영되는지 코드 추적
- stale artifact가 성공으로 오인되는지 반복 검토
- 하위 domain exception이 stage별로 누출되는지 전수 추적
- skip된 dbt asset이 materialization으로 기록되는지 수동 확인
- result list가 사후 변경 가능한지 재검토

## What Still Requires Deep Review

- public contract의 의미를 변경하는 결정
- 새로운 stage 또는 domain dependency 도입
- Dagster asset graph나 ownership 변경
- recovery, approval, evaluation과 read-only lifecycle 경계 변경
- 새로운 persistence, concurrency, transaction model
- test oracle 자체가 production logic과 결합될 위험이 큰 변경

## Research Verdict

`data_operations` 개선의 우선순위는 production refactor보다 **contract decision과 test harness 설치**가 앞선다. 이 foundation이 없으면 각 fix가 새로운 모호성을 만들고, 다음 리뷰에서 다시 전체 경계를 해석해야 한다.

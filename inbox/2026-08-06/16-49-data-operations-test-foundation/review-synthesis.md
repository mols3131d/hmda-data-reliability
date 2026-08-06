---
title: Data Operations Review Synthesis
description: 기존 domain review의 finding을 root cause, 우선순위와 testability 관점에서 재평가한다.
tags:
  - data-operations
  - review
  - prioritization
  - root-cause
---

# Review Synthesis

## Verdict

**Revise.** 현재 구조를 다시 설계할 필요는 없다. Stage 분리, Dagster의 pipeline ownership, read-only incident lifecycle은 유지할 가치가 있다. 문제는 boundary contract가 configuration, result와 orchestration event에서 완전히 닫히지 않은 것이다.

## Root Causes

기존 다섯 finding은 독립적인 결함처럼 보이지만 세 가지 root cause로 압축된다.

### Configuration is accepted without proving operational effect

- custom dbt artifact path는 request가 수용하지만 command가 사용하지 않는다.
- `run_dbt_build`는 shared request가 수용하지만 stage function contract가 아니라 orchestration control이다.

**Root cause:** schema validation이 configuration의 operational validity를 보장한다고 간주한다.

### Boundary output describes implementation activity, not domain truth

- `source_file_count`는 discovered path count지만 문서는 processed file count로 읽힌다.
- skipped dbt build도 materialization result를 생성한다.

**Root cause:** 반환 type과 metadata가 생성되면 의미도 성립한다고 간주한다.

### Boundary ownership is documented but not enforced

- `data_operations`가 error를 통일한다고 문서화했지만 raw와 lifecycle dependency error가 누출된다.
- result가 immutable이라고 문서화했지만 nested list는 mutable하다.

**Root cause:** 문서 contract에 대응하는 regression oracle이 없다.

## Priority

| Priority | Finding | Why now | Best first move |
| ---: | --- | --- | --- |
| P1 | dbt artifact path contract | 정상적인 custom configuration이 reachable failure를 만든다. | fake dbt executable 기반 red component test |
| P1 | skipped Silver/Gold materialization | 데이터가 갱신되지 않았는데 갱신 event가 기록될 수 있다. | event absence를 oracle로 하는 integration test와 contract decision |
| P1 | public error boundary | caller가 하위 domain 구현에 결합된다. | stage별 exception translation matrix test |
| P2 | source file count semantics | 운영 metadata가 실제 실행 범위를 오해하게 한다. | 의미 결정 후 multi-file component test |
| P2 | nested result mutability | 사후 mutation으로 evidence가 변할 수 있다. | deep immutability unit test |

## Finding Validation

### Artifact path mismatch

확정된 defect다. Request는 개별 artifact path를 설정으로 받지만 `dbt build` command에는 target output location을 전달하지 않는다. 현재 test는 stub이 원하는 위치에 파일을 직접 생성하므로 false green이 가능하다.

### Error unification

문서 contract 기준으로 defect다. 다만 broad `except Exception`은 해결이 아니다. Translation 대상은 `HMDADataFoundationError`, `ReliabilityError`, DuckDB connection/operation failure처럼 public stage가 책임지는 예상 가능한 application failure로 제한해야 한다.

### Skip materialization

단순한 API 배치 취향이 아니다. Standard pipeline spec은 raw 다음 dbt build 실행을 요구한다. dbt를 실행하지 않은 asset에 materialization을 기록하면 event semantics가 실제 data state와 달라진다.

### File count

현재 naming과 문서가 모호하다. “처리 파일”을 file 자체가 query에 참여한 것으로 볼지, 선택 partition에 row를 실제 기여한 것으로 볼지 먼저 결정해야 한다. 결정을 하지 않고 단순히 `len(filtered_paths)`로 바꾸면 빈 contribution file 같은 edge case가 남는다.

### Immutability

문서가 “모두 변경 불가”를 요구하므로 nested collection mutation은 contract gap이다. 하지만 deep immutability가 필요하지 않다면 문서를 완화하는 것도 가능한 결정이다. Evidence 성격의 result라는 점에서는 tuple이 더 일관된다.

## Additional Risks

### Baseline shape compatibility

현재 compatibility는 asset과 partition만 비교한다. Detector는 baseline에 없는 current null-rate column을 `0.0` baseline으로 해석한다. `profile_columns`가 다른 snapshot을 비교할 수 있는지가 명시되지 않아 false positive 가능성이 있다.

이는 현재 spec 위반으로 단정하지 않고 decision gap으로 유지한다.

### Artifact validity

현재 artifact 존재만 확인한다. Foundation 단계에서는 우선 invocation-to-path 연결과 stale rejection이 중요하다. JSON schema 또는 invocation metadata 검증은 reliability impact analysis가 실제로 필요로 하는 최소 구조를 기준으로 별도 결정해야 한다.

### Raw load failure atomicity at application boundary

Partition loader 내부 transaction은 보호되지만, application boundary에서 failure 후 어떤 state와 metadata가 보장되는지 직접 검증하는 test가 없다. Loader domain test가 충분하면 중복하지 말고, `data_operations`가 추가 보장을 선언할 때만 contract test를 둔다.

## Review Scope Reduction After Foundation

아래 test가 설치되면 이후 일반 변경 리뷰에서는 해당 동작을 다시 전수 분석하지 않는다.

| Protected by test | Review can focus on |
| --- | --- |
| artifact path end-to-end | 새로운 dbt option과 security/environment 영향 |
| stage error translation | 새로운 exception class와 context policy |
| event semantics | asset graph 또는 job contract 변경 |
| count semantics | provenance 정의 변경 |
| deep immutability | 새 result field의 의미 |

## Final Assessment

현재 finding은 architecture rewrite의 근거가 아니라 **누락된 executable contract를 설치할 근거**다. 각 finding을 하나의 대형 fix PR에 묶으면 review cost가 다시 증가한다. Contract decision과 focused red test를 작은 단위로 만들고, production fix는 그 test를 통과시키는 범위로 제한해야 한다.

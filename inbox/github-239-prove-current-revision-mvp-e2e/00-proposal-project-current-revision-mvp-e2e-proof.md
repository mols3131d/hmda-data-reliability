---
type: proposal
title: "Current-Revision MVP E2E Proof Proposal"
description: "Proposes a same-revision end-to-end proof that closes the MVP acceptance boundary with executable evidence."
---

# Current-Revision MVP E2E Proof Proposal

> [!IMPORTANT]
> **제안:** 새 기능을 더 만들기 전에, 현재 MVP가 실제로 완결됐는지를 하나의 clean revision에서 끝까지 증명한다. 과거의 개별 성공 기록은 선행 근거로 사용하되 current revision의 acceptance를 대신하지 않는다.

## Proposal Summary

다음 핵심 작업으로 Current-revision MVP E2E proof를 진행한다.

현재 repository에는 중요한 개별 proof가 이미 있다.

| Work | Already proven |
| --- | --- |
| #220 | deterministic system recovery E2E |
| #228 | OpenSpec 및 dependency/runtime 변경의 CI admission |
| #229 | 실제 Apache Airflow DAGRun |

문제는 이 proof들이 서로 다른 revision에서 만들어졌다는 점이다. [`docs/mvp.md`](../../docs/mvp.md)는 각 capability가 한 번씩 성공했는지가 아니라 **하나의 current revision에서 Data Lake, Reliability, bounded Agentic review, live model invocation, Safety와 Reproducibility가 함께 성립하는지**를 MVP 완료 조건으로 둔다.

따라서 지금 필요한 것은 기능 추가가 아니라 현재 구현을 하나의 시스템으로 검증하고 MVP를 닫을 수 있는지 판정하는 일이다.

## Why Now

### Individual Success Does Not Prove the Current System

MVP가 증명해야 하는 대상은 다음 연결 전체다.

```text
HMDA source
→ Bronze / dbt analytical state
→ Airflow data-plane execution
→ deterministic incident / recovery
→ bounded Review AI
→ actual provider invocation
→ safety boundary
→ reproducible evidence
```

각 부분이 과거에 성공했더라도 이후 repository가 바뀌면 현재 상태에서 이 연결 전체가 유지된다고 볼 수 없다. 특히 중요한 실패는 component 내부보다 경계 사이에서 나타날 수 있다.

- Airflow task는 성공했지만 promoted data나 Asset evidence가 기대와 다를 수 있다.
- Recovery는 성공했지만 approval identity와 mutation 대상이 어긋날 수 있다.
- Review AI output은 정상처럼 보여도 deterministic validator나 evidence binding과 불일치할 수 있다.
- Provider failure가 deterministic recovery authority에 영향을 주면 안 된다.

Current-revision E2E는 이런 **경계 사이의 실패**를 찾기 위한 proof다.

### Evidence Must Be Bound to a Revision

과거 proof는 해당 revision에 대한 유효한 evidence다. 하지만 Airflow runtime, dependency, shared utility, validation, artifact handling 또는 Agentic contract가 바뀌면 그 결과를 현재 revision의 acceptance로 그대로 사용할 수 없다.

Live model invocation도 마찬가지다. model/config, prompt identity, evidence와 project revision이 함께 남아야 어떤 상태를 검증했는지 설명할 수 있다.

Current-revision proof는 acceptance를 exact Git revision에 묶어 이 문제를 해결한다.

### Deterministic and Live Proofs Are Not Interchangeable

Review AI와 Runtime AI의 deterministic tests는 contract, validator, provider adapter와 persistence를 반복 검증하는 데 적합하다. 그러나 실제 provider가 호출됐고 어떤 evidence와 revision에서 결과가 만들어졌는지는 live invocation으로만 증명할 수 있다.

따라서 둘 다 필요하다.

- **Deterministic contract proof:** contract와 guard가 반복 검증 가능하다.
- **Live invocation proof:** 실제 model call과 persisted provenance가 proof revision에 결합된다.

### Safety Is About Authority, Not AI Quality

이 프로젝트에서 AI는 advisory다. 핵심은 응답의 자연스러움이 아니라 **AI output이 deterministic recovery authority를 바꾸거나 mutation을 직접 일으킬 수 없다는 것**이다.

Current-revision proof는 최소한 다음을 확인해야 한다.

- LLM output만으로 recovery 또는 data mutation이 실행되지 않는다.
- Provider가 unavailable이어도 deterministic recovery authority는 달라지지 않는다.
- Malformed 또는 policy-invalid output은 deterministic validation을 우회하지 못한다.
- Approval은 다른 proposal이나 revision에 재사용되지 않는다.

### Delaying Increases Proof Cost

Deterministic recovery, actual Airflow runtime, CI admission 등 통합 proof의 선행 조건은 이미 마련됐다. 여기서 기능을 더 추가하면 proof revision이 계속 움직이고 실패 원인도 넓어진다.

지금 acceptance를 확정해야 이후 발견되는 문제가 기존 gap인지 새 regression인지 구분할 수 있고, 다음 개발 단계도 더 작은 상태에서 시작할 수 있다.

## What to Prove

Canonical acceptance는 [`docs/mvp.md`](../../docs/mvp.md)가 소유한다. 이 작업은 acceptance를 새로 정의하지 않고 current revision에서 다음 여섯 항목을 각각 `PASS`, `FAIL`, `BLOCKED`로 판정한다.

| Acceptance | Proof question |
| --- | --- |
| Data Lake proof | HMDA source가 Bronze와 dbt analytical layer까지 같은 revision에서 흐르는가? |
| Reliability proof | Representative synthetic incident가 deterministic recovery와 re-validation까지 닫히는가? |
| Agentic contract proof | Structured review와 deterministic validation/evaluation을 반복 검증할 수 있는가? |
| Live Agentic proof | 실제 provider invocation과 provenance가 proof revision에 결합되는가? |
| Safety proof | AI가 deterministic guardrail과 proposal-bound approval을 우회하지 못하는가? |
| Reproducibility proof | 핵심 deterministic path와 evidence chain을 같은 revision에서 다시 설명할 수 있는가? |

여섯 항목이 모두 `PASS`일 때만 MVP completion을 주장한다. 하나라도 `FAIL` 또는 `BLOCKED`이면 결과는 유효한 진단이지만 MVP 완료 증거는 아니다.

## How to Maintain the Proof Revision

Acceptance evidence는 **exact proof revision SHA**에만 유효하다.

1. Proposal, checklist와 실행 준비 artifact처럼 repository에 커밋해야 하는 변경은 final full proof 전에 끝낸다.
1. Final full proof는 그 시점의 exact branch HEAD에서 실행한다.
1. 실행 후 tracked change가 없으면 그 HEAD를 proof revision으로 사용한다.
1. 결과와 evidence pointer는 proof SHA를 바꾸지 않는 PR metadata 또는 runtime evidence에 기록할 수 있다.
1. 실행 후 implementation이나 repository artifact를 다시 수정하면 새 revision으로 보고 영향을 받는 proof를 다시 실행한다.

이 규칙은 결과를 기록하기 위한 commit 때문에 실제 검증한 SHA와 최종 HEAD가 어긋나는 문제를 막는다.

## Execution Approach

1. **Proof revision 준비** — clean tracked state에서 exact Git SHA를 고정하고 checklist와 configuration 준비를 끝낸다.
1. **Deterministic baseline 확인** — 전체 baseline과 Data Lake, Reliability, Review AI, Runtime AI의 focused validation을 먼저 통과시킨다.
1. **실제 boundary 실행** — 같은 revision에서 HMDA Data Lake, Apache Airflow runtime, synthetic recovery lifecycle과 actual provider invocation을 실행한다.
1. **Persisted evidence 확인** — exit code뿐 아니라 data state, dbt artifact, Airflow state/Asset evidence, proposal/approval identity, invocation provenance와 validation 결과를 직접 대조한다.
1. **Reproducibility 확인** — 핵심 deterministic path를 다시 실행해 의미적으로 같은 결과와 evidence chain을 재현할 수 있는지 확인한다. Live LLM 문장 자체의 동일성은 요구하지 않지만 provenance와 deterministic validation은 추적 가능해야 한다.

Test-only 우회로 production contract를 대신 증명하지 않는다. Deterministic baseline이 깨져 있으면 live provider 결과로 이를 보완하지 않는다.

## Allowed Changes in This PR

이 branch는 문서 전용이 아니다. Proof가 기존 MVP contract 위반을 직접 드러내면 같은 branch에서 최소 remediation을 수행할 수 있다.

다만 다음 조건을 모두 만족해야 한다.

- Proof가 직접 재현한 failure 또는 blocker를 해결한다.
- 이미 정의된 MVP contract를 만족시키는 변경이다.
- 새 capability를 추가하지 않는다.
- 가장 작은 coherent change로 제한할 수 있다.
- 변경 후 영향을 받는 proof를 새 SHA에서 다시 실행할 수 있다.

새 dependency 또는 architecture 확장, 독립적인 refactor, MVP scope 변경처럼 별도 판단이 필요한 변경은 이 PR에 포함하지 않는다. 그런 변경이 필요하면 별도 work unit으로 분리하고 이 proof는 해당 시점에 `FAIL` 또는 `BLOCKED`로 남긴다.

## Scope

포함한다.

- current revision deterministic baseline
- HMDA Data Lake 실행과 evidence 확인
- Apache Airflow data-plane 실행
- representative synthetic incident → recovery → re-validation
- Review AI / Runtime AI deterministic validation
- actual provider invocation과 persisted provenance 검증
- negative safety boundary 검증
- reproducibility rerun
- 위 admission rule을 만족하는 MVP blocker의 최소 remediation
- MVP acceptance 판정과 proof SHA/evidence reference 기록

의도적으로 제외한다.

- 새로운 product capability
- MVP scope 확장
- cloud/distributed deployment
- Airflow scheduling 또는 distributed executor 확대
- autonomous RCA, multi-agent workflow, approval UI
- production SLO나 security-grade authorization
- unrelated cleanup, refactor 또는 문서 정리

## Result Classification

이 작업의 목적은 모든 결과를 초록색으로 만드는 것이 아니라 **현재 상태를 정직하게 판정하는 것**이다.

실패를 발견하면 먼저 다음 evidence를 고정한다.

```text
Revision:
Stage:
Command:
Expected:
Observed:
Primary error:
Relevant evidence:
Acceptance impact:
```

결과는 다음처럼 구분한다.

- **PASS:** 요구한 proof와 evidence가 proof revision에서 성립한다.
- **FAIL:** 실행 가능했지만 contract 또는 acceptance를 위반했다.
- **BLOCKED:** 환경이나 선행 조건 때문에 유효한 proof 자체를 만들 수 없다.

`FAIL`을 발견했다고 즉시 scope를 넓히지 않는다. 먼저 이 PR의 remediation admission rule을 적용한다.

## Expected Outcome

이 작업이 최종적으로 답해야 하는 질문은 하나다.

> **이 proof revision은 HMDA data plane, deterministic reliability, bounded Agentic review와 live invocation을 함께 실행해도 안전하고 재현 가능한 MVP인가?**

모든 acceptance가 `PASS`라면 MVP closeout을 근거 있게 시작할 수 있다. `FAIL`이면 정확한 미완성 지점을 알 수 있고, `BLOCKED`이면 무엇이 실제 proof를 막는지 분리할 수 있다.

어느 결과든 서로 다른 revision의 성공 기록을 조합해 완성을 추정하는 것보다 강하다. 현재 시스템이 실제로 무엇을 증명할 수 있는지 exact revision과 evidence로 설명할 수 있기 때문이다.

## Starting Point

- Branch base: `main@7497a57bbd2ed03ba6f887611bd32bda3b7e9520`
- Canonical MVP owner: [`docs/mvp.md`](../../docs/mvp.md)
- Long-term trust boundary: [`docs/VISION.md`](../../docs/VISION.md)

이 문서는 작업 제안과 실행 방향을 소유하는 non-canonical Inbox artifact다. MVP acceptance와 durable contract는 canonical owner와 실제 executable evidence가 소유한다.

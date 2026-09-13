---
type: proposal
title: "Current-Revision MVP E2E Proof Proposal"
description: "Proposes a same-revision end-to-end proof that closes the MVP acceptance boundary with executable evidence."
---

# Current-Revision MVP E2E Proof Proposal

> [!IMPORTANT]
> **제안:** 새 기능을 더 만들기 전에, 현재 MVP가 실제로 완결됐는지를 하나의 clean revision에서 끝까지 증명한다. 과거의 개별 성공 기록은 선행 근거로 사용하되 현재 revision의 acceptance를 대신하지 않는다.

## Decision

이 작업을 다음 핵심 작업으로 진행하는 것을 권장한다.

현재 repository에는 deterministic recovery E2E, OpenSpec/CI admission, 실제 Airflow DAGRun 등 중요한 proof가 이미 존재한다. 그러나 [`docs/mvp.md`](../../docs/mvp.md)가 요구하는 완료 조건은 각 capability가 서로 다른 시점에 한 번씩 성공했다는 사실이 아니다. **하나의 current revision에서 Data Lake, Reliability, bounded Agentic review, live model invocation, Safety와 Reproducibility가 함께 성립해야 한다.**

따라서 지금 필요한 것은 기능 수를 늘리는 일이 아니라 현재 구현을 하나의 시스템으로 검증하고, MVP를 실제로 닫을 수 있는지 판정하는 일이다. 이 proof를 건너뛰면 서로 다른 revision의 성공 기록을 조합해 현재 MVP가 완료됐다고 추정하게 된다. 그 상태에서 closeout이나 다음 capability 개발을 시작하면 이후 발견되는 실패가 regression인지 원래 남아 있던 gap인지 구분하기 어려워진다.

## Why This Proof Is Necessary

### Component Success Is Not System Proof

#220은 deterministic system recovery E2E를, #228은 OpenSpec과 dependency/runtime 변경의 CI admission을, #229는 실제 Apache Airflow DAGRun을 각각 강화했다. 이 작업들은 중요한 선행 조건이지만 서로 다른 revision에서 수행됐다.

그 사이 repository는 계속 바뀌었다. 각 변경이 독립적으로 안전하더라도 현재 상태에서 모든 경계가 동시에 성립한다는 보장은 없다. MVP가 주장하는 시스템은 다음 연결 전체다.

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

개별 component proof는 이 연결을 대신할 수 없다.

### Evidence Has a Revision Boundary

과거 proof가 틀렸다는 뜻은 아니다. 과거 proof는 해당 revision의 사실이다. 문제는 그것을 현재 revision의 acceptance로 그대로 사용할 수 없다는 점이다.

Airflow runtime, dependency, shared utility, validation, artifact handling 또는 Agentic contract가 바뀌면 이전 성공 기록만으로 현재 상태를 설명할 수 없다. Live model invocation 역시 model/config, prompt identity, evidence와 project revision이 함께 남아야 현재 실행의 증거가 된다.

Current-revision proof는 이 freshness 문제를 exact Git revision에 묶어 해결한다.

### The Highest-Risk Failures Sit Between Boundaries

이 프로젝트의 중요한 실패는 한 함수가 틀리는 경우에만 있지 않다. 각 계층이 따로는 정상이어도 연결했을 때 contract가 깨질 수 있다.

- Airflow task가 성공했지만 promoted data나 Asset evidence가 기대와 다를 수 있다.
- Reliability recovery가 성공했지만 approval identity와 실제 mutation 대상이 어긋날 수 있다.
- Review AI output이 정상처럼 보여도 deterministic validator 또는 evidence binding과 불일치할 수 있다.
- Provider failure가 deterministic recovery authority에 영향을 주면 안 된다.
- 모든 단계가 성공해도 같은 revision과 evidence chain으로 연결되지 않으면 재현 가능한 system proof가 아니다.

Current-revision E2E는 이런 **경계 사이의 실패**를 발견하기 위한 작업이다.

### Live Agentic Proof Is a Different Kind of Evidence

Review AI와 Runtime AI의 deterministic tests는 schema, validation, provider adapter와 persistence contract를 반복 검증하는 데 적합하다. 그러나 실제 provider가 호출됐고 어떤 입력과 revision에서 결과가 만들어졌는지는 live invocation으로만 증명할 수 있다.

MVP는 둘을 모두 요구한다.

- **Deterministic contract proof:** contract와 guard가 반복 검증 가능하다.
- **Live invocation proof:** 실제 model call과 persisted provenance가 current revision에 결합된다.

둘 중 하나만 있어서는 Agentic acceptance가 닫히지 않는다.

### Safety Is an Authority Boundary

이 프로젝트에서 AI는 advisory다. 자연스러운 응답을 생성하는 것보다 중요한 것은 **AI가 없어도 deterministic recovery authority가 유지되고, AI output만으로 mutation을 일으킬 수 없다는 것**이다.

따라서 happy path만으로는 충분하지 않다. Current-revision proof는 최소한 다음 질문에 evidence로 답해야 한다.

- LLM output만으로 recovery 또는 data mutation이 실행될 수 있는가? → 아니어야 한다.
- provider가 unavailable이어도 deterministic recovery authority가 달라지는가? → 달라지지 않아야 한다.
- malformed 또는 policy-invalid output이 deterministic validation을 우회하는가? → 우회하지 않아야 한다.
- approval이 다른 proposal이나 revision에 재사용될 수 있는가? → 금지되어야 한다.

## Why Now

핵심 deterministic recovery와 실제 Airflow runtime proof가 이미 존재하고, canonical Spec 변경과 dependency/runtime 변경을 CI에 연결하는 admission gap도 닫혔다. 즉 통합 proof를 수행할 선행 기반이 마련됐다.

반대로 기능을 더 추가하면 proof revision이 계속 움직이고 실패 원인도 넓어진다. **현재 구현이 MVP acceptance를 충족하는지 먼저 확정하는 것이 다음 개발 단계의 출발점을 더 작고 명확하게 만든다.**

## What This Work Will Prove

Canonical acceptance는 [`docs/mvp.md`](../../docs/mvp.md)가 소유한다. 이 작업은 그 여섯 항목을 새로 정의하지 않고 current revision에서 각각 `PASS`, `FAIL`, `BLOCKED`로 판정한다.

| Acceptance | Proof question |
| --- | --- |
| Data Lake proof | HMDA source가 Bronze와 dbt analytical layer까지 같은 revision에서 흐르는가? |
| Reliability proof | representative synthetic incident가 deterministic recovery와 re-validation까지 닫히는가? |
| Agentic contract proof | structured review와 deterministic validation/evaluation을 반복 검증할 수 있는가? |
| Live Agentic proof | 실제 provider invocation과 provenance가 proof revision에 결합되는가? |
| Safety proof | AI가 deterministic guardrail과 proposal-bound approval을 우회하지 못하는가? |
| Reproducibility proof | 핵심 deterministic path와 evidence chain을 같은 revision에서 다시 설명할 수 있는가? |

여섯 항목이 모두 `PASS`일 때만 MVP completion을 주장한다. `FAIL` 또는 `BLOCKED`가 하나라도 있으면 이 작업의 결과는 유효한 진단이지만 MVP 완료 증거는 아니다.

## Proof Revision and Evidence Recording

Acceptance evidence는 **exact proof revision SHA**에 묶는다. 실행 결과는 그 SHA에 대해서만 유효하다.

최종 full proof 이후 tracked file을 변경하면 branch HEAD가 달라지므로 새 HEAD를 검증했다고 주장하지 않는다. 이를 피하기 위해 다음 원칙을 적용한다.

1. repository에 커밋해야 하는 proposal, checklist와 실행 준비 artifact는 최종 full proof 전에 정리한다.
1. 최종 full proof는 그 시점의 exact branch HEAD를 대상으로 실행한다.
1. 실행 뒤 새 tracked change가 없으면 그 HEAD를 acceptance의 proof revision으로 사용한다.
1. 실행 결과와 evidence pointer는 proof SHA를 바꾸지 않는 PR metadata 또는 runtime evidence에 기록할 수 있다.
1. 실행 뒤 repository artifact나 implementation을 다시 수정해야 한다면 새 revision이 생긴 것으로 보고 영향을 받는 proof를 다시 실행한다.

이 규칙은 “결과를 기록하기 위해 commit했더니 검증한 SHA가 다시 과거가 되는” 순환을 막고, 최종 acceptance가 실제 검증한 revision을 가리키게 한다.

## Execution Strategy

### 1. Prepare the Proof Revision

Clean tracked state에서 branch의 exact Git SHA를 고정한다. 실행 전 필요한 checklist와 configuration 준비를 끝낸다.

### 2. Close Deterministic Evidence First

전체 deterministic baseline과 focused Data Lake, Reliability, Review AI, Runtime AI surface를 먼저 확인한다. 이 단계가 깨져 있으면 live provider 결과로 보완하지 않는다.

### 3. Run the Real Boundaries

같은 revision에서 HMDA Data Lake, Apache Airflow runtime, synthetic recovery lifecycle과 actual provider invocation을 실행한다. test-only 우회로 production contract를 대신 증명하지 않는다.

### 4. Inspect Persisted Evidence, Not Only Exit Codes

명령의 성공 여부만 보지 않는다. Data state, dbt artifact, Airflow state/Asset evidence, proposal/approval identity, invocation provenance와 validation 결과를 직접 대조한다.

### 5. Re-run the Deterministic Core

핵심 path를 다시 실행해 의미적으로 같은 결과와 evidence chain을 재현할 수 있는지 확인한다. Live LLM output의 문장 자체가 동일할 필요는 없지만 invocation provenance와 deterministic validation은 추적 가능해야 한다.

## This Branch Is Not Documentation-Only

이 branch의 목적은 계획 문서를 만드는 것이 아니라 **MVP proof를 실제로 완료하는 것**이다.

Proof가 현재 MVP contract를 위반하는 구현 결함을 발견하면 같은 branch에서 remediation할 수 있다. 다만 다음 조건을 모두 만족해야 한다.

- proof가 직접 재현한 failure 또는 blocker를 해결한다.
- 이미 정의된 MVP contract를 만족시키는 변경이며 새 capability를 추가하지 않는다.
- 가장 작은 coherent change로 제한할 수 있다.
- 변경 후 영향을 받는 proof를 새 SHA에서 다시 실행할 수 있다.

새 dependency 또는 architecture 확장, 독립적인 refactor, MVP scope 변경처럼 별도 판단이 필요한 변경은 이 PR에 흡수하지 않는다. 그런 변경이 필요하면 별도 work unit으로 분리하고 이 proof는 해당 시점에 `FAIL` 또는 `BLOCKED`로 남긴다.

## Scope Boundary

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

- 새로운 product capability 추가
- MVP scope 확장
- cloud/distributed deployment
- Airflow scheduling 또는 distributed executor 확대
- autonomous RCA, multi-agent workflow, approval UI
- production SLO나 security-grade authorization
- unrelated cleanup, refactor 또는 문서 정리

## Evidence and Failure Policy

이 작업은 모든 것을 초록색으로 만드는 것이 목적이 아니다. **현재 상태를 정직하게 판정하는 것**이 목적이다.

실패를 발견하면 먼저 evidence를 고정한다.

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

그 다음 결과를 구분한다.

- **PASS:** 요구한 proof와 evidence가 proof revision에서 성립한다.
- **FAIL:** 실행 가능했지만 contract 또는 acceptance를 위반했다.
- **BLOCKED:** 환경이나 선행 조건 때문에 유효한 proof 자체를 만들 수 없다.

FAIL을 발견했다고 즉시 scope를 넓히지 않는다. remediation admission rule을 먼저 적용한다.

## Expected Outcome

이 작업이 답해야 하는 질문은 하나다.

> **이 proof revision은 HMDA data plane, deterministic reliability, bounded Agentic review와 live invocation을 함께 실행해도 안전하고 재현 가능한 MVP인가?**

모든 acceptance가 `PASS`라면 MVP closeout을 근거 있게 시작할 수 있다. `FAIL`이라면 정확한 미완성 지점을 알 수 있고, `BLOCKED`라면 무엇이 실제 proof를 막는지 분리할 수 있다.

어느 결과든 개별 성공 기록을 조합해 완성을 추정하는 것보다 강하다. 현재 시스템이 실제로 무엇을 증명할 수 있는지 exact revision과 evidence로 설명할 수 있기 때문이다.

## Starting Point

- Branch base: `main@7497a57bbd2ed03ba6f887611bd32bda3b7e9520`
- Canonical MVP owner: [`docs/mvp.md`](../../docs/mvp.md)
- Long-term trust boundary: [`docs/VISION.md`](../../docs/VISION.md)

이 문서는 작업 제안과 실행 방향을 소유하는 non-canonical Inbox artifact다. MVP acceptance와 durable contract는 canonical owner와 실제 executable evidence가 소유한다.

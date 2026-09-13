---
type: proposal
title: "Current-Revision MVP E2E Proof Proposal"
description: "Proposes a same-revision end-to-end proof that closes the MVP acceptance boundary with executable evidence."
---

# Current-Revision MVP E2E Proof Proposal

> [!IMPORTANT]
> **제안:** 새 기능을 더 만들기 전에, 현재 MVP가 실제로 완결됐는지를 하나의 clean revision에서 끝까지 증명한다. 이미 확보한 개별 테스트와 runtime proof를 재사용하되, 서로 다른 시점의 성공 기록을 합쳐서 현재 상태가 검증됐다고 간주하지 않는다.

## Decision

이 작업을 다음 핵심 작업으로 진행하는 것을 권장한다.

현재 repository에는 deterministic recovery E2E, OpenSpec/CI admission, 실제 Airflow DAGRun 등 중요한 proof가 이미 존재한다. 그러나 이 결과들은 서로 다른 revision과 작업 단위에서 만들어졌다. [`docs/mvp.md`](../../docs/mvp.md)가 요구하는 완료 조건은 개별 capability가 각각 한 번 성공했다는 사실이 아니라, **하나의 current revision에서 Data Lake → Reliability → bounded Agentic review → live model invocation → Safety → Reproducibility가 함께 성립한다는 증거**다.

따라서 지금 필요한 것은 기능 수를 늘리는 일이 아니라 **현재 구현을 하나의 시스템으로 검증하고 MVP를 닫을 수 있는지 판정하는 일**이다.

## Why This Proof Is Necessary

### Component Success Is Not System Proof

#220은 deterministic system recovery E2E를, #228은 OpenSpec과 dependency/runtime 변경의 CI admission을, #229는 실제 Apache Airflow DAGRun을 각각 강화했다. 이 작업들은 중요한 선행 조건이지만 서로 다른 revision에서 수행됐다.

그 사이 repository는 계속 바뀌었다. 각 변경이 독립적으로 안전하더라도 현재 `main`에서 모든 경계가 동시에 성립한다는 보장은 없다. 특히 다음 연결은 개별 테스트만으로 완전히 대신할 수 없다.

```text
actual HMDA source
→ Bronze / dbt analytical state
→ Airflow data-plane execution
→ deterministic incident / recovery
→ bounded Review AI
→ actual provider invocation
→ safety boundary
→ reproducible evidence
```

MVP는 이 연결 전체가 하나의 증명 단위다.

### Evidence Becomes Stale When the Revision Changes

과거 proof가 틀렸다는 뜻은 아니다. 과거 proof는 해당 revision의 사실이다. 문제는 그것을 현재 revision의 acceptance로 그대로 사용할 수 없다는 점이다.

예를 들어 Airflow runtime이 과거 revision에서 성공했더라도 이후 configuration, dependency, shared utility, validation 또는 artifact handling이 바뀌면 현재 상태는 다시 확인해야 한다. Live model invocation도 prompt, model configuration, evidence binding과 project revision이 함께 기록돼야 현재 실행의 증거가 된다.

**Current-revision proof는 evidence freshness를 Git SHA에 고정한다.** 어떤 상태를 검증했고 어떤 결과를 얻었는지 다시 설명할 수 있게 만드는 것이 목적이다.

### The Most Important Failures Live Between Boundaries

이 프로젝트의 위험은 한 함수가 틀리는 것에만 있지 않다. 각 계층이 따로는 맞지만 연결했을 때 contract가 깨지는 경우가 더 중요하다.

- Airflow task는 성공했지만 실제 promoted data나 Asset evidence가 맞지 않을 수 있다.
- Reliability recovery는 성공했지만 approval identity와 실제 mutation 대상이 어긋날 수 있다.
- Review AI output은 정상처럼 보여도 deterministic validator 또는 evidence binding과 불일치할 수 있다.
- Provider failure가 deterministic recovery authority에 영향을 주면 안 된다.
- 각 단계가 성공해도 같은 revision과 evidence chain으로 연결되지 않으면 재현 가능한 시스템 proof가 아니다.

Current-revision E2E는 이런 **경계 사이의 실패**를 발견하기 위한 작업이다.

### Live Agentic Proof Cannot Be Replaced by Deterministic Tests

Review AI와 Runtime AI의 deterministic tests는 schema, validation, provider adapter와 persistence contract를 반복 검증하는 데 적합하다. 그러나 실제 provider가 호출됐고 그 판단이 어떤 입력과 revision에서 만들어졌는지는 live invocation으로만 증명할 수 있다.

MVP는 최소 한 번의 observable live model proof를 요구한다. 따라서 최종 acceptance는 다음 둘을 분리해서 모두 확인해야 한다.

- **Deterministic contract proof:** 같은 입력에 대해 계약과 guard가 반복 검증 가능하다.
- **Live invocation proof:** 실제 model call과 persisted provenance가 current revision에 결합된다.

둘 중 하나만 있어서는 MVP의 Agentic acceptance가 닫히지 않는다.

### Safety Must Be Proven as an Authority Boundary

이 프로젝트에서 AI의 역할은 advisory다. 자연스러운 응답을 생성했다는 사실보다 중요한 것은 **AI가 없어도 deterministic recovery authority가 유지되고, AI output만으로 mutation을 일으킬 수 없다는 것**이다.

따라서 happy path만 실행해서는 충분하지 않다. Current-revision proof는 최소한 다음 질문에 근거로 답해야 한다.

- LLM output만으로 recovery 또는 data mutation이 실행될 수 있는가? → 아니어야 한다.
- provider가 unavailable이어도 deterministic recovery authority가 달라지는가? → 달라지지 않아야 한다.
- malformed 또는 policy-invalid output이 deterministic validation을 우회하는가? → 우회하지 않아야 한다.
- approval이 다른 proposal이나 revision에 재사용될 수 있는가? → 금지되어야 한다.

이 경계가 실제 current revision에서 유지돼야 MVP가 주장하는 bounded Agentic review가 설득력을 가진다.

## Why Now

지금은 이 proof를 수행하기 좋은 시점이다.

핵심 deterministic recovery와 실제 Airflow runtime proof가 이미 존재하고, canonical Spec 변경과 dependency/runtime 변경을 CI에 연결하는 admission gap도 닫혔다. 즉 새로운 기능을 추가하기 전에 현재 시스템을 통합 검증할 수 있는 선행 기반이 마련됐다.

반대로 이 시점에서 기능을 더 추가하면 proof revision이 계속 움직이고 실패 원인도 넓어진다. **현재 구현이 MVP acceptance를 충족하는지 먼저 확정한 뒤 다음 단계로 넘어가는 편이 더 작고 명확한 작업 단위를 만든다.**

## What This Work Will Prove

최종 보고는 [`docs/mvp.md`](../../docs/mvp.md)의 acceptance에 맞춰 다음 여섯 항목을 각각 `PASS`, `FAIL`, `BLOCKED`로 판정한다.

| Acceptance | Proof question |
| --- | --- |
| Data Lake proof | 실제 HMDA source가 Bronze와 dbt staging/mart까지 같은 revision에서 흐르는가? |
| Reliability proof | synthetic incident가 deterministic detection → approved recovery → re-validation까지 닫히는가? |
| Agentic contract proof | structured review와 deterministic validation/evaluation을 반복 검증할 수 있는가? |
| Live Agentic proof | 실제 provider invocation과 provenance가 current Git revision에 결합되는가? |
| Safety proof | AI가 approval/recovery authority를 우회하지 못하는가? |
| Reproducibility proof | 핵심 deterministic path와 evidence chain을 같은 revision에서 다시 설명하고 재실행할 수 있는가? |

Airflow data-plane proof는 Data Lake와 system execution evidence의 일부로 함께 확인한다. 과거 #229 결과를 참고하되 current revision에서 필요한 실행을 다시 수행한다.

## Execution Strategy

### 1. Pin a Clean Proof Revision

Proof 시작 시 branch의 exact Git SHA와 clean tracked worktree를 고정한다. 실행 도중 코드나 설정을 수정해 SHA가 바뀌면 기존 결과를 새 revision의 acceptance로 승격하지 않는다.

### 2. Close Deterministic Evidence First

전체 deterministic tests와 focused Data Lake, Reliability, Review AI, Runtime AI surface를 먼저 확인한다. 이 단계가 깨져 있으면 live provider 결과로 보완하지 않는다.

### 3. Run the Real Boundaries

같은 revision에서 실제 HMDA source, DuckDB/dbt, Apache Airflow runtime, synthetic recovery lifecycle과 actual provider invocation을 실행한다. test-only 우회로 production contract를 대신 증명하지 않는다.

### 4. Inspect Persisted Evidence, Not Only Exit Codes

명령의 성공 여부만 보지 않는다. Data state, dbt artifact, Airflow state/Asset evidence, proposal/approval identity, invocation provenance와 validation 결과를 직접 대조한다.

### 5. Re-run the Deterministic Core

핵심 path를 다시 실행해 의미적으로 같은 결과와 evidence chain을 재현할 수 있는지 확인한다. Live LLM output의 문장 자체가 동일할 필요는 없지만 invocation provenance와 deterministic validation은 추적 가능해야 한다.

## This Branch Is Not Documentation-Only

이 branch의 목적은 계획 문서를 만드는 것이 아니라 **MVP proof를 실제로 완료하는 것**이다.

Proof가 현재 MVP contract를 위반하는 구현 결함을 발견하면, 해당 blocker를 이 branch에서 최소 범위로 수정할 수 있다. 다만 수정은 기존 MVP acceptance를 사실로 만들기 위한 remediation으로 제한한다.

수정으로 revision이 바뀌면 영향을 받는 proof를 새 SHA에서 다시 실행한다. 이 규칙은 실패를 숨기기 위한 임시 우회나 test-only bypass를 막고, 최종 결과가 실제 repository state를 설명하게 한다.

## Scope Boundary

포함한다.

- current revision deterministic baseline
- 실제 HMDA Data Lake 실행과 evidence 확인
- 실제 Apache Airflow data-plane 실행
- representative synthetic incident → recovery → re-validation
- Review AI / Runtime AI deterministic validation
- actual provider invocation과 persisted provenance 검증
- negative safety boundary 검증
- reproducibility rerun
- proof에서 발견된 MVP blocker의 최소 remediation
- 최종 acceptance report

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

그 다음 결과를 다음처럼 구분한다.

- **PASS:** 요구한 proof와 evidence가 current revision에서 성립한다.
- **FAIL:** 실행 가능했지만 contract 또는 acceptance를 위반했다.
- **BLOCKED:** 환경이나 선행 조건 때문에 유효한 proof 자체를 만들 수 없다.

FAIL을 발견했다고 즉시 scope를 넓히지 않는다. 현재 MVP acceptance를 막는 결함인지 먼저 판단하고, 맞다면 가장 작은 coherent remediation을 수행한다.

## Expected Outcome

가장 좋은 결과는 단순히 테스트가 모두 통과했다는 보고서가 아니다. 다음 질문에 하나의 revision과 evidence chain으로 답할 수 있는 상태다.

> **현재 repository의 이 Git revision은 실제 HMDA data plane, deterministic reliability, bounded Agentic review와 live invocation을 함께 실행해도 안전하고 재현 가능한 MVP인가?**

답이 `PASS`라면 MVP closeout을 근거 있게 시작할 수 있다. `FAIL`이라면 정확한 미완성 지점을 알 수 있고, `BLOCKED`라면 무엇이 실제 proof를 막는지 분리할 수 있다.

어느 결과든 지금보다 더 강한 상태다. 개별 성공 기록을 조합해 완성을 추정하는 대신, **현재 시스템이 실제로 무엇을 증명할 수 있는지 명확하게 알게 되기 때문이다.**

## Starting Point

- Branch base: `main@7497a57bbd2ed03ba6f887611bd32bda3b7e9520`
- Canonical MVP owner: [`docs/mvp.md`](../../docs/mvp.md)
- Long-term trust boundary: [`docs/VISION.md`](../../docs/VISION.md)

이 문서는 작업 제안과 실행 방향을 소유하는 non-canonical Inbox artifact다. 최종 acceptance와 durable contract는 canonical owner와 실제 executable evidence가 소유한다.

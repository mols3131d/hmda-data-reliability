# MVP Status

> **Snapshot:** 2026-08-16 / evidence base `main@f7bd019`
> **Overall:** 🟡 Partial — 기존 Data Lake와 deterministic Reliability 기반은 구현되어 있지만,
> Reliability domain의 bounded Agentic review와 current-revision end-to-end acceptance가 남아 있다.

## Domain Status

| Domain | Implementation | Current revision validation | Gap |
| --- | --- | --- | --- |
| [HMDA Data](hmda-data.md) | 🟢 Implemented | ⚪ Not Verified | 현재 revision에서 Source→Bronze acceptance를 다시 실행하지 않았다. |
| [Data Platform](data-platform.md) | 🟢 Implemented | ⚪ Not Verified | 현재 revision에서 Bronze→dbt analytical layer acceptance를 다시 실행하지 않았다. |
| [Data Operations](data-operations.md) | 🟢 Implemented | ⚪ Not Verified | 현재 revision에서 execution/promotion failure boundary를 다시 검증하지 않았다. |
| [Reliability](reliability.md) | 🟡 Partial | ⚪ Not Verified | bounded Agentic contract proof와 live model proof가 없다. |
| [Orchestration](orchestration.md) | 🟢 Implemented | ⚪ Not Verified | 현재 revision에서 Dagster local data-plane acceptance를 다시 실행하지 않았다. |

`Implemented`는 repository에 해당 domain capability의 구현 evidence가 존재한다는 뜻이다.
현재 revision에서 acceptance를 통과했다는 뜻이 아니며, 그 상태는 별도
`Current revision validation`으로 관리한다.

System-level proof는 이 domain 상태와 아래 blocker에서 **파생**한다. 별도의 capability
progress 표를 독립적으로 유지하지 않는다.

## MVP Blockers

### 1. Bounded Agentic Contract

Reliability domain에 외부 model availability와 독립적으로 반복 검증할 contract proof가 필요하다.

최소 proof:

- structured review contract와 validation
- deterministic evidence binding
- `RecoveryProposal`/approval/recovery authority를 만들거나 변경하지 않는 forbidden-action guardrail
- synthetic case 기반 deterministic evaluator
- invalid output의 fail-closed behavior

### 2. Live Agentic Proof

같은 current revision에서 실제 model invocation이 최소 한 번 필요하다.

최소 evidence:

- model과 주요 config
- prompt identity/version과 project revision
- 사용한 deterministic evidence references와 `RemediationDraft` identity
- structured review result
- latency와 provider가 제공하는 usage(token/cost)
- contract validator와 safety evaluator 결과

이 proof는 configured provider/network를 요구할 수 있으며 deterministic CI regression과
같은 것으로 취급하지 않는다.

### 3. Current-Revision End-to-End Acceptance

Agentic gap을 구현한 뒤 같은 repository revision에서 전체 proof를 다시 확인해야 한다.

```text
HMDA source
→ Bronze
→ dbt analytical layer
→ deterministic incident + RemediationDraft
├→ Agentic contract proof + live model proof ── advisory ─┐
└→ validated RecoveryProposal → human approval ──────────┤
                                                         └→ recovery
→ deterministic re-validation
```

기존 PR이나 과거 revision의 passing 결과만으로 이 gate를 완료 처리하지 않는다.

## Completion Decision

현재 상태에서는 **MVP 완료를 선언하지 않는다.**

최소 Data Lake와 deterministic Reliability는 기반으로 사용할 수 있지만, Project Pivot이
목표로 하는 Data Lake + Agentic Reliability가 아직 같은 current revision에서 하나의
완결된 proof로 연결되지 않았다.

## Evidence

- `src/project_pivot/hmda_data/`, `tests/hmda_data/`
- `src/project_pivot/data_platform/`, `dbt/`, `tests/data_platform/`, `tests/dbt/`
- `src/project_pivot/data_operations/`, `tests/data_operations/`
- `src/project_pivot/reliability/`, `tests/reliability/`
- `src/project_pivot/orchestration/`, `tests/orchestration/`
- current OpenSpec contracts and archived completion evidence

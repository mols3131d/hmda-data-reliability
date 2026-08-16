# MVP Status

> **Snapshot:** 2026-08-16 / evidence base `main@f7bd019`
> **Overall:** 🟡 Partial — 최소 Data Lake와 deterministic Reliability 기반은 존재하지만,
> MVP가 요구하는 실제 Agentic review와 current-revision acceptance가 아직 완료되지 않았다.

## Capability Status

| Capability | Implementation | Current revision validation | Gap |
| --- | --- | --- | --- |
| Minimal Data Lake | 🟢 Implemented | ⚪ Not Verified | 현재 revision에서 전체 data-plane acceptance를 다시 실행하지 않았다. |
| Deterministic Reliability | 🟢 Implemented | ⚪ Not Verified | 기존 evidence는 있으나 현재 revision 전체 regression을 다시 확인하지 않았다. |
| Agentic Reliability | 🟡 Partial | ⚪ Not Verified | 실제 model invocation, structured review evidence와 deterministic review evaluation이 필요하다. |
| Human-Controlled Recovery | 🟢 Implemented | ⚪ Not Verified | 현재 revision에서 end-to-end recovery acceptance를 다시 실행하지 않았다. |

## Domain Status

| Domain | Implementation | Why |
| --- | --- | --- |
| [HMDA Data](hmda-data.md) | 🟢 Implemented | local source validation, Bronze input와 synthetic case 기반이 존재한다. |
| [Data Platform](data-platform.md) | 🟢 Implemented | DuckDB/dbt analytical layer와 artifact evidence 기반이 존재한다. |
| [Data Operations](data-operations.md) | 🟢 Implemented | stage execution, validation/promotion과 failure boundary가 존재한다. |
| [Reliability](reliability.md) | 🟡 Partial | deterministic lifecycle/recovery는 존재하지만 bounded Agentic review gate가 미완료다. |
| [Orchestration](orchestration.md) | 🟢 Implemented | Dagster local data-plane boundary가 존재한다. |

`Implemented`는 repository에 해당 capability의 구현 evidence가 존재한다는 뜻이다.
현재 revision에서 필요한 acceptance를 실제 실행했다는 뜻은 아니며, 그 상태는 별도
`Current revision validation`으로 관리한다.

## MVP Blockers

### 1. Bounded Agentic Review

MVP 완료에는 실제 model invocation이 deterministic incident evidence와
`RemediationDraft`를 읽고 structured review를 반환해야 한다.

최소 proof:

- structured result contract
- evidence-bound review
- invocation identity/evidence
- deterministic safety evaluation
- AI output이 approval/recovery authority가 아님을 확인하는 guardrail

### 2. Current-Revision Acceptance

Agentic gap을 구현한 뒤 같은 repository revision에서 다음 end-to-end proof를 다시 확인해야 한다.

```text
HMDA source
→ Bronze
→ dbt analytical layer
→ deterministic incident
→ Agentic review
→ human approval
→ recovery
→ deterministic re-validation
```

기존 PR이나 과거 revision의 passing 결과만으로 이 gate를 완료 처리하지 않는다.

## Completion Decision

현재 상태에서는 **MVP 완료를 선언하지 않는다.**

최소 Data Lake와 deterministic Reliability는 MVP 기반으로 사용할 수 있지만, 프로젝트가
목표로 하는 Data Lake + Agentic Reliability의 두 capability가 아직 같은 current revision에서
완결된 proof로 연결되지 않았다.

## Evidence

- `src/project_pivot/hmda_data/`, `tests/hmda_data/`
- `src/project_pivot/data_platform/`, `dbt/`, `tests/data_platform/`, `tests/dbt/`
- `src/project_pivot/data_operations/`, `tests/data_operations/`
- `src/project_pivot/reliability/`, `tests/reliability/`
- `src/project_pivot/orchestration/`, `tests/orchestration/`
- current OpenSpec contracts and archived completion evidence

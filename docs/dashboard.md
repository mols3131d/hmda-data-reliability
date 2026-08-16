# Development Dashboard

> [!CAUTION]
> **Human convenience snapshot only.** 이 문서는 canonical source, agent context 또는 validation evidence가 아니다.
> Agent는 사용자가 dashboard 자체를 묻거나 dashboard refresh를 명시적으로 요청한 경우를 제외하고 이 파일을 repository orientation, planning, review 또는 validation에 사용하지 않는다.
> Dashboard를 읽은 경우에도 모든 factual claim은 owning source에서 다시 검증해야 한다.

> **Snapshot:** 2026-08-16 / evidence base `main@f7bd019`
> **Recorded overall:** 🟡 Partial — 기존 Data Lake와 deterministic Reliability 기반은 구현되어 있지만,
> Reliability domain의 bounded Agentic review와 current-revision end-to-end acceptance가 남아 있다고 기록된 snapshot이다.

이 파일의 상태 값은 이번 문서 구조 변경에서 재검증하거나 갱신하지 않았다. 현재 사실이 필요하면 source/configuration, tests와 실제 실행 결과, current OpenSpec, [`ARCHITECTURE.md`](ARCHITECTURE.md)와 [`domains/**`](domains/OVERVIEW.md)를 직접 확인한다.

## Recorded Domain Status

| Domain | Implementation | Current revision validation | Recorded gap |
| --- | --- | --- | --- |
| [HMDA Data](domains/hmda-data.md) | 🟢 Implemented | ⚪ Not Verified | 현재 revision에서 Source→Bronze acceptance를 다시 실행하지 않았다. |
| [Data Platform](domains/data-platform.md) | 🟢 Implemented | ⚪ Not Verified | 현재 revision에서 Bronze→dbt analytical layer acceptance를 다시 실행하지 않았다. |
| [Data Operations](domains/data-operations.md) | 🟢 Implemented | ⚪ Not Verified | 현재 revision에서 execution/promotion failure boundary를 다시 검증하지 않았다. |
| [Reliability](domains/reliability.md) | 🟡 Partial | ⚪ Not Verified | bounded Agentic contract proof와 live model proof가 없다. |
| [Orchestration](domains/orchestration.md) | 🟢 Implemented | ⚪ Not Verified | 현재 revision에서 Dagster local data-plane acceptance를 다시 실행하지 않았다. |

`Implemented`와 `Not Verified`는 위 snapshot 시점의 사람이 읽는 요약이다. 이 표를 executable contract나 current evidence inventory로 사용하지 않는다.

## Recorded MVP Blockers

### Bounded Agentic Contract

- structured review contract와 validation
- deterministic evidence binding
- `RecoveryProposal` / approval / recovery authority를 만들거나 변경하지 않는 forbidden-action guardrail
- synthetic case 기반 deterministic evaluator
- invalid output의 fail-closed behavior

### Live Agentic Proof

- model과 주요 config
- prompt identity/version과 project revision
- 사용한 deterministic evidence references와 `RemediationDraft` identity
- structured review result
- latency와 provider가 제공하는 usage(token/cost)
- contract validator와 safety evaluator 결과

### Current-Revision End-to-End Acceptance

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

## Refresh Policy

Dashboard refresh는 별도 작업으로 수행한다.

1. 기준 `main` revision을 고정한다.
2. source/configuration, tests, current OpenSpec과 canonical docs를 직접 읽는다.
3. test 존재와 실제 실행 결과를 구분하고, validation claim은 matching revision의 실행 evidence로만 기록한다.
4. 확인하지 않은 항목은 `Not Verified`로 남긴다.
5. 이 snapshot만 갱신하며 canonical contract를 dashboard에 새로 정의하지 않는다.

일반 기능·문서·테스트·spec 작업은 dashboard를 자동으로 따라 갱신하지 않는다.

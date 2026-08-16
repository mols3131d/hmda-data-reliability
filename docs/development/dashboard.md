# Development Dashboard

> [!CAUTION]
> **Human convenience snapshot only.** 이 문서는 canonical source, agent context 또는 validation evidence가 아니다.

> [!NOTE]
> 이 snapshot은 문서 lifecycle 구조 변경 중 상태를 재산정하지 않고 이전 dashboard에서 이동한 것이다.
> 현재 내용은 installed `mols-markdown-dashboard` 형식으로 다시 생성·검증한 결과가 아니다.
> 다음 명시적 dashboard refresh에서 current evidence를 기준으로 교체한다.

> **Snapshot:** 2026-08-16 / evidence base `main@f7bd019`
> **Recorded overall:** 🟡 Partial

이 snapshot의 상태 값은 이번 문서 구조 변경에서 재검증하거나 갱신하지 않았다. 현재 사실이나 contract가 필요하면 해당 owning source를 직접 확인한다.

## Recorded Domain Status

| Domain | Recorded implementation | Recorded validation | Recorded gap |
| --- | --- | --- | --- |
| [HMDA Data](../domains/hmda-data.md) | 🟢 Implemented | ⚪ Not Verified | Current-revision acceptance 미확인 |
| [Data Platform](../domains/data-platform.md) | 🟢 Implemented | ⚪ Not Verified | Current-revision acceptance 미확인 |
| [Data Operations](../domains/data-operations.md) | 🟢 Implemented | ⚪ Not Verified | Current-revision failure-boundary acceptance 미확인 |
| [Reliability](../domains/reliability.md) | 🟡 Partial | ⚪ Not Verified | Agentic proof와 current-revision E2E acceptance 미완료로 기록됨 |
| [Orchestration](../domains/orchestration.md) | 🟢 Implemented | ⚪ Not Verified | Current-revision acceptance 미확인 |

위 표는 snapshot 시점의 인간용 요약이다. `Implemented`, `Partial`, `Not Verified`를 current contract나 실행 evidence로 재사용하지 않는다.

## Recorded MVP Focus

Snapshot 시점에 남은 focus는 다음 세 항목으로 기록되어 있다.

- Bounded Agentic review proof
- Live Agentic model proof
- Current-revision end-to-end acceptance

각 항목의 정의와 완료 조건은 [`../mvp.md`](../mvp.md)가 소유한다. Dashboard는 acceptance나 safety contract를 복제하지 않는다.

Dashboard의 읽기·갱신 규칙은 [`../AGENTS.md`](../AGENTS.md#dashboard-policy)를 따른다.

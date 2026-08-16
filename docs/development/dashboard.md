# Development Dashboard

> [!CAUTION]
> **Human convenience snapshot only.** 이 문서는 canonical source, agent context 또는 validation evidence가 아니다.
> Agent는 사용자가 dashboard 자체를 묻거나 dashboard refresh를 명시적으로 요청한 경우를 제외하고 이 파일을 repository orientation, planning, review 또는 validation에 사용하지 않는다.

> [!NOTE]
> 이 snapshot은 문서 lifecycle 구조 변경 중 상태를 재산정하지 않고 이전 dashboard에서 이동한 것이다.
> 현재 내용은 `mols-markdown-dashboard`의 strict `Development Progress / Implementation Gaps / Verification Gaps` render로 검증됐다고 주장하지 않는다.
> 다음 **명시적 dashboard refresh 작업**에서 current canonical Spec, source, tests와 matching-revision 실행 근거를 다시 조사해 해당 skill 형식으로 재생성한다.

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

## Refresh Policy

Dashboard refresh는 별도 작업으로 수행한다.

1. `mols-markdown-dashboard` skill을 사용한다.
2. 기준 `main` revision을 고정한다.
3. current capability contract는 `openspec/specs/**`에서 확인한다. `openspec/changes/**`는 계획·작업 artifact이므로 current contract의 근거로 사용하지 않는다.
4. current implementation은 source/configuration에서 확인한다.
5. tests에서 Requirement별 Verification Target을 확인하고, matching revision의 실제 command/CI/runtime evidence로 검증 상태를 판정한다. Test 존재만으로 성공을 추론하지 않는다.
6. Requirement와 Verification Target을 의미 단위로 집계해 `Development Progress`의 정확한 `n/n`을 만든다.
7. 미구현 Requirement는 `Implementation Gaps`, 실패·미검증·blocked·manual-only target은 `Verification Gaps`에 둔다.
8. 확인하지 못한 상태나 denominator를 추측하지 않는다.
9. Dashboard에 canonical contract나 acceptance definition을 새로 작성하지 않고 owning document를 참조한다.
10. 기본 repository artifact는 Markdown으로 유지한다. Skill이 내부 작업용 YAML을 사용하더라도 별도 요청 없이 machine-readable dashboard SSOT로 저장하지 않는다.

일반 기능·문서·테스트·spec 작업은 dashboard를 자동으로 따라 갱신하지 않는다.

---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: "MVP Proof Preparation Tasks"
description: "Proof 준비와 baseline test fixture remediation을 추적하며 runtime acceptance 완료를 대신하지 않는다."
tasks_completed: 6
tasks_total: 6
---

## Tasks

- [x] 기존 proof entrypoint, canonical owner와 실행 환경 gap의 Research를 제공한다.
  - **Done when:** Inbox `02-research-project-mvp-proof-readiness.md`에 revision, source/test 근거와 provider uncertainty가 기록된다.
- [x] Same-revision 실행과 evidence 보존 계획을 제공한다.
  - **Done when:** Inbox `03-plan-project-mvp-proof-execution.md`가 SHA freeze, baseline/rerun, authority boundary와 runtime result owner를 명시한다.
- [x] Checklist의 live 판정과 proof record owner를 명확히 한다.
  - **Done when:** typed failure를 live PASS로 취급하지 않고, 실행 후 tracked result 편집 없이 proof SHA 및 acceptance record를 찾을 수 있다.
- [x] Classifier의 active Change regression tests를 repository의 mutable Change inventory에서 격리한다.
  - **Done when:** 실제 classifier와 기존 target/bulk assertion을 유지한 채 임시 filesystem fixture에서 active/absent/mixed 시나리오가 통과하고 관련 scripts suite가 회귀 없이 실행된다.
  - **Test first:** `da579b8` baseline과 focused reproduction에서 active target 3건이 실패했다. 이는 product failure의 RED가 아니라 누락된 fixture setup의 재현이다.
- [x] MVP requirement별 production implementation과 독립 oracle 매핑을 제공한다.
  - **Done when:** Inbox audit가 9개 영역의 implementation/evidence gap과 fixture 한계를 구분한다.
- [x] 승인된 proposal과 다른 request target scope를 source 처리 전에 거부한다.
  - **Done when:** table/year/file 불일치가 각각 source 접근 없이 `ApprovalGateError`를 반환하고 기존 recovery tests가 통과한다.
  - **Test first:** missing-source와 실제 request/profile 정합성을 갖춘 mismatch 사례로 pre-source 차단 누락을 먼저 재현한다.
  - **Validation:** mismatch 3건 RED (`BackfillValidationError` source IO), gate 수정 후 module 25 passed. 최종 acceptance는 별도 exact SHA runtime record가 소유한다.

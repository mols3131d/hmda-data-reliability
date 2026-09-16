---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: "MVP Proof Preparation Tasks"
description: "Proof 준비와 baseline test fixture remediation을 추적하며 runtime acceptance 완료를 대신하지 않는다."
tasks_completed: 4
tasks_total: 4
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

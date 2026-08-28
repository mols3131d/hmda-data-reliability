---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: "Review AI와 Runtime AI ownership refactor"
description: "기존 review behavior를 보존하면서 test-first로 package ownership과 import direction을 분리합니다."
tasks_completed: 0
tasks_total: 3
tags:
  - "domain:review-ai"
  - "domain:runtime-ai"
---

## Tasks

- [ ] 1. 새 ownership을 executable specification으로 고정한다
  - **Test first:** `review_ai` public review surface, `runtime_ai` settings/provider surface, Reliability AI re-export 부재와 기존 review/provenance behavior를 검증한다.
  - **Done when:** test가 새 import path와 dependency boundary를 사용하며 기존 behavioral assertion은 약화되지 않는다.

- [ ] 2. source package를 `review_ai`와 `runtime_ai`로 분리한다
  - **Done when:** `review_ai -> reliability/runtime_ai`, `runtime_ai -> no review_ai/reliability`, `reliability -> no AI package` import direction이 성립한다.
  - **Done when:** prompt identity, typed result, validation, provider retry/limits와 invocation evidence semantics가 유지된다.

- [ ] 3. 내부 caller와 canonical guide를 정렬하고 검증한다
  - **Done when:** live harness와 test command가 새 owner를 사용하고 Reliability/domain ownership 문서가 현재 source와 일치한다.
  - **Validation:** focused review/runtime test, Ruff, project type check와 영향 범위에 필요한 pytest를 실행한다.

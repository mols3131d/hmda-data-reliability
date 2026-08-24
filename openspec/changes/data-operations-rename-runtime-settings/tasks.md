---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Runtime setting identity migration tasks
description: current runtime identity contract를 test-first로 적용하고 검증한다.
tags:
  - domain:data-operations
  - capability:data-operations-stage-execution
---

## Tasks

- [ ] Runtime request와 orchestration adapter test가 `HMDA_RELIABILITY_*` setting과 current default identity를 기대하도록 변경한다.
- [ ] Data Operations request, orchestration adapter, dbt profile/subprocess와 example configuration을 current setting으로 변경한다.
- [ ] Airflow/dbt/asset adjacent technical identity를 behavior 변경 없이 current ownership에 맞게 정리하고 관련 test를 동기화한다.
- [ ] Canonical Spec과 current documentation을 current identity로 동기화한다.
- [ ] Targeted tests와 repository CI를 통과시키고 historical area를 제외한 active retired identity occurrence가 없음을 검증한다.

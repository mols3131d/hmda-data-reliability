---
type: plan
title: "Spec-Driven TDD RPI Review Plan"
description: "OpenSpec 전용 제어 책임을 유지하고 일반 루프 및 스키마 복제를 검토한다."
---

# Spec-Driven TDD RPI Review Plan

> [!NOTE]
> **검토 가설 및 작업 인계.** 실제 수정은 아직 수행하지 않았다. 공통 목적·검증 방식은 [bundle](../README.md)을 따른다.

## Baseline

[Source](../../../../.rulesync/skills/prj-spec-driven-tdd-rpi/SKILL.md)는 **active `spec-driven-tdd` 구현 Goal** 전용 RPI controller다. 217줄에 `entry`, `terminal`, `scope_policy`, recursion, 30-loop cap, transition, handoff가 담겨 있다. [OpenSpec schema](../../../../openspec/schemas/spec-driven-tdd/schema.yaml)는 proposal/specs/design/tasks/apply 계약을 소유한다.

## Preserve

- 일반 RPI와 중첩 실행하지 않는 **OpenSpec 전용 활성화 조건**.
- `terminal: research | planning | goal`에 따른 쓰기·실행 경계와 승인 없는 Apply 금지.
- schema-owned artifact dependency, `skip_specs: true`, 허용 범위 내 review feedback 처리.
- child scope가 부모 scope·권한·budget을 넓히지 않는 조건과 완료/인계 의미.

## Review Candidates

- schema의 artifact 책임·execution rule을 Skill에서 재설명한 부분.
- 공통 `mols-loops`와 유사한 convergence, recursion, loop budget, completion 설명.
- 10개의 control argument, 반복된 transition·saturation·handoff 세부가 실제 동작에 기여하는지.

## Tasks

1. active OpenSpec 구현과 일반 조사/문서/agent asset 요청을 비교해 activation을 확인한다.
2. schema와 generic loop의 owner를 대조하고 **전용 controller만 담당해야 할 delta**를 추출한다. 둘을 병렬 실행하지 않는다.
3. 간단한 `skip_specs: true` 구현과 변경된 Spec을 수반한 구현에서 terminal/Apply gate를 검증한다.
4. 상태·scope·권한의 필수 제약은 유지하면서 재진술과 불필요한 조합만 줄이는 후보를 만든다.

## Acceptance

OpenSpec의 실제 lifecycle·ownership·허가 경계가 유지되며, 일반 작업에 217줄짜리 controller가 주입되지 않는다. 단지 길다는 이유로 무조건 삭제하지 않는다.

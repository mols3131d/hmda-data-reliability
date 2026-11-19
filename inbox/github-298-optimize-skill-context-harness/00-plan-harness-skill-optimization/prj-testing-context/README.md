---
type: plan
title: "Testing Context Optimization Work Plan"
description: "작은 테스트 컨텍스트 라우터가 실제로 필요한 문서만 로드하는지 확인한다."
---

# Testing Context Optimization Work Plan

> [!NOTE]
> **초기 검토 가설.** 이 PR의 목표는 검토에 그치지 않고 실제 최적화와 검증을 완료하는 것이다. 공통 목표·완료 조건은 [bundle](../README.md)을 따른다.

## Baseline

[Source](../../../../.rulesync/skills/prj-testing-context/SKILL.md)는 27줄의 선택기다. `tests/AGENTS.md`(테스트 파일 수정), `test-design.md`(oracle/시나리오), `testing.md`(pytest 실행/markers/CI)와 필요할 때 `pyproject.toml`을 구분한다.

## Preserve

- 질문별로 **다른 canonical 문서**를 로드하는 명시적 context router.
- `tests/**` 대상의 path-scoped write boundary와 관련성 없는 전체 문서 선로드 방지.
- 문서 정본을 Skill에 복사하지 않는 구조.

## Review Candidates

- 현재 짧은 mapping이 실제로 불필요한 문서까지 로드하는지.
- `AGENTS.md` 및 `prj-load-context-development`의 선택 방식과 중복되거나 충돌하는지.
- 일반 테스트 설계와 pytest 실행을 혼동하는 near-miss가 있는지.

## Tasks

1. oracle 설계, test file 수정, marker 실행, 일반 source 설명의 네 요청에서 선택 문서를 비교한다.
2. 큰 `testing.md` 전체를 불필요하게 미리 읽는 경우가 확인되는지 조사한다.
3. 실질적 결함이 없다면 유지한다. 축소 또는 흡수 제안은 동일한 selection accuracy가 확인될 때만 한다.

## Acceptance

필요한 테스트 문서는 발견되고, 무관한 가이드가 로드되지 않는다. 짧다는 이유로 또는 스킬 수를 줄이려는 목적만으로 삭제하지 않는다.

## Work Status

- **Initial review:** 준비됨. `Review Candidates`는 검증 전 가설이다.
- **Optimization:** 미완료. 검토 후 실제 변경 또는 근거 있는 유지 결정을 기록한다.
- **Verification:** 미완료. 관련 로딩·라우팅·행동 검증과 결과를 이 문서에 남긴다.

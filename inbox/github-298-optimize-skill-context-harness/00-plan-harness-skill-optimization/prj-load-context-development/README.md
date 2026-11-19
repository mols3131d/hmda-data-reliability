---
type: plan
title: "Development Context Optimization Work Plan"
description: "개발 컨텍스트 주입과 독립 리뷰 절차를 분리한다."
---

# Development Context Optimization Work Plan

> [!NOTE]
> **초기 검토 가설.** 이 PR의 목표는 검토에 그치지 않고 실제 최적화와 검증을 완료하는 것이다. 공통 목표·완료 조건은 [bundle](../README.md)을 따른다.

## Baseline

[Source](../../../../.rulesync/skills/prj-load-context-development/SKILL.md)는 개발 범위에서 `DEVELOPMENT.md`를 로드하고 architecture/MVP, testing, VCS 문서를 조건에 따라 선택한다. 같은 파일에는 일반 구현 원칙과 긴 독립 리뷰 gate도 포함되어 있다. [Root instructions](../../../../AGENTS.md)도 일부 문서 선택을 소유한다.

## Preserve

- 구현 작업에 필요한 개발 환경·도구·도메인 문서의 **조건부 주입**과 중단 기준.
- target path의 `AGENTS.md` 및 Rules를 유지하는 project routing.
- 구현 완료를 정당화할 때 self-review와 independent review를 혼동하지 않는 경계. 현재 runtime이 독립 리뷰를 지원하지 않으면 coverage gap을 숨기지 않는다.

## Review Candidates

- `AGENTS.md`가 이미 제공하는 문서 로딩 규칙을 다시 서술하는 부분.
- 기본 코딩 판단(KISS/DRY/YAGNI 등)이 공통 coding context와 겹치는지.
- Independent Review Gate의 자세한 disposition·rerun flow가 `prj-load-context-review`의 계약을 이중 소유하는지.

## Tasks

1. Development-only 구현 작업과 review-only 작업에서 실제 Skill 선택과 `DEVELOPMENT.md`·architecture·MVP 로딩을 비교한다.
2. 리뷰 gate를 유지하면서 중복된 상세 판단의 실제 owner를 확인하고 필요한 최소 변경을 구현한다. 지원하지 않는 subagent를 무조건 요구하지 않는다.
3. 작은 수정 전후에 개발 시 필수 route가 유지되고 review-only에서 오활성화되지 않는지 확인한다.

## Acceptance

Development의 **문서 라우터 가치**가 유지된다. 독립 리뷰 판단의 owner가 하나이며, context와 절차가 중복 주입되지 않는다. 삭제는 별도 결론이지 기본값이 아니다.

## Work Status

- **Initial review:** 준비됨. `Review Candidates`는 검증 전 가설이다.
- **Optimization:** 미완료. 검토 후 실제 변경 또는 근거 있는 유지 결정을 기록한다.
- **Verification:** 미완료. 관련 로딩·라우팅·행동 검증과 결과를 이 문서에 남긴다.

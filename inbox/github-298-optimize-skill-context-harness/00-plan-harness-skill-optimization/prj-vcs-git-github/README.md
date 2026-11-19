---
type: plan
title: "Git/GitHub Context Optimization Work Plan"
description: "작업별 GitHub 정책 선택과 상태 재확인을 유지한다."
---

# Git/GitHub Context Optimization Work Plan

> [!NOTE]
> **초기 검토 가설.** 이 PR의 목표는 검토에 그치지 않고 실제 최적화와 검증을 완료하는 것이다. 공통 목표·완료 조건은 [bundle](../README.md)을 따른다.

## Baseline

[Source](../../../../.rulesync/skills/prj-vcs-git-github/SKILL.md)는 branch/commit/PR/review에 따라 각기 다른 VCS canonical guide와 template을 로드한다. [Chatbot entrypoint](../../../../CHATBOT.md)는 repository content 변경과 mutable Git/GitHub state에서 이 스킬을 로드하도록 명시한다.

## Preserve

- branch·commit·PR 작성/리뷰/병합별 **조건부 정책·템플릿 로딩**.
- mutable GitHub state를 판단 시점에 확인하고, 단순 read-only file inspection에는 불필요하게 선택하지 않는 boundary.
- 컨텍스트 로딩이 실제 mutation 승인이나 VCS 실행 권한을 만들지 않는 구분.

## Review Candidates

- `github-context`와 겹치는 일반 live-context 설명이 있는지. 단, project-specific VCS guide selection은 별도 가치다.
- operation이 명확할 때 entry README를 무조건 로드하게 만드는지.
- `branch.md`, `commit.md`, `pull-request.md`, templates의 owner가 충분히 분리되어 있는지.

## Tasks

1. PR 생성과 commit 작성에서 해당 guide/template만 선택하는지 확인한다.
2. read-only source 검토, GitHub 상태 판단과 일반 문서 변경의 실제 trigger를 구분한다.
3. 중복 설명이 확인되면 최소 축소하되 `CHATBOT.md` 의존성과 GitHub workflow의 실제 계약을 보존한다.

## Acceptance

작업별 정책이 계속 주입되고 적절한 mutable state를 확인한다. 이 스킬을 제거하려면 chatbot entrypoint와 repository workflow를 포함한 대체 경로를 먼저 검증해야 한다.

## Work Status

- **Initial review:** 준비됨. `Review Candidates`는 검증 전 가설이다.
- **Optimization:** 미완료. 검토 후 실제 변경 또는 근거 있는 유지 결정을 기록한다.
- **Verification:** 미완료. 관련 로딩·라우팅·행동 검증과 결과를 이 문서에 남긴다.

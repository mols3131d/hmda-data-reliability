---
type: plan
title: "Review Context Optimization Work Plan"
description: "독립 리뷰의 프로젝트 판정 계약을 보존하고 중복 orchestration을 검토한다."
---

# Review Context Optimization Work Plan

> [!NOTE]
> **초기 검토 가설.** 이 PR의 목표는 검토에 그치지 않고 실제 최적화와 검증을 완료하는 것이다. 공통 목표·완료 조건은 [bundle](../README.md)을 따른다.

## Baseline

[Source](../../../../.rulesync/skills/prj-load-context-review/SKILL.md)는 최상위 독립 리뷰에서 `prj-review-code`, `prj-vcs-git-github` 및 필요 시 OpenSpec/Inbox 문서를 선택한다. `mols-review-dualvantage` 위임, caller-owned disposition과 최종 `clear | changes_required | blocked` 평가도 정의한다.

## Preserve

- 독립 리뷰와 구현 self-review의 구분, reviewer 분석과 caller **최종 판단**의 역할 분리.
- scope authority가 finding severity보다 우선한다는 정책, 승인 밖 remediation 금지.
- reviewed revision·evidence·coverage gap과 material change 이후 재평가.
- 리뷰 대상과 결과의 소비자에 따라 필요한 문서만 **선택적으로** 로드한다.

## Review Candidates

- `prj-load-context-development`, VCS review guide, 리뷰 하위 스킬에 같은 policy가 반복되는 위치.
- 너무 상세한 disposition table과 반복 precedence 설명이 행동을 추가로 개선하는지.
- DualVantage가 없는 runtime까지 동일 delegation 경로를 강제하거나, reviewer 내부 절차를 caller가 복제하는지.

## Tasks

1. 독립 PR 리뷰와 구현 self-review를 near-miss로 비교해 trigger와 필수 context 차이를 확인한다.
2. 사용 가능한 runtime과 subagent에서 실제 delegation 가능성, fallback의 보증 수준을 구분한다.
3. 프로젝트-specific review admission·assessment를 하나의 owner에 남기고, 중복 실행 절차만 줄이는 최소 변경을 구현한다.
4. `scope_decision`, `unknown`, `follow_up`이 실제 변경 권한으로 잘못 승격되지 않는지 검증한다.

## Acceptance

프로젝트 리뷰 기준이 손실 없이 전달되고, 미지원 런타임을 독립 리뷰 성공으로 오인하지 않는다. 새로운 검토가 모든 PR에서 불필요하게 연쇄 호출되지 않는다.

## Work Status

- **Initial review:** 준비됨. `Review Candidates`는 검증 전 가설이다.
- **Optimization:** 미완료. 검토 후 실제 변경 또는 근거 있는 유지 결정을 기록한다.
- **Verification:** 미완료. 관련 로딩·라우팅·행동 검증과 결과를 이 문서에 남긴다.

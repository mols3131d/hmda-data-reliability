---
type: report
title: "Core Documentation Consistency Baseline"
description: "Use when reviewing the initial evidence-backed consistency candidates and protected non-findings for PR #226."
tags:
  - consistency
  - documentation
  - evidence
---

# Core Documentation Consistency Baseline

## Scope

이 baseline은 PR #226의 수정 전 탐색 범위를 좁히기 위한 working artifact다. `main`의 `f098190b75df5ae359ab6fc2bb4646cbcddde8bd`를 기준으로 [`README.md`](../../README.md), [`docs/VISION.md`](../../docs/VISION.md), [`docs/mvp.md`](../../docs/mvp.md), [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md), [`DEVELOPMENT.md`](../../DEVELOPMENT.md)를 우선 비교했다.

아래 항목은 canonical contract가 아니다. 확인된 사실과 수정 전 추가 검증이 필요한 판단 후보를 구분한다.

## Established Ownership

[`docs/AGENTS.md`](../../docs/AGENTS.md)는 장기 방향을 `VISION.md`, current MVP의 목표·scope·acceptance를 `mvp.md`, architecture와 domain boundary를 `ARCHITECTURE.md` 및 `domains/**`에 배정한다. Current capability의 normative contract는 `openspec/specs/**`, 실제 implementation state는 source와 configuration이 소유한다.

따라서 이번 작업은 문서가 각 owner를 정확하게 가리키고 같은 개념을 충돌 없이 설명하는지에 집중한다. 문서끼리 차이가 있다는 이유만으로 한쪽 표현을 다른 쪽에 기계적으로 복제하지 않는다.

## Initial Candidates

| Candidate | State | Evidence and implication |
| --- | --- | --- |
| Analytical layer naming | Verify and align | `ARCHITECTURE.md`와 `DEVELOPMENT.md`는 주로 `Silver / Gold`, `mvp.md`는 주로 `dbt staging / marts`를 사용한다. 같은 계층을 가리키는 표현이라면 짧은 mapping 또는 한쪽 용어 정리가 필요하고, 다른 의미라면 그 차이를 보존해야 한다. |
| Recovery proposal abstraction | Verify and align | `ARCHITECTURE.md`는 partition/freshness용 `RecoveryProposal`과 schema/table용 `SchemaRecoveryProposal`을 구분한다. 상위 문서가 `RecoveryProposal`을 전체 recovery의 단일 concrete type처럼 읽히게 만드는 위치가 있는지 확인하고, 필요하면 generic `validated recovery proposal` 수준으로 정리한다. |
| AI delegation repetition | Prune selectively | `VISION.md`, `README.md`, `mvp.md`, `ARCHITECTURE.md`가 deterministic truth, advisory AI, human-controlled mutation을 반복한다. 현재 의미 충돌은 확인되지 않았으므로 삭제 자체가 목표가 아니다. 각 문서의 독자 판단에 필요한 최소 맥락만 남길 수 있는지 검토한다. |
| Dense long-form prose | Polish selectively | 특히 `VISION.md`와 `ARCHITECTURE.md`에는 하나의 문단에서 여러 조건·예외·결론을 함께 처리하는 부분이 있다. 기술적 의미를 보존하면서 독자가 boundary를 더 빨리 찾도록 분리할 후보만 선별한다. |
| Manual paragraph wrapping | Mechanical cleanup | `mvp.md`의 Active goal 등 source-level 수동 줄바꿈이 repository Markdown rule의 paragraph 작성 원칙과 맞는지 changed scope에서 정리한다. 의미 변경과 분리해서 취급한다. |

## Protected Non-Findings

현재 확인 범위에서는 다음 차이를 문제로 만들 근거가 없다. 수정 과정에서 불필요하게 설계를 바꾸지 않기 위한 보호 조건이다.

- `README.md`와 `mvp.md`는 현재 MVP에서 AI가 직접 recovery authority를 갖지 않는다고 일관되게 설명한다.
- `mvp.md`와 `ARCHITECTURE.md`는 Airflow를 data-plane orchestration으로 제한하고 reliability lifecycle, approval, recovery를 자동 결합하지 않는다는 방향이 일치한다.
- `VISION.md`가 장기적으로 AI delegation 확대 가능성을 설명하는 것은 현재 MVP의 advisory-only boundary와 충돌하지 않는다. 서로 다른 lifecycle과 abstraction level의 설명이다.
- 핵심 문서가 OpenSpec을 current normative capability owner로 두는 구조는 현재 documentation trust boundary와 일치한다.

## Verification Questions

실제 edit 전에 다음 질문을 각 candidate별로 닫는다.

1. 두 표현이 정말 같은 domain concept를 가리키는가, 아니면 서로 다른 abstraction인가?
1. 더 구체적인 owner가 이미 정확한 용어 또는 contract를 정의하는가?
1. 현재 문구가 독자를 잘못된 authority, execution boundary 또는 safety assumption으로 유도하는가?
1. 수정 없이 짧은 link나 mapping만으로 해석 비용을 줄일 수 있는가?
1. 다듬기가 의미·조건·예외를 바꾸지 않는가?

검증 결과가 명확한 candidate만 PR의 canonical 문서 수정으로 승격한다.

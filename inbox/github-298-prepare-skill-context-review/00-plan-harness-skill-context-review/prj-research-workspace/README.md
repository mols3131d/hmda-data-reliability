---
type: plan
title: "Research Workspace Review Plan"
description: "근거와 템플릿 라우팅의 실제 가치를 유지하며 범용 조사 절차를 검토한다."
---

# Research Workspace Review Plan

> [!NOTE]
> **검토 가설 및 작업 인계.** 실제 수정은 아직 수행하지 않았다. 공통 목적·검증 방식은 [bundle](../README.md)을 따른다.

## Baseline

[Source](../../../../.rulesync/skills/prj-research-workspace/SKILL.md)는 질문·범위·템플릿·엄밀도·출력 형태를 선택한다. `references/workflow.md`, `evidence.md`, `output.md`를 조건부로 로드하는 **research context router** 역할도 한다.

## Preserve

- 답을 바꿀 수 있는 근거를 우선하고, 충돌과 미확인을 구분하는 Evidence 기준.
- 실제 필요할 때만 조사 템플릿을 탐색·로드하는 범위와 provenance.
- research가 planning/implementation authority를 대신하지 않는 경계.
- 결과 소비자에 따라 Chat과 durable Inbox artifact를 선택하는 기능.

## Review Candidates

- 모든 조사에 6개의 `auto` argument와 일반적 Research → Output 절차를 고정할 필요가 있는지.
- template discovery의 비용과 관련 없는 문서 선로드 가능성.
- 기존 LLM의 근거 추적 능력으로 처리 가능한 일반 지시와 스킬로 주입할 전문 기준의 구별.

## Tasks

1. 간단한 코드 사실 조사와 템플릿을 요구하는 근거 조사에서 로딩 경로를 비교한다. 구현 요청에서는 이 스킬이 불필요하게 선택되지 않는지도 확인한다.
2. 세 reference가 실제로 조건부 로드되는지, 어느 정도로 독립적인 가치가 있는지 검토한다.
3. 불필요한 argument·ceremony만 최소화하고, 선택적 근거/템플릿 주입이 사라지지 않게 조정안을 설계한다.

## Acceptance

필요한 Evidence·Template 컨텍스트는 선택되고, 작은 조사에는 과도한 워크플로를 요구하지 않는다. 스킬 삭제를 결정하려면 같은 라우팅 기능이 검증된 대체 경로에 있어야 한다.

---
type: brief
title: "PR 284 — Reliability Agentic Refactoring Work Handoff"
description: "PR #284의 전체 리팩터링 완료 목표, 현재 상태와 다음 작업 착수 순서·필수 검증을 새 작업 주체에게 인계한다."
tags:
  - reliability
  - ai-engineering
  - handoff
---

# PR 284 — Reliability Agentic Refactoring Work Handoff

> **상태:** [Draft PR #284](https://github.com/mols3131d/hmda-data-reliability/pull/284)는 **소스 리팩터링 전체 완료를 목표**로 한다. 현재는 조사·계획·인계 문서만 준비되었으며, 구현/CI/런타임 평가 완료가 아니다.

## Goal

`reliability`의 결정론적 Assessment/Remediation과 `reliability_ai`의 실제 Agent Investigation/Delegated Execution/Reporting을 코드로 완성하고, 기존 API·OpenSpec·테스트·Langfuse 연동을 일관되게 이전·검증한다.

- Owning branch: `agent/refactor/evolve-reliability-agentic-architecture`
- Owning work unit: `inbox/github-284-evolve-reliability-agentic-architecture/`
- 기준 revision: `main` `061a2f6435879d466dda329c14b8232d03e95b7d` (초기 조사 기준; 작업 전 최신 base/head 재확인)
- 준비 자료: [Research](00-research-reliability-agentic-boundary-audit.md) · [Plan / PR Completion Criteria](01-plan-reliability-agentic-complete-refactor.md)
- Architecture review: [Notion](https://app.notion.com/p/40f13d7e58b9810bae96f9ea42d80d80)

## Next Action

1. PR head/base, 열린 후속 이슈·현재 OpenSpec change와 테스트 baseline을 확인한다. 기존 `review_ai`, `reliability`, `data_operations`, `runtime_ai` 공개 소비자를 파악한다.
2. **Plan W0**: 대표 변경 4건의 변경 책임·공유 계약·호환 전략을 결정한다. 검증 없는 폴더 4분할부터 시작하지 않는다.
3. Spec/계약의 변경 승인이 필요한 부분을 구분한 뒤, 완료 기준이 있는 구현 단위부터 작업한다. 각 단위에서 호출 경로와 실패 경로를 같이 검증한다.
4. 도구 기반 조사와 위임 실행을 mock만으로 끝내지 말고, 허용된 실제 provider/도구 실행 증거 및 Langfuse 평가 결과로 검증한다.
5. 전체 변경 완료 전까지 PR을 Draft로 유지한다. 검증 근거와 체크리스트는 구현 시 실제 상태에 맞춰 갱신한다.

## Non-Negotiable Boundaries

- **변경 요청 범위:** 리팩터링과 실제 에이전트 기능 구현. 과거 실행 기록·Git history 재작성 금지.
- **안전:** Incident·Evidence와 RecoveryProposal·Approval·검증된 state mutation의 정본 경계를 유지한다. 기존 MVP의 read-only AI 제한을 넘는 직접 DB 수정은 별도 명시적 승인과 정본 Spec 변경 없이는 실행하지 않는다.
- **협업:** 다른 작업 agent가 공유 계약을 서로 다르게 정의하지 않게 한다. 병렬 가능성과 파일 충돌이 없다는 사실을 동일시하지 않는다.
- **정본:** Inbox는 비정본 working artifact이며 실제 요구사항/구현 판단은 적용되는 OpenSpec·repository guidance·source와 테스트를 따른다.
- **출처·계정:** GitHub 작업 계정은 `mols3131d` / `mols3131d@gmail.com`만 사용한다.

## Done Means

실제 소스 재구성, 도구 호출 Agent, 위임 업무 수행과 보고, 호환 이전, 결정론적 안전 검증, Langfuse/human 평가, 최신 base/head 통합 테스트가 모두 끝나고 **[Plan](01-plan-reliability-agentic-complete-refactor.md)의 PR Completion Criteria**를 근거로 완료 표시할 수 있어야 한다. 준비 문서 제출만으로 완료가 아니다.

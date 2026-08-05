---
type: openspec-spec-driven-tdd-plan-review
category: review
title: "HMDA EDA core scope reduction plan review"
description: "Research 결론과 현재 repository를 기준으로 replacement plan의 범위, 추적성과 실행 가능성을 검토한다."
status: "approved"
---

> [!NOTE]
> **Approved.** Proposal, Specs, Design과 Tasks가 6개 core column descriptive EDA라는 동일한 범위를 유지하며, 제거·유지·보류 항목과 검증 경계가 구현 전에 충분히 결정되어 있다.

## Overview

| Target | Scope | Status |
| --- | --- | --- |
| Proposal · Specs · Design · Tasks | EDA scope reduction, subsystem removal, Notebook, Foundation evidence | Approved |

## Traceability

| From | To | Evidence | Result |
| --- | --- | --- | --- |
| Proposal | Specs | 두 modified capability가 각각 delta spec을 가진다. | Pass |
| Specs | Design | 6개 core, 제거 evidence, public API, Notebook과 actual-source 경계가 Decision에 연결된다. | Pass |
| Specs / Design | Tasks | Core contract, subsystem removal, Notebook, docs·runtime evidence와 validation workstream이 존재한다. | Pass |

## Verification

| Check | Evidence | Result |
| --- | --- | --- |
| Intent and scope are explicit | Keep·Remove·Out of Scope와 replacement 관계가 Proposal에 명시됐다. | Pass |
| Requirements are observable and testable | 모든 추가·변경 Requirement에 정상 또는 실패 Scenario가 있다. | Pass |
| Design satisfies Specs without unnecessary scope | 계산, UI, runtime evidence와 제거 subsystem의 책임이 분리됐다. | Pass |
| TDD tasks cover changed behavior | Core·API·Notebook은 RED → GREEN → REFACTOR 순서이며 문서·runtime validation이 후속된다. | Pass |
| Open questions and dependencies do not block Apply | API deprecation, evidence 위치, Notebook smoke owner가 Design Decision으로 해소됐다. | Pass |

## Status

| Decision | Rationale |
| --- | --- |
| Approved | 구현 범위, migration과 validation이 닫혔고 기존 extension의 병행 Apply를 차단한다. |

---
type: openspec-spec-driven-tdd-plan-review
category: review
title: "HMDA EDA core scope reduction plan review"
description: "Research 결론과 현재 repository를 기준으로 replacement plan의 범위, 추적성과 실행 가능성을 두 차례 검토한다."
status: "approved"
---

> [!NOTE]
> **Approved.** 두 차례 셀프 리뷰에서 발견한 lifecycle, 책임 경계와 testability 문제를 수정했다. Proposal, Specs, Design과 Tasks는 6개 core column descriptive EDA와 single active replacement라는 동일한 범위를 유지한다.

## Overview

| Target | Scope | Status |
| --- | --- | --- |
| Proposal · Specs · Design · Tasks | EDA scope reduction, old change deletion, Notebook, Foundation evidence | Approved |

## Review Iterations

| Loop | Focus | Findings | Resolution |
| ---: | --- | --- | --- |
| 1 | Research alignment·lifecycle | 기존 extension 보존이 삭제 결정과 충돌했고 EDA가 column 존재 계약까지 소유하는 문구가 있었다. | 기존 change 삭제와 direct reference 제거를 task로 고정하고, 존재는 ingestion·type과 metric은 EDA로 분리했다. |
| 2 | Adversarial testability | Type family, Gold non-null grain denominator, representative fixture와 test source 구분, regression 범위가 불명확했다. 또한 완료된 plan cleanup이 Apply task에 섞일 수 있었다. | Type matrix와 coverage 공식을 명시하고 small deterministic source 용어를 사용했으며 validation을 직접 관련 contract로 제한했다. 기존 change 삭제는 plan review에서 완료하고 implementation task와 분리했다. |

## Traceability

| From | To | Evidence | Result |
| --- | --- | --- | --- |
| Proposal | Specs | 두 modified capability가 각각 delta spec을 가지며 존재·타입 책임을 분리한다. | Pass |
| Specs | Design | 6개 core, type matrix, non-null grouping coverage, 제거 evidence, public API, Notebook과 actual-source 경계가 Decision에 연결된다. | Pass |
| Specs / Design | Tasks | Core contract, subsystem removal, Notebook, docs·runtime evidence와 validation workstream이 존재한다. | Pass |

## Verification

| Check | Evidence | Result |
| --- | --- | --- |
| Intent and scope are explicit | Keep·Remove·Out of Scope와 replacement deletion 관계가 Proposal에 명시됐다. | Pass |
| Requirements are observable and testable | 모든 추가·변경 Requirement에 정상 또는 실패 Scenario가 있고 denominator·type 범위가 닫혔다. | Pass |
| Design satisfies Specs without unnecessary scope | 계산, UI, runtime evidence, Gold mart와 제거 subsystem의 책임이 분리됐다. | Pass |
| TDD tasks cover changed behavior | Core·API·Notebook은 RED → GREEN → REFACTOR 순서이며 문서·runtime validation이 후속된다. 완료된 plan cleanup은 Apply task에서 제외됐다. | Pass |
| Open questions and dependencies do not block Apply | API deprecation, evidence 위치, Notebook smoke owner, type family와 grain 계산 기준이 Decision으로 해소됐다. | Pass |
| Active change set is unambiguous | 기존 extension은 삭제되고 replacement 하나만 실행 대상으로 남는다. | Pass |

## Status

| Decision | Rationale |
| --- | --- |
| Approved | 구현 범위, migration과 validation이 닫혔고 삭제된 extension과의 병행 해석 가능성을 제거했다. |

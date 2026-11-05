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

## Critical Decisions and Gaps

| 주제 | 인계할 판단 또는 제약 |
| --- | --- |
| PR 목표 | **#284에서 소스 리팩터링 전체 완료**. 4개 논리 책임·도구 사용 조사·범위가 정해진 위임 실행·인간/상위 모델 보고·계약/평가 이전까지. 문서만으로 완료 불가 |
| 현행 Spec | 기존 `review_ai`는 `null_spike`·3단계·**no tools**. 신규 Agent는 별도 entry point/Spec 검토. 기존 동작의 암묵적 변경 금지 |
| 설계 맥락 | `TaskEnvelope`·`InvestigationResult`·`ActionProposal`·`ExecutionReceipt`·`ReportEnvelope`, 증거 snapshot vs live 조회, Coordinator/Investigator/Verifier/Executor/Reporter 역할은 **구현 후보**. 최소 필수 계약과 owner는 [Plan](01-plan-reliability-agentic-complete-refactor.md)에서 확인 |
| 프레임워크 | 기존 순서상 #284 이후 확대 검토. #284 내부의 **실제 tool agent 기능**을 누락하거나, 반대로 Deep Agents/복수 에이전트/범용 loop를 미리 강제하지 않는다. native runtime 후보를 최소 실험하고 비용·효용으로 채택 |
| PR #285 | [진행 중](https://github.com/mols3131d/hmda-data-reliability/pull/285): Skill/부트스트랩/스크립트/태스크 명령. #284와 공유 파일·실행 커맨드 의존성만 조정; 무관한 기능은 기다리거나 덮어쓰지 않음 |
| 로컬 AI 기준 | RTX 3070 8GB·Qwen3.5 4B, 16K 우선·32K 조건부. Thinking ON/OFF와 실제 tool-call 품질은 미검증; 8K 실행 완료를 16K 성능 증거로 승계하지 않음 |
| Langfuse | `4.15.6` native Prompt/Dataset/Experiment/Tracing 유지. 기존 [PR #280 데이터/버전](https://github.com/mols3131d/hmda-data-reliability/blob/main/inbox/github-280-improve-review-ai-output-quality/17-brief-review-ai-session-handoff.md)을 확인하고 원격 `setup`을 무작정 재실행하지 않음. 사람 평가 완료 여부 재확인 |

이전에 작성된 아키텍처 v2의 원문은 현재 GitHub/Notion 정본으로 지정된 자료가 아니므로 **이 PR의 Research·Plan에 필요한 계약/역할·검증 경계를 복원했다**. [Notion 적합성 평가](https://app.notion.com/p/40f13d7e58b9810bae96f9ea42d80d80)는 설계 원문이 아닌 리뷰 자료다. 승인된 새로운 요구사항은 별도 OpenSpec/정본 문서로 소유시킨다.

## Next Action

1. [PR #284](https://github.com/mols3131d/hmda-data-reliability/pull/284)의 **현재** head/base와 [PR #285](https://github.com/mols3131d/hmda-data-reliability/pull/285) 병렬 변경, 열린 OpenSpec change·기존 테스트/실행 baseline을 확인한다. `review_ai`, `reliability`, `data_operations`, `runtime_ai` 공개 소비자와 공유 변경 파일을 식별한다.
2. **Plan W0:** 대표 변경 4건의 실제 수정 지점, 공유 계약, 구 `no tools` 경로의 이전/병행 전략, Evidence snapshot identity, 프레임워크 PoC 필요성을 결정한다. 검증 없는 폴더 4분할부터 시작하지 않는다.
3. Spec/계약의 변경 승인이 필요한 부분을 구분한 뒤, 완료 기준이 있는 구현 단위부터 작업한다. 각 단위에서 호출 경로와 실패 경로를 같이 검증한다.
4. 도구 기반 조사와 위임 실행을 mock-only로 끝내지 말고, 허용된 실제 provider/도구 실행과 실패 증거를 검증한다. 기존 Langfuse 데이터 변경 부작용을 피하고, 유용성 평가는 사람의 별도 판단으로 남긴다.
5. 전체 변경 완료 전까지 PR을 Draft로 유지한다. 검증 근거와 체크리스트는 구현 시 실제 상태에 맞춰 갱신한다.

## Non-Negotiable Boundaries

- **변경 요청 범위:** 리팩터링과 실제 에이전트 기능 구현. 과거 실행 기록·Git history 재작성 금지.
- **안전:** Incident·Evidence와 RecoveryProposal·Approval·검증된 state mutation의 정본 경계를 유지한다. 기존 MVP의 read-only AI 제한을 넘는 직접 DB 수정은 별도 명시적 승인과 정본 Spec 변경 없이는 실행하지 않는다.
- **협업:** 다른 작업 agent가 공유 계약을 서로 다르게 정의하지 않게 한다. 병렬 가능성과 파일 충돌이 없다는 사실을 동일시하지 않는다.
- **정본:** Inbox는 비정본 working artifact이며 실제 요구사항/구현 판단은 적용되는 OpenSpec·repository guidance·source와 테스트를 따른다.
- **출처·계정:** GitHub 작업 계정은 `mols3131d` / `mols3131d@gmail.com`만 사용한다.

## Done Means

실제 소스 재구성, 도구 호출 Agent, 위임 업무 수행과 보고, 호환 이전, 결정론적 안전 검증, Langfuse/human 평가, 최신 base/head 통합 테스트가 모두 끝나고 **[Plan](01-plan-reliability-agentic-complete-refactor.md)의 PR Completion Criteria**를 근거로 완료 표시할 수 있어야 한다. 준비 문서 제출만으로 완료가 아니다.

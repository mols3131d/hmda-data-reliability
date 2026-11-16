---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Enable Bounded Reliability Investigation
description: "PR #284의 제한된 조사·위임 기능과 개발 에이전트의 독립 변경·정확한 통합을 위한 계약 전환·평가·이전 범위를 정의한다."
---

## Why

PR #284의 작업 소스는 `review_ai`의 고정 3단계 검토를 `reliability_ai`의 도구 기반 조사와 위임 보고로 바꾸었으나, 정본 `reliability-agentic-review`와 `review-ai-prompt-engineering`은 아직 no-tools·3단계 prose 실행을 요구한다. 기존 Inbox의 완료 체크나 통과한 회귀만으로 이 계약 차이가 해소되지는 않는다.

사건 근거를 실제로 조회하는 조사 기능과 그 결과를 이용하는 보고 기능을 검증 가능한 계약으로 전환해야 한다. 기존 입력 일관성, 승인 분리, native Prompt·Dataset·관측, 원문 보존과 사람 평가를 전환 과정에서 잃지 않아야 한다.

동등한 목표는 여러 개발 에이전트가 올바른 책임 안에서 변경을 완결하고 공유 계약을 유지하며 정확하게 통합할 수 있는 구조다. 현재 API와 안내의 불일치, provider 입력 정책의 별도 경로, 조사·Recovery 조합의 검증 공백은 독립 변경과 통합을 어렵게 한다. [05 Progress Report](../../../inbox/github-284-evolve-reliability-agentic-architecture/05-report-reliability-agentic-progress-and-remaining-work.md)와 [06 Architecture Review](../../../inbox/github-284-evolve-reliability-agentic-architecture/06-review-reliability-multi-agent-development-architecture.md)는 이 미완료 접점의 근거이며, 정본 요구사항을 대신하지 않는다.

## What Changes

- `null_spike`의 불변 입력과 결정론적 사실은 유지하고, 고정 3단계 collection을 예산·범위가 제한된 도구 기반 조사 결과로 대체한다.
- 사건 Evidence 조회·snapshot profile 비교·호출자가 지정한 dbt artifact 영향 분석을 제공한다. 사건 snapshot과 후속 current artifact 관측의 출처를 구분한다.
- 위임 Task의 허용 도구·실행 예산을 실제 호출에 적용하고, 조사 실패·승인 대기·부분 실행·실패를 구분하는 인간 또는 상위 모델 대상 보고를 제공한다.
- `review_ai` API·CLI·guide를 `reliability_ai`로 이전한다. 과거 실행 자료를 삭제하거나 새로운 형식·revision으로 소급 재작성하지 않는다.
- Langfuse native Prompt·실제 호출 관측·기존 합성 Dataset 실험을 새 조사 경로에 연결하고, 실제 모델 실행과 사람 평가를 서로 다른 완료 근거로 유지한다.
- 공개 진입점·공유 계약·가까운 검증을 일치시켜 개발 에이전트가 책임 안에서 변경을 완결하고 실제 연결된 결과를 확인할 수 있게 한다. 개발 협업의 독립 완료·계약 충돌·통합 재작업 근거는 제품 모델 품질과 구분한다.

## Boundaries

- **In Scope:** PR #284의 조사·위임 보고 계약 전환, 필요한 deterministic API 이전 검증, native 평가 연결과 현재 문서·CLI 이전, 해당 변경에서 개발 에이전트의 책임 소유권·공유 의미·통합 검증을 일치시키는 보완과 실제 협업 근거.
- **Out of Scope:** AI가 생성한 조치를 승인·RecoveryProposal·mutation 권한으로 승격하는 기능, 새로운 자동 복구 정책, 범용 SQL·파일 경로 도구, Deep Agents·MCP·제품 runtime의 다중 에이전트 필수 도입, generic plugin·DI 계층이나 신규 orchestrator, 과거 실행 및 Git 이력 재작성. 제품 runtime의 다중 에이전트가 선택적이라는 제한은 개발 협업 아키텍처 목표를 제외하지 않는다.
- **Authority:** Investigation은 read-only다. Execution이 호출할 수 있는 복구는 호출자가 별도로 제공한 authoritative request와 외부 Approval을 기존 deterministic gate로 검증하는 경로에 한한다. 이 Change는 AI의 쓰기 권한을 추가하지 않는다.

## Capabilities

### Modified Capabilities

#### `reliability-agentic-review`

- 고정 단계 실행 대신 bounded tool investigation, Task 제한, 사실·가설·불확실성·실행 결과 보고와 실패 근거 보존을 정의한다.
- 기존 native 합성 평가를 새 진입점으로 이전하고 결과 완전성, 실제 revision·prompt·도구 출처와 사람 평가의 분리를 유지한다.

#### `review-ai-prompt-engineering`

- 고정된 세 질문을 조사 지시문·도구 사용·구조화 보고 지침으로 바꾼다. 기존 Spec ID는 유지하고 package·도메인 이름의 이전과 혼동하지 않는다.
- 한국어 Markdown seed, Langfuse native 조합과 시작 시 prompt 객체·실제 버전 고정, 원격 조회 실패 시 no-fallback 경계를 유지한다.

## Impact

- 소유 도메인은 `reliability_ai`이며 `reliability`와 `runtime_ai`의 공개 계약을 소비한다. 결정론적 truth·승인·Recovery 의미는 `reliability`, provider 호출 mechanics는 `runtime_ai`에 남는다.
- 적용 대상은 조사·위임 API, 도구 gateway, Prompt seed와 native 평가 CLI, 대응 테스트, Architecture·도메인·평가 guide 및 발견 가능한 진입점이다.
- 기존 합성 Dataset과 Prompt는 먼저 조회해 실제 이름·버전·사례·부작용을 확인한다. 반복 실행은 원격 setup을 자동 재실행하지 않는다.
- 현재 작업 트리에는 이 Change 생성 전에 수행된 구현과 검증이 있다. 이는 적용 시 재검증할 선행 자료이며, 이 제안서가 그 작업의 사전 계획이나 정본 동기화 완료를 소급 증명하지 않는다.
- 개발 협업 근거는 실제 대표 변경의 소유 범위·연결 검증·충돌·재작업에서 확보한다. 폴더 분리·개별 green·제품의 Task 계약만으로 협업 비용 감소를 입증했다고 보지 않으며, 비교 가능한 작업 근거 없이 생산성 향상을 주장하지 않는다.

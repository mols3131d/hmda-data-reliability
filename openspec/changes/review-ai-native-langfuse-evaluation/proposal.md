---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Native Langfuse Review Evaluation
description: 현재 세 단계 검토를 Langfuse native 실험·사람 평가에 연결하고 중복된 로컬 평가 모델을 제거합니다.
---

## Why

현재 로컬 평가 코드는 점수·합계·비교 결과와 보고서를 직접 보관하지만 실제 모델 출력이나 사람 평가가 완료됐음을 증명하지 않는다. 사용자가 [전환 계획](../../../inbox/github-280-improve-review-ai-output-quality/11-plan-review-ai-langfuse-evaluation.md)의 다음 작업을 승인했다. Langfuse가 제공하는 Dataset·SDK experiment·Score Config·Annotation Queue·compare를 사용하고 프로젝트는 현재 검토 실행과 대상 무결성·평가 완비만 책임진다.

## What Changes

- 합성 corpus를 명시적 opt-in Dataset·SDK experiment에 연결하고 기존 한국어 세 단계·로컬 원문·시간 예산을 재사용한다.
- 합성 사례와 단계 답변·collection을 허용된 원격 input/output에 연결한다. Metadata에는 고정 식별자·digest·상태와 정제된 설정만 남긴다.
- 다섯 기준의 0·1·2 categorical 점수와 사람의 사유, Annotation Queue·native compare를 사용한다.
- 거대한 ReviewValue 평가·합계·비교 모델과 재수출·전용 직렬화·Markdown 보고서를 제거한다. 사례 payload·실제 canonical input·workflow/output 연결과 사람 annotation의 완비 검사는 남긴다.
- 의도한 코드 변경 비교에는 서로 다른 실제 revision을 허용하되 사례·rubric·비교 조건을 고정하고 실제 SHA를 보존한다.
- 로컬 검토 결과와 외부 전송·원격 조회·사람 평가의 증거를 구분한다.

## Boundaries

- **In Scope:** 합성 corpus·SDK Dataset task·사례/단계 관측·native 점수와 검토 대기열·얇은 연결 및 완비 검사·기존 평가 모델 제거·현재 안내.
- **Out of Scope:** 실제 HMDA 적재·외부 운영 데이터 수집·Prompt Management 이전·모델 JSON 출력 복원·옛 projection과 호환 wrapper 부활·자동 LLM judge·점수로 GitHub 승인/병합 또는 recovery 권한 생성.
- 실제 원격 조회와 사람이 작성한 평가가 없으면 그 증거를 완료로 기록하지 않는다. Fake SDK·합성 점수·flush 반환으로 대체하지 않는다.

## Capabilities

### Modified Capabilities

#### `reliability-agentic-review`

- 현재 검토와 provenance를 Langfuse native 평가로 연결하고 원문 전송·평가 기록 소유권·비교 조건과 실패 경계를 조정한다.

## Impact

- 적용 기준은 `33e1a453`이다. [조사](../../../inbox/github-280-improve-review-ai-output-quality/10-research-review-ai-langfuse-evaluation.md)는 이전 구현과 공식 기능의 근거로 사용한다.
- SDK pin은 `langfuse==4.15.6`을 유지한다. 최신 v5 문서의 API를 현재 지원 계약으로 간주하지 않는다.
- 과거 실행 파일·Inbox·Git 기록은 보존하며 현재 결과로 변환하지 않는다.

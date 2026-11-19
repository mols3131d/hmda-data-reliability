---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Replace the Reliability AI Investigation Runtime
description: 기존 사고 조사 실행부를 교체하고 모델 제공자 선택, 근거 기록과 오프라인 재현을 지원합니다.
---

## Why

현재 사고 조사 함수가 모델 호출, 도구 분기와 실행 기록을 함께 관리한다. 조사와 평가에 OpenAI 호환 호출 형태가 연결되어 있어 Codex 구독 인증을 추가하거나 적재 조사에서 같은 흐름을 사용하기 어렵다. 턴마다 누적 요청과 응답이 반복 저장된다. [실행부 교체 설계](../../../inbox/github-291-build-ingestion-agent-harness/07-design-reliability-ai-runtime-replacement/README.md)

## What Changes

- 기존 사고 조사 API·위임 실행·합성 평가를 새 조사 실행부로 전환하고 이전 모델·도구 루프를 제거한다.
- 로컬 제공자로 ChatGPT 구독 OAuth를 사용하는 Codex를 우선 연결한다. Ollama를 포함한 명시적 OpenAI 호환 설정과 어댑터 주입을 계속 지원한다.
- 턴과 근거를 중복 없이 참조할 수 있는 기록을 남기고, 같은 입력·경계 결과로 조사를 오프라인에서 재현한다. 공개 결과와 과거 실행 자료의 읽기 계약을 유지한다.
- 백필의 필수 DB 연결이 누락되면 모델 호출 전에 차단한다. 복구는 성공한 조사와 별도로 승인된 요청이 있는 경우 기존 실행기에 인계한다.

## Boundaries

- **In Scope** 사고 조사와 기존 호출부의 전환, 두 제공자 연동, 로컬 실행 기록과 Langfuse 연결, 위임 복구 전제 확인.
- **Out of Scope** HMDA 적재 조사 자체의 구현, HMDA 적재·Airflow 실행 계약 변경, 복구 권한 확대, 사람 평가나 벤치마크 플랫폼 구축.

## Capabilities

### Modified Capabilities

#### `reliability-agentic-review`

- 제공자 선택 및 제한된 호출, 조사 근거 보존과 재현, 위임 백필의 사전 차단을 정의한다. [현재 명세](../../specs/reliability-agentic-review/spec.md)

## Impact

- `reliability_ai`의 사고 조사·위임·평가는 같은 실행부를 사용한다. `runtime_ai`는 제공자별 전송과 오류 정규화를 담당한다.
- [적재 조사 Change](../reliability-ai-investigate-hmda-ingestion/proposal.md)는 이 실행부를 사용해 원천 준비와 Airflow 실행 결과를 읽는다.

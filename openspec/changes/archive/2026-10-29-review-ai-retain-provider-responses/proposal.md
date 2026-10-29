---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Retain Provider Responses
description: 출력 검증 실패의 원인을 직접 조사할 수 있도록 모델 응답 본문을 로컬에 보존합니다.
---

## Why

실제 invocation `ar-20261028-8bd47b3a40d6`은 응답을 받았지만 조건부 priority 검증에 실패해 본문을 잃었다. 사용자는 2026-10-28에 검증 성공 여부와 관계없이 출력 자체를 저장하도록 명시적으로 요청했다. 이 요구는 과거 raw 응답 미보존 결정을 로컬 응답 파일에 대해 변경한다.

## What Changes

- Runtime이 반환한 bounded 응답 본문을 검증 전에 별도 로컬 파일로 보존한다.
- 실행 결과에 응답 파일 경로를 제공하고 실패해도 본문을 직접 읽을 수 있게 한다.
- 기존 sanitized invocation record, fail-closed validation과 외부 projection 경계를 유지한다.

## Capabilities

### Modified Capabilities

- `reliability-agentic-review`: 로컬 응답 보존과 결과의 경로 제공.

## Boundaries

출력 계약 완화, 자동 repair/retry, 원문 콘솔·로그·Langfuse 전송과 provider 설정 변경은 포함하지 않는다. Runtime이 본문을 반환하지 않은 unavailable/oversized 실패에는 보존할 본문이 없다. 과거에 저장하지 않은 응답은 복원하지 않는다.

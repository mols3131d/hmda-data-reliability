---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Extract Review AI Prompt Resources
description: 프롬프트 지시문을 독립 텍스트 파일로 분리해 직접 읽고 편집할 수 있게 합니다.
---

## Why

Review AI의 버전별 지시문이 Python 렌더링 코드 안에 있어 프롬프트 내용을 찾아 읽고 편집하기 어렵다.

## What Changes

- `review_ai/prompt.py`를 동일 import 경로의 `review_ai/prompt/` 패키지로 바꾼다.
- v1, v2, v3 지시문을 각각 UTF-8 `.txt` 파일로 분리한다.
- 기존 메시지 바이트, digest, 입력 투영과 validation 동작을 보존한다.

## Capabilities

`reliability-agentic-review`의 관찰 가능한 계약은 바뀌지 않는 순수 리팩터링이며 `skip_specs: true`를 사용한다.

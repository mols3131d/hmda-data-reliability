---
type: brief
title: PR 287 LLM Test Structure Work Status
description: "PR #287의 작업 브랜치와 최신 main 비교, 구현 현황, 검증 범위, 다음 조사 항목을 기록한다."
tags:
  - testing
  - llmops
  - ci
---

# PR 287 LLM Test Structure Work Status

2026-11-18 KST 기준 PR #287은 Open / Draft이며 `review readiness`는 `not_ready`다. 기존 조사와 `main` 변경에 대한 인계가 작성됐다. 현재 PR에서 LLM 테스트 분류, 실호출의 opt-in 및 guard, CI 선택 규칙의 구현과 회귀 검증이 남아 있다. [PR #287](https://github.com/mols3131d/hmda-data-reliability/pull/287)

## Branch And Evidence

| 항목 | 확인한 상태 |
| --- | --- |
| 작업 브랜치 | `agent/test/refactor-llm-test-structure` |
| 동기화 전 PR head | `fc2d581ccb3d3282413889c6a5c0807fe6e18dbb` |
| 동기화 대상 `main` | `a326d8d9cfb8c7cc477e46b3df67c05e62d093dc` |
| 동기화 전 분기점 | `7efb332c2efd78f77ee724440e28285ebb3ee55f`. 양쪽에 각 3개 커밋이 있었다. |
| 기존 PR 변경 | `00` 조사와 `01` 인계 두 문서. `fc2d581c`는 최신 아키텍처에 맞춰 조사 가정을 재검토하라는 인계를 추가했다. |
| `main` 반영 | GitHub에서 충돌 없이 병합했다. 병합 커밋 `7339f7cb68e74d5e7c4e468683b7391cd6030689`의 부모는 기존 PR head와 동기화 대상 `main`이다. |

이전 CI Lite 실행 `44018335858`은 `a326d8d9`와 `fc2d581c`의 prospective merge `ac9289b612abdaa6401dd723398d9949f0fdf947`에서 변경 분류까지 통과했다. Markdown 검사와 `Run selected tests`는 건너뛰었다. [이전 CI Lite 실행](https://github.com/mols3131d/hmda-data-reliability/actions/runs/44018335858)

새 브리핑은 로컬 Markdown 검사를 통과했다. 기존 두 문서에는 목록 번호(`MD029`)와 제목 표기(`MD036`) 관련 검사 결과가 남아 있다.

## Current Test Boundaries

- `main`의 PR #284에서 기존 Review AI 구조가 `reliability_ai`의 `investigation`, `execution`, `evaluation`으로 바뀌었다. 테스트 조사 경로는 `tests/reliability_ai`, `tests/runtime_ai`, `tests/scripts/ci`를 기준으로 잡는다. [Architecture](../../docs/ARCHITECTURE.md), [Main Alignment Handoff](01-brief-llm-test-structure-main-alignment-handoff.md)
- `unit`, `component`, `integration`은 테스트가 연결하는 경계를 표현한다. 로컬 pytest와 CI의 기본 필터에서 제외하는 marker는 `memory`와 `stress`다. 실제 LLM·원격 서비스 실행 여부는 fixture, 주입된 transport, SDK 호출 경로를 추적해 확인해야 한다. [Testing Guide](../../docs/development/testing.md), [pytest 설정](../../pyproject.toml), [CI 실행기](../../scripts/ci/run_checks.py)
- 기존 회귀 검증에는 `ScriptedTransport`, `httpx.MockTransport`, Langfuse client 대체 fixture가 쓰인다. Langfuse native Dataset Experiment는 별도 명시 실행으로 운영한다. 이번 작업에서는 pytest 수집·실행과 외부 LLM·Langfuse 호출을 수행하지 않았다. [Main Alignment Handoff](01-brief-llm-test-structure-main-alignment-handoff.md), [Reliability AI Evaluation](../../docs/development/review-ai-evaluation.md)

## Remaining Work

1. 현재 테스트를 수집하고 SDK, transport, fixture를 추적해 offline fake, SDK와 모의 HTTP, 로컬 실모델, 원격 서비스, 과금 가능 provider 경로를 확인한다.
1. `llm_live`, `llm_paid`, `service_live` 후보는 확인된 호출 사례와 차단 필요성에 근거해 채택 여부를 결정한다. 실호출 경로에는 명시적인 opt-in과 적용 가능한 호출 한도를 검토하고, 직접 node 실행과 `-m` 재지정에서도 기본 차단을 검증할 수 있게 설계한다.
1. 필요한 pytest 설정과 full·scoped CI 선택 규칙을 함께 수정한다. 기존 SDK 모의 전송 회귀 검증, opt-in 누락과 한도 초과, 변경 영향이 불명확할 때의 CI 동작을 검증한다.

기존 제안과 미결 질문은 조사와 인계에 보존돼 있다. [Original Research](00-research-review-ai-llm-test-structure.md), [Main Alignment Handoff](01-brief-llm-test-structure-main-alignment-handoff.md)

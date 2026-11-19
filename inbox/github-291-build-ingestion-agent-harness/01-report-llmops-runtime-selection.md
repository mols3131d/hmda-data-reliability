---
type: report
title: LLMOps Redesign Runtime Selection
description: LangGraph와 Deep Agents의 선택 기준과 PR 291에서 비교할 범위를 정리합니다.
tags:
  - llmops
  - langgraph
  - deep-agents
  - reliability-ai
  - langfuse
---

# LLMOps Redesign Runtime Selection

**권고는 기존 Python 실행부와 Langfuse를 기준으로 삼고, PR #291의 읽기 전용 조사에서 필요한 만큼만 바꾸는 것이다.** 정해진 절차의 흐름과 중단 후 재개가 문제라면 LangGraph를 우선한다. 증거가 부족하거나 상충할 때 모델이 다음 조회를 고르는 일이 중요하다면 Deep Agents를 시험한다.

## Decision Criteria

LangGraph에서는 코드가 단계, 실패 시 분기, 재개 위치를 정한다. Deep Agents는 그 위에서 모델이 계획을 세우고 도구를 고르도록 돕는다. 현재 Python 조사도 허용된 도구 안에서 모델이 다음 조회를 고를 수 있으므로, Deep Agents는 그 기준보다 나은 결과를 보여야 한다. [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview), [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview), [현재 조사 코드](../../src/hmda_reliability/reliability_ai/investigation/service.py)

| 가장 큰 문제 | 우선 선택 | 판단 기준 |
| --- | --- | --- |
| 실행 기록이나 평가 결과를 비교하기 어렵다 | 현재 실행부 + Langfuse | 프롬프트 버전, 사용한 근거, 결과와 사람 평가를 같은 실행에서 확인할 수 있는가? |
| 절차에 분기가 많고 중단 뒤 이어가기 어렵다 | LangGraph 중심 | 실패 지점이 분명하고, 재개해도 이미 끝난 작업이 중복되지 않는가? |
| 사건마다 필요한 근거와 조사 순서가 달라진다 | Deep Agents 중심 | 중요한 근거를 더 자주 찾거나 사람이 다시 확인하는 일을 줄이는가? 추가 호출·지연·운영 부담을 감당할 수 있는가? |

## First Trial In PR 291

PR #291은 아직 계획 단계다. 첫 비교는 허용된 자료를 읽고, 근거와 함께 `ready`, `blocked`, `needs_human`을 반환하는 데까지 한다. 실제 적재와 복구는 기존 서비스가 맡는다. 앞으로 쓰기를 연결할 경우, 실행 직전에 대상·현재 상태·권한을 재확인하고 재시도해도 변경이 한 번만 일어나는지 검증해야 한다. [PR #291 계획](https://github.com/mols3131d/hmda-data-reliability/blob/617aba0434bed79273c55530f67bfc04189afffd/inbox/github-291-build-ingestion-agent-harness/01-plan-ingestion-agent-harness-mvp.md#L15-L63), [실행 경계](../../docs/ARCHITECTURE.md#execution-boundaries), [중단 후 재개](https://docs.langchain.com/oss/python/langgraph/interrupts)

1. **같은 조건에서 비교한다.** 모델, 프롬프트, 입력, 도구와 예산을 고정한다. 현재 Python 조사와 두 후보에 정상 사례와 근거가 상충하는 사례를 준다. 미구현 적재 조사는 같은 입출력을 쓰는 간단한 Python 흐름을 비교 기준으로 삼는다.
1. **권한과 실패 처리부터 확인한다.** 범위 밖 조회·변경·원문 전송을 막고, 한도를 넘기면 이유를 남기고 종료해야 한다. 로컬 근거를 보존하고, Langfuse 전송 실패가 모델 재호출을 일으키지 않는지 확인한다. 재개를 도입하면 중복 실행도 검사한다.
1. **사람에게 생긴 이점을 확인한다.** 후보 이름을 가리고 근거의 정확성, 불확실성 표시, 다음 조치의 구체성을 평가한다. 수동 재조회 횟수와 함께 지연·토큰·도구 호출을 비교한다. 정상 사례의 품질을 유지하면서 중요한 누락이나 재작업이 반복해서 줄어들 때 도입 범위를 넓힌다. [현행 평가 기준](../../docs/development/review-ai-evaluation.md#human-evaluation)

Langfuse는 두 방식 모두에서 프롬프트 관리, 실행 추적, 실험과 사람 평가에 쓸 수 있다. 원격 추적은 실행 ID로 실제 조회해 확인한다. [현재 실행·평가 절차](../../docs/development/review-ai-evaluation.md), [Langfuse 연동](https://langfuse.com/integrations/frameworks/langgraph)

2026-11-19 문서·코드 조사 기준은 로컬 `origin/main` `fe67f9eb6b76f4f4f3215c355dbdff91f689b7f7`과 PR #291 `617aba0434bed79273c55530f67bfc04189afffd`이다. 후보 실행·원격 추적 조회·사람 평가는 검증 과제로 남아 있다.

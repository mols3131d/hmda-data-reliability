---
type: report
title: Reliability AI Implementation Status
description: 기존 사고 조사, 승인된 복구 연결, 모델 호출과 HMDA 적재의 구현 범위를 확인하고 PR 291의 남은 작업을 정리합니다.
tags:
  - reliability-ai
  - llmops
  - ingestion
---

# Reliability AI Implementation Status

**기존 코드로 `null_spike` 사고를 조사하고, 호출자가 승인한 복구 요청을 기존 실행기에 넘길 수 있다.** 조사에는 Python 실행 루프, OpenAI 호환 모델 호출, Langfuse 프롬프트와 관측을 사용한다. HMDA 적재도 별도 Airflow 경로로 동작한다. PR #291의 새 LangGraph 실행부, Codex 구독 로그인 연동, 적재 조사는 설계 단계다.

## Current Implementation

| 영역 | 현재 가능한 작업 |
| --- | --- |
| 사고 조사 | `investigate_incident`가 모델 응답에 따라 사건 근거 조회, 사건에 묶인 프로필 비교, 지정된 dbt 산출물의 영향 조회를 반복한다. 허용 도구와 호출 횟수·시간을 제한한다. 보고서의 수치는 확정된 입력에서 가져오고 모델은 발견 사항·가설·불확실성을 작성한다. [조사 서비스](../../src/hmda_reliability/reliability_ai/investigation/service.py), [도구 범위](../../docs/domains/review-ai.md#investigation) |
| 위임과 승인 | `execute_delegated_task`가 호출자의 Task와 사고·대상·범위를 대조한다. 조사에 성공하고 일치하는 승인 요청과 실행 연결을 받은 경우 기존 backfill 또는 schema recovery 실행기를 호출한다. 실행 결과를 `ReportEnvelope`에 담고, 승인이 필요한 복구는 제안으로 반환한다. [위임 서비스](../../src/hmda_reliability/reliability_ai/execution/service.py) |
| 모델 호출 | `OpenAICompatibleAdapter` 하나가 Chat Completions를 호출한다. Ollama도 호환 주소로 연결할 수 있다. 호출 시간, 재시도, 응답 크기를 제한하고 도구 호출과 사용량을 공통 형식으로 돌려준다. [호출 코드](../../src/hmda_reliability/runtime_ai/provider.py), [연결 설정](../../docs/development/review-ai-evaluation.md#configure-connections) |
| 실행 근거와 평가 | 조사 서비스가 Langfuse의 버전 있는 프롬프트를 가져오고 실제 모델·도구 호출 구간을 관측한다. 파싱 전에 응답 본문과 도구 호출 자료를 로컬에 보존한다. 합성 Dataset 실험 CLI도 같은 사고 조사 함수를 호출한다. [평가 및 관측](../../docs/domains/review-ai.md#provenance-and-evaluation), [실험 CLI](../../src/hmda_reliability/reliability_ai/evaluation/experiment.py) |
| HMDA 적재 | `hmda_data_plane`의 기존 흐름은 Bronze 적재 → 품질 게이트 → 조건부 dbt 분석이다. Raw Asset 이벤트에 적용 연도·행 수를 남긴다. 적재 준비에서 확인한 원천 버전을 실제 실행에 결합하는 기능은 PR #291 설계에 남아 있다. [적재 실행기](../../src/hmda_reliability/data_operations/runner.py), [Airflow DAG](../../src/hmda_reliability/orchestration/dags/hmda_data_plane.py) |

## Verification

2026-11-19 KST 기준 로컬 `90bbbe668313baf35470416581d5c8642e9c6996`에서 실행했다. 이 체크아웃과 PR #291 base 사이에 위 애플리케이션 코드와 의존성 차이는 없으며, 실행한 테스트의 차이는 pytest marker 위치 변경이다.

| 실행 | 결과와 확인 범위 |
| --- | --- |
| `uv run --no-sync pytest -q tests/reliability_ai tests/runtime_ai` | **253개 통과.** 모의 모델 응답과 오프라인 Langfuse 경로에서 도구 제한, 실패 기록, 승인 경계, 관측을 검증했다. |
| `uv run --no-sync pytest -q tests/hmda_data/test_ingestion.py tests/hmda_data/test_ingestion_partition.py tests/orchestration/test_airflow_dag.py tests/orchestration/test_airflow_dagrun.py -p no:cacheprovider` | **57개 통과.** 격리된 DuckDB와 Airflow에서 적재·품질 차단·dbt 분석 및 Asset 근거를 확인했다. |

이번 검토에서 실제 Ollama·Codex 응답, Langfuse 서버에서의 관측 재조회, 사람의 응답 품질 평가는 수행하지 않았다. 기존 코드의 `InvestigationResult.status=completed`는 응답 구조 검증과 필수 로컬 저장이 끝났다는 뜻이다. [오프라인 검증 범위](../../docs/development/testing.md#reliability-ai-evaluation), [사람 평가 기준](../../docs/mvp.md#mvp-acceptance)

## PR 291 Progress

[PR #291](https://github.com/mols3131d/hmda-data-reliability/pull/291)은 Draft다. 원격 base `35d099c748cbe08ae6a12ce60acd7574fe086719`와 head `617aba0434bed79273c55530f67bfc04189afffd`의 차이는 준비 문서 4개다. 현재 로컬에는 [적재 조사 OpenSpec](../../openspec/changes/reliability-ai-investigate-hmda-ingestion/tasks.md)이 있고, 7개 작업 모두 구현 전이다. 기존 사고 조사 실행부 교체는 별도 Change로 준비할 차례다.

1. **기존 사고 조사 실행부 교체.** LangGraph는 의존성에 있고 LangChain Core는 그 하위 의존성으로 잠겨 있다. 애플리케이션에서 둘을 사용하는 조사 실행 경로는 아직 없다. 기존 조사 API와 이를 호출하는 위임·평가 경로가 새 그래프를 사용하도록 전환하고, 도구 제한·근거 보존·승인 경계를 검증한다. 모델 제공자는 ChatGPT 구독 OAuth로 로그인한 Codex를 먼저 연결하고 로컬에서 확인한다. Ollama도 선택할 수 있게 한다. [Codex 연동 설계](04-design-runtime-ai-codex-oauth-provider.md)
1. **적재 조사 추가.** 새 실행부에서 `prepare`로 실제 적재에 앞서 원천 버전과 준비 근거를 확인하고, `review_run`으로 지정한 Airflow 실행의 결과를 읽는다. 1단계에서 정한 모델 연결을 두 흐름에 적용한다. [적재 조사 설계](02-proposal-ingestion-llmops/README.md)

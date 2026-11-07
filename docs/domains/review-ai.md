---
title: "Reliability AI: Bounded Investigation And Delegation"
description: "사건 snapshot의 도구 조사, 외부 승인 요청의 위임 실행, 실패 근거와 native 평가 경계를 설명합니다."
categories:
  - reliability
  - artificial-intelligence
tags:
  - ai-delegation
  - deterministic-validation
  - evidence-first
  - provenance
---

# Reliability AI: Bounded Investigation And Delegation

**`reliability_ai`는 제한된 근거 조사와 caller가 승인한 복구 요청의 조합을 소유한다.** 결정론적 facts·승인·복구 정책은 Reliability에 남긴다. 현재 입력은 `null_spike`이며 모델의 설명·가설·권고는 truth나 실행 권한이 아니다.

## Scope And Dependencies

| Owner | Responsibility |
| --- | --- |
| `reliability` | 탐지·초안·exact proposal Approval·stale 검사·복구·재검증·reconciliation |
| `reliability_ai.investigation` | 불변 사건 입력·bounded 도구 조사·구조화 보고·실패 근거 |
| `reliability_ai.execution` | Task 제한·복구 요청의 사건 일치·기존 executor 호출·실제 결과 보고 |
| `runtime_ai` | Provider-neutral 계약·OpenAI-compatible 전송·timeout·retry |

Source 의존은 `reliability_ai -> reliability`, `reliability_ai -> runtime_ai`다. Reliability는 AI를 import하지 않고 Runtime은 도메인 판단·Langfuse를 소유하지 않는다. 현재 capability 계약은 [Investigation Spec](../../openspec/specs/reliability-agentic-review/spec.md)과 [Prompt Spec](../../openspec/specs/review-ai-prompt-engineering/spec.md)이 소유한다.

## Investigation

[AgenticReviewInput](../../src/hmda_reliability/reliability_ai/contracts.py)은 Incident·Evidence·Draft의 identity·reference set과 유일한 canonical profile을 검증하고 깊게 복사한다. [Context projection](../../src/hmda_reliability/reliability_ai/context.py)은 초기 자료와 Evidence 도구 결과의 허용 필드·크기·개인 경로 정책을 공유한다. `missing_evidence`와 `unconfirmed_context`는 다르다.

[investigate_incident](../../src/hmda_reliability/reliability_ai/investigation/service.py)는 시작에 읽은 native Prompt를 고정하고 모델의 종료 또는 도구 선택을 따른다. 고정 호출 순서는 없다. Caller의 allowlist, 호출 수·누적 prompt bytes·시간 예산을 매 호출 전에 적용한다. 동기 호출이나 원격 추론의 강제 취소는 보장하지 않는다.

| Default Tool | Observed Scope |
| --- | --- |
| `get_incident_evidence` | 제공된 catalog의 Evidence를 bounded projection으로 조회 |
| `compare_profiles` | 사건 snapshot의 canonical column과 실제 baseline/current/delta·출처 조회 |
| `inspect_dbt_impact` | trusted caller가 지정한 pair만 shared reader lock에서 분석; current projection ID·관측 시각 기록 |

Profile 도구는 live profiling이 아니다. Dbt의 current 관측은 과거 사건 snapshot을 대체하지 않는다. 빈 downstream은 미해결 asset과 leaf를 구별하지 못하므로 no-impact로 확정하지 않는다. 모델은 SQL·임의 파일·다른 target·mutation·Approval을 요청할 수 없다.

결과의 canonical facts는 입력에서 유지하고 모델은 findings·hypotheses·uncertainties를 작성한다. `completed`는 유효한 최종 구조와 필수 로컬 저장만 뜻한다. 설명의 사실성·한국어 준수·효용은 별도 평가 대상이다. 실패 상태와 이미 회수한 partial 기록을 성공으로 바꾸거나 재생성으로 감추지 않는다.

## Delegated Execution

[execute_delegated_task](../../src/hmda_reliability/reliability_ai/execution/service.py)는 Task·조사 입력·caller의 approved request를 먼저 대조한다. 다른 incident·target·partition·snapshot reference, 동시 Backfill/schema 요청은 차단한다. Task와 caller 설정의 교집합·최소 예산을 사용하고 조사 실패 뒤에는 mutation으로 진행하지 않는다.

AI의 `ActionProposal`이나 상위 모델의 위임은 승인이 아니다. Caller가 별도로 제공한 authoritative request만 기존 deterministic executor로 전달한다. [ReportEnvelope](../../src/hmda_reliability/reliability_ai/execution/contracts.py)는 원래 Task, 조사·proposal·실행 receipt와 차단·미확인 사항을 함께 전달한다. 실행 receipt는 실제 결과의 소비자이며 domain의 mutation·재검증·reconciliation 의미를 다시 정의하지 않는다.

## Provenance And Evaluation

Runtime의 exact UTF-8 본문은 파싱·원격 output·완료 판정 전에 private create-only 저장한다. Manifest는 canonical input·revision·실제 Prompt name/version·compiled 메시지/digest·설정·turn·usage·도구·결과를 연결한다. Trusted artifact 경로는 로컬에만 남긴다. 별도 observation record는 core 저장 뒤 발생한 SDK 오류도 기록한다.

Native generation과 tool은 실제 호출 구간에 생성되고 같은 조사 아래 sibling이다. 허가된 합성 사례만 정제된 system·history·tool IO를 원격에 보낸다. Metadata에는 본문·credential·provider 예외·개인 경로를 자동 캡처하지 않는다. 관측 장애는 모델 재호출이나 core 결과 변경의 이유가 아니다.

[명시적 setup](../../src/hmda_reliability/reliability_ai/evaluation/setup.py)과 [반복 Dataset task](../../src/hmda_reliability/reliability_ai/evaluation/experiment.py)는 분리한다. API·위임·CLI는 같은 investigation 경로를 쓴다. Offline 통과·SDK 반환·원격 재조회·사람 평가는 각각 다른 근거다. 등록·실험·실패 해석과 다섯 기준의 사람 평가는 [Evaluation Guide](../development/review-ai-evaluation.md)를 따른다.

## Change And Verification

[공개 API](../../src/hmda_reliability/reliability_ai/__init__.py)에서 입력·조사·Task·보고 계약을 찾을 수 있다. 공유 입력·오류·상태 의미를 바꾸면 해당 생산자와 소비자를 함께 확인한다. 기존 [도구 테스트](../../tests/reliability_ai/test_investigation_tools.py), [조사 테스트](../../tests/reliability_ai/test_investigation_agent.py), [위임 연결 테스트](../../tests/reliability_ai/test_execution_service.py), [실험 테스트](../../tests/reliability_ai/test_experiment_runner.py)가 가까운 검증점이다.

도구 의미 변경은 context·registry, 호출 lifecycle 변경은 investigation, 복구 조합 변경은 execution이 소유한다. 같은 service나 공유 계약을 함께 바꾸는 작업은 독립 변경으로 가정하지 않는다. Package 분리·개별 green은 연결 검증이나 개발 협업 비용 감소의 증거를 대신하지 않는다.

---
type: design
title: Reliability AI Runtime Migration and Verification
description: 기존 사고 조사 실행부의 교체 순서와 전환을 완료할 검증 근거를 정합니다.
---

# Reliability AI Runtime Migration and Verification

## Cutover

1. **사고 조사 교체용 OpenSpec Change를 먼저 작성한다.** `reliability-agentic-review`가 소유한 공개 진입점, 예산, 결과 상태, 근거 보존, 위임 복구 계약을 기준으로 삼는다. 제공자 선택과 백필 사전 차단, 새 기록 형식에서 달라지는 동작을 delta와 검증 사례에 반영한다. [현재 명세](../../../openspec/specs/reliability-agentic-review/spec.md)
1. **기존 호출자를 새 그래프로 전환한다.** `investigate_incident`의 `AgenticReviewInput`과 `InvestigationResult`를 유지한다. `execute_delegated_task`와 평가 CLI가 이 진입점을 통해 같은 그래프를 사용하게 한다. 기존 호환 어댑터 주입과 설정은 호출부에서 수용한다. [공개 진입점](../../../src/hmda_reliability/reliability_ai/__init__.py), [제공자 선택](provider-and-evidence.md#provider-contract)
1. **기존 실행 루프를 제거한다.** 세 호출 경로가 같은 그래프를 사용하는지 확인하고 `investigation/service.py`의 모델·도구 반복 루프와 그 전용 연결 코드를 걷어낸다. 기존 실행 ID와 산출물을 보존하고, 새 형식의 기록에는 스키마 버전을 붙인다. 이미 보존한 과거 실행의 결과와 원문은 기존 방식으로 읽을 수 있게 한다. [교체 대상 코드](../../../src/hmda_reliability/reliability_ai/investigation/service.py#L295), [근거 보존 계약](../../../openspec/specs/reliability-agentic-review/spec.md#requirement-investigation-provenance-and-failure-retention)
1. **적재 조사를 연결한다.** 기존 사고 조사 교체에서 검증한 모델 제안 계약, 예산 처리, 기록 방식을 적재 전 `prepare`와 적재 후 `review_run`에 적용한다. 적재 Change가 원천·실행 근거와 두 진입점의 검증을 소유한다. [적재 조사 OpenSpec Change](../../../openspec/changes/reliability-ai-investigate-hmda-ingestion/proposal.md)

## Acceptance Evidence

| 검증 | 완료를 보여주는 근거 |
| --- | --- |
| 호출자 전환 | 공개 조사·위임·평가 CLI가 같은 그래프를 사용한다. 과거 산출물과 새 공개 결과로 상태·원문·도구 결과의 호환을 확인한다. 기존 루프 제거, 호환 설정과 어댑터를 함께 전달한 경우의 주입 우선순위, Codex 기본 선택을 확인한다. |
| 사고 조사 | 도구 없이 작성한 모델 보고서도 검증과 저장을 거쳐 완료된다. 프롬프트 조회 실패와 전체 입력 초과는 모델 호출이 0회다. 배치의 호출 순서와 초과 차단, 정확히 도구 한도에 도달한 뒤 도구 없는 보고, 반복 조회 종료를 확인한다. |
| 기한과 재시도 | 수락 전 실패와 수락 여부 불명확·수락 후 단절을 구별한다. 불명확한 수락과 늦은 응답으로 조사가 완료되거나 복구가 실행되지 않는지 확인한다. 중복 이벤트는 새 실행을 시작하지 않는다. 최종 저장이 기한을 넘으면 원문과 `budget_exhausted`를 회수한다. |
| 복구 경계 | 사건·대상 불일치, 허용되지 않은 작업, 승인 백필의 DB 연결 누락은 모델과 복구 호출이 0회다. 조사 실패 시 복구 호출은 0회다. `partial`과 `not_reported`는 실행기가 보고한 검증과 변경 상태에 맞춰 반환한다. |
| 기록과 재현 | 파싱과 최종 저장을 각각 실패시켜 이전 원문·도구 결과를 회수한다. 기록한 Prompt·입력·시각·저장 결과로 같은 종료 사유를 재현한다. 누락·불일치·손상은 재현 불가로 처리하고 실제 Prompt·Dataset·모델·도구·관측·복구 호출이 0회인지 확인한다. |
| Codex 구독 OAuth | 같은 합성 조사에서 첫 턴이 승인 가능한 조회를 제안하고, 독립 스레드의 다음 턴이 해당 제안 ID와 관찰값으로 보고한다. 범위 밖 파일·명령·네트워크·상속 도구가 실제로 작동하지 않는지 확인한다. |
| Ollama | 명시적으로 선택하여 같은 그래프에서 조회 제안과 구조화된 결과를 받는다. 호환 요청의 기존 재시도 분류·횟수와 제공자·시도·실패 원인의 연결을 확인한다. |
| Langfuse | 기존 native Dataset의 버전과 합성 항목을 사용한다. 기대값은 모델 입력에서 제외하며 누락·중복·실패 항목은 CLI 실패로 반환한다. 전송 장애는 재호출 없이 기록한다. 원격에서 같은 리비전의 Dataset 항목·조사·턴 관측을 대조한다. |

Codex 실실행을 첫 제공자 검증으로 진행한다. 각 실행에는 코드 리비전, 입력 ID, 프롬프트 버전, 선택한 제공자와 모델, 결과와 실패 이유를 남긴다. 원격 관측 조회는 사람의 조사 효용 평가와 별개의 검증 항목이다. [Codex 로컬 검증](../04-design-runtime-ai-codex-oauth-provider.md#local-verification), [MVP 수용 기준](../../../docs/mvp.md#mvp-acceptance)

## Before and After

이력이 누적되는 같은 다중 턴 사례에 동일한 모델·도구 응답을 공급한다. 두 실행에서 같은 결과와 근거를 회수할 수 있는 상태로, 원문과 보조 파일을 포함한 로컬 조사 기록 전체의 바이트가 줄었는지 확인한다. 모델 호출 수와 시도별 입력 바이트도 각각 남긴다. 실제 지연이나 사용량은 제공자·모델·입력을 맞춘 실실행에서 비교한다. Codex 구독 첫 실행은 연동 증거로 기록한다. [기존 구현과 검증 범위](../05-report-reliability-ai-implementation-status.md)

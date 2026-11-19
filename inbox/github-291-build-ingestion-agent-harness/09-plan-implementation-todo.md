---
type: plan
title: PR 291 Implementation Checklist
description: 기존 사고 조사 교체와 적재 조사 추가의 작업 순서, 검증 근거와 사람에게 넘길 지점을 기록합니다.
---

# PR 291 Implementation Checklist

완료 표시는 PR 작업 트리에서 검증한 단위에 붙인다. 상세 수용 조건은 [사고 조사 작업](../../openspec/changes/reliability-ai-replace-investigation-runtime/tasks.md)과 [적재 조사 작업](../../openspec/changes/reliability-ai-investigate-hmda-ingestion/tasks.md)에 있다. 실행 근거와 재개 지점은 [진행 보고서](10-report-implementation-progress.md)에 누적한다.

| 순서 | 할 일 | 완료를 확인하는 방법 | 현재 상태 |
| --- | --- | --- | --- |
| 1 | PR 작업 트리 동기화, 설계 반영, 교체 전 측정 | 같은 합성 입력의 결과·모델 호출 수·전체 조사 파일 바이트 보존 | 완료 |
| 2 | 사고 조사 루프를 LangGraph로 교체하고 기존 위임 경로 연결 | 실제 공개 API에서 한도와 조회 순서, 승인 범위, 실패 시 복구 0회 | 진행 중 |
| 3 | 원문과 조회를 한 번씩 보존하고 공개 결과 복원·재현 | 과거 형식 읽기, 손상 및 저장 실패 구분, 같은 입력의 저장량 감소 | 진행 중 |
| 4 | Codex 구독 OAuth 우선 선택, Ollama 명시 선택 | 모의 전송 회귀와 실제 격리된 합성 두 턴을 별도로 확인 | 진행 중 |
| 5 | 평가 CLI·Langfuse 연결 | 합성 항목 사전 검사, 버전 고정, 조사 ID로 실제 원격 기록 확인 | 대기 |
| 6 | 적재 전 준비 상태와 적재 후 실행 상태 조사 | CSV·Parquet와 실제 로더 규칙, 허용 DAG 실행·시도로 근거 제한 | 대기 |
| 7 | 적재 판단·모델·관측·재현 통합 | 확정 시 모델 0회, 미확인 시 허용 조회, 오프라인 외부 호출 0회 | 대기 |
| 8 | 운영 가이드, 독립 검토, 회귀 검증, Draft PR 갱신 | 실행한 명령과 결과, 미검증 항목 및 사람의 결정 기록 | 대기 |

사람에게 필요한 계정 인증·접근 권한 또는 결과 채택 결정이 발생하면 진행 보고서에 필요한 조치와 재개 조건을 기록한다.

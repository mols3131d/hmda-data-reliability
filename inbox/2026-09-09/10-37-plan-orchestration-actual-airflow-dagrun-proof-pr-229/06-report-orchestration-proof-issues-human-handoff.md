---
type: report
title: "Airflow Proof Issues And Human Handoff"
description: "실측으로 확인한 증명 공백과 재현성·전달 위험을 분류하고, 인간의 결정 및 승인 후 에이전트 후속 작업을 구분한다."
tags: [orchestration, airflow, evidence-gap, human-decision, pr-229]
---

# Airflow Proof Issues And Human Handoff

> [!IMPORTANT]
> 이 보고서는 작업 중간에 인간 핸드오프를 재분류한 기록이다. 2026-09-10 옵션 A에 따라 계약별 증거 대조와 관련 테스트 실행을 완료했으며, scheduler-service 실행은 canonical spec과 MVP의 완료 조건이 아닌 것으로 판정했다. 현재 이슈 상태와 완료 판단은 [07 보고서](07-report-orchestration-pr-229-issues-blockers.md)가 소유한다.

## Assessment

**현재 확인된 핵심 문제는 프로덕션 DAG 결함이 아니라 요구한 증명과 실제 확보한 증거의 범위 차이다.** 두 테스트 실행은 기대 결과를 보였지만 scheduler service 실행이나 전체 spec 충족을 입증하지 않는다. 이 보고서는 2026-09-09 [실측 결과](04-report-orchestration-actual-airflow-dagrun-proof-result.md), [작업 목록](tasks.md) 및 직전 작업의 검토·전달 기록을 정리한다. 신규 런타임 조사나 재실행 결과가 아니다.

## Open Issues

### Proof Scope

| ID | Evidence | Impact | Disposition |
| --- | --- | --- | --- |
| P1 | 두 DAGRun 모두 `triggered_by=TEST`, `creating_job_id=null`, `scheduled_by_job_id=null` | scheduler-managed 수동 실행 증거는 없음 | 자동 생성은 H1 결정으로 범위 밖. 수동 실행의 runtime 증거 공백과 보완 방법은 에이전트가 판단·검증 |
| P2 | CLI terminal state와 start/end 순서는 있으나 모든 중간 상태 전이를 수집하지 않음 | lifecycle 전체 전이를 실측했다고 주장할 수 없음 | 에이전트가 계약과 위험에 맞는 관찰 방법을 선택. 요구된 전이를 생략하거나 관찰하지 않은 상태를 입증했다고 주장하지 않음 |
| P3 | gate 실패와 정상 promotion 두 시나리오만 실행 | raw/build/promotion 실패, skip 등 나머지 spec 시나리오에 대한 실측 공백 | 에이전트가 기존 테스트와 실행 증거를 계약에 대조하고 공백을 보완. 목표 축소가 필요한 경우에만 인간 결정 요청 |

P1의 용어는 분리해야 한다. **Scheduler-created**는 누가 DAGRun을 생성했는지를, **scheduler-managed**는 누가 의존성 판단과 태스크 실행을 관리했는지를 검증하는 질문이다. 자동 schedule 생성은 확정된 MVP 범위 밖이다. 수동 실행의 runtime 검증을 자동 스케줄 도입과 혼동하지 않는다.

### Reproducibility And Delivery

| ID | Observed State | Risk | Proposed Handling |
| --- | --- | --- | --- |
| P4 | 전체 로그·metadata 추출 JSON·회수 artifact·projection 검증은 Git 미추적 `.local/pr229-proof-evidence/`에 보존 | 로컬 정리나 환경 소실 시 원격 검토자가 증거를 재확인하기 어려움 | 에이전트가 기존 증거를 유지하고 최소 JSON·검증 요약을 선별. 신규 외부 공개나 삭제 정책이 필요한 경우에만 승인 요청 |
| P5 | 원본 격리 SQLite DB와 fixture는 worktree 정리로 제거; 임시 실행기도 영구 harness가 아님 | 기존 DB 재조회는 불가하고 재실행에는 fixture 및 환경 재구성이 필요 | 추출 증거와 재현 설명을 보존하고, 반복 검증이 필요해질 때만 영구 tooling을 별도 판단 |
| P6 | 독립 검토는 보존 증거의 정합성을 확인했으나 바이트 비교·public projection 함수·lint를 독립 실행하지 않음 | 독립 재현까지 완료한 것으로 과장될 수 있음 | 에이전트가 필요한 검증과 독립 검토를 구성하고 도구 한계를 명시. 검증 기준을 면제받아야 할 때만 인간에게 요청 |
| P7 | 결과 보고서와 tasks가 미commit·미push; PR 본문만 직전 작업에서 갱신 | 설명 본문과 원격 diff의 전달 상태가 다름 | 승인된 문서와 최소 증거 범위만 commit·push한 뒤 PR 설명을 그 revision에 맞춤 |

P4와 P5는 증거 보존·재현성 위험이지 데이터 오염 증거가 아니다. 메인 DB와 manifest의 무오염은 실행 전후 SHA-256, 크기, mtime_ns 비교로 확인했다. 원본 worktree 제거는 요청된 안전 제약을 지킨 결과다.

## Resolved Findings

| Finding | Resolution | Remaining Caution |
| --- | --- | --- |
| 선행 정찰의 scheduler 완료·전체 spec 일치 표현 | 최종 보고서, tasks와 직전 PR 본문 갱신에서 범위 정정 | 과거 정찰·handoff 문서를 그대로 재사용하지 말고 최종 보고서의 정정을 함께 읽어야 함 |
| 샘플 20행이라는 사전 설명 | Asset 이벤트 기준 실제 적재 19행으로 기록 | 정상 fixture는 별도로 만든 1,000행이며 혼동하지 않음 |
| Git 미추적 샘플이 새 worktree에 없어 첫 시도 실패 | 허용된 메인 샘플만 읽어 격리 fixture로 복사; finally 정리 후 재실행 성공 | 메인 실데이터 전체 적재나 외부 경로 사용으로 우회하지 않음 |
| Projection 비교 결과의 별도 보존 증거 부재 | 회수 artifact를 다시 비교하고 `projection-verification.json`으로 통과 결과 보존 | 독립 검토자의 계산 재실행은 아니었음 |
| `gh pr edit`의 Projects GraphQL 오류 | REST API로 본문만 갱신하고 저장 결과 확인 | DAG 실행 장애와 무관하며 이번 문서 작업에서 GitHub 상태를 재확인하지 않음 |

해결된 항목은 신규 blocker로 재등록하지 않는다. 선행 자료의 표현 정정과 실제 동작 결함을 구분하며, 두 시나리오의 통과를 근거로 미검증 경로의 결함 부재까지 추론하지 않는다.

## Human Decisions

**일반적인 검증·실행·증거 정리는 인간 핸드오프 대상이 아니다.** H1은 확정된 운영 범위로 보존하고 H2~H4의 기술 판단은 에이전트 책임으로 전환한다. 미검증 항목이 해결됐다는 뜻이나 기존 acceptance를 면제한다는 뜻은 아니다.

### H1 Scope Decision

2026-09-09 요청자 결정: **현재 MVP는 자동·주기 실행을 도입하지 않으며, 필요할 때 인간이 실행한다.** `schedule=None`을 유지한다. 실행 주기는 정해지지 않았고 일일 실행 가정은 현재 요구사항이나 검증 기준에 반영하지 않는다.

이 결정에 따라 자동 schedule에 의한 DAGRun 생성은 MVP 검증 대상에서 제외하며, 그 증거가 없다는 이유로 MVP 완료를 차단하지 않는다. 앞선 P1 및 완료 브리프의 자동 생성 여부에 대한 결정 대기 표현은 이 결정으로 대체한다. 과거 `dags test` 실행이 scheduler service 검증으로 바뀌는 것은 아니다.

**수동 실행이라는 운영 방식과 실제 Airflow scheduler를 통한 실행 관리 검증은 별개의 문제다.** 에이전트는 기존 목표와 계약을 기준으로 필요한 runtime 증거를 판단하고 확보해야 한다. 이를 scheduler-created와 scheduler-managed 중 하나를 고르라는 기술 질문으로 다시 인간에게 넘기지 않는다. 현재 `dags test` 증거만으로 충분하다고 자동 판정하지도 않는다.

### Dropped Handoffs

| Former ID | Removed Question | Agent Responsibility |
| --- | --- | --- |
| H2 | 어떤 테스트와 중간 상태를 관찰할지 인간이 설계 | 계약별 증거를 대조하고 테스트 수준·시나리오·관찰 방법을 선택. 기존 테스트와 실제 실행의 증명 범위를 구분하고 필요한 공백 보완 |
| H3 | 격리 실행에 필요한 프로세스를 매번 사전 승인 | 승인된 작업 범위 내 임시 프로세스 구성·종료·정리를 담당. 실제 권한 제한이나 기존 제약과의 충돌이 있을 때만 구체적으로 요청 |
| H4 | 일반적인 증거 파일 선택·보존과 검증 방법을 인간이 지정 | 기존 저장소 방식으로 최소 증거를 정리하고 검증 가능성과 비밀정보를 확인. 기존 증거는 임의 삭제하지 않음 |
| H5 일부 | Commit할 파일 목록을 인간이 직접 선별 | 에이전트가 관련 문서·최소 증거의 전달 범위를 준비. Commit·push 실행 권한과 최종 승인만 분리 |

### Remaining Authority

| Item | Human Decision | When Needed |
| --- | --- | --- |
| H5: Repository delivery | 준비된 변경의 commit·push 요청, Ready 전환·merge 등 명시적 승인 | 해당 작업을 수행하기 직전. 현재 문서 정리나 기술 검증을 막는 선행 조건은 아님 |
| Scope exception | 요구된 검증을 제외하거나 production DAG/spec 변경, 자동·주기 실행 도입 등 명시적 경계를 변경할지 결정 | 기존 범위 안에서 해결할 수 없는 구체적인 문제가 확인됐을 때만 |
| Access or disclosure exception | 필요한 추가 접근 권한이나 새로운 외부 저장·공개를 허용할지 결정 | 실제 도구 제한 또는 외부 전송 필요가 확인됐을 때만. 일반 로컬 증거 정리를 위한 포괄적 질문은 하지 않음 |

예외 항목은 현재 발생한 blocker가 아니라 조건부 escalation 기준이다. 미충족 검증을 임의로 완료 처리하거나, 이 문서 정리 요청을 commit·push 및 범위 밖 실행 권한으로 해석하지 않는다.

## Agent Follow-Up

후속 검증 작업에서는 H2~H4의 답변을 기다리지 않고, 승인된 범위 안에서 다음을 에이전트가 담당한다.

1. 승인된 목표를 기준으로 runtime 생성 주체, scheduler 처리, 필요한 TI 전이와 이벤트를 판별할 검증 조건을 작성한다. 영구 tooling이나 계약 변경이 필요하면 적용되는 OpenSpec 절차로 분리한다.
1. 저장소 내부 disposable worktree, 소형 fixture, 독립 Airflow metadata DB·DuckDB·dbt target·TMPDIR을 구성한다. 메인 DB·manifest는 실행 전후 지문으로 보호한다.
1. 승인된 실행 경로에서 필요한 증거만 수집하고 실패·미관찰·성공을 구분한다. 프로세스 종료와 worktree 제거를 보장한다.
1. 승인된 최소 증거를 보존하고 독립 검토 범위를 충족한 뒤 문서·PR을 실제 검증 revision에 맞춰 갱신한다. Commit·push 및 Ready·merge 권한은 각각 확인한다.

이번 요청에서는 이 보고서의 핸드오프 분류만 갱신한다. 추가 runtime 실행, production/spec 수정, 증거 삭제, commit·push 또는 PR 상태 전환은 수행하지 않는다.

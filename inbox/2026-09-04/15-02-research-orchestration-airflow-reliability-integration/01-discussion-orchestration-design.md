---
type: discuss
title: "Orchestration Design Tradeoffs"
description: "오케스트레이션 설계에서 검토한 옵션과 트레이드오프를 결정별로 기록한다."
tags:
  - orchestration
  - airflow
  - reliability
---

# Orchestration Design Tradeoffs

## Decisions

| ID | 쟁점 | 옵션 | 트레이드오프 | 현재 선택 |
| --- | --- | --- | --- | --- |
| D1 | Airflow 역할 | 로직 직접 구현 / 실행만 조율 | 직접 구현은 빠르지만 domain 로직이 DAG에 중복됨 | 실행만 조율 |
| D2 | DAG 구성 | 하나의 DAG / 여러 DAG | 하나면 같은 batch 흐름을 보기 쉽고, 여러 개면 독립 운영은 쉽지만 coordination이 늘어남 | 하나의 DAG |
| D3 | Reliability 위치 | publish 전 / publish 후 | 전자는 trusted current를 보호하지만 candidate-aware 검증이 필요. 후자는 단순하지만 untrusted state가 current가 될 수 있음 | publish 전 |
| D4 | 운영 baseline | fixed golden / rolling history / cross-period / last trusted | fixed는 단순하지만 drift에 약함. rolling/cross-period는 강하지만 MVP 복잡도가 큼 | last trusted |
| D5 | Incident 상태 | Airflow FAILED / custom state / SUCCESS + INCIDENT | FAILED는 눈에 잘 띄지만 실행 실패와 데이터 문제를 섞음. custom state는 복잡함 | SUCCESS + INCIDENT |
| D6 | 최초 baseline | 첫 candidate 즉시 채택 / 사람 승인 / deterministic bootstrap | 즉시 채택은 false trust 위험. 사람 승인은 기준이 불명확해질 수 있음. bootstrap은 재현 가능하지만 gate 설계 필요 | deterministic bootstrap |
| D7 | Bootstrap 채택 | 사람 승인 / 자동 채택 / 조건부 승인 | 사람 승인은 안전해 보이지만 형식적 gate가 될 수 있음. 조건부 승인은 상태 모델이 늘어남 | PASS 후 자동 채택 |
| D8 | Trusted state 범위 | dbt artifact만 / 실제 데이터까지 | artifact만 보호하면 Bronze·mart가 이미 바뀔 수 있음. 실제 데이터까지 포함하면 publish 단위가 커짐 | 실제 데이터까지 포함 |
| D9 | Candidate 격리 | current 직접 변경 / 같은 DB 별도 schema / 별도 DuckDB | 직접 변경은 rollback 의존. 별도 schema는 routing 복잡. 별도 DuckDB는 MVP에서 단순하지만 파일 lifecycle 필요 | run-scoped DuckDB |
| D10 | Publish 방식 | mutate+rollback / artifact-only / WAP | rollback은 untrusted current 노출. artifact-only는 실제 데이터 보호 못함. WAP는 안전하지만 publish protocol 필요 | WAP |

## Open Questions

| ID | 질문 | 주요 옵션 | 핵심 트레이드오프 |
| --- | --- | --- | --- |
| O1 | Bootstrap minimum gate | 기존 validation 재사용 / absolute rule 추가 | 재사용은 단순하지만 false trust 위험. 새 rule은 근거가 필요함 |
| O2 | Trusted generation identity | 기존 snapshot ID 확장 / 별도 `generation_id` | 기존 ID 변경은 파급이 큼. 별도 ID는 contract가 하나 늘지만 경계가 선명함 |
| O3 | Baseline 저장 | Airflow metadata / DuckDB / local artifact store | Airflow는 vendor 종속. DuckDB는 같은 failure boundary. artifact store는 pointer 관리 필요 |
| O4 | Candidate assessment API | 기존 lifecycle 확장 / 별도 Data Operations API | 확장은 구현량이 작지만 의미가 섞임. 별도 API는 경계가 선명함 |
| O5 | Publish commit point | 여러 current 파일 교체 / generation bundle + active pointer | 개별 교체는 partial failure가 복잡. pointer 방식은 generation layout이 필요함 |
| O6 | Recovery | current 직접 mutation / recovery candidate 후 publish | 직접 mutation은 단순하지만 WAP invariant와 충돌. candidate 방식은 일관적이지만 구현 증가 |
| O7 | Task 간 outcome 전달 | 큰 domain result / 작은 ID+outcome | 큰 payload는 결합도가 높음. 작은 contract는 별도 evidence lookup이 필요함 |
| O8 | Candidate cleanup | 즉시 삭제 / 일정 기간 보존 | 즉시 삭제는 단순하지만 조사 evidence가 사라짐. 보존은 storage 관리 필요 |

## Next

다음 결정은 `O1 Bootstrap minimum gate`다.

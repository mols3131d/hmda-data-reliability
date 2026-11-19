---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: HMDA Ingestion Investigation Tasks
description: 원천 준비 검사부터 그래프 분기, 실행 조회, 기록·재현과 운영자 인계까지의 구현 결과를 순서대로 정의합니다.
tasks_completed: 0
tasks_total: 7
---

## Tasks

구현의 계약은 [적재 조사 명세](specs/reliability-ai-ingestion-investigation/spec.md)와 [설계](design.md)다. 각 행동 변경은 먼저 관찰 가능한 기대 결과를 테스트로 고정한다. [테스트 설계 기준](../../../docs/development/test-design.md)

- [ ] 원천 스냅샷을 고정하고 지정 범위의 준비 판정을 계산한다.
  - **Test first:** 고정 CSV·Parquet에 사람이 계산한 파일 집합·누락 열·대상 행 수를 사용한다. 파일을 하나 지정했을 때도 적재기가 검사하는 전체 파일의 필수 열을 확인한다.
  - **Done when:** 정상·확정 위반·미확인 입력이 각각 `ready`, `blocked`, `needs_human`을 반환하고, 다른 버전의 관찰값을 섞을 수 없다. 임시 Bronze와 원천은 조회 전후 동일하다.

- [ ] 선행 Reliability AI 교체 Change의 provider contract를 사용하는 적재 조사 그래프를 구현한다.
  - **Test first:** fake Codex와 Ollama adapter 응답으로 초기 근거가 다른 입력에서 서로 다른 허용 조회가 선택되고, 규칙과 다음 조치가 확정된 입력에서는 모델 호출이 없는지 확인한다.
  - **Done when:** LangGraph가 조사 상태·도구 권한·분기·종료를 관리하고 LangChain Core가 provider request/result를 전달한다. Codex App Server와 Ollama adapter는 구조화 제안과 실패 정보를 같은 contract로 돌려준다. 잘못된 근거 ID, 범위 밖 도구 요청 및 복수 호출을 거부한다.

- [ ] 허용된 Airflow 실행의 단계 결과를 읽어 사후 보고를 반환한다.
  - **Test first:** Airflow 응답 형식의 고정 데이터로 태스크 상태, 다른 실행·시도의 asset 기록, 실제 입력 버전의 일치·불일치·미확인을 검증한다.
  - **Done when:** 지정된 실행의 단계 상태와 확인된 갱신 근거를 구분해 반환한다. 증거가 부족한 경우 행 수와 입력 일치 여부의 미확인을 보고하며 조회 과정에서 상태 변경 요청을 보내지 않는다.

- [ ] 조사 예산과 provider 실패 처리를 로컬 기록에 연결한다.
  - **Test first:** 제어 가능한 시계와 늦게 반환하는 Codex 또는 Ollama fake adapter 응답으로 기한 이후 추가 조회가 차단되고 응답과 종료 이유가 보존되는지 검사한다.
  - **Done when:** 조사 ID로 입력·정책·그래프·provider/model 버전, 모델 턴·도구 호출과 실제 시도 횟수, 이전에 확인한 판정과 실패 이유를 찾을 수 있다. 예산 소진과 각 provider 장애를 같은 조사 결과 계약으로 인계한다.

- [ ] 중단 기록을 연결하고 조사 결과를 오프라인에서 재현한다.
  - **Test first:** 저장된 기록에서 정상·기한 소진 결과를 다시 계산하고, 필수 기록 누락과 프로세스 중단 뒤 새 조사 요청의 결과를 검사한다.
  - **Done when:** 재현 ID에서 원 조사의 판정·인계·종료 이유를 다시 계산하며 외부 모델과 Airflow 호출이 모두 0건이다. 중단 뒤 새 조사는 이전 조사 ID를 참조하고, 불충분한 기록은 이유를 반환한다.

- [ ] 프롬프트 버전과 허용된 Langfuse 관측을 조사 ID에 연결한다.
  - **Test first:** 고정 프롬프트와 테스트용 exporter로 프롬프트 확보 실패, 합성 사례 투영, 비합성 입력의 원격 본문 제외와 전송 실패를 검증한다.
  - **Done when:** 새 그래프가 모델을 호출한 조사에 실제 프롬프트 버전과 관측 결과를 연결한다. 전송 실패 시 로컬 결과를 유지하고 추가 모델 호출이 0건이다.

- [ ] 운영자가 준비 조사부터 실행 결과 확인까지 재현할 수 있는 사용 경로를 제공한다.
  - **Done when:** 실제 로컬 원천과 고정 응답 모델로 준비 조사·인계를 실행하고, 지정 DAG 기록과의 연결 및 오프라인 재현을 통합 검증한다. 기존 적재·Airflow 테스트를 통과한다. 운영 가이드와 관련 도메인 문서에 호출법, 결과 해석, 검증된 실행 범위를 기록한다.

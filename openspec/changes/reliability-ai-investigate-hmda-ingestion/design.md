---
type: openspec-spec-driven-tdd-design
category: design
title: HMDA Ingestion Investigation Design
description: 공용 조사 실행부에 적재 모드, 원천 검사, Airflow 근거 조회를 연결합니다.
---

## Technical Delta

[제안서](proposal.md)와 [적재 조사 명세](specs/reliability-ai-ingestion-investigation/spec.md)를 선행 계약으로 사용한다. 공용 그래프·제공자·기록·재현·관측의 연결은 [사고 조사 실행부 교체 설계](../reliability-ai-replace-investigation-runtime/design.md)를 따른다.

### D1. Ingestion Policy

- `hmda_reliability.reliability_ai.ingestion`의 `investigate_ingestion`은 `prepare`에 신뢰된 `DataOperationRequest`, `review_run`에 허용된 실행 참조와 선택적 이전 조사 ID를 받는다. 해당 모드의 읽기 전용 도구와 판정 규칙을 공용 그래프에 연결한다.
- 준비 판정과 다음 조치를 별도 상태에 두고, 둘 다 확정되면 공용 모델 분기 전에 반환한다. 조회 제안은 정규화된 공용 형식으로 받아 턴당 한 건을 확인한다. 해당 제안 ID를 도구 결과에 연결하고 다음 턴이 필요하면 그 결과를 전달한다. [판단과 도구 정책](../../../inbox/github-291-build-ingestion-agent-harness/02-proposal-ingestion-llmops/decision-contract.md)

### D2. Captured Source and Shared Read Path

- **Decision:** 식별 가능한 고정 사본을 재사용하고, 변경 가능한 입력은 허용된 파일을 원래 상대 이름으로 로컬에 캡처한다. 상대 이름과 파일별 SHA-256의 정렬 목록을 정규 JSON으로 직렬화해 입력 버전을 만든다. 원천 ID는 캡처된 승인 파일에만 매핑한다.
- **Decision:** HMDA Data 내부의 원천 파서와 파티션 필터를 적재와 조회가 공유하게 한다. 사전 검사는 격리된 임시 DuckDB에 대상 행을 읽고, 실제 적재기에 전달되는 전체 파일의 필수 열과 요청 연도·파일의 대상 행을 확인한다.
- **Trade-off:** 원천 사본을 확보하거나 파싱하는 데 시간이 들 수 있다. 완료한 검사는 해당 버전의 근거로 재사용하고, 호출 예산에 맞춰 미확인 범위를 인계한다. [파일별 구조 검사](../../../src/hmda_reliability/hmda_data/ingestion/_common.py), [파티션 필터와 검사](../../../src/hmda_reliability/hmda_data/ingestion/partition.py)

### D3. Airflow Result Reader

- **Decision:** 조사 쪽 읽기 어댑터에서 Airflow 공개 REST API의 태스크 인스턴스를 조회한다. `raw_load`, `quality_gate`, `dbt_build`를 기존 DAG의 세 태스크 ID에 매핑한다. stage state는 `dag_id`, `run_id`, `task_id`, `map_index`, `try_number`로 식별하며, 추가 증거는 같은 시도로 연결할 수 있을 때 결합한다.
- **Rationale:** 현재 DAG는 XCom 저장을 끄고 성공한 적재의 asset 기록에 결과 일부를 남긴다. 기본 asset 기록에서 시도와 실제 원천 버전을 함께 얻을 수 없는 경우 명세의 미확인 결과를 적용한다. [Airflow DAG](../../../src/hmda_reliability/orchestration/dags/hmda_data_plane.py)

### D4. Captured Inputs for Replay

- 초기 원천 검사와 Airflow 조회의 관찰도 모델 턴의 도구 결과처럼 실행 기록에 연결한다. 재현 시 이를 공용 재현 경계에 공급해 원래 자료를 다시 읽지 않고 같은 적재 규칙을 평가한다.

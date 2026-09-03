---
type: openspec-spec-driven-tdd-design
category: design
title: 2026년 가상 합성 데이터 평가 설계
description: 메인 DB 격리를 위한 샌드박스 경로 오버라이드와 연도 간 프로파일 기준선 비교 메커니즘을 정의한다.
---

## Technical Delta

### D1. 샌드박스 경로 오버라이드를 통한 평가 환경 격리

- **Decision:** 가상 2026년 합성 결함 데이터를 평가할 때 메인 데이터베이스(`data/hmda_reliability.duckdb`)를 직접 사용하지 않고, `DataOperationRequest`의 `database_path` 오버라이드를 통해 격리된 샌드박스 DB(예: `data/sandbox_2026.duckdb` 또는 pytest의 `tmp_path`)에서 실행한다.
- **Rationale:** 1,354만 건의 실제 2025년 메인 데이터를 무결하게 보존하면서, 2026년 파티션 적재, dbt 모델 빌드, 신뢰성 수명주기 분석을 완벽히 독립된 환경에서 안전하게 검증하기 위함이다.

### D2. 연도 파티션 간 프로파일 스냅샷 및 기준선 비교 메커니즘

- **Decision:** 2026년 결함 데이터의 프로파일 스냅샷(`ProfileSnapshot`)을 측정한 뒤, 정상 통계치(`null_rates={'income': 0.002}`)를 갖춘 기준선 스냅샷과 결합하여 `run_incident_lifecycle()`에 전달한다.
- **Rationale:** `run_incident_lifecycle()`은 동일한 asset과 partition 구조를 가진 baseline과 current의 통계 차이를 결정론적으로 비교하므로, 2026년 파티션 맥락에 맞춘 정상 기준선을 공급하여 `null_spike` 사고와 downstream dbt 계통(`stg_hmda_loans`, `mart_hmda_loan_outcomes`) 영향도를 정확히 도출하기 위함이다.

### D3. target_year 매개변수 유효성 검증 및 단일 연도 파티션 보장

- **Decision:** `null_spike`에 `target_year`를 지정할 때 $2000 \le \text{target\_year} \le 2100$ 범위와 정수 타입(`bool` 제외)을 엄격히 검증하고, `target_column == "activity_year"`인 모순 요청 및 2개 이상의 서로 다른 원천 연도가 혼합된 입력을 사전에 거부(`SyntheticCaseError`)한다.
- **Rationale:** DuckDB의 `REPLACE` 절 내 동일 컬럼 바인딩 충돌을 방지하고, 다중 연도 원천이 단일 목표 연도로 병합될 때 발생하는 윈도우 파티션 계산 왜곡(Partition Collapse)을 방지하여 통계적 일관성을 보장하기 위함이다.

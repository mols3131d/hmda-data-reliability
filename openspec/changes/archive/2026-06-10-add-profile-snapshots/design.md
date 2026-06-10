## Context

foundation 단계는 raw ingestion, dbt artifact, reliability contract를 준비했다. 다음 detector 단계는 문자열 판단이 아니라 partition별 수치 profile을 입력으로 받아야 한다.

현재 `ProfileSnapshot` contract는 존재하지만 계산기가 없다. 이번 변경은 DuckDB 테이블을 직접 profile하여 contract 인스턴스를 만드는 작은 모듈을 추가한다.

## Goals / Non-Goals

**Goals:**

- DuckDB table + partition predicate를 입력받아 `ProfileSnapshot`을 생성한다.
- row count, 컬럼별 null rate, schema hash, freshness timestamp를 계산한다.
- 동일 입력에 대해 deterministic한 snapshot id와 schema hash를 만든다.
- 테스트 fixture에서 JSON 직렬화와 주요 metric 값을 검증한다.

**Non-Goals:**

- baseline 비교와 incident 발행
- profile snapshot 영구 저장소
- Dagster asset materialization
- dbt artifact 파싱
- 분산 처리 최적화

## Decisions

### 프로파일러는 reliability 패키지에 둔다

`project_pivot.reliability.profiling`에 profile 계산 모듈을 둔다. taxi 전용 모듈에 넣지 않는다.

대안: `taxi_data` 아래 구현. 하지만 후속 detector와 agent가 택시 데이터 외 asset에도 같은 contract를 써야 하므로 제외한다.

### Partition predicate는 명시적 컬럼/값으로 받는다

초기 구현은 `partition_column`, `partition_value`를 받아 `WHERE CAST(column AS DATE) = ?` 형태로 필터링한다. partition 문자열은 `YYYY-MM-DD`로 유지한다.

대안: 임의 SQL predicate 문자열 입력. 유연하지만 profile 모듈이 SQL injection 위험과 파싱 책임을 갖게 되어 제외한다.

### Freshness는 timestamp 컬럼의 최대값으로 계산한다

`freshness_column`이 제공되면 partition 내 `max(column)`을 freshness로 사용한다. 값이 없으면 `observed_at`으로 fallback한다.

대안: 파일 metadata 또는 ingestion metadata 사용. 아직 metadata layer가 없으므로 이번 slice에서는 제외한다.

### Schema hash는 DuckDB column metadata 기반으로 계산한다

`DESCRIBE table` 결과의 column name/type을 정렬된 JSON으로 만든 뒤 SHA-256을 계산한다. data value가 아닌 schema drift 감지 입력만 담당한다.

대안: row 샘플까지 포함. profile과 drift detection 책임이 섞이고 비용이 커져 제외한다.

## Risks / Trade-offs

- [Risk] date partition 외 asset에는 바로 맞지 않을 수 있다. -> MVP는 daily partition 기준이며 후속 change에서 predicate 타입을 확장한다.
- [Risk] null rate 계산 SQL이 컬럼 수만큼 길어진다. -> MVP 테이블 규모에서는 단순 SQL이 더 명확하다.
- [Risk] freshness 컬럼이 없는 asset도 있다. -> fallback을 두되 metric payload에 freshness source를 남긴다.

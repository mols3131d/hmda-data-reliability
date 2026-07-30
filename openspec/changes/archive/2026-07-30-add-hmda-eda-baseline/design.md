## Context

HMDA 원천 데이터는 `data/raw/hmda/year_2025.csv`에서 시작한다. 현재 노트북은 DuckDB `DESCRIBE`만 실행해 schema discovery를 돕지만, reliability의 `ProfileSnapshot`과 incident detector가 사용하는 baseline evidence를 탐색할 수 없다.

이번 변경은 화면용 Marimo EDA만 확장한다. profile snapshot 생성과 incident lifecycle은 기존 reliability API의 책임으로 유지한다.

## Goals / Non-Goals

**Goals:**

- required column 존재·타입 불일치를 명확한 상태로 표시한다.
- 전체와 `activity_year`별 volume baseline, required column별 null baseline을 표시한다.
- `ProfileSnapshot` 필드에 대응되는 화면용 evidence 구조를 만든다.
- 원천 freshness의 측정 가능 여부와 Bronze ingestion 경계를 분명히 한다.

**Non-Goals:**

- `ProfileSnapshot` 저장 또는 production lifecycle 실행
- detection threshold, incident, remediation, recovery 변경
- 원천 데이터 수정·null 보정·SLA 정의
- 파일 수정 시각을 데이터 freshness로 사용하는 구현

## Decisions

### 노트북은 원천 CSV를 한 번 읽는 공통 relation을 사용한다

`read_csv_auto` 옵션은 현재의 `header`, `nullstr=['NA', '']`, `sample_size`, `ignore_errors`를 유지한다. schema, volume, null 분석은 이 relation을 재사용해 입력 해석 차이를 막는다.

대안: 섹션마다 별도 CSV reader를 사용한다. `NA`와 빈 문자열 처리 및 schema inference가 달라질 수 있어 제외한다.

### Required schema는 HMDA source contract를 따른다

필수 컬럼은 `activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`이다. 기대 타입은 노트북에 명시한 portable DuckDB type family로 비교하며, 누락과 타입 불일치를 callout으로 표시한다.

대안: `schema_hash`만 표시한다. hash는 drift 입력에는 적합하지만 사람이 어떤 컬럼을 바로잡아야 하는지 알 수 없어 제외한다.

### Evidence는 화면 구조와 저장 구조를 분리한다

노트북은 `row_count`, `null_rates`, schema 정보, freshness status를 포함하는 JSON-serializable `eda_evidence` 구조를 만든다. 화면은 이 구조를 표와 callout으로 렌더링한다. `baseline`과 `current`는 입력 역할을 설명하는 label일 뿐 profile snapshot이나 detector를 실행하지 않는다.

대안: 노트북에서 `ProfileSnapshot`을 직접 생성·저장한다. 관측과 production lifecycle 책임이 섞여 기존 read-only 경계를 위반하므로 제외한다.

### Freshness는 source observation timestamp가 있을 때만 측정한다

원천 CSV에 `observed_at`이 있고 유효 timestamp가 있으면 최대값을 source freshness로 표시한다. 없으면 `미측정` callout을 표시한다. 파일 수정 시각은 filesystem metadata이며 data freshness가 아니다. Bronze `ingested_at`은 raw table EDA 경로에서만 ingestion time으로 별도 표시한다.

## Risks / Trade-offs

- [Risk] CSV inferred type은 입력 샘플에 따라 달라질 수 있다. -> 노트북은 현재 sample size를 표시하고 type 결과를 source evidence로 한정한다.
- [Risk] source observation timestamp 이름이 달라질 수 있다. -> MVP는 `observed_at`만 인식하고 다른 이름의 매핑은 후속 변경에서 추가한다.
- [Risk] full source 파일은 샘플보다 클 수 있다. -> 화면에 입력 경로와 source 범위를 표시해 baseline 해석을 제한한다.

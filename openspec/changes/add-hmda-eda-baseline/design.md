## Context

HMDA 원천 데이터는 `data/raw/hmda/year_2025.csv`에서 시작한다. EDA는 required schema, volume, required-column null, freshness boundary와 화면용 evidence를 제공하지만, 현재 CSV reader의 `ignore_errors=true`는 파싱 실패 행을 relation에서 제외할 수 있다. 이 상태에서 계산한 row count와 null rate는 원천 전체가 아닌 파싱 성공 행의 baseline이 된다.

기존 task의 완료 표시는 정적 검사와 이전 실행에 의존한다. baseline 화면이 현재 valid sample과 full source에서 실제로 계산·렌더링됐는지, 손상 CSV가 evidence 생성을 막는지는 새 kernel에서 다시 확인해야 한다.

이번 변경은 화면용 Marimo EDA만 확장·정상화한다. profile snapshot 생성과 incident lifecycle은 기존 reliability API의 책임으로 유지한다.

## Goals / Non-Goals

**Goals:**

- required column 존재·타입 불일치를 명확한 상태로 표시한다.
- 전체와 `activity_year`별 volume baseline, required column별 null baseline을 표시한다.
- `ProfileSnapshot` 필드에 대응되는 화면용 evidence 구조를 만든다.
- 원천 freshness의 측정 가능 여부와 Bronze ingestion 경계를 분명히 한다.
- 파싱 오류 또는 입력 파일 부재에서 불완전한 baseline evidence가 생성되지 않게 한다.
- valid sample, malformed fixture, full source의 실행 결과를 새 Marimo kernel에서 확인한다.

**Non-Goals:**

- `ProfileSnapshot` 저장 또는 production lifecycle 실행
- detection threshold, incident, remediation, recovery 변경
- 원천 데이터 수정·null 보정·SLA 정의
- 파일 수정 시각을 데이터 freshness로 사용하는 구현

## Decisions

### 노트북은 원천 CSV를 한 번 읽는 공통 relation을 사용한다

`read_csv_auto`는 `header=true`, `nullstr=['NA', '']`, `sample_size=200000`를 사용하고 `ignore_errors`를 설정하지 않는다. schema, volume, null 분석은 하나의 relation을 재사용해 입력 해석 차이를 막고, reader가 오류를 반환하면 어떤 baseline metric도 계산하지 않는다.

대안: `ignore_errors=true`를 유지하고 손실 행 수를 경고한다. CSV는 인용된 줄바꿈을 포함할 수 있어 물리 줄 수와 레코드 수를 정확히 비교하려면 별도 parser가 필요하다. fail-fast reader가 더 작고 확실한 계약이므로 제외한다.

### Input은 명시된 파일을 사전 확인하고, sample과 full source 검증을 분리한다

기본 input은 `data/raw/hmda/year_2025.csv`이며 `HMDA_EDA_DATA_PATH`로 대체할 수 있다. DuckDB reader 전에 file 존재를 확인해 경로 오류를 명확하게 반환한다. 4.8 GB full source는 최종 단일 실행 gate로 한정하고, 기능 검증은 작은 valid sample과 temporary malformed fixture로 수행한다.

대안: 기본값을 sample로 변경한다. 운영자가 full-file baseline 대신 sample 결과를 보게 될 위험이 있어 제외한다. full source의 비용은 명시적 최종 gate와 실행 기록으로 관리한다.

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
- [Risk] full source 파일은 약 4.8 GB로 실행 시간이 길다. -> valid fixture를 먼저 검증하고 full-file 실행은 한 번만 수행해 duration과 결과를 기록한다.
- [Risk] fail-fast 전환 뒤 실제 source parse error가 발견될 수 있다. -> baseline 생성 실패로 기록한다. 원천 정정 또는 quarantine 경로는 별도 변경으로 결정한다.
- [Risk] 이전 UI output이 남아 있을 수 있다. -> 모든 runtime gate는 새 Marimo kernel에서 실행한다.

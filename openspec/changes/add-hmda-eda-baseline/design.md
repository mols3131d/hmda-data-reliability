## Context

HMDA 원천 데이터는 `data/raw/hmda/year_2025.csv`에서 시작한다. EDA는
required schema, volume, required-column null, freshness boundary와 화면용
evidence를 제공하지만, 이전 CSV reader의 `ignore_errors=true`는 파싱 실패
행을 relation에서 제외할 수 있었다. 이 상태에서 계산한 row count와 null
rate는 원천 전체가 아닌 파싱 성공 행의 baseline이 된다.

현재 `notebooks/eda_mo.py`는 reader 설정, schema 검사, aggregate query,
`eda_evidence` 생성과 UI 렌더링을 한 파일에서 수행한다. DuckDB에는 `2GB`
limit과 2 threads가 설정되어 있지만 Marimo를 포함한 process 전체 hard
limit, swap, timeout, temp disk와 반복 측정 경로는 없다. 기본 입력은 약
4.76 GiB이므로 정적 검사나 노트북의 정상 종료만으로 결과 무결성 또는
memory budget 준수를 판정할 수 없다.

기존 baseline 출력과 read-only 경계는 유지해야 한다. memory test는 일반
test보다 무겁고 runner가 실제 process hard limit을 지원할 때만 유효하다.

## Goals / Non-Goals

**Goals:**

- required column 존재·타입 불일치를 명확한 상태로 표시한다.
- 전체와 `activity_year`별 volume, required column별 null baseline을
  표시한다.
- `ProfileSnapshot` field에 대응되는 화면용 evidence 구조를 만든다.
- 원천 freshness의 측정 가능 여부와 Bronze ingestion 경계를 구분한다.
- 파싱 오류 또는 입력 파일 부재에서 불완전한 evidence 생성을 막는다.
- 노트북과 test가 공유하는 하나의 HMDA EDA 계산 entrypoint를 제공한다.
- 작은 fixture의 correctness와 대표 fixture의 process-level memory budget을
  서로 다른 test 계층에서 검증한다.
- 메모리 실행 조건과 결과를 재현 가능한 형태로 보고한다.
- DuckDB connection과 실행별 temp resource lifecycle을 명시한다.

**Non-Goals:**

- 모든 HMDA 입력에 대한 절대적인 OOM 안전성을 선언하지 않는다.
- `ProfileSnapshot` 저장 또는 production lifecycle을 실행하지 않는다.
- detection threshold, incident, remediation, recovery를 변경하지 않는다.
- 원천 데이터, Bronze, dbt model 또는 database schema를 변경하지 않는다.
- 파일 수정 시각을 data freshness로 사용하지 않는다.
- Marimo process 자체를 memory-budget gate로 사용하지 않는다.
- 새로운 dataframe 또는 profiling framework를 도입하지 않는다.

## Decisions

### CSV reader는 fail-fast이고 입력 파일을 사전 확인한다

기본 input은 `data/raw/hmda/year_2025.csv`이며 `HMDA_EDA_DATA_PATH`로
대체할 수 있다. DuckDB reader 전에 file 존재를 확인한다.
`read_csv_auto`는 `header=true`, `nullstr=['NA', '']`,
`sample_size=200000`를 사용하고 `ignore_errors`를 설정하지 않는다. reader가
오류를 반환하면 어떤 baseline metric이나 `eda_evidence`도 성공 결과로
반환하지 않는다.

대안으로 `ignore_errors=true`를 유지하고 손실 행 수를 경고할 수 있다.
CSV는 인용된 줄바꿈을 포함할 수 있어 물리 줄 수와 record 수를 정확히
비교하려면 별도 parser가 필요하다. fail-fast reader가 더 작고 확실한
계약이므로 제외한다.

### 계산 경계를 `hmda_data` domain에 둔다

`src/project_pivot/hmda_data/eda.py`에 source path와 DuckDB resource 설정을
받는 작은 public entrypoint를 두고 JSON-serializable evidence를 반환한다.
entrypoint는 reader, schema/metric 계산과 connection close를 소유한다.
노트북은 실행 버튼 이후 이 함수를 호출하고 기존 table과 callout을
렌더링한다.

대안으로 노트북 파일을 test에서 직접 실행할 수 있지만, reactive UI state와
kernel lifecycle이 계산 비용 및 실패 원인에 섞이므로 사용하지 않는다.

### Required schema와 evidence 의미는 기존 source contract를 유지한다

필수 컬럼은 `activity_year`, `state_code`, `county_code`, `loan_purpose`,
`action_taken`, `loan_amount`, `income`이다. 기대 타입은 portable DuckDB
type family로 비교하며 누락과 타입 불일치를 callout으로 표시한다.

evidence는 `row_count`, `null_rates`, schema 정보, freshness status를 포함한
JSON-serializable 구조다. 화면은 이를 표와 callout으로 렌더링한다.
`baseline`과 `current`는 입력 역할 label일 뿐 profile snapshot이나 detector를
실행하지 않는다.

원천 CSV에 `observed_at`이 있고 유효 timestamp가 있으면 최대값을 source
freshness로 표시한다. 없으면 `미측정`으로 표시한다. 파일 수정 시각은
filesystem metadata이며, Bronze `ingested_at`은 별도 raw-table 경로의
ingestion time이다.

### DuckDB aggregate를 유지하고 Python materialization을 제한한다

원천 전체를 Python/Arrow dataframe으로 변환하지 않고 DuckDB relation과
aggregate query로 처리한다. `activity_year` 결과는 HMDA domain에서 기대되는
작은 cardinality를 검증한 뒤 evidence list로 변환한다. `.df()`,
`.to_arrow_table()`과 원천 row의 `fetchall()`은 허용하지 않는다.

대형 중간 결과를 Parquet stage로 저장하는 대안도 있으나 현재 query는 단일
scan과 작은 grouping 결과이므로 추가 I/O와 cleanup 비용이 더 크다.

### Correctness와 memory-budget 실행을 분리한다

작은 deterministic CSV fixture의 component test는 entrypoint 결과의 schema,
row count, required-column null count/rate, activity-year count와 freshness
status를 검증한다. malformed fixture는 parse failure와 evidence 미생성을
검증한다.

대표 fixture는 제한된 측정 process 밖에서 만들거나 versioned artifact로
제공한다. manifest에는 fixture version, seed, schema, row 수, row 폭, null,
activity-year cardinality/skew와 파일 수를 기록한다.

memory test는 `memory` marker로 분리하고 일반 병렬 test에서 제외한다.
실행 wrapper는 `systemd-run --user` 또는 동등한 container hard limit을
process tree에 적용한다. 제한을 적용할 수 없는 환경의 실행은 통과로
기록하지 않는다.

### 초기 memory budget은 보수적인 고정값으로 시작한다

초기 조건은 process 3 GiB, swap 0, DuckDB 1600 MB, DuckDB 2 threads,
timeout 15분이다. 실행별 전용 temp directory를 사용한다. 같은 fixture를
세 번 실행해 최대 peak RSS를 판정값으로 사용하고 hard limit의 85% 초과를
개선 대상으로 보고한다.

이 값은 보편적인 상한이 아니라 첫 representative workload의 정책값이다.
fixture 또는 배포 환경이 바뀌면 manifest와 함께 명시적으로 version을
갱신한다.

### Memory 측정과 결과 정확성을 함께 판정한다

wrapper는 exit code, cgroup OOM/timeout 상태, peak RSS, elapsed time,
temp disk와 environment version을 기록한다. test는 schema와 business
invariant를 검사한다. output 또는 evidence 파일의 존재만으로 통과시키지
않으며 세 반복 중 하나라도 결과 검증이나 resource 조건에 실패하면 전체
실행을 실패로 판정한다.

## Risks / Trade-offs

- [CSV inferred type이 입력 sample에 따라 달라짐] → sample size와 추론
  결과를 evidence에 표시하고 결과를 해당 source 실행으로 한정한다.
- [DuckDB가 일부 field-count mismatch를 dialect/schema 추론으로 수용함] →
  DuckDB가 반환하는 parse error는 fail-fast로 처리하고 더 엄격한 field-count
  계약은 별도 근거가 생길 때 추가한다.
- [source observation timestamp 이름이 다름] → MVP는 `observed_at`만
  인식하고 다른 이름은 별도 변경에서 매핑한다.
- [full source 실행 시간이 김] → 작은 fixture correctness를 먼저 실행하고
  representative workload는 격리된 memory job에서 수행한다.
- [CI runner가 user systemd 또는 cgroup memory control을 제공하지 않음] →
  지원 runner에만 memory job을 배치하고 hard limit 사전 확인 실패를
  통과로 기록하지 않는다.
- [대표 fixture가 실제 source의 row 폭·skew를 재현하지 못함] → manifest를
  version 관리하고 full-source 수동 실행과 주기적으로 비교한다.
- [고유 `activity_year`가 비정상적으로 많음] → cardinality guard 초과를
  명시적인 validation failure로 처리한다.
- [이전 Marimo UI output이 남아 있음] → runtime smoke는 새 kernel에서
  수행한다.

## Migration Plan

1. 작은 valid/malformed fixture로 현재 output과 fail-fast 계약을 고정한다.
1. 계산 entrypoint와 resource lifecycle을 구현하고 correctness test를
   통과시킨다.
1. 노트북을 entrypoint 호출로 전환하고 새 kernel에서 smoke를 검증한다.
1. 대표 fixture manifest와 memory runner를 추가하고 지원 환경에서 3회
   baseline을 기록한다.
1. EDA reference, 개발 문서와 task 상태를 실제 검증 결과에 맞춘다.

노트북 전환에 문제가 생기면 UI 호출부만 기존 query 셀로 되돌릴 수 있다.
새 entrypoint와 test는 원천과 database schema를 변경하지 않으므로 별도
데이터 rollback은 필요하지 않다.

## Open Questions

- CI에서 process hard limit을 제공할 runner는 로컬 WSL user systemd인지
  memory-limited container인지 구현 시 확인한다.
- 대표 fixture를 저장소 artifact로 보관할지 CI 준비 step에서 생성할지는
  runner storage와 실행 시간을 측정한 뒤 확정한다.

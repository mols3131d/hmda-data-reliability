# MVP Data Information Needs

> **목적:** Foundation에서 MVP reliability 기능을 개발하기 전에, 데이터의 의미와 품질 경계를 확인할 최소 EDA 범위를 정의한다.

## 1. EDA Boundary

EDA는 일반적인 데이터 탐색이나 시각화가 아니다. MVP capability가 데이터에 대해 잘못된 가정으로 구현되지 않도록 evidence를 제공한다.

```text
HMDA raw data
    |
    +-- Descriptive EDA
    |     의미 · population · grain · 분포 · 결측 · code · anomaly
    |
    +-- ProfileSnapshot
    |     partition metric · baseline/current 비교
    |
    +-- dbt staging/mart
          분석 grain · metric · lineage
```

EDA는 다음을 수행하지 않는다.

- incident 생성
- detector threshold 학습
- raw value 정제·삭제
- remediation 또는 recovery 실행
- `ProfileSnapshot` API 대체

## 2. Questions EDA Must Answer

| Question | Why MVP needs it |
| --- | --- |
| 한 row는 무엇을 의미하는가? | volume과 중복 해석의 기준을 고정하기 위해 |
| 핵심 field와 허용 code는 무엇인가? | schema drift와 category anomaly를 해석하기 위해 |
| 기본 population과 grain은 무엇인가? | profile, mart, impact 결과를 같은 단위로 비교하기 위해 |
| 결측·특수값·수치 범위는 어떠한가? | null spike와 suspicious value를 구분하기 위해 |
| raw → staging → mart 관계는 무엇인가? | affected asset과 remediation context를 설명하기 위해 |
| 결과를 재현할 수 있는가? | synthetic evaluation과 regression evidence를 만들기 위해 |

## 3. MVP Consumer Map

| Consumer | Required information | EDA does not decide |
| --- | --- | --- |
| Profile snapshot | row count, null baseline, schema, freshness boundary, partition 후보 | detector threshold |
| Basic detection | volume 기준, null 대상 field, schema drift 대상, freshness 가능 여부 | incident 생성 |
| Impact analysis | raw → staging → mart asset와 grain 관계 | downstream 복구 순서 |
| Remediation draft | anomaly 유형과 영향 field/partition의 설명 근거 | remediation 실행 |
| Recovery validation | backfill 대상 partition과 row-count 비교 기준 | approval·overwrite 실행 |
| Evaluation | synthetic case가 재현해야 할 정상·이상 조건 | production 성능 보장 |

## 4. Required Scope

### Dataset And Row Semantics

- source file 목록, 파일별 row count, source year
- raw row의 의미와 중복 가능성
- `activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken` 기준 population
- source row와 Bronze row의 보존·추적 field

### Schema And Field Roles

- 전체 column 수와 inferred type
- MVP 핵심 field의 required/nullable 여부
- raw → staging cast 결과와 `try_cast`에 따른 null 가능성
- `loan_amount`, `income`, `action_taken`, `loan_purpose`의 역할
- `observed_at` 부재 시 freshness를 `unmeasured`로 처리하는 경계

### Code And Category Distribution

다음 field의 실제 code, count, share, unknown code 여부를 확인한다.

- `action_taken`
- `loan_purpose`
- `state_code`
- 필요 시 `county_code`

HMDA data dictionary의 의미와 현재 mart의 aggregation rule을 함께 표시한다. EDA와 mart가 approval·denial을 서로 다르게 해석하지 않아야 한다.

### Numeric Distribution And Anomaly

- `loan_amount`, `income`의 non-null count, min, p25, median, p75, max
- 음수·0·극단값 count와 share
- raw representation과 staging cast 결과 비교
- 의미가 확정되지 않은 값은 `observed anomaly`로 기록

자동 삭제·정제는 별도 domain decision 없이는 수행하지 않는다.

### Missingness And Coverage

- required field별 null count/rate
- `activity_year × core field` null pattern
- `state_code × loan_purpose` coverage
- null 허용 field와 분석 제외 field 구분

### Grain And Downstream Alignment

EDA aggregate는 현재 mart grain과 연결 가능해야 한다.

```text
activity_year + state_code + loan_purpose
```

새 business grain이나 canonical metric을 EDA가 임의로 만들지 않는다.

## 5. Reproducibility Checks

| Check layer | Purpose | Evidence |
| --- | --- | --- |
| Deterministic fixture | exact expected value 검증 | fixture test |
| Representative fixture | memory/temp budget 검증 | resource test/report |
| Actual source | 현재 데이터 관찰 | observation command/result |
| Notebook | human-readable rendering과 runtime path 확인 | notebook smoke |
| Read-only boundary | 원천 byte와 lifecycle side effect 보호 | focused test |

실제 source 결과는 immutable test assertion으로 고정하지 않고 observation evidence로 관리한다.

## 6. Explicit Exclusions

- 전체 99개 field 전수 분석
- predictive modeling, feature engineering
- fairness/disparate impact 분석
- causal analysis
- production monitoring과 alerting
- detector threshold 자동 학습
- incident lifecycle, remediation, recovery 실행
- raw value 자동 정제·삭제
- dashboard UI

필요해진 항목은 별도 MVP capability 또는 후속 Research로 분리한다.

## 7. Completion Criteria

EDA Research와 후속 OpenSpec이 충분하려면 다음을 확인할 수 있어야 한다.

- MVP capability별 data question과 EDA metric이 연결되어 있다.
- population, grain, code semantics, null policy가 명시되어 있다.
- suspicious value를 오류로 단정하지 않고 해석 상태를 구분한다.
- raw/staging/mart/ProfileSnapshot의 책임 경계가 유지된다.
- fixture, resource, actual-source, notebook 검증 방식이 분리되어 있다.
- 추가 metric이 필요한 경우 어떤 MVP decision을 지원하는지 설명할 수 있다.

## 8. Decisions To Carry Forward

- `income < 0`과 extreme `loan_amount`는 현재 `observed anomaly`로 유지한다.
- approval/denial grouping은 현재 dbt mart와 일치시킨다.
- 실제 source 전체 결과는 immutable test fixture가 아니라 observation evidence로 취급한다.

## Handoff

이 문서는 [Research entry point](research.md)의 하위 artifact다. 다음 OpenSpec proposal은 이 문서의 metric 목록을 그대로 복사하지 말고, MVP decision과 validation을 기준으로 최소 scope를 확정해야 한다.

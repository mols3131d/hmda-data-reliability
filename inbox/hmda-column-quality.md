# HMDA Column Quality

## Summary

- Public HMDA LAR의 99개 컬럼은 모두 기본 품질 검사를 받는다.
- 각 컬럼은 하나의 semantic type으로 라우팅되어 유형별 검사를 받는다.
- 핵심 7개 컬럼만 baseline 비교, 분포 변화, incident 기준까지 심화한다.
- 이 문서는 컬럼 계약을 설명하며 리팩터링 중인 `analysis.py` 구현을 고정하지 않는다.

## Quality Levels

| Level | 대상 | 검사 범위 |
| --- | --- | --- |
| Common | 전체 99개 | 존재, physical type, null, blank, distinct, parse failure |
| Type-specific | semantic type별 | 범위, 허용 코드, 정규식, 순서, 반복 슬롯 규칙 |
| Core | 핵심 7개 | baseline 비교, 분포 변화, 임계값, incident 연결 |

> [!IMPORTANT]
> `EDA_DROP_COLUMNS`는 일반 단일 컬럼 EDA에서만 제외되는 목록이다. 전체 품질 검사에서는 제외하지 않는다.

## Core Quality Columns

| Column | 역할 | 심화 검사 |
| --- | --- | --- |
| `activity_year` | 파티션·기간 경계 | 예상 연도, 혼입 연도, 연도별 행 수 |
| `state_code` | 주 단위 지역 품질 | null, 형식, unknown 값, 분포 변화 |
| `county_code` | 카운티 단위 지역 품질 | null, 5자리 형식, state_code 동반 여부 |
| `loan_purpose` | 핵심 업무 분류 | 허용 코드, unknown 값, 분포 변화 |
| `action_taken` | 신청 처리 결과 | 허용 코드, unknown 값, 분포 변화 |
| `loan_amount` | 핵심 금액 지표 | null, 파싱, 0 이하, 분위수·분포 변화 |
| `income` | 핵심 신청인 수치 | null, 파싱, 음수 비율, 분위수·분포 변화 |

## Physical Types

Physical type은 HMDA 설명 문서가 아니라 프로젝트 ingestion schema와 동기화한다.

| Type | Count | 의미 |
| --- | ---: | --- |
| Integer | 67 | 정수 측정값과 숫자형 코드 |
| Float | 15 | 금액·비율·기간 등 연속형 값 |
| String | 17 | 식별자, 지역 코드, 구간형 값 |
| Boolean | 0 | 현재 직접 Boolean 컬럼 없음 |
| Date | 0 | 현재 날짜 컬럼 없음 |
| Datetime | 0 | 현재 시각 컬럼 없음 |

## Semantic Types

Semantic type은 상호 배타적이며 99개 컬럼을 모두 포함한다.

### Year (1)

**Checks:** 예상 연도, 파싱 실패, 혼입 연도

`activity_year`

### Identifier (1)

**Checks:** 형식, 길이, null, 중복

`lei`

### Geographic code (4)

**Checks:** 형식, 선행 0, null, 상위 지역 존재

`derived_msa-md`, `state_code`, `county_code`, `census_tract`

### Derived category (5)

**Checks:** null, 허용 범주, 분포 변화

`derived_loan_product_type`, `derived_dwelling_category`, `derived_ethnicity`, `derived_race`, `derived_sex`

### Nominal category (24)

**Checks:** 허용 코드, unknown 값, null, 분포 변화

`conforming_loan_limit`, `action_taken`, `purchaser_type`, `preapproval`, `loan_type`, `loan_purpose`, `lien_status`, `hoepa_status`, `construction_method`, `occupancy_type`, `manufactured_home_secured_property_type`, `manufactured_home_land_property_interest`, `applicant_credit_score_type`, `co-applicant_credit_score_type`, `applicant_ethnicity_observed`, `co-applicant_ethnicity_observed`, `applicant_race_observed`, `co-applicant_race_observed`, `applicant_sex`, `co-applicant_sex`, `applicant_sex_observed`, `co-applicant_sex_observed`, `submission_of_application`, `initially_payable_to_institution`

### Coded flag (9)

**Checks:** 허용 코드, 면제값, null

`reverse_mortgage`, `open-end_line_of_credit`, `business_or_commercial_purpose`, `negative_amortization`, `interest_only_payment`, `balloon_payment`, `other_nonamortizing_features`, `applicant_age_above_62`, `co-applicant_age_above_62`

### Currency (9)

**Checks:** 파싱, null, NaN/Inf, 범위, 분포 변화

`loan_amount`, `total_loan_costs`, `total_points_and_fees`, `origination_charges`, `discount_points`, `lender_credits`, `property_value`, `income`, `ffiec_msa_md_median_family_income`

### Ratio/percentage (6)

**Checks:** 파싱, null, 범위, NaN/Inf

`combined_loan_to_value_ratio`, `interest_rate`, `rate_spread`, `multifamily_affordable_units`, `tract_minority_population_percent`, `tract_to_msa_income_percentage`

### Duration (4)

**Checks:** 파싱, null, 음수, 비정상 범위

`loan_term`, `prepayment_penalty_term`, `intro_rate_period`, `tract_median_age_of_housing_units`

### Count (3)

**Checks:** 파싱, null, 음수, 비정상 범위

`tract_population`, `tract_owner_occupied_units`, `tract_one_to_four_family_homes`

### Ordinal (4)

**Checks:** 허용 구간, 특수 토큰, 순서

`total_units`, `ageapplicant`, `debt_to_income_ratio`, `co-applicant_age`

### Multi-response (29)

**Checks:** 슬롯별 허용 코드, 위치 공백, 중복 응답

`applicant_ethnicity-1`, `applicant_ethnicity-2`, `applicant_ethnicity-3`, `applicant_ethnicity-4`, `applicant_ethnicity-5`, `co-applicant_ethnicity-1`, `co-applicant_ethnicity-2`, `co-applicant_ethnicity-3`, `co-applicant_ethnicity-4`, `co-applicant_ethnicity-5`, `applicant_race-1`, `applicant_race-2`, `applicant_race-3`, `applicant_race-4`, `applicant_race-5`, `co-applicant_race-1`, `co-applicant_race-2`, `co-applicant_race-3`, `co-applicant_race-4`, `co-applicant_race-5`, `aus-1`, `aus-2`, `aus-3`, `aus-4`, `aus-5`, `denial_reason-1`, `denial_reason-2`, `denial_reason-3`, `denial_reason-4`

## Shared Metadata

| Contract | 목적 |
| --- | --- |
| `NUMERIC_BOUNDS` | 명백한 범위 위반 후보 탐지 |
| `ORDINAL_LEVELS` | 구간형·순서형 값의 허용 수준 관리 |
| `IDENTIFIER_PATTERNS` | LEI와 지역 코드 형식 검사 |
| `MULTI_RESPONSE_GROUPS` | ethnicity, race, AUS, denial reason 반복 슬롯 구성 |
| `MISSING_LIKE_TOKENS` | `NA`, `Exempt`, `8888`, `9999` 등 특수값 구분 |
| `allowed_values_for()` | 안정적으로 문서화된 categorical code 조회 |

## Multi-response Groups

| Group | Columns |
| --- | --- |
| `applicant_ethnicity` | `applicant_ethnicity-1`, `applicant_ethnicity-2`, `applicant_ethnicity-3`, `applicant_ethnicity-4`, `applicant_ethnicity-5` |
| `co_applicant_ethnicity` | `co-applicant_ethnicity-1`, `co-applicant_ethnicity-2`, `co-applicant_ethnicity-3`, `co-applicant_ethnicity-4`, `co-applicant_ethnicity-5` |
| `applicant_race` | `applicant_race-1`, `applicant_race-2`, `applicant_race-3`, `applicant_race-4`, `applicant_race-5` |
| `co_applicant_race` | `co-applicant_race-1`, `co-applicant_race-2`, `co-applicant_race-3`, `co-applicant_race-4`, `co-applicant_race-5` |
| `aus` | `aus-1`, `aus-2`, `aus-3`, `aus-4`, `aus-5` |
| `denial_reason` | `denial_reason-1`, `denial_reason-2`, `denial_reason-3`, `denial_reason-4` |

반복 슬롯은 개별 컬럼 검사 후 그룹 수준에서 다음만 추가한다.

- 앞 슬롯이 비었는데 뒤 슬롯에 값이 존재하는지
- 같은 응답 코드가 한 행에서 반복되는지
- 슬롯별 허용 코드가 지켜지는지

## Incident Boundary

전체 컬럼 검사는 관측 결과를 만든다. 자동 incident 생성은 핵심 컬럼과 명시적으로 승인된 규칙에만 적용한다.

| 결과 | 전체 컬럼 | 핵심 컬럼 |
| --- | ---: | ---: |
| 품질 통계 생성 | Yes | Yes |
| unknown·범위 위반 후보 기록 | Yes | Yes |
| baseline 비교 | 선택 | Yes |
| incident 생성 | No | Yes |
| remediation 검증 | No | Yes |

## Ownership

- 컬럼 분류와 품질 규칙: `shared.py`
- 전체 파일 분석과 evidence 생성: `analysis.py`
- 시각화와 탐색 UI: marimo notebooks
- incident 판정과 lifecycle: reliability 영역

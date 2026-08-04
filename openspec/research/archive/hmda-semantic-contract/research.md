---
type: openspec-rpi
category: research
title: "HMDA public data semantic contract"
description: "MVP reliability가 의존할 HMDA public data의 source identity, field semantics와 analytical grain 계약을 정의한다."
status: "completed"
tags:
  - "hmda"
  - "data-contract"
  - "semantics"
  - "reproducibility"
---

## Summary

> [!NOTE]
> MVP 전에 99개 이상의 모든 HMDA field를 catalog화할 필요는 없다. 대신 현재 EDA와 mart가 실제로 사용하는 핵심 field에 대해 **source identity, raw representation, official code 의미, missing·unknown 처리와 analytical grain**을 하나의 versioned contract로 고정해야 한다. 특히 dynamic dataset과 static snapshot은 같은 연도라도 내용이 달라질 수 있으므로 `activity_year`만으로 dataset을 식별하면 재현성이 없다.

## Question

- **Primary:** Project Pivot이 MVP reliability 판단에 사용할 최소 HMDA semantic contract는 무엇인가?
- **Scope:** public national loan-level dataset과 현재 핵심 field인 `activity_year`, `action_taken`, `loan_purpose`, `state_code`, `loan_amount`, `income` 및 mart grain만 포함한다. 전체 HMDA submission validation rule 구현은 제외한다.
- **Stop Condition:** 데이터 재실행과 anomaly 해석에 필요한 identity·semantic·grain 계약, 그리고 raw 보존 경계를 정의할 수 있으면 종료한다.

## Findings

### F1. HMDA dataset identity는 연도보다 넓다

FFIEC/CFPB는 dynamic national dataset과 fixed-date snapshot·one-year static dataset을 별도로 제공한다. Dynamic dataset은 late submission과 resubmission을 반영해 주기적으로 갱신되며, static dataset은 고정된 freeze date를 가진다. 따라서 동일한 `activity_year`라도 dataset class와 취득 시점에 따라 row와 값이 달라질 수 있다.

최소 source identity는 다음을 포함해야 한다.

| Field | Meaning |
| --- | --- |
| `activity_year` | HMDA reporting year |
| `dataset_class` | dynamic, snapshot 또는 one-year static |
| `freeze_or_retrieved_at` | static freeze date 또는 dynamic 취득 시점 |
| `source_url` | 공식 publication location |
| `file_name` | 원본 file identity |
| `checksum` | 실제 ingest한 byte identity |
| `schema_version` | 적용한 public LAR schema/contract version |

- **Evidence** - FFIEC HMDA Data Publication과 2024 dataset publication page
- **Implication** - baseline과 synthetic comparison은 `activity_year`만이 아니라 source identity 전체를 가져야 한다.

### F2. Filing semantics와 public analytical dataset semantics를 구분해야 한다

Filing Instructions Guide는 filer가 제출할 LAR field와 code rule을 설명한다. 반면 Project Pivot이 ingest하는 public dataset은 Bureau가 privacy protection을 위해 수정해 공개한 analytical dataset이다. Filing rule을 public value의 물리적 표현에 그대로 강제하면 정상적인 public transformation을 오류로 분류할 수 있다.

- **Evidence** - HMDA Filing Instructions Guide, FFIEC public data publication 설명
- **Implication** - contract는 `regulatory meaning`과 `public representation`을 별도 field로 관리해야 한다. 현재 MVP는 public representation을 executable contract로 삼고 Filing Guide는 의미 해석의 근거로 사용한다.

### F3. 극단값은 자동 invalid가 아니라 관찰 대상이다

공식 snapshot 안내는 `loan_amount`와 `income`에 upper limit가 없으며 outlier가 포함될 수 있다고 경고한다. 따라서 고정 threshold를 넘는 값을 삭제·보정하거나 schema violation으로 처리하면 공식 데이터의 유효한 tail을 손상할 수 있다.

- **Evidence** - FFIEC Snapshot National Loan Level Dataset 안내
- **Implication** - numeric rule은 `hard invalid`, `suspicious observation`, `distribution drift`를 구분해야 한다. 현재 EDA의 raw 보존형 anomaly evidence 방향을 유지한다.

### F4. core field contract는 세 층으로 분리해야 한다

| Layer | Contract | Example |
| --- | --- | --- |
| Physical | column presence, parse type, raw preservation | `loan_amount` parse 가능 여부, source byte 불변 |
| Semantic | official code label, NA·unknown representation, unit | `action_taken` code 의미, income 단위와 missing token |
| Analytical | inclusion rule, derived grouping, grain | `activity_year + state_code + loan_purpose`, approval/denial grouping |

- **Evidence** - active HMDA EDA change, dbt staging/mart architecture, official public field definitions
- **Implication** - schema test만 통과해도 의미 drift가 발생할 수 있으므로 semantic mapping과 mart grouping을 동일 contract에서 추적해야 한다.

### F5. unknown code와 missing token은 증거로 남겨야 한다

새 code, 잘못된 source 또는 parser drift를 구분하려면 raw value와 적용한 mapping version이 필요하다. 알 수 없는 값을 자동으로 `other`에 합치면 incident detection이 가장 필요한 신호를 잃는다.

권장 representation은 다음과 같다.

| Input State | Stored Value | Evidence |
| --- | --- | --- |
| known code | raw code 유지 | canonical label과 mapping version |
| documented NA/exempt | raw token 유지 | semantic state `not_applicable` 등 |
| unknown code | raw token 유지 | `unknown_code` observation |
| parse failure | 원본 byte 보존 | field, token, parser error |

- **Evidence** - active EDA proposal의 raw preservation·unknown code requirement
- **Implication** - cleaning보다 evidence-first classification이 Project Pivot의 reliability 목적에 맞다.

## Options

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| 전체 HMDA field catalog 선행 | coverage가 넓다 | MVP를 지연하고 사용하지 않는 field 유지비가 크다 |
| 핵심 field versioned contract | 현재 EDA·mart·reliability와 직접 연결된다 | 새 field 사용 시 contract 확장이 필요하다 |
| dbt schema test만 사용 | 구현이 단순하다 | source identity, code 의미와 raw representation을 충분히 표현하지 못한다 |

## Conclusion

- **Answer** - 최소 contract는 source identity와 핵심 field의 physical·semantic·analytical 규칙을 함께 소유해야 한다.
- **Recommendation** - 여섯 핵심 field와 current mart grain만 version 1로 고정한다. raw value를 보존하고 official mapping version, unknown·NA classification, suspicious numeric observation과 dataset provenance를 직렬화한다.
- **Next Step** - `hmda-public-data-contract` OpenSpec change에서 contract schema, official source mapping, dbt/EDA 소비 방식과 drift test를 정의한다. 사용하지 않는 전체 field catalog는 점진적으로 추가한다.

## Validation Candidates

1. snapshot fixture와 dynamic-like revised fixture가 서로 다른 source identity로 기록되는지 확인한다.
2. known, documented NA, unknown와 malformed token을 혼합해 raw 보존과 semantic classification을 검증한다.
3. 극단 `loan_amount`·`income` 값이 삭제되지 않고 suspicious evidence로만 기록되는지 검증한다.
4. official code mapping과 mart approval/denial grouping 간 일관성을 test한다.
5. mapping version 변경 시 기존 baseline과의 semantic drift가 명시적으로 감지되는지 확인한다.

## Evidence

| Evidence | Supports | Location |
| --- | --- | --- |
| HMDA dataset classes and update behavior | F1, F2 | https://ffiec.cfpb.gov/data-publication/ |
| 2024 dynamic/static freeze metadata | F1 | https://ffiec.cfpb.gov/data-publication/2024 |
| Snapshot outlier caution | F3 | https://ffiec.cfpb.gov/data-publication/snapshot-national-loan-level-dataset/ |
| 2024 Filing Instructions Guide | F2, F4 | https://files.ffiec.cfpb.gov/documentation/2024-hmda-fig.pdf |
| Active EDA scope and raw preservation | F3, F5 | `openspec/changes/hmda-eda-foundation-extension/proposal.md` |
| Active EDA tasks | F4, F5 | `openspec/changes/hmda-eda-foundation-extension/tasks.md` |
| Architecture and mart boundary | F4 | `docs/ARCHITECTURE.md` |

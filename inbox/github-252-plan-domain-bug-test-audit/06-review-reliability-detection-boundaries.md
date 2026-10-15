---
type: review
title: Reliability Detection Boundary Review
description: Reliability incident detection에서 zero threshold와 비교 불가능한 null-rate 입력의 계약 및 테스트 검출력을 검토합니다.
tags:
  - domain:reliability
  - testing
  - review
---

# Reliability Detection Boundary Review

2026-10-15 후속 실행: [Cloud validation](08-report-cloud-validation.md)에서 실제 재현·테스트 결과를 기록했다. 현재 진행 상태는 [completion checklist](03-plan-audit-completion-checklist.md)를 따른다. 이 문서의 실행 불가/미실행 표기는 이전 세션의 이력이다.

> **Assessment: finding confirmed at source-predicate level; full runtime regression Not Verified.** 실제 `pytest` 실행이 아닌 고정 source 확인과 격리된 경계식 검산 결과다. 일반 기본값으로 사용하는 감지 경로의 실패로 확대하지 않는다.

- **Target:** Reliability incident detection의 threshold, null-rate baseline, related test oracle
- **Revision:** `8bc62fa6ec995f2e57456d55712b36ff11b1f1d9` (`main`, 2026-10-14)
- **Scope:** `DetectionThresholds`, `BasicIncidentDetector`, `DetectionRequest`, 기본 detector test, normative incident-detection spec

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| R-DET-01 | 🟡 Minor | 허용된 zero threshold에서 변화가 없는 profile에도 volume/null-spike incident 조건이 참 | 기존 계약 아래 zero-boundary 회귀 테스트 및 최소 조건 수정 제안 |
| R-DET-02 | 🔵 Note | current null-rate column이 baseline에 없으면 baseline=0으로 가정 | 미측정 baseline 의미를 spec으로 판단한 뒤 regression 여부 결정 |

## Details

### R-DET-01 — Minor

#### Locations

- [`src/hmda_reliability/reliability/detection/thresholds.py`](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/reliability/detection/thresholds.py#L6): `volume_drop_ratio`, `null_spike_delta`의 `ge=0.0`
- [`src/hmda_reliability/reliability/detection/detector.py`](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/reliability/detection/detector.py#L42): `drop_ratio < threshold`, `delta < threshold`인 경우만 skip
- [`tests/reliability/test_basic_incident_detection.py`](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/tests/reliability/test_basic_incident_detection.py#L20): normal profile은 양의 threshold(0.5/0.1), zero-boundary 검증 없음
- [`openspec/specs/reliability-incident-detection/spec.md`](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/openspec/specs/reliability-incident-detection/spec.md#L11): 차이가 발생하지 않을 때 incident 없음이라는 Normal comparison 계약

#### Evidence

두 유효한 입력에서 baseline과 current의 row count가 100으로 같고, income null-rate가 각각 0.2로 같다고 한다. Threshold model은 `volume_drop_ratio=0`, `null_spike_delta=0`을 허용한다. `drop_ratio=0`, `null_delta=0`일 때 현 구현의 `if value < threshold: return/continue`가 모두 거짓이므로 두 incident를 구성하는 경로로 진입한다.

기존 source 비교식을 그대로 재현한 **독립 경계식 + Pydantic 허용값 계산**에서 두 조건이 참이었다. 이 검산은 production import, 실제 `detect_basic_incidents` 호출, DuckDB, pytest를 실행한 증거는 아니다. Default threshold 0.5/0.1에서는 무변화가 걸러진다.

#### Impact

0을 `어떤 양의 악화라도 탐지`하도록 설정하는 호출자에서는 정상 상태를 오탐할 수 있다. 오류 영향은 조건부이며, 기본 배포 설정의 사고 발생으로 단정하지 않는다.

#### Action

`DetectionThresholds(0, 0)`에서 동등한 profile은 결과가 비어야 하고, row count 100→99 또는 null rate 0.2→0.21처럼 **실제 증가·감소**는 감지해야 한다는 독립 oracle 테스트를 추가한다. 기존 zero 허용 계약을 유지하려면 비교식에 양의 악화 조건을 추가하는 방식이 범위가 작다. 현재 PR에서는 production/test 파일을 변경하지 않는다.

### R-DET-02 — Note

#### Locations

- [`src/hmda_reliability/reliability/detection/detector.py`](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/reliability/detection/detector.py#L70): `baseline.null_rates.get(column, 0.0)`
- [`src/hmda_reliability/reliability/detection/request.py`](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/src/hmda_reliability/reliability/detection/request.py#L26): baseline/current의 asset·partition만 동일성을 검증
- [`openspec/specs/reliability-incident-detection/spec.md`](https://github.com/mols3131d/hmda-data-reliability/blob/8bc62fa6ec995f2e57456d55712b36ff11b1f1d9/openspec/specs/reliability-incident-detection/spec.md#L9): 비교 가능한 profile pair의 의미를 컬럼 범위까지 명확히 하지 않음

#### Evidence

Baseline에 `new_column` 측정이 없지만 current에 null rate 0.20이 있을 때, `get(..., 0.0)`에 따라 증가량이 0.20으로 계산돼 null spike 후보가 된다. 이는 이전 null rate가 실제 0이었다는 근거 없이 생성되는 값이다. 다만 schema drift가 같이 검출될 수 있고 명세가 이 상황을 어떻게 다뤄야 하는지 명확히 정의하지 않아 **확정 defect로 분류하지 않는다**.

#### Action

Baseline 측정 불가 상태를 skip·explicit inconclusive·schema drift 동반 중 어떤 계약으로 처리할지 결정한 뒤, missing baseline column 테스트와 code 변경 여부를 판단한다. 임의로 zero-default를 삭제하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 고정 baseline source·spec·unit test 경로 교차 확인 | 위 locations; zero-boundary test는 해당 detector module에서 발견되지 않음 |
| ✅ Pass | 격리된 입력 조건/분기식 검산 | local Python Pydantic이 두 threshold 0을 허용하고, 동등 입력에서 두 skip predicate가 false임을 확인 |
| ⚪ Not Verified | 실제 앱 import + pytest 및 end-to-end incident result | 비공개 repository clone DNS 불가, 현재 Python에 duckdb 없음 |
| ⚪ Not Verified | 해당 구성값의 실제 production 사용 여부 | Repository default `0.5/0.1`과 별도로 caller-specific zero 설정 전수 실행 미확인 |
| ⚪ Not Verified | Independent review 및 defect fix | 같은 컨텍스트 셀프 리뷰만 수행, production/test 변경 없음 |

## Self-Review Loop

1. **Research:** source model에서 zero가 유효한 계약이고 detector의 양쪽 비교식이 threshold 동등값을 탐지하는지 확인.
2. **Disconfirmation:** 기존 normal detector test와 default threshold를 확인해 일반 정상 profile 검출 버그라는 과대 해석을 철회. `R-DET-01`을 명시적 zero 설정에만 해당하는 Minor로 한정.
3. **Improvement:** missing baseline 결측률을 같은 종류의 확정 버그로 취급할지 검토했다가, spec의 comparability 명세 부족을 확인하고 `R-DET-02`를 Note/계약 판단으로 분리.
4. **Convergence:** 실행되지 않은 실제 pytest, fault injection, independent review를 완료라고 기록하지 않음. [완료 체크리스트](03-plan-audit-completion-checklist.md)에 후속 테스트 필요.

## Risks And Limits

위 findings는 기존 `main` 구현에 대한 감사이며 #252의 Inbox 문서 변경이 새로 만든 회귀 문제가 아니다. `R-DET-01` 수정은 테스트가 RED로 실패하는지부터 확인하고 별도 작은 구현 PR로 연결하는 편이 원래 계획의 범위 및 validation 요구에 부합한다. 새로운 계약이나 프로젝트 scope가 필요한 경우 승인을 거친다.

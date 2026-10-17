---
type: report
title: Detector Contract Cases And Decision
description: PR 252의 남은 탐지 경계를 규칙별 사례와 실제 소비자에 대조하고, 최소 수정의 기술적 결정과 검증 범위를 기록합니다.
tags:
  - reliability
  - testing
---

# Detector Contract Cases And Decision

## Scope And Authority

시작 revision은 `dbc25c18a06b59d153947b136b1e11154ec44863`이다. 사용자는 결정론적 범위에서 PR 완료까지 실행하고 세션 간 근거를 보존하도록 요청했다. 기존 `0` 허용/거부 질문에 특정 번호로 답한 것은 아니며, 아래는 완료 위임 아래 기존 계약과 호환성을 근거로 내린 기술적 결정이다. 비결정적 품질 평가는 포함하지 않는다.

## Evidence And Decision

[Thresholds](../../src/hmda_reliability/reliability/detection/thresholds.py)는 `0`을 유효한 공개 입력으로 허용한다. [Detector](../../src/hmda_reliability/reliability/detection/detector.py)의 volume/null 규칙은 각각 감소와 증가를 측정한다. [Canonical spec](../../openspec/specs/reliability-incident-detection/spec.md)은 양수 기준의 equality를 포함하고, freshness는 현재 age를 별도로 비교한다. 반면 Normal comparison의 `넘지 않을 때` 문구는 이 경계와 모호하게 충돌한다.

**결정:** volume/null은 실제 양의 악화와 `악화량 >= 기준`을 모두 요구한다. `0`은 계속 유효하며 어떤 양의 악화도 탐지한다. Freshness는 관측 age의 `>=` 비교를 유지하고 schema 규칙은 변경하지 않는다. 새 옵션·epsilon·rounding·컬럼별 정책 엔진을 추가하지 않는다.

## Case Matrix

별도 표기가 없으면 schema는 같고 freshness는 유효 기간 안이다. Volume/null의 `0` 설정을 함께 사용한 경우를 기준으로 한다.

| Case | Input | Expected Result |
| --- | --- | --- |
| No change | 100 → 100행, null 12.5% → 12.5% | volume/null 경보 없음; 데이터 전체가 정상이라는 보장은 아님 |
| Volume only | 100 → 99행, null 동일 | volume만 탐지 |
| Null only | 100행 유지, null 12.5% → 25% | null만 탐지 |
| Both | 100 → 99행, null 12.5% → 25% | volume과 null 모두 탐지 |
| Improvement | 100 → 101행, null 12.5% → 0% | volume/null 경보 없음 |
| Positive volume equality | 100 → 50행, volume 기준 50% | volume 탐지 유지 |
| Positive null equality | null 12.5% → 25%, null 기준 12.5%p | null 탐지 유지 |
| Zero-row baseline | baseline 0행 | 분모가 없으므로 volume 비교 제외; 다른 규칙은 독립 실행 |
| Freshness equality | age와 기준이 모두 0분 | freshness 탐지 유지; 양의 악화 guard를 적용하지 않음 |
| Unchanged old timestamp | 수집 시각은 같지만 현재 age가 기준 이상 | freshness 탐지 유지 |
| Unavailable freshness | 측정 불가 | freshness 판단 제외; 다른 규칙은 독립 실행 |
| Changed schema | 같은 행 수·null, 다른 schema hash | schema만 탐지 |

## Consumer Boundaries

- [Incident lifecycle](../../src/hmda_reliability/data_operations/incident_lifecycle.py)은 caller가 전달한 비교 baseline과 threshold를 사용한다. `0`을 명시한 caller는 위 경계 수정의 영향을 받는다.
- [Quality gate](../../src/hmda_reliability/reliability/quality_gate.py)는 직전 관측 대신 고정 null-rate 기준과 5%p threshold를 사용한다. 과거부터 존재한 결측도 이 고정 기준을 위반하면 계속 차단한다. 기존 exact-5%p·필수 컬럼·빈 partition 회귀를 유지한다.
- Baseline에 없는 null-rate를 0으로 보는 R-DET-02는 별도 계약 Note다. 기존 fallback을 유지하며 이를 관측된 정상값이나 확인된 새 결함으로 승격하지 않는다. Caller asset/partition 불일치 거부도 유지한다.

## Execution And Resume

계약 명확화와 구현은 [reliability-detection-positive-degradation](../../openspec/changes/reliability-detection-positive-degradation/) Change가 소유한다. Schema는 `spec-driven-tdd`이며 terminal은 `goal`, scope policy는 `narrow-only`다. 기존 구현 loop counter 5/30을 이어간다.

다음은 delta Spec·Design·Tasks를 작성하고, production 변경 전에 독립 기대값의 회귀에서 실제 assertion 실패를 확인하는 것이다. 이후 최소 수정, focused/full validation, 독립 review-lead, 최종 base/head CI와 전달을 완료한다. 이 보고서의 사례표는 아직 runtime 통과 근거가 아니다.

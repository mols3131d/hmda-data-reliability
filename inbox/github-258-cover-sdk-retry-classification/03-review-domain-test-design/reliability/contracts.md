---
type: review
title: Reliability Contracts Test Design Review
description: Reliability 데이터 모델의 검증·불변성·승인과 evidence 연결에 대한 테스트 oracle을 검토합니다.
---

# Reliability Contracts Test Design Review

> [!NOTE]
> 실제 모델 validation과 독립적인 invalid input을 사용한다. Recovery 요청과 profile population의 정렬은 별도 composition 공백으로 남는다.

- **Target**: Reliability contracts와 공통 fixture.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [contracts 테스트](../../../../tests/reliability/contracts/), [test_fixtures.py](../../../../tests/reliability/test_fixtures.py), [conftest.py](../../../../tests/reliability/conftest.py) 전체 body와 관련 모델 targeted 대조.

## Findings

이 모델 단위에 추가로 채택한 material finding은 없다. [Recovery R2](recovery.md#r2--major-profile-population-binding)는 profile 계산 자체나 일반 contract validation의 부재가 아니라, 정상 request가 선택하는 population과 복구 observation을 결합하는 공백이다.

## Contract Assessment

| Contract | Scenario And Oracle | Strength And Limit |
| --- | --- | --- |
| Approval | 필수 승인자·시간·action, 불변 action, exact proposal 연결 | 실제 Pydantic 거부·동등성; 외부 사람이 실제 승인했다는 증거는 아님 |
| Evidence | 필수 refs, provider 중립 provenance, JSON 값의 허용·거부 | malformed payload를 실제 모델로 검증 |
| Incident | 상태·severity·evidence 연결 | authored 고정 값; lifecycle 실행은 별도 composition |
| Lineage | asset와 artifact path·evidence 참조 | 모델 shape와 analyzer의 graph 해석을 구분 |
| Profile | finite metric, 범위, measured/unavailable freshness 일관성 | 단순 truthiness보다 구체적 invalid scenario |
| Recovery proposal | candidate=expected-after, exact target·actions, freshness binding | immutable snapshot과 승인 scope 검증 |
| Schema recovery | complete table state, exact approval/result의 mutation/action 일관성 | result의 profile population은 성공 예제만으로 충분히 검증되지 않음 |
| Validation | result/evidence 필수 관계 | 실제 serialization·validation 사용; 실제 DB effect는 executor 리뷰 |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 full-body 검토 | Batch B 두 관점, contract 8개·fixture test·support |
| ✅ Pass | 현재 실행 근거 | [전체 suite](../validation.md#test-execution) |
| ⚪ Not Verified | 사람의 승인 결정·효용 | fixture의 승인 상태와 구분되는 외부 영역 |

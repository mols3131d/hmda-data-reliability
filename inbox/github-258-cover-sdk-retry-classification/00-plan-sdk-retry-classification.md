---
type: plan
title: SDK Retry Classification Regression Plan
description: 실제 SDK 오류 분류와 재시도 정책 사이의 검증 공백을 닫는 후속 PR의 범위·사례·검출 기준과 전달 상태를 기록합니다.
tags:
  - testing
  - runtime-ai
---

# SDK Retry Classification Regression Plan

## Scope And Baseline

사용자는 [PR #252](https://github.com/mols3131d/hmda-data-reliability/pull/252)의 병합과 신규 PR 준비를 요청했다. PR #252는 `75fff57e`를 대상으로 Ready 전환 후 squash 병합했고, 병합 결과 `a8864328e8a92316d32cad386746c3c5f4b983cd`에서 후속 branch `agent/test/cover-sdk-retry-classification`을 생성했다.

현재 provider는 올바르게 동작한다. 앞선 검토에서 SDK의 4xx 분류를 잘못 바꿔도 기존 Runtime AI 테스트 35개가 통과하는 반례를 확인했으므로, 다음 PR은 해당 검증 공백을 보완한다. [기존 bounded invocation 계약](../../openspec/specs/reliability-agentic-review/spec.md#requirement-provider-compatible-bounded-invocation)을 따르는 테스트 보강이며 새로운 동작 계약은 만들지 않는다.

| Boundary | Work |
| --- | --- |
| In Scope | 기존 Runtime AI 테스트의 실제 SDK·HTTP 경계에서 retry classification, 성공까지의 재시도와 호출 상한 검증 |
| Out of Scope | production code·Spec·의존성·CI 변경, 실제 외부 provider 호출, AI 품질 평가, 인간 승인 정책 변경 |

## Cases And Oracles

실제 SDK와 adapter를 통과하고 HTTP transport만 대체한다. Sleep은 지연 없이 제어한다. 기대 호출·attempt 수는 고정 값이며 production 계산을 복제하지 않는다. 기존 retry budget 0의 세 오류 사례도 유지한다.

| New Case | Retry Budget | Expected Result |
| --- | ---: | --- |
| HTTP 400 | 1 | HTTP 1회, attempt 1회, provider_client_error |
| HTTP 500 → 200 | 1 | HTTP 2회, attempt 2회, 성공 content 보존 |
| Connection failure → 200 | 1 | HTTP 2회, attempt 2회, 성공 content 보존 |
| HTTP 500 반복 | 2 | HTTP 3회, attempt 3회, provider_server_error |
| Connection failure 반복 | 2 | HTTP 3회, attempt 3회, provider_connection_error |

현재 올바른 production에서 새 테스트는 GREEN이어야 한다. 검출력은 격리 복사본에서 오류 분류를 잘못 바꿨을 때 실제 호출·결과 assertion이 RED가 되는 것으로 확인한다. Import guard로 복사본 로딩을 검증하며 원본에 mutation을 적용하지 않는다.

## Delivery Checklist

- [x] PR #252 병합과 최신 main baseline을 확인하고 별도 branch를 생성한다.
- [x] 기존 SDK 오류 테스트를 확장하고 일시 오류 후 성공 회귀를 추가한다.
- [x] Runtime AI suite, 변경 파일 Ruff/format·type 검사와 격리 negative control을 통과한다.
- [x] 정확한 구현 상태의 독립 review-lead assessment를 확보한다.
- [x] 실행·검토 근거를 보존하고 branch를 푸시해 신규 Draft PR을 연다.

## Resume

구현 `eb71f46e23a532d66c1a5ff8ce85c1af03965c03`의 로컬 검증과 [독립 리뷰](02-review-sdk-retry-implementation.md)를 마쳤고 [Draft PR #258](https://github.com/mols3131d/hmda-data-reliability/pull/258)을 생성했다. 이 PR이 branch와 현재 GitHub work unit을 소유한다. [실행 근거](01-report-sdk-retry-validation.md)와 같은 테스트 blob을 유지하며 최종 문서 head의 CI는 PR 본문과 checks에서 확인한다. 이후 재개 시 source/test 동일성·현재 main·새로운 feedback을 확인한다. Untracked 사용자 파일과 PR #252의 로컬 후속 검토 보고서는 포함하거나 되돌리지 않는다. 신규 PR의 Ready 전환·승인·병합은 별도 사용자 결정으로 남긴다.

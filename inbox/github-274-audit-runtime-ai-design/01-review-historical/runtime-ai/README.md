---
type: review
title: Runtime AI Test Design Review
description: Provider settings·실제 SDK wire contract·오류 분류와 재시도 연결 테스트의 oracle을 검토합니다.
---

> [!WARNING]
> **Historical only:** PR #258 (`bdce0f4e`)의 과거 리뷰입니다. 현행 문제나 승인 완료의 증거가 아닙니다. 이 PR에서 현재 source/Spec/tests에 재검증하여 채택 여부를 판정하세요.

# Runtime AI Test Design Review

> [!NOTE]
> 실제 SDK 오류 분류와 production 재시도를 HTTP 경계까지 연결한다. 과거 양수 retry budget 공백은 현재 보호되며 추가 material finding은 확인하지 못했다.

- **Target**: Runtime AI settings/contracts·OpenAI-compatible provider.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [test_provider.py](../../../../tests/runtime_ai/test_provider.py), [test_settings.py](../../../../tests/runtime_ai/test_settings.py), initializer 전체와 관련 source·계약.

## Findings

채택한 material finding은 없다. SDK HTTP 오류가 `max_retries=0`에서만 검사되던 과거 공백은 현재 5개 보강 case가 해결했다. 과거 report를 현재 미해결 결함으로 재사용하지 않는다.

## Subdomain Assessment

평면 package를 책임 단위로 나눈 review view다.

| Area | Scenario And Independent Oracle | Boundary And Limit |
| --- | --- | --- |
| Settings/DTO | 고정 기본값·sanitized config·URL 검증·환경 미사용 | 실제 모델 validation; DTO도 실제 adapter 사례에서 사용 |
| Wire success | exact model/messages/limits payload·content·usage·trace | 실제 OpenAI SDK, HTTP만 `httpx.MockTransport`로 대체 |
| Client failure | HTTP 400, 양수 budget에서도 1회·typed error·attempt count | 사전 분류된 transport error만 직접 넣는 검사가 아님 |
| Persistent failure | 500·connection 오류와 설정된 호출 상한 | 실제 SDK wrapping→retryable 판단→production retry 사용 |
| Transient recovery | 첫 500/connection 뒤 성공, HTTP 2회·public attempts·정확한 content | SDK hidden retry와 adapter retry를 호출 수로 구별 |
| Zero budget/limits | 기존 budget 0, response size·deadline·typed failure | 모든 상태 코드·실제 외부 서버 조합을 포괄하는 것은 아님 |

주요 근거는 provider 테스트 98·176·208·254·275·297·314·339행과 settings 22·63·75·95·106행이다. Request 객체 내부 비교만으로 끝내지 않고 literal wire·public result를 비교한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 full-body 검토 | Batch D 두 관점 3파일 |
| ✅ Pass | 현재 전체 실행 | [954 passed / 2 skipped](https://github.com/mols3131d/hmda-data-reliability/blob/bdce0f4e8e871b1301bac8f8ab3a37c7ba50bd91/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/validation.md#test-execution), Runtime만의 수로 오인하지 않음 |
| ⚪ Not Verified | 외부 provider의 현재 가용성·운영 응답 | 네트워크 경계는 통제된 HTTP transport |

## Risks And Limits

이 판단은 현재 계약과 대표 오류·재시도 경계에 한정된다. Review AI service가 같은 입력을 전달하는지는 [Review AI AI2](https://github.com/mols3131d/hmda-data-reliability/blob/bdce0f4e8e871b1301bac8f8ab3a37c7ba50bd91/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/review-ai/README.md#ai2--minor-provider-and-provenance-handoff)가 별도로 다룬다. Adapter test 통과로 caller의 모든 wiring을 증명하지 않는다.

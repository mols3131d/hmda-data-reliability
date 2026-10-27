---
type: review
title: Runtime AI Current Test Audit
description: Runtime AI의 현행 테스트 전수 검토, 과거 finding 재판정, 최소 회귀 보강과 검증 근거를 기록합니다.
---

# Runtime AI Current Test Audit

> [!NOTE]
> 도메인 테스트 검토와 허용된 보강을 수행했다. 독립 리뷰는 clear이며 최종 전달 상태는 아래 Current Review에서 확인한다. Draft/Ready/approval/merge는 별도 인간 결정이다.

- **Target:** [PR #274](https://github.com/mols3131d/hmda-data-reliability/pull/274)의 exclusive test lane과 read-only support/reserved integration.
- **Revision:** base `be1dca8d044494e92a0d25c791471a41b5d11bcf`; implementation/test head `a3dec4f33aa56276e92877714cd3b3bc178fdb64`. 최초 준비 branch에 최신 main을 merge하여 검증했다.
- **Scope:** current tracked 3파일 전체 본문을 두 specialist가 각자 검토했다. Source/Spec은 관련 계약 대조용이며 수정하지 않았다.

## Findings And Adoption

과거 [Runtime AI report](01-review-historical/runtime-ai/README.md)는 채택할 추가 finding이 없었다. 그보다 앞선 positive retry budget 공백은 `obsolete`다. 현행 실제 SDK+HTTP tests가 400 단일 호출, persistent 500/connection 상한과 transient recovery를 이미 보호한다.

| ID | Decision | Current evidence and action |
| --- | --- | --- |
| R1 | accepted / implemented | 기존 SDK wire test에 non-default `max_output_tokens=17`과 literal wire `max_tokens=17`을 사용해 기본값 1024를 상수로 쓰는 회귀를 구별한다. |
| R2 | accepted / implemented | 32-byte 한도에서 ASCII 33자와 한글 11자(UTF-8 33 bytes)를 거부하고 재시도 없이 한 번만 호출하는지 검사한다. |

## Contract Coverage

실제 OpenAI SDK에 HTTP boundary만 `httpx.MockTransport`로 주입한다. Literal wire payload, 반환 content/usage/trace, 실제 HTTP 횟수와 typed failure가 oracle이며, 미리 분류한 오류 대역만으로 retry를 증명하지 않는다. Settings는 명시 identity/URL/range/default/secret exclusion과 환경 비의존을 검사한다. Review AI caller wiring과 live endpoint 가용성은 #277 및 별도 live evidence의 범위다.

## File Coverage

이 표는 위 revision의 검토 ledger다. 테스트 수와 파일 수는 별개이며 reserved 파일의 검토는 수정 권한을 뜻하지 않는다.

| File | Coverage | Contract / oracle |
| --- | --- | --- |
| [tests/runtime_ai/__init__.py](../../tests/runtime_ai/__init__.py) | reviewed | package 설명 support |
| [tests/runtime_ai/test_provider.py](../../tests/runtime_ai/test_provider.py) | reviewed | 실제 SDK HTTP wire, retry budget, transient/persistent 오류, UTF-8 bytes, non-default tokens |
| [tests/runtime_ai/test_settings.py](../../tests/runtime_ai/test_settings.py) | reviewed | explicit identity, URL/range/defaults, secret 제외, 환경 비의존 |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Current domain suite | `uv run --no-sync pytest -q -ra tests/runtime_ai`: **41 passed (1.68s)**. Testmon selection 없이 domain 전체를 실행했다. |
| ✅ Pass | Changed Python | Ruff check/format check와 ty check 통과. 위 implementation head의 변경 파일 대상이다. |
| ✅ Pass | Artifact mechanics | Native rumdl, Inbox validator, 실제 YAML parser의 필수값 검사, local links와 git diff check 통과. |
| ⚪ Not Verified | Runtime limits | live provider 호출은 이 deterministic suite의 범위 밖이다. |

## Current Review

**Assessment: clear.** Review-lead가 quality/adversarial 두 specialist의 독립 결과를 조정했다. 정확한 reviewed implementation head는 `a3dec4f33aa56276e92877714cd3b3bc178fdb64`이며 base는 `be1dca8d044494e92a0d25c791471a41b5d11bcf`다. 기존 46파일 baseline 중 이 lane의 변경된 테스트와 현재 문서 3개를 두 관점에서 다시 대조했다.

수용한 공백은 닫혔고 남은 `current_required` finding은 없다. Source/공유 tooling 후속은 `follow_up / scope_change`로 분리했다. Reviewer는 suite를 재실행하지 않았으며 위 실행 결과는 coordinator evidence다. 이 판정은 test/document review gate이며 제품 source 후속의 해결이나 correctness approval을 의미하지 않는다.

최종 Inbox-only delivery는 이 head의 test/source/Spec blob을 보존한다. 전달 후 exact remote head, prospective merge CI와 review readiness는 [현재 PR 본문](https://github.com/mols3131d/hmda-data-reliability/pull/274)에서 확인한다. Draft/Ready/approval/merge를 자동 전환하지 않는다.

## Handoff

[Plan](00-plan-runtime-ai-tests.md)과 위 검토 ledger에서 이어간다. 과거 [historical bundle](01-review-historical/README.md)은 그대로 보존하며 현재 검증 수로 재사용하지 않는다. Final Inbox-only delivery는 위 head의 test/source/Spec blob을 보존하고 exact remote head/CI는 PR 본문에서 확인한다.

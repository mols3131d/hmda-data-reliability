---
type: report
title: SDK Retry Classification Validation
description: 후속 SDK 테스트의 실제 실행 결과와 세 가지 잘못된 오류 분류를 검출한 격리 negative control을 확인할 때 읽습니다.
tags:
  - testing
  - runtime-ai
---

# SDK Retry Classification Validation

## Tested State

Baseline은 PR #252의 squash merge `a8864328e8a92316d32cad386746c3c5f4b983cd`다. [변경 테스트](../../tests/runtime_ai/test_provider.py)의 Git blob은 `d7cc1fdcae6ca840cc56efb82a416e6bb88a0c81`이다. Production·Spec·dependency·CI 변경은 없다. 범위와 다섯 새 사례는 [계획](00-plan-sdk-retry-classification.md)을 따른다.

기존 SDK 오류 테스트의 retry budget 0 사례 세 개를 보존하고 양수 budget의 4xx·5xx·connection exhaustion 세 개를 더했다. 별도 두 사례는 실제 SDK 경계에서 일시적 5xx·connection 오류 뒤 성공을 검사한다. HTTP transport만 대체하고 sleep은 지연 없이 제어한다. SDK 오류 분류나 adapter를 테스트 double로 대체하지 않는다.

## Local Validation

| Check | Result |
| --- | --- |
| Runtime AI suite | `.venv/bin/python -m pytest tests/runtime_ai -q -ra`: **40 passed, 1.34s** |
| Ruff lint / format | 변경 테스트 파일 통과; format 변경 불필요 |
| Type check | `ty check tests/runtime_ai/test_provider.py` 통과 |
| Editor diagnostics / diff | 변경 테스트 오류 없음; `git diff --check` 통과 |
| Scope identity | `src`, `openspec`, dependency와 CI 경로의 diff 없음 |

Tach plugin은 unaffected 경고를 표시했지만 이 실행은 `--tach`를 사용하지 않았고 40개를 모두 실행했다. 이 변경에 저장소 전체 suite나 실제 외부 provider 호출은 재실행하지 않았다. 이전 PR의 949개 결과를 이 변경의 새 실행 결과로 합산하지 않는다.

## Negative Controls

임시 directory에 source·Runtime AI tests·pytest configuration을 복사했다. 자동 fixture가 매 테스트의 provider import 경로가 격리 복사본인지 검증했다. 각 mutation 전에 원래 source를 복원했고 다음 한 곳만 바꿨다.

| Isolated State | Result | Observed Detection |
| --- | --- | --- |
| 수정하지 않은 source + 새 테스트 | **40 passed**, 0.47s | 기준 실행 정상 |
| HTTP 상태 분류를 항상 retryable로 변경 | **1 failed / 39 passed**, 0.53s | client-positive-budget: 실제 HTTP 2회가 기대 1회와 불일치 |
| HTTP 상태 분류를 항상 non-retryable로 변경 | **2 failed / 38 passed**, 0.51s | server-budget-exhausted: 1회가 기대 3회와 불일치; server→success가 조기 unavailable |
| Connection 오류를 non-retryable로 변경 | **2 failed / 38 passed**, 0.58s | connection-budget-exhausted: 1회가 기대 3회와 불일치; connection→success가 조기 unavailable |

실패는 수집·환경 오류가 아니라 실제 호출 횟수 assertion 또는 성공해야 할 invocation의 `ProviderUnavailableError`였다. 격리 copy의 Git metadata 부재 진단은 출력됐지만 모든 pytest 실행은 정상 수집 후 예상한 결과로 끝났다. 원본 provider의 SHA256은 실행 전후 `90b1a4fb4eb4a494fee3d193d33bb873f7378249b687d00425bf205a70ead3b6`로 같았다.

이 결과는 지정한 세 가지 오류 분류 변형의 검출 근거다. 임의의 모든 잘못된 구현을 검출한다는 점수나 증명으로 확대하지 않는다.

## Review And Delivery

최종 테스트 구현은 `eb71f46e23a532d66c1a5ff8ce85c1af03965c03`이며 [독립 review-lead](02-review-sdk-retry-implementation.md)의 assessment는 clear다. 두 specialist가 정적 검토를 완료했고 raw caller log를 대조했으며, 자체 pytest 재실행과 구분했다.

[Draft PR #258](https://github.com/mols3131d/hmda-data-reliability/pull/258)을 생성했고 구현 head의 [CI Lite 39032342173](https://github.com/mols3131d/hmda-data-reliability/actions/runs/39032342173)이 success였다. Job `117395184304`의 Python·selected tests step이 실제 실행됐다. 이 테스트 전용 PR은 Runtime AI suite만 선택하며 source·build·boundary 등 불필요한 step은 scope상 생략한다. 후속 문서 head는 테스트 blob 동일성을 확인하고 최신 CI를 별도로 PR 본문과 checks에 남긴다.

신규 브랜치의 native pre-push도 affected 16 passed와 OpenSpec 21 passed, lint/format을 통과했다. 수치가 겹치는 실행을 합산하지 않는다. 사람의 승인·merge와 승인 정책 변경은 이 후속 PR의 준비 범위에 포함하지 않는다.

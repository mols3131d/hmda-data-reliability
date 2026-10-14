---
type: report
title: Review AI Evaluation Test Layout Completion
description: PR #251 평가 테스트 재배치의 실제 변경, revision별 검증 결과와 남은 경계를 기록한다.
---

# Review AI Evaluation Test Layout Completion

2026-09-29 KST. [10번 계획](10-plan-review-ai-evaluation-test-layout/02-plan-improvement.md)의 평가 테스트 재배치를 완료했다. 이 보고서의 구현 기준은 PR [#251](https://github.com/mols3131d/hmda-data-reliability/pull/251)의 commit `be207e5df72dcacea89ec8baa0cde90e1d6f4298`이며, 검증 당시 base는 `5532dca2fd93696d40ba870471fa2359c5662335`였다. **테스트 배치 작업의 완료**를 기록하는 것이며 PR 전체의 병합 승인이나 원격 평가 완료를 뜻하지 않는다.

## Delivered Change

- [`test_utility_evaluation.py`](../../tests/review_ai/evaluation/test_utility_evaluation.py), [`test_langfuse_projection.py`](../../tests/review_ai/evaluation/test_langfuse_projection.py), [golden JSON](../../tests/review_ai/evaluation/fixtures/utility_comparison_6e64cc7.json)을 `tests/review_ai/evaluation/` 아래로 이동했다. Git은 세 파일 모두 내용 변경 없는 100% rename으로 인식했다. 테스트 시나리오, assertion, marker와 fixture 값은 바꾸지 않았다.
- [Testing Guide](../../docs/development/testing.md)의 선택적 SDK 단일 테스트 명령을 새 경로로 갱신했다. PR #251의 [기존 완료 보고서](01-report-review-ai-evaluation-subdomain-completion.md), [테스트 설계 리뷰](07-review-review-ai-evaluation-test-design.md), [CI skip 보고서](08-report-review-ai-langfuse-ci-skip-tradeoffs.md)는 과거 검증 시점의 테스트·fixture 링크를 해당 commit에 고정했다.
- Production source, OpenSpec 행동 계약, CI selector와 Langfuse 설치·skip 정책은 변경하지 않았다. [10번 번들](10-plan-review-ai-evaluation-test-layout/README.md)의 조사·계획 자료는 재배치된 현재 경로를 안내한다.

## Verification

| Scope | Result and evidence |
| --- | --- |
| Collection and contents | 이동 전후 52개 pytest node ID는 파일 경로만 치환하면 일치했고 marker 구성도 같았다. 세 파일의 SHA-256이 각각 동일했다. |
| Local tests | 이동한 두 모듈 **52 passed**; `tests/review_ai tests/runtime_ai` **187 passed**; 새 경로의 선택적 Langfuse SDK 테스트 **1 passed**. |
| Static and routing | Ruff check/format, `ty check tests/review_ai/evaluation`, `tach check`, 변경 Markdown·Inbox 검사와 `git diff --check` 통과. 새 테스트·fixture 경로를 입력한 CI selector가 `tests/review_ai`를 선택했다. |
| Independent review | `3af4bf0..be207e5` 재배치 diff에 대한 quality/adversarial 검토 결과 `clear`, 현재 범위의 blocking finding 없음. Reviewer가 이동한 두 모듈의 **52개 테스트**를 별도로 실행했다. |
| Remote CI | 정확한 구현 head `be207e5`의 [CI Lite run 36487686728](https://github.com/mols3131d/hmda-data-reliability/actions/runs/36487686728) 성공: selected tests **186 passed, 1 skipped**. Package build, dependency boundary, Python, OpenSpec, Markdown와 Inbox 검사 통과. |

CI의 1개 skip은 `langfuse` 선택 의존성이 기본 CI에 설치되지 않아 [SDK media 테스트](../../tests/review_ai/evaluation/test_langfuse_projection.py)가 실행되지 않은 것이다. 로컬의 **1 passed**는 설치된 SDK에서 그 테스트가 동작함을 보여주지만 원격 Langfuse ingestion, UI 또는 human utility 평가 근거는 아니다. CI 포함 선택지는 [08번 보고서](08-report-review-ai-langfuse-ci-skip-tradeoffs.md)가 다룬다.

## Remaining Boundary

PR #245/#248의 과거 Inbox 보고서에는 이동 전 테스트 경로를 가리키는 상대 링크 10개가 남아 있다. 이 링크는 현재 checkout에서 깨지지만 PR #251의 테스트 수집·CI 선택·실행에는 영향을 주지 않는다. 각 보고서가 소유한 과거 근거 revision에 링크를 고정하는 후속 정리가 필요하다.

구현 head `be207e5`에서 기본 전체 pytest, 외부 Python consumer, wheel 설치 후 실행, 실제 Langfuse ingestion/UI와 human utility 평가는 **Not Verified**다. 보고서 추가 등 후속 문서 commit이 PR head를 바꾸면 그 head의 CI 상태는 다시 확인해야 한다. PR #251은 보고서 작성 시점에 **open Draft**이며 Ready 전환과 병합은 별도 결정이다.

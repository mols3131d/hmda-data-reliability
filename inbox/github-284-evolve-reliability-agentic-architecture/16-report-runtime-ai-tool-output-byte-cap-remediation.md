---
type: report
title: "PR #284 Tool-Call Output Byte Cap Remediation Report"
description: "정상 도구 호출의 출력 바이트 상한 누락 F1을 재현·수정하고 SDK 경계 회귀, 전체 검증과 독립 리뷰 근거를 기록한다."
tags:
  - runtime-ai
  - reliability-ai
  - testing
  - code-review
---

# PR #284 Tool-Call Output Byte Cap Remediation Report

## Outcome

**[11월 15일 PR 리뷰의 F1](https://github.com/mols3131d/hmda-data-reliability/pull/284#issuecomment-6895621881)을 실제 SDK 경계에서 재현하고 수정했다.** 긴 호출 ID·함수명, 여러 호출의 누적 구조와 UTF-8·JSON escape가 정상 응답의 출력 바이트 예산에 포함된다. 최종 focused 테스트 15개와 전체 non-resource 테스트 1,215개가 통과했고, 독립 DualVantage 검토 후 이번 보완 범위의 프로젝트 판정은 `clear`다.

F1은 `explicit_target / current_required`, 중요도 `Medium`으로 수용했다. [이전 UNC 완료 보고서](15-report-reliability-ai-unc-path-projection-remediation.md)의 `clear`는 해당 수정 범위에 한정되며, 별도 F1의 해결 근거를 대신하지 않는다.

| Basis | Verified Value |
| --- | --- |
| Verified date | `2026-11-16` |
| Owning PR / branch | [#284](https://github.com/mols3131d/hmda-data-reliability/pull/284), `agent/refactor/evolve-reliability-agentic-architecture` |
| Baseline HEAD | `fdfd4245514ed748dbcd00880de7d1aacac61e1b` |
| Implementation commit | `39820f62c66e36e319abb321ab705f7f3eeb72ae`, ED25519 서명 검증 성공 |
| PR base at verification | `f1de6256cdd1e034f655b2f2ee3997481d0b195c` |
| Reviewed source/test diff SHA256 | `ebe2046fee9223cc85b066e4d2f9bd61f2d64cb04128be6bbda938655a2ca0ed` |
| OpenSpec | [기존 Task 5](../../openspec/changes/reliability-agentic-review-enable-bounded-tools/tasks.md) 재개 후 완료, `7/7 all_done` |

## Remediation

[Runtime adapter](../../src/hmda_reliability/runtime_ai/provider.py)의 정상 응답 검사는 본문과 각 호출의 인자만 합산하고 있었다. ID·함수명·목록과 객체 구조가 커져도 상한을 통과할 수 있었다.

- 정상 호출은 전체 normalized `tool_calls` 목록을 `ensure_ascii=False`, `separators=(",", ":")`로 JSON 직렬화한 UTF-8 바이트와 본문 UTF-8 바이트를 합산한다. ID·type·함수명·인자와 목록·객체 구조를 포함한다.
- 본문-only는 기존 본문 바이트만, 비정상 호출은 기존 본문과 `raw_tool_calls` 바이트 합을 유지한다. 정확한 상한은 허용하고 초과하면 기존 `ProviderResponseTooLargeError`로 재시도 없이 거부한다. Attempt·usage·trace·response metadata를 유지한다.
- [기존 SDK 테스트](../../tests/runtime_ai/test_provider_tools.py)에 6개 매개변수 사례를 추가했다. 고정된 compact JSON 리터럴을 독립 oracle로 사용하며, 각 사례에서 정확한 상한의 성공과 1바이트 작은 한도의 거부를 확인한다. 실제 OpenAI SDK와 `httpx.MockTransport`를 연결하고 외부 서비스는 호출하지 않는다.
- 새 의존성·공개 API·설정·최대값·도구 권한·retry 정책을 추가하거나 변경하지 않았다. 과거 리뷰·실행 자료는 그대로 보존했다.

## Verification

| Check | Result and Evidence |
| --- | --- |
| RED before production edit | `11 passed, 4 failed`. 정상 호출 4개 사례 모두 초과 응답에서 `ProviderResponseTooLargeError`가 발생하지 않았다. 본문-only·비정상 raw 사례는 통과했다. |
| Final focused pytest | `.venv/bin/python -m pytest tests/runtime_ai/test_provider_tools.py -q -p no:sugar --tb=short`: `15 passed` |
| Final full non-resource pytest | 절대 `TMPDIR/TMP/TEMP`를 지정하고 `.venv/bin/python -m pytest -n auto -q -p no:sugar --tb=short`: `1,215 passed, 1 skipped`, 실패·오류 0건 |
| Static checks | 변경 두 Python 파일의 Ruff lint·format, project-wide `ty check`, `tach check` 모두 통과 |
| OpenSpec and tracking | 기존 Change strict validation 통과, Task 5 완료 후 `7/7 all_done` 확인 |
| Independent review | 별도 Verifier·Challenger의 검토에서 material 후보·현재 범위 필수 미해결 항목 0건. Verifier가 focused pytest `15 passed`와 시작·종료 diff 해시 일치를 독립 확인했다. |
| Commit integrity | 구현 commit 서명 검증 성공, commit의 source/test diff 해시가 reviewed state와 일치. Pre-commit은 Python 두 파일을 변경하지 않았다. |

테스트 전담 agent는 테스트 파일만 수정했고, 구현 담당자가 실제 RED/GREEN과 전체 회귀를 실행했다. 독립 리뷰는 그와 별도의 context에서 수행했다. Challenger는 정적 검토만 수행했으며 실행 도구 제한으로 baseline diff·해시·pytest를 독립 실행하지 못했다. 이 검증은 Verifier가 수행한 범위로 구분한다. 전체 suite·정적 검사 결과는 구현 담당자의 근거이며 독립 재실행했다고 주장하지 않는다.

## Limits And Delivery

- 상한은 정규화된 호출 목록과 본문의 출력 표현에 적용한다. 전체 HTTP response envelope, SDK 수신 전 네트워크 크기 또는 수신·파싱 중 메모리 상한을 보장하지 않는다.
- 실제 provider·Langfuse 전송, 제품 모델 최종 revision 재실험과 5개 기준 인간 효용 평가는 실행하지 않았다. 기존 모델 품질·채택 판단과 이번 결정론적 코드 보완의 완료를 구분한다.
- 이 보고서 커밋까지 일반 push한 뒤 PR 본문의 최종 검증·F1 처리 근거·References·`revision.base/head`를 갱신한다. 새 head의 CI는 결과를 확인하기 전 통과로 표시하지 않는다.
- Ready 전환·approval·review thread 해결·merge·archive는 수행하지 않는다. GitHub의 Draft 상태와 사람의 최종 채택 권한은 유지한다.

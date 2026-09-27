---
type: report
title: Review AI Evaluation Subdomain Completion
description: PR 251의 main 통합, 전체 comparison golden 검증 보강과 독립 quality/adversarial 리뷰의 완료 근거를 기록한다.
---

# Review AI Evaluation Subdomain Completion

2026-09-27 KST. PR #251의 evaluation 하위 도메인 리팩터링을 마무리하며 [09 셀프 리뷰](../github-248-review-ai-langfuse-evaluation/09-review-review-ai-evaluation-subdomain-self-review.md)의 F1 테스트 공백을 해소했다. 독립 `review-lead`는 아래 exact code head에 **`clear`**를 반환했고 `current_required` finding이 없었다. Quality와 adversarial specialist가 모두 검토했으며 이전 adversarial coverage gap은 이 revision에서 해소됐다.

## Revision Basis

- **PR:** [#251](https://github.com/mols3131d/hmda-data-reliability/pull/251), `agent/refactor/review-ai-evaluation-subdomain`.
- **Current base:** `5532dca2fd93696d40ba870471fa2359c5662335` (`main`, 부모 #248의 squash merge).
- **Integration commit:** `24419a2`; 최신 main의 tree는 기존 stacked parent `6e64cc70a5dca8ff8cd423a9f2240848f4b2e7dd`와 같았다. Merge conflict는 renamed module import/reference와 새 test 경로에서 발생했다. 새 경로를 유지하고 이전 adapter의 재등장을 제거한 결과 integration commit의 tree는 직전 branch tree와 같다.
- **Reviewed code head:** `5bde8a45e8af26f0f418634a862157f251fca9ef`.
- 아래 독립 리뷰와 실행 결과는 이 code head에만 적용된다. 이후 `a2d85c1`은 Python 파일 다섯 개를 수정하고 선택적 Langfuse 투영 DEBUG 로그를 추가했다. 따라서 이후 source head에 대한 검증으로 해석하지 않는다. 이후 source 검토는 [로컬 코드 리뷰](02-review-review-ai-evaluation-subdomain-localized-code.md)와 [고강도 리뷰](03-review-review-ai-evaluation-subdomain-high-intensity.md)를 참조한다.

## Follow-up Evidence

2026-09-28 KST. 두 독스트링을 현재 구현과 public export에 맞췄고 PR 본문도 current base/head 및 revision별 validation으로 갱신했다. [고강도 리뷰 해소 기록](04-review-resolution-review-ai-evaluation-subdomain-high-intensity.md)은 F1–F3의 조치와 검증을 기록한다.

- **Resolution source head:** `724580a7f1c051acb9f2a5ed3c43a00a947b4b59`.
- **Current PR CI:** [CI Lite run 36341207619](https://github.com/mols3131d/hmda-data-reliability/actions/runs/36341207619)에서 selected tests **186 passed, 1 skipped**. Skip은 CI에 `langfuse` dependency가 없어 optional SDK integration test를 실행하지 못한 결과다.
- **Current pre-push checks:** affected tests **11 passed**, Ruff check와 format 통과.
- **Independent review:** 정확한 base/head의 focused quality review에서 **55 tests passed**; adversarial review에서 추가 material regression은 없었다. Stale PR body를 갱신한 뒤 review lead는 PR description과 evidence attribution을 `clear`로 판정했다.
- `5bde8a4`의 independent `clear`, Review AI/Runtime AI **187 passed**, 기본 전체 suite **707 passed, 1 skipped**는 해당 historical code head에만 적용되며 `724580a`의 전체 suite 근거가 아니다.

## F1 Resolution

새 [static fixture](../../tests/review_ai/fixtures/utility_comparison_6e64cc7.json)는 pre-refactor revision `6e64cc70a5dca8ff8cd423a9f2240848f4b2e7dd`의 `src`와 기존 test helper를 temporary archive에서 실행해 얻었다. Historical `evaluation.py`가 실제 import origin인지 확인한 뒤 compared와 case-version mismatch의 blocked JSON을 캡처했다. 현재 `ReviewValue*` 모델로 expected 값을 생성하지 않았다.

[Golden test](../../tests/review_ai/test_utility_evaluation.py)는 nested score/delta keys, criterion 및 decision/status enum 문자열, embedded outputs, attribution과 두 output digest를 포함한 전체 JSON을 비교한다. Human decision `accept`, `reject`, `no_change`는 test의 literal 값으로 검증한다. JSON text 비교는 Python equality가 같다고 보는 bool/int 및 int/float 차이도 검출한다.

Repository 밖 temporary source copy에서 `baseline_score`를 `before_score`로, `candidate_score`를 `after_score`로 함께 바꾸고 import origin을 확인한 뒤 동일 mutation을 두 test revision에 적용했다. 기존 테스트는 **15 passed**로 변경을 놓쳤고, 보강된 테스트는 golden assertion에서 **4 failed, 15 passed**였다. 정상 repository의 보강된 evaluation module은 **19 passed**다. Mutation은 production source에 반영하지 않았으며 temporary copy는 제거했다.

F1은 새로운 runtime defect 수정이 아니라 리팩터링이 보존해야 할 wire contract의 회귀 검출력 보강이다. Evaluation와 adapter runtime 구현, `reliability.evaluation`, provider의 `utility_contributions`는 이 remediation에서 바꾸지 않았다. 기존 Task 1·4를 다시 열어 보강과 검증을 수행했고 별도 remediation task를 추가하지 않았다.

## Validation

| Check | Result | Evidence |
| --- | --- | --- |
| Golden module | Pass | 19 passed; commit hook의 fixture formatting 뒤에도 다시 확인했다. |
| Mutation detection | Pass | 기존 tests 15 passed; 새 golden cases 4개는 필드 rename mutation에서 실패했다. |
| Review AI and Runtime AI | Pass | 187 passed, skip 없음; optional Langfuse 4.15.6이 설치된 로컬 환경이다. |
| Full default pytest | Pass | `pytest -x -q -p no:cacheprovider --tb=short`: 707 passed, 1 skipped in 187.24s. 기본 memory/stress 제외와 기존 timeout 설정을 유지했다. |
| Platform skip | Expected | Windows npm/Node process-boundary test는 Linux에서 skip된다. 이전 Airflow child timeout은 이번 전체 실행에서 재현되지 않았다. |
| Static and architecture | Pass | Ruff check/format, project-wide `ty check`, `tach check`, `git diff --check`. |
| OpenSpec and documents | Pass | Change strict validation, 변경 canonical Markdown/Change와 Inbox contract 검사. |
| Independent review | Clear | Quality/adversarial specialist 검토 완료; lead는 current-required finding 없음으로 판정했다. |
| Independent focused execution | Pass | Reviewer가 evaluation/Langfuse/public-surface 55 tests를 직접 실행했다. |

전체 pytest는 local Airflow child/IPC를 허용하는 실행 환경에서 수행했다. Timeout을 늘리거나 assertion/skip 조건을 바꾸지 않았다. 기본 suite는 실제 provider나 원격 Langfuse project를 호출하지 않는다.

## Independent Review Coverage

Reviewer는 main base부터 code head까지 전체 diff를 검토했다. Alias 없는 Python API rename, 새 package exports, optional adapter import/child entrypoint, serialized field/enum/rubric/digest 계약과 fail-closed comparison을 확인했다. Adversarial specialist의 symbol/path 정규화 AST 비교에서도 runtime 의미가 보존됐다.

별도 malformed-JSON stdin probe로 새 `python -m hmda_reliability.review_ai.evaluation.langfuse`가 exit 1 및 빈 stdout/stderr로 종료하는 것을 확인했고, optional adapter import가 Langfuse SDK를 로드하지 않는 것도 검토했다. 이 probe는 SDK export 성공이나 원격 ingestion을 증명하지 않는다.

Reviewer가 직접 실행한 55개 test와 caller가 실행해 제공한 전체 707개 결과를 구분한다. Golden capture/mutation 및 static/OpenSpec/Inbox 검사는 caller의 실행 근거이며 specialist가 모두 재실행한 것으로 표현하지 않는다.

## Delivery Boundary

부모 #248은 병합됐고 #251은 `main`을 대상으로 한다. 최신 prospective merge CI는 [PR checks](https://github.com/mols3131d/hmda-data-reliability/pull/251/checks)가 소유한다. 이 보고서의 local 실행 성공이나 부모 CI를 #251의 최신 CI 결과로 대체하지 않는다.

외부 Python consumer, wheel 설치 후 실행, memory/stress suite, 실제 Langfuse ingestion/UI와 human utility 평가는 Not Verified다. Remote proof는 이 refactor의 approved scope 밖이다. Ready 전환, approval과 merge는 사람의 결정으로 남는다.

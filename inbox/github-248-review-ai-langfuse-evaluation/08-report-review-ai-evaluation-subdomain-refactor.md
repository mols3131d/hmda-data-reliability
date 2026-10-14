---
type: report
title: Review AI Evaluation Subdomain Refactor
description: PR 248 후속 하위 도메인 리팩터링의 구현, 검증, 독립 리뷰 결과와 남은 확인 공백을 기록합니다.
---

# Review AI Evaluation Subdomain Refactor

2026-09-27 KST. 이 보고서는 PR #248의 계획을 보완한 뒤 진행한 Review AI evaluation 하위 도메인 리팩터링을 기록한다. 구현은 `agent/refactor/review-ai-evaluation-subdomain` branch의 `73702f1eba2983ce667bef46624a96bcae5d7170`에 있다. PR #248은 이 branch의 부모이므로 후속 change는 stacked 상태이며 부모보다 먼저 merge하지 않는다.

## 변경 내용

- `review_ai/evaluation.py`를 `review_ai/evaluation/value.py`로 이동하고 `review_ai/evaluation/__init__.py`에서 value API만 export한다.
- `HumanUtilityEvaluation`, `UtilityComparisonEvidence`, `UtilityComparisonStatus`, `UtilityRubric` 및 관련 함수 이름을 `ReviewValue*` API로 바꿨다. 확인된 in-repository consumer를 함께 갱신했으며, package version `0.1.0`의 의도적인 Python API breaking change로 취급한다. 호환 alias는 추가하지 않았다.
- `langfuse_projection.py`를 `review_ai/evaluation/langfuse.py`로 이동했다. live harness import와 child `python -m` entrypoint를 새 경로로 바꾸고 child 경로를 고정하는 테스트를 추가했다.
- Comparison field/enum values와 output digest 알고리즘이 이동 전과 같은지 golden regression test를 추가했다. `utility_contributions` wire field, MVP Utility Proofs acceptance와 reliability recovery evaluation은 변경하지 않았다.
- Canonical Review AI Spec, Review AI domain guide, testing guide와 실행 경로를 갱신하고, 새 subdomain을 위한 OpenSpec Change를 추가했다.

계획 리뷰에서 빠졌던 child `python -m` 실행 경로와 `docs/development/testing.md` helper reference를 별도 migration consumer로 추가했다. 계획은 `6e64cc70a5dca8ff8cd423a9f2240848f4b2e7dd`에 반영했다. 기존 Inbox 검토물은 각자 대상 revision의 증거로 보존했다.

## 검증 결과

| Check | Result | Evidence |
| --- | --- | --- |
| Test-first regressions | Pass | 새 API 테스트는 이동 전 `evaluation`이 package가 아니라는 import error로 실패했다. Child-path 테스트는 기존 launcher가 옛 module path를 사용하는 것을 검출했다. |
| Review AI and Runtime AI | Pass | `pytest -p no:cacheprovider -q tests/review_ai tests/runtime_ai`: 183 passed. |
| Independent quality review | Pass | Exact implementation commit `73702f1...`에서 evaluation, Langfuse projection과 public surface 51 tests passed. Quality reviewer는 current-required correctness finding이나 material test-coverage gap을 보고하지 않았다. |
| Python and architecture checks | Pass | Project-wide `ty check`, Ruff check/format, `tach check`, `git diff --check`, pre-commit hooks. |
| Spec and documentation | Pass | OpenSpec strict validation, 변경 Markdown `rumdl check`, Inbox validator가 통과했다. |
| Parent PR CI | Pass | PR #248의 plan-update head `6e64cc7`에서 CI Lite #1094의 Inbox/OpenSpec, dependency, build, Python, selected-test와 runtime-smoke steps가 성공했다. 이 CI run은 후속 구현 branch를 검증한 것은 아니다. |
| Full repository pytest | Not complete | `pytest -x -q -p no:cacheprovider --tb=short`는 153 passed 후 `tests/orchestration/test_airflow_dagrun.py::test_disabled_analytics_is_skipped_without_asset_update`에서 실패했다. Airflow child가 `load_raw_hmda_loans` 시작 중 60초 timeout을 초과했다. orchestration 파일은 이 change에서 수정하지 않았다. 전체 suite pass로 간주하지 않는다. |

## 독립 리뷰와 범위 한계

독립 `review-lead`는 **`blocked`**를 반환했다. 필수 adversarial specialist를 두 차례 요청했지만 agent thread limit 때문에 실행되지 않았다. 따라서 adversarial failure-path 관점은 **Not Verified**이며, quality review나 자체 점검으로 대체하지 않았다. PR은 이 누락이 보이는 Draft 상태로 둔다.

Quality reviewer는 새 package export, optional Langfuse child 경계, launcher path, Spec과 가이드 참조를 확인했고 current-required 결함을 찾지 못했다. 외부 Python package consumer는 checkout에서 확인할 수 없으므로 breaking API rename의 외부 영향은 **Not Verified**다.

완료된 기존 OpenSpec design `review-ai-langfuse-projection/design.md`에는 당시 구현 경로 `review_ai.langfuse_projection`과 `utility_output_digest()`가 남아 있다. 독립 review-lead는 이를 **follow-up / independent_requirement**로 분류했으며 현재 source, canonical Spec과 사용자 guide의 잘못된 경로는 아니다. 이전 change의 당시 설계를 재작성하지 않았다.

실제 Langfuse endpoint/project가 없어 remote ingestion, 배포 UI와 human rubric 평가도 **Not Verified**다. 실행 결과 `submitted_unverified`는 전달 확인이나 utility acceptance를 뜻하지 않는다.

PR #248은 plan revision과 CI Lite #1094 결과를 반영해 body를 갱신했으며 `open`, Draft 상태로 유지된다. 새 구현 branch는 그 PR을 base로 쌓인다. CI Lite는 PR base가 `main`일 때만 실행되므로 #251이 #248 branch를 base로 둔 동안 workflow run은 생성되지 않는다. #248 merge 후 #251을 `main`으로 retarget하고 CI Lite를 다시 확인한다.

```yaml
revision:
  implementation_base: 6e64cc70a5dca8ff8cd423a9f2240848f4b2e7dd
  implementation_head: 73702f1eba2983ce667bef46624a96bcae5d7170
  parent_pr_head: 6e64cc70a5dca8ff8cd423a9f2240848f4b2e7dd
  review_status: blocked_adversarial_specialist_unavailable
```

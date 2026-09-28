---
type: review
title: Review AI Evaluation Test Layout Plan Self-Review
description: PR #251 평가 테스트 재배치 계획의 실행 가능성, 검증 기준과 PR 경계를 셀프 리뷰한다.
---

# Review AI Evaluation Test Layout Plan Self-Review

> [!IMPORTANT]
> **Revise before implementation** — 세 파일을 `tests/review_ai/evaluation/`으로 묶는 방향과 CI 선택은 타당하다. 다만 PR 분리 조건은 repository policy와 맞춰야 하고, 수집 결과 비교 기준과 이전 보고서의 링크 처리도 명시해야 한다. 이는 작성자의 셀프 리뷰이며 독립 리뷰가 아니다.

- **Target** — [test layout plan](10-plan-review-ai-evaluation-test-layout.md)
- **Revision** — 계획서 commit `0778a3f7a1ab9f65fb32a565a213600cc2540e33`; PR #251 base `5532dca2fd93696d40ba870471fa2359c5662335`
- **Scope** — 테스트 이동 범위, pytest 수집 비교, 기존 문서 링크, CI 경로 선택과 PR ownership. 테스트 파일은 이동하지 않았다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟠 Major | 인간 review 시작만으로 후속 PR로 분리하는 조건이 동일 변경 목적의 기존 PR 유지 규칙과 충돌한다. | #251의 같은 리팩터링 범위라면 review 상태와 무관하게 해당 PR에서 갱신·재검증하고, 목적을 별도로 분리하기로 결정한 경우에만 후속 PR을 택한다. |
| F2 | 🟡 Minor | pytest node ID는 파일 이동만으로 바뀌는데 “수집 case가 같다”는 비교 기준이 정의되지 않았다. | 이동 전후 node ID의 파일 경로를 정규화해 함수명·parameter ID와 marker를 비교한다고 명시한다. |
| F3 | 🟡 Minor | 이동 후 깨지는 과거 보고서의 상대 링크가 구체적으로 식별되지 않았다. | #251의 01·07·08 보고서에 있는 옛 테스트·fixture 링크를 이동 전 SHA에 고정하거나 현재 파일 링크로 갱신할 대상을 명시한다. |

## Details

### F1 — PR Ownership

#### F1 Locations

- [Test layout plan](10-plan-review-ai-evaluation-test-layout.md) — 마지막 문단
- [Pull Request policy](../../docs/development/vcs-git/pull-request.md) — Scope와 Lifecycle

#### F1 Evidence

계획은 인간 review가 시작되면 테스트 이동을 별도 후속 PR로 전달할 수 있다고 한다. Repository policy는 같은 변경 목적의 후속 수정을 기존 PR에서 이어가고, 별도 목적이나 접근 방식일 때 새 PR을 사용한다. 인간 review 시작 자체는 목적 변경이 아니다. 현재 #251은 Draft이며 제출된 GitHub review는 없다.

#### F1 Impact

계획을 문자 그대로 실행하면 평가 하위 도메인 리팩터링의 테스트 배치만 다른 PR로 분리해 ownership과 검증 근거가 갈릴 수 있다. Review가 이미 진행됐다면 변경 후 재검토가 필요하다는 사실을 명시하면 된다.

### F2 — Collection Comparison

#### F2 Locations

- [Test layout plan](10-plan-review-ai-evaluation-test-layout.md) — Execution Plan 4, Acceptance And Boundary 1

#### F2 Evidence

현재 두 module의 `pytest --collect-only -q` 결과는 52개이며 node ID가 `tests/review_ai/test_utility_evaluation.py::...`처럼 파일 경로를 포함한다. 제안한 이동이 성공하면 그 접두 경로는 반드시 달라진다.

#### F2 Impact

정규화 없이 전체 node ID를 비교하면 정상적인 rename을 실패로 판정한다. 함수명·parameter ID와 marker는 유지하고 파일 경로만 새 위치로 매핑해 비교해야 한다.

### F3 — Historical Links

#### F3 Locations

- [Test layout plan](10-plan-review-ai-evaluation-test-layout.md) — Execution Plan 2
- [Completion report](01-report-review-ai-evaluation-subdomain-completion.md), [test design review](07-review-review-ai-evaluation-test-design.md), [CI skip report](08-report-review-ai-langfuse-ci-skip-tradeoffs.md)

#### F3 Evidence

세 보고서에는 이동 대상 테스트 또는 golden fixture를 가리키는 상대 링크가 있다. 현재 경로의 파일이 사라지면 링크가 깨진다. 계획의 “과거 기록은 보존하거나 SHA에 고정”이라는 표현은 이 링크들의 처리 방식을 특정하지 않는다.

#### F3 Impact

역사적 검증 내용을 새 위치의 현재 파일로 조용히 바꾸면 근거 revision이 흐려질 수 있다. 반대로 링크를 그대로 두면 독자가 파일에 접근하지 못한다. 각 링크의 목적에 따라 이동 전 SHA의 permalink 또는 새 경로를 선택해야 한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 대상·fixture 경로 | 두 테스트 파일과 golden fixture가 계획의 현재 경로에 있으며, golden test는 `Path(__file__).with_name("fixtures")`를 사용한다. 상위 `conftest.py`도 유지된다. |
| ✅ Pass | CI 선택 경로 | 새 파일·fixture 경로를 `classify_changes.sh --stdin`에 넣으면 `tests=true`, `targets=tests/review_ai`다. |
| ✅ Pass | 기준 pytest 수집 | 현재 두 module은 52개 case로 수집된다. |
| ⚪ Not Verified | 이동 후 수집·실행 | 이 셀프 리뷰에서는 테스트 파일을 이동하거나 새 경로의 pytest를 실행하지 않았다. |
| ⚪ Not Verified | 독립 리뷰 | 작성자 본인의 계획을 같은 맥락에서 검토했다. |

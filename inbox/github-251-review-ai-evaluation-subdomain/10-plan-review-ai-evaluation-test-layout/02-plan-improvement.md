---
type: plan
title: Review AI Evaluation Test Layout Improvement Plan
description: 셀프 리뷰를 반영해 Review AI evaluation 테스트와 golden fixture를 하위 도메인으로 묶는 이동 계획이다.
---

# Review AI Evaluation Test Layout Improvement Plan

## Goal

평가 계약과 선택적 Langfuse adapter의 테스트를 `tests/review_ai/evaluation/`에 모아 소유 범위를 찾고 따로 실행하기 쉽게 한다. **테스트 시나리오·assertion·marker와 production 동작은 바꾸지 않는다.** 이는 `src/`를 기계적으로 복제하는 작업이 아니라, 두 평가 테스트와 그 golden fixture가 이미 공유하는 검증 경계를 드러내는 작은 경로 변경이다.

테스트·source 기준은 PR #251 head `4de6d33e9c2fe626d9ce78aa9ab1ef5330bdf396`이다. 구현 시 현재 base/head와 다른 작업의 변경을 다시 확인한다. 테스트 설계의 현재 근거는 [research](00-research.md)가 소유한다.

## Target Layout

| Current | Proposed |
| --- | --- |
| `tests/review_ai/test_utility_evaluation.py` | `tests/review_ai/evaluation/test_utility_evaluation.py` |
| `tests/review_ai/test_langfuse_projection.py` | `tests/review_ai/evaluation/test_langfuse_projection.py` |
| `tests/review_ai/fixtures/utility_comparison_6e64cc7.json` | `tests/review_ai/evaluation/fixtures/utility_comparison_6e64cc7.json` |

파일 이름과 test body는 유지한다. Golden test가 `Path(__file__).with_name("fixtures")`를 사용하므로 fixture를 같은 상대 위치로 옮기면 oracle을 수정할 필요가 없다. 상위 [`conftest.py`](../../../tests/review_ai/conftest.py)는 계속 공유한다. `test_live_harness.py`는 harness 경계, `test_public_surface.py`는 package-root API 경계에 남긴다. 새 helper, `conftest.py` 또는 `__init__.py`는 필요성이 검증되지 않으면 만들지 않는다.

## Test Design Boundary

이번 변경의 검증 대상은 테스트 배치가 바뀌어도 기존 시나리오와 독립 oracle이 그대로 실행되는지다. `test_utility_evaluation.py`의 pre-refactor golden JSON과 digest 비교, `test_langfuse_projection.py`의 optional SDK 경계와 unit/component/integration marker를 보존한다. 새 behavior나 oracle을 설계하지 않는다. Root 공개 API와 live harness를 검증하는 두 test는 옮기지 않고 관련 suite에서 함께 실행한다. 계약별 기존 보호 범위는 [test design review](../07-review-review-ai-evaluation-test-design.md)를 참조한다.

## Execution Plan

1. 이동 전 두 module의 pytest 수집 결과와 focused 결과를 기록한다. 기준 수집은 52 case다. 현재 git 상태를 확인한 뒤 세 파일을 rename으로 이동한다. 테스트 내용은 수집 경로 외에는 수정하지 않는다.
1. [Testing Guide](../../../docs/development/testing.md)의 optional SDK 단일 테스트 명령을 새 경로로 갱신한다. PR #251의 [01 completion report](../01-report-review-ai-evaluation-subdomain-completion.md), [07 test design review](../07-review-review-ai-evaluation-test-design.md), [08 CI skip report](../08-report-review-ai-langfuse-ci-skip-tradeoffs.md)에 있는 이동 대상 테스트·fixture의 상대 링크는 각 문서가 설명하는 이전 revision으로 고정하거나, 현재 파일을 안내하는 링크에 한해 새 경로로 갱신한다. 다른 PR의 Inbox를 일괄 재작성하지 않는다.
1. [CI selector](../../../.github/workflows/classify_changes.sh)의 `--stdin` 입력으로 새 두 `.py` 경로와 fixture 경로가 모두 `tests/review_ai`를 선택하는지 다시 확인한다. 기준 revision에서는 이 결과를 확인했다. 분류기가 그대로 동작하면 workflow나 selector를 수정하지 않는다.
1. 이동 후 두 module의 node ID에서 옛 파일 경로만 새 경로로 매핑해 함수명·parameter ID가 같고 marker가 유지되는지 비교한다. 새 경로의 두 module·상위 public-surface/live-harness test 및 `tests/review_ai tests/runtime_ai`를 실행한다. Golden JSON 비교가 같은 fixture를 읽는지 확인한다. 선택 SDK 검증은 새 경로의 test node에서 별도로 실행하며, 기본 CI의 기존 skip을 이 이동의 실패나 성공으로 오해하지 않는다.
1. 변경 Markdown·Inbox 검사, `git diff --check`와 PR의 prospective merge CI를 확인한다. Git rename diff에서 의도치 않은 assertion·fixture 값·marker 변경이 없는지 검토한 뒤 PR 본문과 review evidence를 새 head 기준으로 다시 판정한다.

## Acceptance And Boundary

- 이동 전후 수집된 52개 node ID의 파일 경로만 매핑했을 때 함수명·parameter ID와 marker가 같고, golden comparison의 기대 JSON과 digest가 유지된다.
- 새 중첩 경로와 fixture 변경이 CI에서 Review AI suite를 선택하며, 경로가 바뀐 직접 실행 명령과 현재 탐색 링크가 유효하다.
- Source review 이후 test path가 바뀌므로 기존 독립 review와 CI를 새 head의 결과로 자동 승격하지 않는다. 기계적 이동 범위를 확인하고 필요한 focused review·CI를 다시 수행한다.
- 이번 계획은 테스트 배치만 다룬다. Langfuse SDK의 CI 설치/skip 정책, 원격 ingestion, human 평가, OpenSpec 행동 계약은 [CI skip 보고서](../08-report-review-ai-langfuse-ci-skip-tradeoffs.md)와 각 owner의 별도 판단으로 남긴다.

같은 리팩터링 목적의 후속 수정이면 PR #251에서 진행하고 변경된 head의 CI와 영향을 받은 review를 다시 확인한다. 이미 인간 review가 시작됐다는 사실만으로 PR을 분리하지 않는다. 변경 목적을 별도로 분리하기로 결정한 경우에만 후속 PR을 사용한다. 이 계획서는 구현이나 Ready·병합 권한을 부여하지 않는다.

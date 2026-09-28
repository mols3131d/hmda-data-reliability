---
type: plan
title: Review AI Evaluation Test Layout
description: Review AI evaluation 테스트와 golden fixture를 하위 도메인으로 묶고 검증 근거를 유지하는 이동 계획이다.
---

# Review AI Evaluation Test Layout

## Goal

평가 계약과 선택적 Langfuse adapter의 테스트를 `tests/review_ai/evaluation/`에 모아 소유 범위를 찾고 따로 실행하기 쉽게 한다. **테스트 시나리오·assertion·marker와 production 동작은 바꾸지 않는다.** 이는 `src/`를 기계적으로 복제하는 작업이 아니라, 두 평가 테스트와 그 golden fixture가 이미 공유하는 검증 경계를 드러내는 작은 경로 변경이다.

계획 기준은 PR #251 head `4de6d33e9c2fe626d9ce78aa9ab1ef5330bdf396`이다. 구현 시 base/head와 다른 작업의 변경을 다시 확인한다.

## Target Layout

| Current | Proposed |
| --- | --- |
| `tests/review_ai/test_utility_evaluation.py` | `tests/review_ai/evaluation/test_utility_evaluation.py` |
| `tests/review_ai/test_langfuse_projection.py` | `tests/review_ai/evaluation/test_langfuse_projection.py` |
| `tests/review_ai/fixtures/utility_comparison_6e64cc7.json` | `tests/review_ai/evaluation/fixtures/utility_comparison_6e64cc7.json` |

파일 이름과 test body는 유지한다. Golden test가 `Path(__file__).with_name("fixtures")`를 사용하므로 fixture를 같은 상대 위치로 옮기면 oracle을 수정할 필요가 없다. 상위 [`conftest.py`](../../tests/review_ai/conftest.py)는 계속 공유한다. `test_live_harness.py`는 harness 경계, `test_public_surface.py`는 package-root API 경계에 남긴다. 새 helper, `conftest.py` 또는 `__init__.py`는 필요성이 검증되지 않으면 만들지 않는다.

## Execution Plan

1. 이동 전 두 module의 pytest 수집 결과와 focused 결과를 기록한다. 현재 git 상태를 확인한 뒤 세 파일을 rename으로 이동한다. 테스트 내용은 수집 경로 외에는 수정하지 않는다.
1. [Testing Guide](../../docs/development/testing.md)의 optional SDK 단일 테스트 명령을 새 경로로 갱신한다. 현재 사용자를 새 파일로 안내하는 PR #251 Inbox 링크도 갱신하되, 과거 revision의 경로·실행 결과를 기술한 기록은 역사적 근거로 보존하거나 해당 SHA에 고정한다. 다른 PR의 Inbox를 일괄 재작성하지 않는다.
1. [CI selector](../../.github/workflows/classify_changes.sh)의 `--stdin` 입력으로 새 두 `.py` 경로와 fixture 경로가 모두 `tests/review_ai`를 선택하는지 다시 확인한다. 기준 revision에서는 이 결과를 확인했다. 분류기가 그대로 동작하면 workflow나 selector를 수정하지 않는다.
1. 이동 후 수집된 test case와 marker가 이동 전과 같은지 비교하고, 새 경로의 두 module·상위 public-surface/live-harness test 및 `tests/review_ai tests/runtime_ai`를 실행한다. Golden JSON 비교가 같은 fixture를 읽는지 확인한다. 선택 SDK 검증은 새 경로의 test node에서 별도로 실행하며, 기본 CI의 기존 skip을 이 이동의 실패나 성공으로 오해하지 않는다.
1. 변경 Markdown·Inbox 검사, `git diff --check`와 PR의 prospective merge CI를 확인한다. Git rename diff에서 의도치 않은 assertion·fixture 값·marker 변경이 없는지 검토한 뒤 PR 본문과 review evidence를 새 head 기준으로 다시 판정한다.

## Acceptance And Boundary

- 이동 전후 pytest 수집 case와 marker가 같고, golden comparison의 기대 JSON과 digest가 유지된다.
- 새 중첩 경로와 fixture 변경이 CI에서 Review AI suite를 선택하며, 경로가 바뀐 직접 실행 명령과 현재 탐색 링크가 유효하다.
- Source review 이후 test path가 바뀌므로 기존 독립 review와 CI를 새 head의 결과로 자동 승격하지 않는다. 기계적 이동 범위를 확인하고 필요한 focused review·CI를 다시 수행한다.
- 이번 계획은 테스트 배치만 다룬다. Langfuse SDK의 CI 설치/skip 정책, 원격 ingestion, human 평가, OpenSpec 행동 계약은 [CI skip 보고서](08-report-review-ai-langfuse-ci-skip-tradeoffs.md)와 각 owner의 별도 판단으로 남긴다.

PR #251이 여전히 Draft이고 인간 review 전이라면 같은 리팩터링 변경으로 묶을 수 있다. 이미 인간 review가 시작됐거나 이 이동이 병합 판단을 불필요하게 지연시키면 별도 후속 PR로 전달한다. 이 계획서는 구현이나 Ready·병합 권한을 부여하지 않는다.

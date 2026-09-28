---
type: research
title: Review AI Evaluation Test Layout Research
description: 평가 테스트를 하위 디렉터리로 옮길 때 기존 테스트 설계와 검증 근거가 유지되는지 조사한다.
---

# Review AI Evaluation Test Layout Research

> [!NOTE]
> `test_utility_evaluation.py`, `test_langfuse_projection.py`와 golden fixture는 evaluation 계약이라는 소유 범위로 묶을 수 있다. 변경의 검증 초점은 새 시나리오 추가가 아니라 기존 52개 case, marker, 독립 oracle과 외부 경계의 보존이다. 실제 이동 후 수집·실행은 아직 확인하지 않았다.

## Question

PR #251의 평가 테스트를 `tests/review_ai/evaluation/`으로 묶을 때 무엇을 함께 옮기고, 어떤 테스트 설계 근거를 보존해야 하는가?

## Scope

- PR #251의 [OpenSpec tasks](../../../openspec/changes/review-ai-evaluation-subdomain-refactor/tasks.md), [test design guide](../../../docs/development/test-design.md), [기존 테스트 설계 리뷰](../07-review-review-ai-evaluation-test-design.md)와 현재 테스트 파일을 대조했다.
- 테스트 배치, oracle, marker, 경로 소비자와 CI 선택만 조사했다. 새 behavior나 Langfuse CI 정책은 결정하지 않는다.

## Findings

### Evaluation Tests Share An Owner

[평가 계약 테스트](../../../tests/review_ai/test_utility_evaluation.py)는 `review_ai.evaluation`의 공개 API, rubric, comparison, digest와 fail-closed behavior를 검증한다. [Langfuse projection 테스트](../../../tests/review_ai/test_langfuse_projection.py)는 같은 하위 도메인의 선택 adapter, annotation, child process와 failure/isolation 경계를 검증한다. 두 module은 각각 `evaluation/value.py`와 `evaluation/langfuse.py`에 대응하며, 기존 수집 결과는 합계 52개 case다. 이 공통 소유 범위가 새 test area를 만드는 근거다. 단순한 `src/` 디렉터리 복제가 근거는 아니다.

[Root 공개 API 테스트](../../../tests/review_ai/test_public_surface.py)와 [live harness 테스트](../../../tests/review_ai/test_live_harness.py)는 평가 package 내부만의 계약을 소유하지 않는다. 따라서 두 파일을 같은 이동 단위로 취급할 근거는 없다.

### Golden Fixture Is An Independent Oracle

`test_comparison_json_matches_pre_refactor_golden`은 [고정 JSON](../../../tests/review_ai/fixtures/utility_comparison_6e64cc7.json)의 전체 serialized comparison을 비교한다. 이 fixture는 pre-refactor revision에서 캡처했으며 current model로 expected 값을 재생성하지 않았다는 [완료 보고서](../01-report-review-ai-evaluation-subdomain-completion.md)의 근거가 있다. Test는 `Path(__file__).with_name("fixtures")`로 파일을 읽으므로 test와 fixture를 같은 상대 구조로 이동하면 oracle의 내용은 바꿀 필요가 없다. Fixture byte나 expected JSON을 수정하면 단순 재배치라는 전제가 깨진다.

### Test Levels And Evidence Limits Remain Distinct

평가 계약 module은 `unit` marker를 공유한다. Langfuse module에는 `unit`, `component`, `integration` marker가 함께 있다. 선택 SDK media test는 기본 CI에서 `langfuse` 부재로 skip되며, [CI skip 보고서](../08-report-review-ai-langfuse-ci-skip-tradeoffs.md)는 이를 원격 수집이나 SDK 동작의 성공 근거로 취급하지 않는다. 경로 변경만으로 skip 정책이나 검증 의미가 바뀌지는 않는다.

현재 [CI selector](../../../.github/workflows/classify_changes.sh)에 새 두 `.py` 경로와 fixture 경로를 `--stdin`으로 넣으면 `tests=true`, `targets=tests/review_ai`가 나온다. 이는 분류 가능성의 사전 근거이며, 실제 이동 commit의 prospective merge CI 결과를 대신하지 않는다.

### Direct Links Need Revision Context

[Testing Guide](../../../docs/development/testing.md)의 선택 SDK 단일 테스트 명령은 현재 경로를 직접 쓴다. PR #251의 [01 완료 보고서](../01-report-review-ai-evaluation-subdomain-completion.md), [07 테스트 설계 리뷰](../07-review-review-ai-evaluation-test-design.md), [08 CI skip 보고서](../08-report-review-ai-langfuse-ci-skip-tradeoffs.md)도 이동 대상 파일에 상대 링크를 둔다. 이전 검증 revision을 설명하는 링크와 앞으로 실행할 명령은 다른 목적이므로 같은 방식으로 일괄 치환하면 provenance가 흐려진다.

## Implications

수집 비교에서는 파일 경로가 달라지는 pytest node ID를 그대로 비교할 수 없다. 파일 경로를 매핑한 뒤 함수명·parameter ID와 marker를 대조해야 한다. 테스트 배치와 문서 경로 수정의 실행 순서, CI와 review 근거 갱신은 [improvement plan](02-plan-improvement.md)이 소유한다.

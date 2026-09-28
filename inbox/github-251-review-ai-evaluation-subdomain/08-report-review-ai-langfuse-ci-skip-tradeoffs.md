---
type: report
title: Langfuse Media Test CI Skip and Trade-offs
description: PR #251 CI에서 건너뛴 Langfuse SDK 테스트의 의미와 CI 포함 선택지를 검토한다.
---

# Langfuse Media Test CI Skip and Trade-offs

## Decision

**이 테스트는 CI에서 실행하기에 적절하지만, 현재 PR #251의 병합을 막는 필수 검증으로 소급하지는 않는다.** 외부 서비스 없이 고정된 SDK 버전의 media 처리 동작을 확인할 수 있어, 필요하다면 관련 변경에만 실행하는 집중 CI 검사가 합리적이다. 현재의 `1 skipped`는 실패가 아니라 **CI에서 해당 SDK 동작을 확인하지 못했다**는 뜻이다.

## Current Evidence

- **Revision:** PR #251 head `957b29341ed0f9abb35608aa6cdeb54670fb41cf` 기준 [CI Lite run 36371778842](https://github.com/mols3131d/hmda-data-reliability/actions/runs/36371778842)는 `186 passed, 1 skipped`로 성공했다.
- **Skipped test:** [`test_pinned_langfuse_media_processor_keeps_data_uri_when_disabled()`](../../tests/review_ai/test_langfuse_projection.py)은 `langfuse._task_manager.media_manager`를 `pytest.importorskip()`으로 가져온다. CI 로그의 skip 사유는 `No module named 'langfuse'`다.
- **Cause:** [CI Lite](../../.github/workflows/ci-lite.yml)는 `uv sync --locked`를 실행한다. `langfuse==4.15.6`은 [`pyproject.toml`](../../pyproject.toml)의 선택 의존성이라 기본 동기화에 포함되지 않는다.
- **Observable contract:** 테스트는 `LANGFUSE_MEDIA_UPLOAD_ENABLED=false`에서 SDK의 media processor에 data URI를 전달해 output이 그대로 남고 media upload queue가 비어 있는지 확인한다. Dummy client를 사용하므로 실제 Langfuse endpoint나 credential은 필요하지 않다. 이 검사는 exporter의 원격 수집, UI 표시 또는 human annotation을 증명하지 않는다.

## Trade-offs

| Option | Benefit | Cost and Limit |
| --- | --- | --- |
| 현재처럼 명시적 skip 유지 | 기본 CI의 설치 범위와 실행 시간이 늘지 않는다. 다른 `186`개 테스트와 과거 local SDK 검증 근거를 유지한다. | SDK media 동작의 회귀를 PR CI에서 발견하지 못하며, skip을 통과로 오해할 수 있다. |
| 관련 변경에만 SDK 선택 의존성을 설치하고 이 테스트 실행 | 실제 고정 SDK에서 exact data URI 보존을 pre-merge로 검증한다. 네트워크 서비스와 secret은 필요 없다. | SDK 다운로드·설치와 캐시 관리 비용이 늘어난다. 테스트가 SDK의 private module/method에 결합돼 있어 의도적인 SDK 업그레이드에도 함께 수정해야 할 수 있다. 이 검사는 여전히 원격 ingestion proof가 아니다. |
| 실제 Langfuse endpoint까지 CI에서 호출 | 원격 전송 경계까지 확인할 수 있다. | Credential, 외부 상태, 네트워크 지연과 실패 가능성이 생긴다. 현재 media 보존 테스트의 목적보다 범위가 크며 human utility proof도 대신하지 못한다. |

## Recommendation

CI coverage를 높이기로 결정한다면 **관련 adapter·test 또는 SDK pin/lock 변경에만 선택 의존성을 설치하는 별도 집중 검사**를 권장한다. 그 경로에서는 SDK 설치 실패나 누락을 skip 성공으로 남기지 않고 검사 실패로 드러내야 한다. 모든 PR의 기본 dependency set에 SDK를 추가하거나 원격 Langfuse 서비스를 merge gate로 만들 필요는 없다.

현재 #251의 [테스트 설계 리뷰](07-review-review-ai-evaluation-test-design.md)는 이 skip을 투명한 검증 한계로 기록하고, 현재 refactor의 required finding으로 분류하지 않았다. CI 확대 여부는 별도 CI 변경으로 결정할 수 있다. 이 보고서는 설계 판단 근거이며 workflow나 테스트를 수정하지 않는다.

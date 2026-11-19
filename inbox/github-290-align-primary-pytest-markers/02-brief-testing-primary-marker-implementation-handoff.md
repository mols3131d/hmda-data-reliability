---
type: brief
title: "Primary Marker Implementation Handoff"
description: "PR #290의 pytest 마커 수정, 수집 및 실행 검증 결과와 원격 검증 위치를 기록한다."
---

# Primary Marker Implementation Handoff

PR #290의 두 마커 충돌을 수정했다. 전체 수집에서 1,229개 항목이 각각 정확히 하나의 primary marker를 가진다. 코드 변경은 `f470e5061fee9ecff12170e8f662a7c62295af39`에 있다.

## Scope and Decisions

- 소유 브랜치는 `agent/test/align-primary-pytest-markers`다. 변경 전 수집은 PR head `505b0992b255f35b508bde1aba04ab5d608fb01c`에서 실행했다.
- `test_delegated_task_reports_real_backfill_and_domain_approval_block`은 실제 DuckDB 파티션, 승인과 복구 실행을 연결하므로 `integration`으로 분류했다.
- `test_native_sdk_records_sibling_generations_and_tool_history`는 모의 provider transport에서 실제 Langfuse SDK의 로컬 trace와 redaction을 검증하므로 `component`로 분류했다.
- 두 모듈의 공통 마커를 함수별로 명시해 파일과 pytest node ID를 보존했다. Primary marker 선언을 제외한 AST가 동일해 fixture, assertion과 나머지 데코레이터도 보존됐음을 확인했다.

## Evidence

| Check | Result |
| --- | --- |
| 전체 수집 및 `item.iter_markers()` | 변경 전 중복 2개, 변경 후 중복과 미표식 0개. 수집 전후 같은 1,229개 node ID를 확인. |
| `-m '<level> and not memory and not stress'` | `unit` 379 → 378, `component` 647 → 647, `integration` 205 → 204. 두 항목의 중복 선택만 제거. |
| Resource marker | 자원 필터를 끈 수집에서 `memory`와 `stress` 항목이 전후 0개. |
| 테스트 실행 | 두 수정 사례 2개와 `tests/reliability_ai` 167개 통과. |
| 정적 검사와 독립 검토 | Ruff lint·format과 CI 범위의 `ty check` 통과. 두 관점의 독립 검토에서 필수 수정 사항 없음. |

## Continuation

전체 실행 결과와 최신 검증 상태는 PR 본문에서 확인할 수 있다. CI Lite는 해당 실행의 prospective merge에 연결된다. Ready 전환과 merge는 사람의 결정이다. [PR #290](https://github.com/mols3131d/hmda-data-reliability/pull/290), [Checks](https://github.com/mols3131d/hmda-data-reliability/pull/290/checks)

변경 전 판단과 검증 명령은 준비 단계 문서에 있다. [Research](00-research-testing-primary-marker-accuracy.md), [Plan](01-plan-testing-primary-marker-selection.md), [Preparation Self-Review](03-review-testing-primary-marker-pr-preparation.md)

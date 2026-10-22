---
type: review
title: PR #268 Malformed Lineage Graph Multi-Perspective Review
description: PR #268의 dbt graph container 구조 검증과 empty-impact 오류 방지를 다관점으로 검토합니다.
tags:
  - domain:reliability
  - capability:reliability-impact-analysis
---

# PR #268 Malformed Lineage Graph Multi-Perspective Review

> [!IMPORTANT]
> **Blocked** — 확인된 필수 수정 finding은 없습니다. `nodes`·`sources`의 비-object graph container를 명시적으로 거부하므로 malformed graph의 false empty-impact success 경로를 막습니다. 별도 독립 specialist 검토 증거를 이번 세션에서 검증하지 못했습니다.

- **Target** — [PR #268](https://github.com/mols3131d/hmda-data-reliability/pull/268)
- **Revision** — base `34519fec148dd2ab38ddf0cc0157c3d3ed9f7247` / reviewed head `d6adddf534a17619179bad7b5ff85fb2f944820d`
- **Scope** — dbt manifest `nodes`/`sources` container 처리, 공개 impact analyzer failure, 정상 빈 graph, 기존 traversal·artifact failure 및 테스트·CI.

## Findings

현재 승인된 변경 범위에서 확인된 `current_required` finding 없음. 코드 관점 assessment: `clear`; 최종 독립-review gate: `blocked` (separate specialist coverage 미검증). 잠재 위험은 아래 Candidate Decisions와 Risks and Limits에서 분리합니다.

## Perspectives

| Perspective | Reviewer / Method | Focus | Assessment and Evidence |
| --- | --- | --- | --- |
| Correctness | 동일 세션, manifest→result 추적 | graph container shape와 typed failure | [manifest parser](../../src/hmda_reliability/reliability/impact/manifest.py)의 `_resources`가 `nodes`와 `sources`를 반복 검사하여 non-dict면 field명을 포함한 `ImpactAnalysisError`를 발생 |
| Adversarial | 동일 세션, 손상 payload 반례 검토 | null/array/string/number/boolean, omission | 검증을 `manifest.get(field,{})`에 적용하므로 명시된 null은 거부하고 생략 필드는 기존 empty-object 의미로 처리 |
| Evidence/Regression | 동일 세션, tests·CI 검토 | 정상 empty, traversal, missing artifact | [회귀 테스트](../../tests/reliability/test_impact_analysis.py)는 양 컨테이너 각각 5가지 malformed 값, 4가지 빈 graph와 missing manifest를 검사; 기존 graph traversal 테스트 유지 |

## Candidate Decisions

| ID | Perspectives | Candidate | Decision | Rationale | Finding |
| --- | --- | --- | --- | --- | --- |
| C1 | Correctness, Adversarial | malformed container가 무시되어 affected assets가 빈 정상 결과로 반환됨 | Drop | 검증되지 않은 object 외 값은 `_resources`에서 `ImpactAnalysisError`로 fail-closed; 새 테스트 10개가 공개 analyzer 호출에서 error를 검증 | — |
| C2 | Adversarial | 누락된 container도 무조건 손상 데이터로 간주해야 함 | Drop | Scope boundary와 기존 동작은 누락된 graph를 빈 object 기본값으로 허용; 새 테스트에서 omission/one-only/both-empty 성공 확인 | — |
| C3 | Adversarial | graph 내부 node value가 dict가 아니어도 필터링됨 | Drop | 이 로직은 변경 전부터 존재하며 이번 PR 범위는 top-level `nodes`/`sources` container 검증. Edge/resource-level schema 강화는 별도 요구/작업으로 분리해야 함 | — |

같은 세션에서 **1차 계약·구현 확인 → 2차 반례·회귀·운영 경계 재검토 → 후보 재판정** 순으로 수행했습니다. 서로 다른 관점은 서로 독립된 subagent 실행을 의미하지 않습니다. `Drop`은 반례 무효화, 기존 safeguard 확인 또는 본 PR의 승인 범위 밖임을 뜻합니다. `Open`은 해결로 간주하지 않습니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | parser·정본 대조 | [`manifest.py`](../../src/hmda_reliability/reliability/impact/manifest.py)와 [impact analysis contract](../../openspec/specs/reliability-impact-analysis/spec.md) |
| ✅ Pass | 오류·빈 graph 테스트 설계 검토 | [`test_impact_analysis.py`](../../tests/reliability/test_impact_analysis.py)에서 malformed 10 조합, 정상 빈 4 조합, missing manifest regression 확인 |
| ✅ Pass | 원본 HEAD CI Lite | [Run 39142538760](https://github.com/mols3131d/hmda-data-reliability/actions/runs/39142538760) `check=success` |
| ⚪ Not Verified | pytest 직접 재실행 | 이 세션에서 로컬 테스트 실행하지 않음 |
| ⚪ Not Verified | 독립 specialist coverage | PR 본문의 과거 DualVantage 완료 진술은 확인했으나 분리 실행을 이번 리뷰의 근거로 대체하지 않음 |

## Risks and Limits

- Resource map의 내부 node-value 유형 검증은 원래대로 dict 아닌 값을 건너뜁니다. 이번 PR의 명시적인 container-shape 수정 범위 밖이며, 후속 요구가 없으면 merge blocker로 취급하지 않습니다.
- **Next:** 독립 증거 확인과 인간 리뷰 후 병합 판단. 결과가 바뀌는 추가 코드 수정은 현재 발견되지 않았습니다.

이 보고서는 비정본 리뷰 산출물입니다. 본문에 기록된 원본 HEAD 이후 보고서 커밋이나 후속 PR 병합으로 검증 state가 바뀌면 review readiness와 CI를 새 revision 기준으로 다시 판단해야 합니다.

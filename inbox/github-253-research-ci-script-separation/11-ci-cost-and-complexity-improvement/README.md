---
type: campaign
title: CI Cost and Complexity Improvement
description: PR 253의 F1 전달·검증과 F2 비용 측정 결과를 연결하고 추가 개선 또는 PR 검토의 판단 경계를 안내한다.
tags:
  - ci
  - testing
  - optimization
---

# CI Cost and Complexity Improvement

[CI 비용·복잡성 보고서](../06-review-ci-cost-and-complexity.md)의 F1~F4를 후속 작업으로 다루는 11번 번들이다. [PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253)의 branch `agent/research-ci-script-separation`이 소유한다. F1은 commit `ec81d5d`로 전달했고 CI·본문도 확인했다. 2026-10-05 재개 작업에서는 F2 cold/warm 측정을 완료했다. 비용 결과와 현재 환경 유지 권고는 [F2 Measurement](research.md#f2-measurement)가 소유한다.

## Start Here

| Need | Document |
| --- | --- |
| F1 과거 근거와 F2 실측·한계·환경 유지 권고 확인 | [Research](research.md) |
| 수정 순서, 회귀 검사와 단계별 완료·중단 조건 확인 | [Plan](plan.md) |
| 추가 개선 또는 PR 검토의 다음 판단 확인 | [Next Session](#next-session) |

F1 구현과 F2 초기 측정은 완료됐다. 이후 사용자 요청에 따라 전체 PR 독립 리뷰에서 확인한 root blob lock 호환성 한 건을 로컬 보완·검증했다. 해당 근거와 미전달 상태는 [Merge Preparation](../08-agent-routes-skills-lock-compatibility/02-report.md#2026-10-05-merge-preparation)이 소유한다. F1 검증 근거는 [Execution Record](plan.md#execution-record)에 있으며 다시 구현하지 않는다. F3는 선택 항목이고 F4는 기존 매핑과 테스트를 함께 유지하는 원칙이다.

## Next Session

원래 다음 작업일로 적은 2026-10-06을 기다리지 않고 2026-10-05 사용자 재개 요청으로 F2 측정을 진행했다. 측정 결과는 로컬 문서이며 아직 commit·push나 PR 본문에는 반영하지 않았다.

1. 추가 작업 전 PR #253의 최신 base/head·CI·본문을 재조회한다. 재개 시 확인한 head는 `ec81d5d`, CI는 success이며 review readiness는 `ready`였다. 문서가 바뀐 로컬 상태까지 전달·검증된 것으로 읽지 않는다. 기존 10번 제안서의 옛 실패·미푸시 표현은 historical snapshot이다.
1. 기본 경로는 전체 환경 유지와 현재 PR의 사람 검토다. Ready 전환·승인·merge와 이번 로컬 문서의 delivery는 별도 요청을 따른다. F2 측정 결과 자체는 PR 완료 blocker가 아니다.
1. 환경 비용 개선을 계속할 경우 [F2 Decision Gate](research.md#decision-gate-remains-open)를 기준으로 기존 Actions의 cache hit/miss·복원 비용과 작은 환경의 검증 동등성 비교 범위를 먼저 제안한다. 새로운 환경·lock·cache 체계나 F3 조건을 자동 구현하지 않는다.

추가 비용 조사를 선택할 때의 재개 요청:

> 11번 번들의 F2 Measurement를 기준으로 다음 개선의 실익을 조사해. 기존 Actions의 cache hit/miss·복원 비용부터 확인하고 작은 환경 비교의 범위를 제안해. 구현·commit/push·Ready 전환·승인·merge는 별도 요청 전에는 하지 마.

## Boundary

이 번들은 non-canonical working artifact다. [현재 CI 계약](../../../docs/development/ci/README.md)을 대체하지 않으며, 이전 보고서의 follow-up을 PR 완료 blocker로 바꾸지 않는다. 기존 PR 마무리는 [완료 제안서](../10-proposal-ci-pr-completion-next-actions.md)의 별도 작업이다.

F2 측정 자체에서는 source·test·workflow·dependency·별도 환경을 바꾸지 않았다. 이후 병합 전 준비 요청은 기존 승인 범위의 필수 parser 보완과 회귀 검증만 로컬에서 수행한다. 환경 분리·F3는 도입하지 않으며, 이전 delivery 승인을 추가 commit·push·본문 갱신이나 PR lifecycle 변경 권한으로 확대하지 않는다. 로컬 비용·실행 수를 Actions 성능·과금 절감으로 일반화하지 않는다.

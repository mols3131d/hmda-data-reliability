---
type: campaign
title: CI Cost and Complexity Improvement
description: PR 253의 F1 구현·검증 기록과 다음 세션의 PR 상태 확인·F2 비용 측정 순서를 안내한다.
tags:
  - ci
  - testing
  - optimization
---

# CI Cost and Complexity Improvement

[CI 비용·복잡성 보고서](../06-review-ci-cost-and-complexity.md)의 F1~F4를 후속 작업으로 다루는 11번 번들이다. [PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253)의 branch `agent/research-ci-script-separation`이 소유한다. F1의 제한적 중복 제거는 구현·로컬 검증·독립 리뷰까지 완료했다. 2026-10-05 사용자가 오늘 변경의 commit·push와 PR 본문 갱신을 승인했으며, 실제 전달 revision과 CI는 최신 PR에서 확인한다.

## Start Here

| Need | Document |
| --- | --- |
| 현재 구현에서 개선 후보가 성립하는지, 무엇이 미측정인지 확인 | [Research](research.md) |
| 수정 순서, 회귀 검사와 단계별 완료·중단 조건 확인 | [Plan](plan.md) |
| 내일 이어갈 작업과 재개 요청 확인 | [Next Session](#next-session) |

다음 비용 작업은 **F2 환경 비용 측정**이다. F1 검증 근거는 [Execution Record](plan.md#execution-record)에 있으며 F1을 다시 구현하지 않는다. F3는 낮은 우선순위의 선택 항목이고 F4는 기존 매핑과 테스트를 함께 유지하는 원칙이다. 세부 범위와 조건은 계획서가 소유한다.

## Next Session

2026-10-06 작업 재개 시 다음 순서를 따른다. 이 목록은 오늘의 미전달 상태를 고정하지 않으며 실제 Git·PR 상태를 먼저 재조회한다.

1. PR #253의 최신 base/head, 오늘 전달된 F1 commit, prospective merge CI와 본문의 revision·Validation을 대조한다. CI가 실패했거나 base/head가 바뀌었다면 그 상태의 검증부터 확인한다. 변경이 없으면 완료된 F1 구현·독립 리뷰를 반복하지 않는다.
1. 현재 변경의 review readiness를 보고한다. Draft는 유지하며 Ready 전환·승인·merge는 사람의 별도 판단에 맡긴다. 기존 10번 제안서의 미푸시 표현과 옛 CI 실패는 historical snapshot이며 현재 blocker로 재사용하지 않는다.
1. [계획의 F2 측정](plan.md#3-measure-f2-before-splitting-the-environment)을 진행한다. 기존 Actions 자료부터 확인하고 부족하면 같은 revision·lock·runtime의 격리된 checkout·새 venv·분리된 cache에서 cold/warm을 반복 측정한다. 주 `.venv`와 공유 cache는 지우지 않는다.
1. 조건·표본 수·시간 범위·cache 근거·실패와 unknown을 같은 번들에 기록하고 환경 분리의 실익을 보고한다. 로컬 결과를 Actions 성능이나 과금 절감으로 일반화하지 않는다. 측정만으로 환경 분리, 새 lock/cache 체계나 F3 build 조건을 구현하지 않는다.

재개 요청은 다음처럼 하면 된다.

> 11번 번들의 Next Session을 진행해. 최신 Git·PR 상태와 F1 전달 결과를 먼저 확인하고, 문제가 없으면 F2 cold/warm 환경 비용 측정까지만 수행해. 환경 분리·F3 구현·추가 commit/push·Ready 전환·승인·merge는 별도 요청 전에는 하지 마.

## Boundary

이 번들은 non-canonical working artifact다. [현재 CI 계약](../../../docs/development/ci/README.md)을 대체하지 않으며, 이전 보고서의 follow-up을 PR 완료 blocker로 바꾸지 않는다. 기존 PR 마무리는 [완료 제안서](../10-proposal-ci-pr-completion-next-actions.md)의 별도 작업이다.

오늘 전달 대상은 기존 PR branch의 F1 workflow·script·회귀 테스트, 관련 설명과 이 번들이다. Dependency·별도 환경 도입과 비용 benchmark는 포함하지 않는다. 오늘의 commit·push·본문 갱신 승인을 다음 세션의 추가 delivery나 PR lifecycle 변경 권한으로 확대하지 않는다. 실행 수 감소를 시간·과금 절감으로 일반화하지 않는다.

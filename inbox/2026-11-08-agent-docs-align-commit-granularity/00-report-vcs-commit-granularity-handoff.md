---
type: report
title: Commit Granularity Alignment Handoff
description: 갱신된 세션 복구 패턴의 커밋 단위 기준을 기존 커밋 정책에 반영하기 위한 차이 분석과 구현 인계.
tags:
  - git
  - commit-granularity
  - session-recovery
---

# Commit Granularity Alignment Handoff

## Status And Goal

**현재는 구현 인계 준비 단계다.** 정본 정책은 아직 수정하지 않았다. PR의 최종 목표는 갱신된 패턴을 검토해 필요한 기준을 `commit.md`에 **구현하고 현재 revision 기준 검증까지 완료**하는 것이다. 보고서 작성만으로 완료 처리하지 않는다.

- 작업 브랜치: `agent/docs/align-commit-granularity` (`main` 기준 `7efb332c2efd78f77ee724440e28285ebb3ee55f`).
- 적용 근거: [Session Recovery Checkpoint Commits](https://github.com/mols3131d/mols-agent-assets/blob/fa5be3bd63e9c29c30017b9e8c833018c092b9a7/catalog/patterns/workflow/session-recovery-checkpoint-commits.md)의 `Commit Granularity`.
- 정본 변경 대상: [`docs/development/vcs-git/commit.md`](../../../docs/development/vcs-git/commit.md). 메시지 형식의 owner는 [`.gitmessage`](../../../.gitmessage)다.

## Gap Assessment

기존 `Change Unit`·`Staging`은 하나의 목적에 속한 spec·문서·test·구현을 묶고 무관한 변경을 분리하도록 이미 규정한다. `Session Recovery`는 강제 체크포인트와 미완료 작업의 완료 위장을 금지하며, `History`는 무단 공개 이력 재작성을 금지한다. 이 기반은 유지한다.

갱신된 패턴에서 추가 반영할 차이는 다음과 같다.

1. **큰 변경의 분할 기준:** 한 PR·작업이 여러 commit을 가질 수 있고, 큰 변경은 검토·검증 가능한 의미 있는 하위 단위로 나눈다는 기준이 현재 문서에는 명확하지 않다. 줄 수·파일 수·세션 길이로 고정 분할하지 않는다.
1. **체크포인트 시점과 상태:** 의미 있는 진척 또는 인계 필요를 기준으로 commit할 수 있다. 세션 종료만을 이유로 강제하지 않으며, 미완료 체크포인트는 작업 브랜치에서 미검증 범위를 분명히 해 통합 가능한 완료 결과로 오인되지 않도록 한다.
1. **커밋 재구성의 경계:** 검토 편의를 위한 분할·통합·재배열은 가능하더라도, 게시·공유된 이력에는 기존 프로젝트의 사용자 승인·다른 참여자 보호 규칙이 우선한다. 기존 `History`를 완화하지 않는다.

패턴의 메시지·복구·기밀성 등 나머지 내용은 앞선 PR #286의 `commit.md`와 `.gitmessage`에 대부분 반영되어 있다. 이를 중복 추가하지 않는다.

## Implementation Scope

- `commit.md`의 `Change Unit`과 필요시 `Staging`·`Session Recovery`를 **최소 수정**해 묶기/나누기/체크포인트 기준을 함께 읽히게 만든다. `History`는 이미 충분한지 먼저 확인하고 불필요한 반복을 추가하지 않는다.
- 짧고 직접적인 정책 표현을 우선한다. 새 section·상세 표·고정 임계값·예외적인 절차를 만들어 복잡도를 높이지 않는다.
- `.gitmessage`는 이미 선택적 본문과 검증 한계·후속 조건 힌트를 제공하므로 **기본적으로 변경하지 않는다**. 새 요구가 발견되면 필요성·scope를 먼저 검증한다.
- 새 Skill·Hook·CLI·CI·자동 커밋 강제·고정 체크포인트 간격, 기존 브랜치 이력 변경은 범위 밖이다.

## Acceptance Scenarios

구현 후 다음 사례에서 오해 없이 결정을 내릴 수 있는지 검토한다.

1. **한 목적의 작은 변경:** 구현·회귀 테스트·필요한 문서는 함께 묶을 수 있다. 파일마다 분리하지 않는다.
1. **큰 변경:** 하나의 PR 안에서도 검토·검증 가능한 하위 변경 목적별로 commit을 분할할 수 있다. 인위적인 줄 수 기준은 없다.
1. **무관한 변경:** 본 작업과 독립적인 로깅 정리는 별도 commit으로 분리한다.
1. **세션 단절:** 의미 있는 진척이 없으면 종료만으로 checkpoint commit을 강제하지 않는다.
1. **미완료 체크포인트:** 작업 브랜치의 미검증·미완료 범위를 숨기지 않으며 통합 준비 완료로 주장하지 않는다.
1. **이력 정리:** 미공유 작업에서 재구성을 검토할 수 있으나, 공개·공유된 이력의 amend/rebase/force-push는 명시적 허가 없이 수행하지 않는다. Squash 후 중간 commit 정보가 사라질 수 있다는 기존 경고를 유지한다.
1. **기존 복구 기능:** 메시지 본문의 선택성, 실제 검증 결과·한계, 원격 ref, 타 작업자 변경 보호, 계정·서명 안전 경계는 유지한다.

## Handoff Actions

1. 이 브랜치와 PR head를 최신 상태로 조회하고, 위 패턴 revision 및 현행 `commit.md`를 대조한다. 패턴은 참고 근거이며 프로젝트 Git 규약을 자동으로 대체하지 않는다.
1. 위 scope에만 정책 수정안을 적용하고 각 acceptance scenario를 정책 문장에 대조해 자체 리뷰한다. 실제 diff에 없는 개선을 완료로 주장하지 않는다.
1. 적용되는 Markdown 검증과 GitHub check를 **구현 후 최신 head**에서 확인한다. 수행하지 못한 검증은 `Not Verified`로 남기고 PR의 `Validation`을 갱신한다.
1. 변경 범위·계정 귀속·공개 이력 안전성·병합 가능 상태를 확인하고 인간 검토에 인계한다. 명시적 요청 없이 Ready 전환, 승인, merge 또는 이력 재작성은 수행하지 않는다.

## References

- [Source pattern — pinned revision](https://github.com/mols3131d/mols-agent-assets/blob/fa5be3bd63e9c29c30017b9e8c833018c092b9a7/catalog/patterns/workflow/session-recovery-checkpoint-commits.md)
- [Commit policy](../../../docs/development/vcs-git/commit.md)
- [Pull Request policy](../../../docs/development/vcs-git/pull-request.md)
- [Previous improvement PR #286](https://github.com/mols3131d/hmda-data-reliability/pull/286)

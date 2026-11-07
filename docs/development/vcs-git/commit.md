---
title: "Commits"
description: "하나의 논리적 변경을 review 가능한 history로 기록하기 위한 commit 단위, staging과 history 관리 기준을 정의합니다."
categories:
  - software-engineering
tags:
  - git
---

# Commits

Commit은 검토 가능한 하나의 논리적 변경을 기록한다. 메시지 형식·type·길이·언어는 [`.gitmessage`](../../../.gitmessage)가 소유한다.

## Change Unit

Commit은 파일·줄 수·세션 길이보다 함께 이해·검토할 수 있는 변경 목적을 기준으로 구성한다. 같은 목적의 spec·문서·test·구현은 묶고 무관한 변경은 분리한다.

큰 작업이나 PR은 검토·검증 가능한 하위 단위별로 여러 commit으로 나눌 수 있다. 파일·요청별로 기계적으로 분할하지 않는다.

## Staging

논리적 변경 단위로 stage하고, 다른 목적의 변경은 별도 commit으로 분리한다.

## Session Recovery

의미 있는 진척이나 인계가 필요할 때 체크포인트 commit을 남길 수 있다. 세션 종료만으로 강제하거나 복구만을 위해 변경을 억지로 분할하지 않는다.

미완료 체크포인트는 작업 브랜치에 남기고, 메시지·PR·작업 기록에 미완료·미검증 범위를 명시해 통합 가능한 완료 상태로 오인되지 않게 한다.

메시지는 변경 이유를 중심으로 작성한다. 본문에는 diff·PR·작업 기록만으로 알기 어려운 중요 판단, 실제 검증 결과·한계, 다음 확인 조건만 필요할 때 덧붙인다. 중복 내용, 미실행 검사의 통과 주장, 자기 SHA의 사전 기재는 제외한다.

세션이나 작업자가 바뀌면 다음 순서로 재개한다.

1. Repository·branch/PR·working tree(staged/unstaged/untracked)를 확인하고 변경 소유권을 구분한다.
1. HEAD에 한정하지 않고 관련 commit의 메시지·diff를 찾아 이후 변경·현재 계약·작업 기록과 대조한다.
1. 과거 검증·계획은 당시 기록으로 취급하고 필요한 검증을 다시 수행한다. 타인의 변경을 덮어쓰지 않는다.

Commit으로 미커밋 로컬 상태를 복구할 수는 없다. 다른 환경에서 재개하려면 접근 가능한 원격 ref에 commit이 게시되어 있어야 한다. 공개 메시지에는 비밀정보·개인정보·비공개 내부 맥락을 남기지 않는다.

## History

Review가 시작된 공개 history는 인간의 명시적 요청 없이 rewrite하지 않는다. 필요하면 merge 시 squash할 수 있다.

Amend·rebase·squash merge·branch 삭제로 중간 commit 기록이 사라질 수 있다. 여러 commit의 진행 상태는 PR·작업 기록에, 장기 결정은 PR·정본 문서에 남긴다.

## Agent Instructions

- Commit 전 작업 범위·staged diff·실제 검증을 확인한다.
- 다중 Git 계정·명의 환경에서는 작성자·커미터·사용 계정·서명 설정을 확인한다.
- 사용자의 무관한 변경은 commit하거나 되돌리지 않는다.
- 명시적 요청 없이 amend·rebase·reset·force-push로 공개 history를 변경하지 않는다.

## Related

- [Branches](branch.md): commit이 속하는 변경 목적과 branch 기준
- [Pull Requests](pull-request.md): validation과 review 결과를 전달하는 기준

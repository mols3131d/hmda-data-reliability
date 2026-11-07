---
title: "Commits"
description: "하나의 논리적 변경을 review 가능한 history로 기록하기 위한 commit 단위, staging과 history 관리 기준을 정의합니다."
categories:
  - software-engineering
tags:
  - git
---

# Commits

Commit은 하나의 논리적 변경을 기록하고 review 가능한 history를 만든다.

Commit message의 형식, type, 길이와 언어는 [`.gitmessage`](../../../.gitmessage)를 canonical source로 사용한다.

## Change Unit

하나의 commit은 하나의 논리적 변경을 표현한다.

같은 목적의 spec, 문서, test와 구현은 함께 포함할 수 있다. File이나 요청 단위로 기계적으로 나누지 않으며, 관련 없는 변경은 포함하지 않는다.

## Staging

변경은 논리적 변경 단위로 stage한다. 같은 목적의 변경은 함께 포함하고, 다른 목적의 변경은 별도 commit으로 분리한다.

## Session Recovery

Commit은 독립적으로 검토 가능한 변경을 우선한다. 세션 복구만을 위해 변경을 억지로 나누거나 미완료 작업을 완료된 변경으로 포장하지 않는다.

Commit message에는 변경 이유를 우선 남긴다. Diff, 기존 본문, PR 또는 작업 기록만으로 알기 어려운 중요한 판단, **실제로 수행한 검증과 한계**, 다음 확인 조건이 있을 때만 본문에 보완한다. 자명하거나 중복되는 정보는 생략하고, 미실행 검사를 통과로 적거나 커밋 자신의 SHA를 메시지에 미리 적지 않는다.

세션이나 작업자가 바뀌어 재개할 때는 다음을 확인한다.

1. 올바른 repository, branch/PR과 현재 working tree(staged, unstaged, untracked)를 확인하고 기존 변경의 소유권을 구분한다.
1. 해당 작업과 관련된 commit의 메시지와 diff를 찾는다. 반드시 HEAD일 필요는 없으며, 이후 변경·현재 계약·작업 기록과 대조한다.
1. 과거의 검증과 계획은 당시의 근거로만 취급하고 현재 필요한 검증을 다시 수행한 뒤 다음 작업을 결정한다. 다른 작업자의 변경을 덮어쓰지 않는다.

Commit에 남지 않은 로컬 상태는 이 방식으로 복구할 수 없다. 다른 환경에서 재개할 commit은 접근 가능한 원격 ref에 게시되어 있어야 한다. 공개 메시지에는 비밀정보, 개인정보 또는 비공개 내부 맥락을 남기지 않는다.

## History

Review가 시작된 공개 history는 인간의 명시적 요청 없이 rewrite하지 않는다. History를 단순하게 유지할 필요가 있으면 merge 시 squash를 사용할 수 있다.

Amend·rebase·squash merge 또는 branch 삭제로 중간 commit의 메시지를 찾기 어려워질 수 있다. 여러 commit에 걸친 진행 상태는 PR·작업 기록에, 오래 보존할 결정은 PR·정본 문서에 둔다.

## Agent Instructions

- Commit 전 작업 범위와 staged diff, 실제 수행한 검증을 확인한다.
- 여러 Git 계정·명의가 연결된 환경에서는 commit 작성자·커미터, 사용 계정과 적용되는 서명 설정을 확인한다.
- 사용자가 만든 관련 없는 변경을 commit하거나 되돌리지 않는다.
- 명시적 요청 없이 amend, rebase, reset 또는 force-push로 공개 history를 변경하지 않는다.

## Related

- [Branches](branch.md): commit이 속하는 변경 목적과 branch 기준
- [Pull Requests](pull-request.md): validation과 review 결과를 전달하는 기준

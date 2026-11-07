---
type: plan
title: Commit Session Recovery Harness Improvement
description: 기존 Git 커밋 규약에 최소한의 재개 단서와 검증 기반 복구 절차를 추가하기 위한 구현 계획.
tags:
  - git
  - session-recovery
  - agent-harness
---

# Commit Session Recovery Harness Improvement

## Goal

의미 있는 커밋의 메시지와 Git 스냅샷에서 변경 이유, 실제 검증 범위와 다음 확인 지점을 저비용으로 복구할 수 있도록 커밋 하네스를 개선한다. **이 PR의 완료 기준은 계획 작성이 아니라 커밋 정책·템플릿 개선과 검증 완료**다.

## Baseline

- `docs/development/vcs-git/commit.md`는 논리적 변경 단위, staging, 공개 이력 보호와 에이전트 안전 경계를 소유한다.
- `.gitmessage`는 메시지의 type·형식·길이·언어와 선택적 body/footer를 소유한다.
- `.rulesync/skills/prj-vcs-git-github/SKILL.md`가 커밋 작업에서 위 문서를 이미 로드하므로 별도 Skill·라우터 신설은 필요하지 않다.
- PR의 검증·진행 정보는 `docs/development/vcs-git/pull-request.md` 및 기존 작업 아티팩트와 역할을 분리한다.

## Scope And Approach

1. **`commit.md` 개선:** 의미 있게 완결된 변경을 우선하며, diff·PR·본문에서 복구되지 않는 판단, 검증 한계, 후속 조건만 선택적으로 커밋 본문에 남기는 기준을 추가한다. 짧은 변경은 제목만 허용한다.
2. **재개 절차:** 저장소·작업 브랜치/PR·현재 working tree 및 소유권을 먼저 확인한다. HEAD만 가정하지 않고 관련 커밋의 메시지·diff를 찾아 이후 변경, 외부 계약과 대조한다. 과거 검증은 현재 사실로 승격하지 않으며 필요한 검증만 다시 수행한다. 다른 환경에서 복구할 커밋은 접근 가능한 원격 ref에 존재해야 한다.
3. **`.gitmessage` 보강:** 선택적 본문에 검증 범위·한계·다음 확인 지점을 자연스럽게 기록할 수 있다는 짧은 힌트만 추가한다. 기존 type, 길이, 언어, footer 제한을 보존한다.
4. **커밋 전 안전성:** 작업 목적과 staged diff를 검토하고 관련 없는 변경·미커밋 작업을 보호한다. 실행 주체의 GitHub 연결 계정 및 로컬 Git 작성자/커미터·서명 설정은 실제 실행 환경에서 확인하되, repository에 개인별 설정을 하드코딩하지 않는다.
5. **장기 지식의 소유권:** 다중 커밋의 계획·진행 상태와 영속적인 결정은 기존 PR, Inbox 또는 정본 문서가 소유한다. 커밋을 작업 일지나 별도 승인·위임 수단으로 만들지 않는다.

## Acceptance

- 간단한 변경에서는 제목만으로 유효한 커밋 메시지를 작성할 수 있다.
- 복구에 중요한 변경은 이유, 관찰된 검증 결과·미검증 범위, 다음 조건을 중복 없이 기록할 수 있다.
- 다른 세션에서 작업을 재개할 때 관련 커밋·현재 ref·working tree를 비교하고, 미커밋 또는 다른 작업자 소유의 변경을 덮어쓰지 않는다.
- 과거의 통과 기록이 현행 검증 성공으로 오인되지 않는다.
- squash merge, amend, rebase, 브랜치 삭제 등으로 중간 커밋이 사라질 수 있음을 반영하고 오래 보존할 의사결정은 적절한 정본/PR에 남긴다.
- 기존 `.gitmessage` 계약과 커밋 단위·history rewrite 제약을 회귀시키지 않는다.
- Markdown 형식·링크와 최소 시나리오를 확인하고 실제 수행 결과만 PR Validation에 반영한다.

## Boundaries

- 복구만을 위해 미완료 변경을 강제로 commit하거나, 잘못된 범위의 변경을 완성된 것으로 포장하지 않는다.
- 별도 checkpoint commit type, 고정 metadata schema, Git hook, CLI, CI, Skill 또는 router를 사전 도입하지 않는다. 실제 필요가 입증될 때만 별도로 제안한다.
- `main`, 타 작업 브랜치, history, 권한, 다른 정책 owner는 변경하지 않는다.
- 공개 커밋 메시지에 비밀정보, 개인정보, 내부 대화 또는 민감한 운영 맥락을 기록하지 않는다.

## Execution Status

- `commit.md`와 `.gitmessage`의 정책 개선을 구현했다 (`aabd068f7d0ff69bf5b439f86ae03ace1907670d` 기준).
- 단순 제목, 미검증 사항, 다른 세션의 재개, 타 작업자 변경, squash 이후 보존 경계를 시나리오로 정적 검토했다.
- 위 구현 커밋의 GitHub `check`는 성공했다. 이는 해당 SHA의 CI 결과이며 이후 커밋의 검증을 대체하지 않는다.
- 로컬 Git 서명 설정과 실제 다른 머신/에이전트의 복구 동작은 실행 검증하지 않았다.
- 다음 단계는 현재 PR HEAD 기준의 CI·scope·readiness 검토다. 사람의 요청 없이 Ready 전환이나 merge하지 않는다.

## References

- [Session Recovery Checkpoint Commits](https://github.com/mols3131d/mols-agent-assets/blob/main/catalog/patterns/workflow/session-recovery-checkpoint-commits.md)
- [Durable Progress Handoff](https://github.com/mols3131d/mols-agent-assets/blob/main/catalog/patterns/workflow/durable-progress-handoff.md)
- [Commits](../../docs/development/vcs-git/commit.md)
- [Git Message Template](../../.gitmessage)

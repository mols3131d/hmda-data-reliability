---
type: plan
title: "Four-Stage Documentation Work Todo"
description: "Use when executing PR #226 through consistency review, consistency improvement, readability polish, and post-polish integrity review."
tags:
  - consistency
  - documentation
  - maintenance
  - readability
  - validation
---

# Four-Stage Documentation Work Todo

PR #226은 문서 정합성과 가독성 다듬기를 한 작업으로 섞지 않는다. **정합성 검토 → 정합성 개선 → 가독성 다듬기 → 파괴 여부 검증**의 네 단계를 순서대로 완료한다.

각 단계에서도 한 번에 전체 문서를 다루지 않는다. 하나의 folder unit을 끝내고 해당 단계의 gate를 통과한 뒤 다음 folder unit으로 이동한다. 다른 폴더의 독립 문제는 즉시 수정하지 않고 `Cross-Folder Queue`에 기록한다.

## Stage Boundaries

| Stage | Main question | Mutation rule | Completion condition |
| --- | --- | --- | --- |
| 1. Consistency Review | 문서들이 현재 owner, contract와 서로 일치하는가? | 원칙적으로 read-only | 수정 대상과 non-finding이 근거와 함께 확정됨 |
| 2. Consistency Improvement | 확정된 정합성 문제를 가장 작게 어떻게 고치는가? | Stage 1 finding만 수정 | folder별 수정과 cross-document logical validation 완료 |
| 3. Readability Polish | 의미를 바꾸지 않고 더 쉽게 읽고 찾게 만들 수 있는가? | semantics frozen | 구조·문장·navigation 개선과 folder별 검증 완료 |
| 4. Integrity Review | 다듬기 과정에서 의미·계약·경계가 손상되지 않았는가? | regression 수정만 허용 | Stage 2 의미와 Stage 3 결과가 동등함을 검증 |

단계를 역전하거나 병합하지 않는다. Stage 2가 끝나기 전에는 readability-only edit를 하지 않고, Stage 3에서는 새 정합성 설계를 만들지 않는다. Stage 4에서는 추가 polish를 하지 않고 파괴된 의미를 복구하는 데만 수정 범위를 제한한다.

## Common Scope Rules

- 한 iteration의 writable scope는 현재 단계의 **한 folder unit**으로 제한한다.
- supporting evidence로 canonical owner, source, OpenSpec, test 또는 다른 문서를 읽을 수 있지만 현재 unit과 무관한 파일을 함께 수정하지 않는다.
- `INDEX.tsv`는 generated projection이므로 직접 편집하지 않는다. human-authored 문서 작업 종료 후 repository-owned generator로 한 번 갱신한다.
- `docs/development/dashboard.md`는 별도 dashboard refresh가 소유하므로 이번 PR에서 읽거나 수정하지 않는다.
- `AGENTS.md`, `CHATBOT.md`, `SKILL.md` 같은 instruction 또는 Agent Asset surface는 supporting authority로만 사용한다. 별도 문제와 명시적 scope가 없으면 수정하지 않는다.
- OpenSpec requirement, implementation, test, runtime behavior 또는 architecture decision 변경이 필요하면 현재 PR에서 확장하지 않고 blocker 또는 follow-up으로 기록한다.
- 각 문서는 [`docs/AGENTS.md`](../../docs/AGENTS.md)의 ownership과 trust boundary, [`docs/documentation/`](../../docs/documentation/README.md)의 일반 문서 정책, [`.rulesync/rules/markdown.md`](../../.rulesync/rules/markdown.md)의 Markdown rule을 따른다.

## Folder Units

각 단계는 아래 순서로 진행한다. 앞 unit의 stage gate가 닫히기 전에는 다음 unit으로 넘어가지 않는다.

| Unit | Folder / surface | Main targets | Special boundary |
| --- | --- | --- | --- |
| F0 | `docs/documentation/` | `README.md`, `principles.md`, `frontmatter.md`, `readme-authoring.md` | policy baseline, 문제 없으면 no-change |
| F1 | `docs/` root | `README.md`, `VISION.md`, `mvp.md`, `ARCHITECTURE.md`, `language.md` | `AGENTS.md` read-only, `INDEX.tsv` generated |
| F2 | `docs/domains/` | `README.md`, `OVERVIEW.md`, domain guides | exact requirement를 guide에 복제하지 않음 |
| F3 | `docs/development/ai-agent/` | `README.md`, `rule.md`, `skill.md` | runtime Agent Asset contract를 재정의하지 않음 |
| F4 | `docs/development/tooling/` | tooling guides | tool/vendor contract와 repository policy 분리 |
| F5 | `docs/development/vcs-git/` | branch, commit, PR, review guides | `.gitmessage`와 GitHub template ownership 보존 |
| F6 | `docs/development/` top level | `README.md`, `ci.md`, `test-design.md`, `testing.md` | `dashboard.md` 제외 |
| F7 | `docs/agents/` | `skills/README.md` | `INDEX.tsv` generated |
| F8 | `docs/references/` | README와 human-readable references | supporting data와 external meaning 보존 |
| F9 | repository root docs | `README.md`, `DEVELOPMENT.md` | `AGENTS.md`, `CHATBOT.md` 제외 |
| F10 | generated projections | `docs/**/INDEX.tsv` | 마지막에 generator로만 갱신 |

# Stage 1 — Consistency Review

이 단계의 목적은 **무엇을 고칠지 먼저 확정하는 것**이다. 문장을 예쁘게 고치거나 발견 즉시 수정하지 않는다.

## Review Checklist Per Folder

각 F0~F9에서 반복한다.

- [ ] 대상 파일 inventory와 각 파일의 role을 확인한다.
- [ ] applicable ownership, canonical source와 supporting evidence를 확인한다.
- [ ] 문서가 소유해야 하는 내용과 소유하면 안 되는 내용을 구분한다.
- [ ] 같은 개념의 용어, lifecycle, authority, safety boundary와 execution flow를 비교한다.
- [ ] stale 설명, 잘못된 owner, 모순, 누락된 mapping과 불필요한 canonical duplication을 찾는다.
- [ ] 단순한 표현 차이와 실제 의미 충돌을 구분한다.
- [ ] 확정 finding마다 `current → expected → owner/evidence → affected files`를 기록한다.
- [ ] 문제가 아닌 의도적인 abstraction 차이는 protected non-finding으로 기록한다.
- [ ] 현재 folder 밖의 문제는 `Cross-Folder Queue`에 기록한다.
- [ ] 이 단계에서는 canonical 문서를 수정하지 않았음을 확인한다.

## Consistency Review Focus

특히 다음 축은 folder별로 반복 확인한다.

- `VISION.md`의 장기 방향과 `mvp.md`의 active phase가 같은 lifecycle로 읽히지 않는가.
- `Silver / Gold`, `staging / marts`, analytical layer 용어의 mapping이 문서마다 달라지지 않는가.
- Airflow가 data plane orchestration을 넘어 reliability, approval 또는 recovery authority를 소유하는 것처럼 읽히지 않는가.
- `RecoveryProposal`, `SchemaRecoveryProposal`과 generic validated recovery proposal이 서로 잘못 일반화되지 않는가.
- `RemediationDraft`, Review AI output, validated proposal, human approval과 mutation authority가 구분되는가.
- Review AI와 Runtime AI 사이에서 review semantics와 provider invocation boundary가 유지되는가.
- root `DEVELOPMENT.md`와 세부 development guide가 같은 workflow를 서로 다르게 정의하지 않는가.
- README가 canonical owner를 대체하지 않고 entrypoint 역할만 수행하는가.

## Stage 1 Exit Gate

- [ ] F0~F9의 consistency review가 모두 끝났다.
- [ ] 각 finding은 근거와 owning source가 명확하다.
- [ ] protected non-finding이 정리되어 불필요한 수정 대상을 제거했다.
- [ ] Cross-Folder Queue가 logical issue별로 정리되어 있다.
- [ ] Stage 2에서 수정할 bounded change set을 확정했다.

# Stage 2 — Consistency Improvement

Stage 1에서 확정된 finding만 수정한다. 새 설계나 readability-only edit를 섞지 않는다.

## Improvement Checklist Per Folder

각 F0~F9에서 Stage 1 findings가 있는 unit만 반복한다.

- [ ] 현재 folder의 Stage 1 findings만 작업 대상으로 가져온다.
- [ ] 가장 좁은 canonical owner에서 문제를 고친다.
- [ ] 다른 문서는 owner를 재정의하지 않고 필요한 mapping, 짧은 맥락 또는 link만 남긴다.
- [ ] 기존 사실, 결정, 관계, 권한, safety condition과 lifecycle을 보존한다.
- [ ] 하나의 finding을 고치기 위해 unrelated wording cleanup을 섞지 않는다.
- [ ] 수정 후 같은 folder 문서끼리 다시 비교해 내부 contradiction이 사라졌는지 확인한다.
- [ ] supporting owner와 다시 대조해 새 drift를 만들지 않았는지 확인한다.
- [ ] changed link, frontmatter, heading과 Markdown mechanics를 확인한다.
- [ ] 미해결 finding은 숨기지 않고 blocker 또는 follow-up으로 남긴다.

## Folder Consistency Done Gate

- [ ] 해당 folder의 확정 findings가 모두 resolved 또는 explicitly deferred 상태다.
- [ ] resolved finding마다 expected owner와 의미가 맞는다.
- [ ] 새 cross-folder contradiction을 만들지 않았다.
- [ ] scope 밖 수정이 없다.
- [ ] 실제 수행한 validation을 기록했다.

## Logical Consistency Validation

F0~F9의 개선이 끝나면 folder 위치가 아니라 의미 단위로 다시 검증한다.

### L1 — Project Story and Lifecycle

- [ ] `README.md` → `VISION.md` → `mvp.md` → `ARCHITECTURE.md`의 읽기 흐름이 자연스럽다.
- [ ] long-term vision, active MVP, durable architecture와 current capability contract가 서로 다른 역할로 유지된다.
- [ ] 현재 상태를 phase goal이나 historical explanation과 혼동하지 않는다.

### L2 — Data and Execution Flow

- [ ] Source → Bronze → analytical layer → reliability evidence 흐름이 일관적이다.
- [ ] Data Platform, Data Operations와 Orchestration ownership이 겹치지 않는다.
- [ ] Airflow의 scope가 data-plane orchestration에 머문다.

### L3 — Reliability and Recovery Authority

- [ ] detection, incident, remediation draft, proposal, approval, recovery, re-validation의 순서와 authority가 일관적이다.
- [ ] advisory artifact와 executable mutation contract가 혼동되지 않는다.
- [ ] concrete proposal type의 차이를 generic prose가 지우지 않는다.

### L4 — AI Delegation and Runtime

- [ ] Vision의 delegation principle과 MVP의 advisory-only boundary가 충돌하지 않는다.
- [ ] Review AI는 evidence-bound review semantics를, Runtime AI는 bounded provider invocation을 소유한다.
- [ ] AI output이 approval 또는 deterministic truth로 승격되는 문구가 없다.

### L5 — Development and Documentation Ownership

- [ ] root `DEVELOPMENT.md`와 세부 development guide의 owner가 분명하다.
- [ ] README, guide, policy, reference, generated projection의 역할이 구분된다.
- [ ] canonical owner가 있는 규칙을 여러 문서가 재정의하지 않는다.

## Stage 2 Exit Gate

- [ ] folder consistency gates가 모두 닫혔다.
- [ ] L1~L5 logical validation을 통과했다.
- [ ] Stage 1 findings의 disposition이 모두 기록됐다.
- [ ] 이 시점의 문서 의미를 **semantic baseline**으로 고정했다.
- [ ] Stage 3에서는 semantic baseline을 변경하지 않는다는 조건을 확인했다.

# Stage 3 — Readability Polish

Stage 2의 semantic baseline을 고정한 채 사람이 더 빠르게 찾고 이해하고 판단할 수 있도록 문서를 다듬는다. **새 사실, 요구사항, 권한, 예외 또는 architecture decision을 추가하지 않는다.**

## Readability Checklist Per Folder

각 F0~F9에서 반복한다.

- [ ] 문서 첫 부분만 읽어도 목적과 responsibility를 파악할 수 있는지 확인한다.
- [ ] 중요한 결론, 조건과 boundary가 세부 설명보다 앞에 오는지 확인한다.
- [ ] 한 문단에 서로 다른 판단이 과도하게 섞이지 않았는지 확인한다.
- [ ] 긴 문장을 분리해도 조건, 인과관계와 예외가 유지되는지 확인한다.
- [ ] heading이 실제 독자 질문이나 검색 단위를 표현하는지 확인한다.
- [ ] list와 table이 같은 추상화 수준의 정보를 다루는지 확인한다.
- [ ] 같은 사실을 heading, prose, table과 callout에서 반복하지 않는지 확인한다.
- [ ] README는 첫 행동과 navigation에 필요한 내용만 남기는지 확인한다.
- [ ] 수동 paragraph wrapping, 장식적 강조와 불필요한 boilerplate를 정리한다.
- [ ] technical term과 repository naming을 임의로 바꾸지 않는다.
- [ ] prose polish만으로 해결되지 않는 의미 문제를 발견하면 Stage 3에서 설계하지 않고 integrity queue에 기록한다.

## Folder Readability Done Gate

- [ ] 변경은 구조, navigation, prose와 표현 개선에 한정된다.
- [ ] Stage 2 semantic baseline의 사실·관계·조건·예외·authority가 그대로다.
- [ ] 문서가 짧아졌더라도 필요한 근거와 safety boundary가 사라지지 않았다.
- [ ] 같은 folder에서 중복과 interpretation cost가 실제로 줄었다.
- [ ] Markdown과 language policy를 다시 확인했다.

## Stage 3 Exit Gate

- [ ] F0~F9의 readability pass가 완료됐다.
- [ ] consistency fix와 readability edit를 구분해 설명할 수 있다.
- [ ] generated index를 제외한 human-authored docs edit가 종료됐다.
- [ ] Stage 4에서 semantic baseline과 최종 문서를 비교할 준비가 됐다.

# Stage 4 — Post-Polish Integrity Review

이 단계는 가독성 개선 자체를 평가하는 단계가 아니다. **Stage 3에서 잘 읽히게 만들면서 의미를 삭제·왜곡·확대·축소하지 않았는지 검증한다.** 추가 polish는 하지 않는다.

## Integrity Checklist Per Folder

각 변경 folder에서 Stage 2 semantic baseline과 Stage 3 결과를 비교한다.

- [ ] 사실이나 current-state claim이 새로 생기거나 사라지지 않았다.
- [ ] requirement, authority, ownership 또는 lifecycle이 달라지지 않았다.
- [ ] MUST/SHALL 수준으로 읽힐 수 있는 강도가 의도치 않게 바뀌지 않았다.
- [ ] 조건, 예외, 전제와 failure behavior가 삭제되지 않았다.
- [ ] generic term으로 다듬으면서 중요한 concrete distinction을 지우지 않았다.
- [ ] 문단·section 이동으로 scope가 다른 규칙에 붙어 의미가 달라지지 않았다.
- [ ] 표나 list 재구성 과정에서 관계, 순서 또는 cardinality가 바뀌지 않았다.
- [ ] link 축소 과정에서 canonical owner로 가는 경로가 사라지지 않았다.
- [ ] frontmatter와 heading 수정이 document selection이나 responsibility를 왜곡하지 않았다.

## Logical Integrity Validation

Stage 2의 L1~L5를 **최종 Stage 3 결과에 대해 다시 실행**한다. 추가로 다음을 확인한다.

### L6 — Terminology Preservation

- [ ] 같은 domain concept에 같은 용어가 사용된다.
- [ ] 의도적으로 다른 abstraction은 다른 용어로 유지된다.
- [ ] readability 목적으로 기술 용어를 바꾸면서 contract identity가 손상되지 않았다.

### L7 — Navigation and Ownership Preservation

- [ ] 중복 제거 후에도 독자가 canonical owner를 찾을 수 있다.
- [ ] entrypoint가 너무 축약되어 다음 행동이나 문서 선택이 불명확해지지 않았다.
- [ ] generated projection이나 reference가 canonical source처럼 승격되지 않았다.

## Damage Handling

Stage 4에서 regression을 찾으면 새 방향을 설계하지 않는다.

1. Stage 2 semantic baseline에서 보존되어야 할 의미를 특정한다.
1. Stage 3 edit 중 의미를 파괴한 최소 부분만 복구한다.
1. 해당 folder integrity checklist를 다시 실행한다.
1. 영향받은 logical validation unit을 다시 실행한다.
1. readability보다 semantic fidelity를 우선한다.

## Generated Projections and Final Validation

Integrity review가 끝난 뒤 F10을 수행한다.

- [ ] repository-owned docs index generator를 실행한다.
- [ ] generated `INDEX.tsv` diff가 human-authored metadata/path 변경으로 설명된다.
- [ ] generated output을 수동 편집하지 않는다.
- [ ] generator 재실행 시 추가 diff가 없다.
- [ ] changed Markdown에 repository-owned formatting/check를 적용한다.
- [ ] internal links와 frontmatter validation을 확인한다.
- [ ] PR diff가 문서 정합성·가독성 작업 범위를 넘지 않는지 최종 확인한다.
- [ ] PR description에 consistency changes, readability changes, integrity validation과 미확인 사항을 구분해 반영한다.

## Stage 4 Exit Gate

- [ ] 변경된 모든 folder의 integrity review가 완료됐다.
- [ ] L1~L7 logical validation이 최종 결과에서 통과했다.
- [ ] 발견된 polish regression이 모두 복구되거나 명시적으로 unresolved 처리됐다.
- [ ] generated projection과 deterministic Markdown/docs validation이 완료됐다.
- [ ] 최종 diff에서 implementation, test, OpenSpec, dashboard, instruction surface의 scope 확장이 없다.

# Cross-Folder Queue

현재 단계에서 다른 folder의 독립 문제를 발견하면 아래 형식으로 기록하고 해당 단계의 적절한 unit에서만 처리한다.

| Found in | Target folder | Stage | Issue | Evidence / owner | Disposition |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

# Progress

| Stage | Status | Completion condition |
| --- | --- | --- |
| 1. Consistency Review | Not started | F0~F9 review + bounded finding set |
| 2. Consistency Improvement | Blocked by Stage 1 | folder fixes + L1~L5 validation + semantic baseline |
| 3. Readability Polish | Blocked by Stage 2 | folder readability gates |
| 4. Integrity Review | Blocked by Stage 3 | semantic regression review + L1~L7 + final validation |

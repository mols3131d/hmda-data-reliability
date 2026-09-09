---
type: plan
title: "Folder and Logical Validation Todo"
description: "Use when executing PR #226 one documentation folder at a time and validating completed edits again by cross-document logical unit."
tags:
  - consistency
  - documentation
  - maintenance
  - validation
---

# Folder and Logical Validation Todo

PR #226은 한 번에 전체 문서를 고치지 않는다. **하나의 폴더 작업을 끝내고 해당 폴더 gate를 통과한 뒤에만 다음 폴더로 이동한다.** 모든 폴더 작업이 끝나면 파일 위치와 무관하게 같은 의미를 공유하는 문서들을 logical unit으로 다시 묶어 검증한다.

이 checklist는 진행 상태를 기록하는 working artifact다. Canonical contract나 repository policy를 새로 정의하지 않는다.

## Execution Rules

- 한 iteration의 writable scope는 아래에 지정된 **한 folder unit**으로 제한한다.
- 현재 folder unit을 수정하는 데 필요한 canonical owner, source, OpenSpec 또는 다른 문서는 supporting evidence로 읽을 수 있지만 함께 수정하지 않는다.
- 다른 폴더에서 문제가 보여도 현재 unit의 수정에 필수적이지 않으면 `Cross-Folder Queue`에 기록하고 넘어간다.
- 각 folder unit은 `Folder Done Gate`를 모두 통과해야 완료로 표시한다.
- `INDEX.tsv`는 generated projection이므로 직접 편집하지 않는다. 모든 문서 edit가 끝난 뒤 repository-owned generator로 갱신한다.
- `docs/development/dashboard.md`는 별도 dashboard refresh에서만 갱신한다. 이번 PR에서는 읽거나 수정하지 않는다.
- `AGENTS.md`, `CHATBOT.md`, `SKILL.md` 같은 instruction/Agent Asset surface는 일반 human documentation polish 대상으로 취급하지 않는다. Supporting authority로만 읽고, 별도 문제와 명시적 scope가 없으면 수정하지 않는다.
- 의미를 바꾸는 설계 변경, OpenSpec requirement 변경, implementation/test 변경이 필요해지면 이 PR에서 해결하지 않고 blocker 또는 follow-up으로 기록한다.

## Folder Done Gate

각 folder unit마다 아래 순서를 반복한다.

- [ ] 대상 파일 inventory와 각 파일의 role을 확인했다.
- [ ] 적용되는 `AGENTS.md`, documentation policy, Markdown rule과 필요한 canonical owner를 확인했다.
- [ ] 각 문서의 목적, 독자, canonical responsibility와 non-responsibility를 구분했다.
- [ ] 내부 중복, 용어 drift, stale 설명, 잘못된 authority, 불필요한 navigation과 prose 밀도를 점검했다.
- [ ] 실제 독자 판단을 개선하는 최소 coherent edit만 적용했다.
- [ ] 폴더 밖에서 발견된 독립 문제는 현재 edit에 섞지 않고 `Cross-Folder Queue`에 기록했다.
- [ ] 변경 후 같은 폴더 문서끼리 다시 읽어 내부 contradiction과 중복이 없는지 확인했다.
- [ ] 변경한 link, heading, frontmatter와 Markdown 표현이 repository rule에 맞는지 확인했다.
- [ ] 해당 unit에서 수행한 validation과 미확인 사항을 기록했다.

## Phase 0 — Policy Baseline

이 단계는 이후 모든 폴더의 판단 기준을 고정하기 위한 read-first unit이다. 정책 문서 자체에서 실제 inconsistency가 발견되지 않으면 수정하지 않는다.

### `docs/documentation/`

Targets:

- `README.md`
- `principles.md`
- `frontmatter.md`
- `readme-authoring.md`
- `INDEX.tsv` — read/generated only

Todo:

- [ ] `README.md`가 policy entrypoint 역할만 맡고 세부 규칙을 중복 소유하지 않는지 확인한다.
- [ ] `principles.md`의 purpose, ownership, canonical-source, maintenance 원칙을 이후 모든 folder unit의 기준으로 고정한다.
- [ ] `frontmatter.md`의 description/metadata 역할을 확인한다.
- [ ] `readme-authoring.md`의 entrypoint 책임과 navigation 기준을 확인한다.
- [ ] 네 문서 사이에 같은 policy를 서로 다르게 정의하는 충돌이 있는지 확인한다.
- [ ] `INDEX.tsv`는 직접 수정하지 않는다는 generated boundary를 확인한다.
- [ ] 실제 문제가 없으면 **no-change completion**으로 종료한다.
- [ ] `Folder Done Gate`를 통과한다.

## Phase 1 — `docs/` Root Documents

Writable candidates:

- `README.md`
- `VISION.md`
- `mvp.md`
- `ARCHITECTURE.md`
- `language.md`

Read-only authority/support:

- `AGENTS.md`
- generated `INDEX.tsv`

Todo:

- [ ] `docs/README.md`가 문서 묶음의 entrypoint 역할에 필요한 navigation만 제공하는지 확인한다.
- [ ] `VISION.md`가 durable direction과 delegation principles만 소유하고 현재 MVP 세부 구현을 과도하게 복제하지 않는지 확인한다.
- [ ] `mvp.md`가 active goal, scope, acceptance만 소유하고 implementation status나 validation result를 소유하지 않는지 확인한다.
- [ ] `ARCHITECTURE.md`가 system/execution/domain boundary를 설명하되 exact OpenSpec requirement를 복제하지 않는지 확인한다.
- [ ] `language.md`가 실제 repository language surface와 모순되지 않는지 확인하되 불필요한 style 확장은 하지 않는다.
- [ ] `Silver / Gold`와 `dbt staging / marts` 표현이 같은 개념인지 검증하고 필요한 최소 mapping만 적용한다.
- [ ] recovery proposal을 generic concept와 concrete contract type이 혼동되지 않게 정리한다.
- [ ] AI advisory, approval, recovery boundary 반복은 각 문서 responsibility에 필요한 수준으로만 유지한다.
- [ ] 긴 문단과 수동 paragraph wrapping은 의미 보존 조건에서만 정리한다.
- [ ] `Folder Done Gate`를 통과한다.

## Phase 2 — `docs/domains/`

Targets:

- `README.md`
- `OVERVIEW.md`
- `hmda-data.md`
- `data-platform.md`
- `data-operations.md`
- `reliability.md`
- `review-ai.md`
- `runtime-ai.md`
- `orchestration.md`
- `INDEX.tsv` — generated only

Todo:

- [ ] `README.md`와 `OVERVIEW.md`의 entrypoint/navigation 역할이 중복되지 않는지 확인한다.
- [ ] 각 domain guide가 responsibility, public surface, flow, non-responsibility만 설명하는지 확인한다.
- [ ] domain 간 ownership이 겹치거나 빈 공간이 생기는 표현을 찾는다.
- [ ] HMDA Data → Data Platform → Data Operations → Reliability 흐름의 책임 이동이 일관적인지 확인한다.
- [ ] Reliability → Review AI → Runtime AI 사이에서 evidence, semantics, provider invocation boundary가 일관적인지 확인한다.
- [ ] Orchestration이 Airflow data-plane dependency와 task state만 소유하고 reliability/approval/recovery authority를 흡수하지 않는지 확인한다.
- [ ] concrete threshold, serialization detail, exact requirement가 guide에 불필요하게 복제됐는지 확인한다.
- [ ] `ARCHITECTURE.md`와 충돌 후보는 현재 folder에서 가능한 경우 guide를 바로잡고, architecture edit가 필요하면 queue에 기록한다.
- [ ] `Folder Done Gate`를 통과한다.

## Phase 3 — `docs/development/ai-agent/`

Targets:

- `README.md`
- `rule.md`
- `skill.md`

Todo:

- [ ] README가 AI Agent development docs의 선택·진입점 역할만 하는지 확인한다.
- [ ] Rule과 Skill 설명이 실제 Agent Asset의 runtime contract를 재정의하지 않는지 확인한다.
- [ ] repository-specific 사용법과 generic asset semantics가 섞이지 않았는지 확인한다.
- [ ] Rulesync/Skill 관련 terminology가 current repository routing과 맞는지 확인한다.
- [ ] 중복 설명은 owning asset 또는 tooling guide로 연결하고 필요한 맥락만 남긴다.
- [ ] `Folder Done Gate`를 통과한다.

## Phase 4 — `docs/development/tooling/`

Targets:

- `README.md`
- `bootstrap.md`
- `formatting.md`
- `lefthook.md`
- `openspec.md`
- `rulesync.md`

Todo:

- [ ] README의 tooling entrypoint와 각 tool guide의 ownership이 분명한지 확인한다.
- [ ] bootstrap의 `setup` / `session` / `update` 경계와 root `DEVELOPMENT.md` 요약이 일치하는지 확인한다.
- [ ] formatting guide와 repository 실제 formatter ownership이 일치하는지 확인한다.
- [ ] lefthook guide가 CI/formatter owner와 충돌하지 않는지 확인한다.
- [ ] OpenSpec guide가 vendor/framework contract를 repository policy처럼 과장하지 않는지 확인한다.
- [ ] Rulesync guide가 generated state, manual edit boundary, source-of-truth 관계를 일관되게 설명하는지 확인한다.
- [ ] 동일 command나 workflow가 여러 문서에 복제되어 stale 위험을 만드는지 확인한다.
- [ ] `Folder Done Gate`를 통과한다.

## Phase 5 — `docs/development/vcs-git/`

Targets:

- `README.md`
- `branch.md`
- `commit.md`
- `pull-request.md`
- `pull-request-review.md`

Todo:

- [ ] README가 operation별 guide routing만 제공하는지 확인한다.
- [ ] branch → commit → PR → review lifecycle의 역할과 authority가 서로 겹치지 않는지 확인한다.
- [ ] `.gitmessage`와 GitHub template의 canonical ownership을 잘못 복제한 부분이 없는지 확인한다.
- [ ] agent-specific constraint가 human workflow의 일반 규칙처럼 섞이지 않는지 확인한다.
- [ ] PR description과 review artifact의 responsibility가 명확히 분리되는지 확인한다.
- [ ] 현재 PR #226의 실제 workflow와 문서가 모순되는 항목이 없는지 확인한다.
- [ ] `Folder Done Gate`를 통과한다.

## Phase 6 — `docs/development/` Top Level

Writable candidates:

- `README.md`
- `ci.md`
- `test-design.md`
- `testing.md`

Excluded:

- `dashboard.md` — separate dashboard refresh only
- `INDEX.tsv` — generated only

Todo:

- [ ] README가 subguide navigation과 development entrypoint 역할에 집중하는지 확인한다.
- [ ] `ci.md`가 현재 CI ownership과 change-impact policy를 정확히 설명하는지 확인한다.
- [ ] `testing.md`와 `test-design.md` 사이에서 execution procedure와 design principle이 중복·충돌하지 않는지 확인한다.
- [ ] root `DEVELOPMENT.md`가 세부 guide를 다시 정의하지 않고 올바르게 연결하는지 확인한다.
- [ ] formatting, test, CI command가 서로 다른 guide에서 상충하지 않는지 확인한다.
- [ ] dashboard는 읽거나 수정하지 않았음을 확인한다.
- [ ] `Folder Done Gate`를 통과한다.

## Phase 7 — `docs/agents/`

Targets:

- `skills/README.md`
- `INDEX.tsv` — generated only

Todo:

- [ ] human-facing Skill documentation entrypoint가 실제 Skill runtime contract를 복제하지 않는지 확인한다.
- [ ] repository에서 Skill을 찾고 사용하는 다음 경로가 current routing/tooling과 맞는지 확인한다.
- [ ] 별도 README가 필요한 responsibility를 실제로 갖는지 확인한다.
- [ ] `Folder Done Gate`를 통과한다.

## Phase 8 — `docs/references/`

Writable candidates:

- `README.md`
- `hmda_eda.md`
- `hmda_lar.md`
- `python-data-pipeline-oom-testing-guide.md`

Supporting/generated data:

- `hmda_eda_reference.json`
- `INDEX.tsv`

Todo:

- [ ] README가 reference collection의 선택 기준과 역할만 설명하는지 확인한다.
- [ ] reference 문서를 durable project policy나 current implementation contract처럼 표현하는 부분이 없는지 확인한다.
- [ ] 외부 사실·규격·데이터 설명의 원래 의미를 prose polish 때문에 바꾸지 않는다.
- [ ] project-specific guide와 supporting reference의 경계가 분명한지 확인한다.
- [ ] JSON/reference data는 prose 다듬기를 이유로 수정하지 않는다.
- [ ] 오래된 내용이 의심되지만 현재 evidence로 검증할 수 없으면 수정하지 않고 unresolved로 남긴다.
- [ ] `Folder Done Gate`를 통과한다.

## Phase 9 — Repository Root Documentation

Writable candidates:

- `README.md`
- `DEVELOPMENT.md`

Excluded instruction/bootstrap surfaces:

- `AGENTS.md`
- `CHATBOT.md`

Todo:

- [ ] root README가 프로젝트 첫 진입점에서 problem, current MVP, design boundary와 다음 문서만 충분히 제공하는지 확인한다.
- [ ] root README가 `VISION.md`, `mvp.md`, `ARCHITECTURE.md`, domain guides의 정본을 불필요하게 복제하지 않는지 확인한다.
- [ ] `DEVELOPMENT.md`가 repository-wide active tool choice, package layout, code convention만 소유하는지 확인한다.
- [ ] `DEVELOPMENT.md`의 tool/layer naming이 수정된 `docs/**`와 일치하는지 확인한다.
- [ ] root docs에서 현재 MVP와 장기 vision을 같은 lifecycle의 상태처럼 섞지 않는지 확인한다.
- [ ] instruction/bootstrap surface는 수정하지 않았음을 확인한다.
- [ ] `Folder Done Gate`를 통과한다.

## Phase 10 — Generated Documentation Projections

모든 human-authored documentation edit가 끝난 뒤 한 번만 수행한다.

- [ ] changed frontmatter와 path를 기준으로 docs index generator를 실행한다.
- [ ] generated `INDEX.tsv` diff가 human-authored metadata 변경으로 설명되는지 확인한다.
- [ ] generated output을 수동 교정하지 않는다.
- [ ] generator 재실행 시 추가 diff가 없는지 확인한다.

# Logical Validation Todo

폴더 단위 작업을 모두 끝낸 후 아래 logical unit을 순서대로 검증한다. 이 단계에서는 **같은 의미를 공유하는 문서 묶음**을 다시 읽으며, folder-local optimization 때문에 cross-document consistency가 깨지지 않았는지 확인한다.

## L1 — Project Story and Lifecycle

Documents:

- root `README.md`
- `docs/VISION.md`
- `docs/mvp.md`
- `docs/ARCHITECTURE.md`

Checks:

- [ ] 장기 vision → 현재 MVP → architecture의 abstraction이 자연스럽게 내려간다.
- [ ] 장기 가능성을 현재 capability로, 현재 MVP를 장기 불변 원칙으로 잘못 표현하지 않는다.
- [ ] 독자가 각 문서의 canonical responsibility를 구분할 수 있다.
- [ ] README가 나머지 세 문서를 대체하지 않고 올바른 entrypoint로 동작한다.

## L2 — Data Layer and Execution Flow

Documents:

- `docs/mvp.md`
- `docs/ARCHITECTURE.md`
- `docs/domains/hmda-data.md`
- `docs/domains/data-platform.md`
- `docs/domains/data-operations.md`
- `docs/domains/orchestration.md`
- root `DEVELOPMENT.md`

Checks:

- [ ] Source → Bronze → dbt analytical layer 흐름이 문서마다 같은 의미로 읽힌다.
- [ ] `Silver / Gold`와 `staging / marts` 관계가 모호하지 않다.
- [ ] Airflow와 data operation/data platform ownership이 충돌하지 않는다.
- [ ] quality gate와 analytics build의 execution boundary가 일관된다.

## L3 — Reliability and Recovery Authority

Documents:

- `docs/VISION.md`
- `docs/mvp.md`
- `docs/ARCHITECTURE.md`
- `docs/domains/reliability.md`

Checks:

- [ ] deterministic detection/safety truth와 AI advisory가 분리된다.
- [ ] `RemediationDraft`와 validated recovery proposal의 역할이 혼동되지 않는다.
- [ ] generic recovery proposal 개념과 `RecoveryProposal` / `SchemaRecoveryProposal` concrete type이 혼동되지 않는다.
- [ ] exact proposal-bound approval과 mutation/re-validation boundary가 일관된다.

## L4 — AI Delegation and LLMOps

Documents:

- `docs/VISION.md`
- `docs/mvp.md`
- `docs/ARCHITECTURE.md`
- `docs/domains/review-ai.md`
- `docs/domains/runtime-ai.md`

Checks:

- [ ] Review AI와 Runtime AI responsibility가 분리된다.
- [ ] provider invocation provenance와 review semantics의 owner가 뒤섞이지 않는다.
- [ ] 현재 MVP의 advisory-only boundary와 장기 delegation expansion direction이 충돌하지 않는다.
- [ ] live evaluation/provenance 요구를 deterministic reliability proof와 동일시하지 않는다.

## L5 — Development Workflow Ownership

Documents:

- root `DEVELOPMENT.md`
- `docs/development/README.md`
- `docs/development/ci.md`
- `docs/development/testing.md`
- `docs/development/test-design.md`
- `docs/development/tooling/**`
- `docs/development/vcs-git/**`

Checks:

- [ ] root summary와 세부 guide 사이에 competing owner가 없다.
- [ ] 동일 command, formatter, test/CI behavior가 서로 다르게 설명되지 않는다.
- [ ] branch/commit/PR/review lifecycle과 현재 repository templates가 모순되지 않는다.
- [ ] tooling-generated state와 human-maintained guidance의 경계가 일관된다.

## L6 — Documentation Ownership and Navigation

Documents:

- `docs/README.md`
- `docs/documentation/**`
- `docs/domains/README.md`
- `docs/domains/OVERVIEW.md`
- `docs/development/README.md`
- `docs/agents/skills/README.md`
- `docs/references/README.md`

Checks:

- [ ] README마다 대표 범위, 선택 시점과 다음 행동이 분명하다.
- [ ] navigation이 generated inventory와 competing source of truth가 되지 않는다.
- [ ] 같은 policy나 responsibility가 여러 README에서 재정의되지 않는다.
- [ ] path + title + description만으로 문서 후보를 구분하기 어렵게 만드는 metadata drift가 없다.

## L7 — Language, Terminology, and Markdown

Checks:

- [ ] H1–H3, field/label, structured metadata가 `docs/language.md` 정책과 맞는다.
- [ ] 같은 domain concept에 특별한 이유 없이 여러 용어가 섞이지 않는다.
- [ ] paragraph 내 수동 줄바꿈, 불필요한 callout/table, 과도한 heading nesting을 정리했다.
- [ ] 긴 문단을 나눈 경우 조건, 예외, causal relation과 authority가 보존됐다.

## L8 — Link, Metadata, and Generated Index Integrity

Checks:

- [ ] 수정한 repository-relative link가 유효하다.
- [ ] 일반 docs frontmatter가 schema와 selection-oriented description 원칙에 맞는다.
- [ ] generated `INDEX.tsv`가 current metadata/path와 일치한다.
- [ ] generated output에 수동-only 변경이 남지 않았다.

## L9 — Scope and Safety Guard

Checks:

- [ ] source, test, OpenSpec requirement 또는 runtime behavior를 이 PR에서 변경하지 않았다.
- [ ] `docs/development/dashboard.md`를 갱신하지 않았다.
- [ ] `AGENTS.md`, `CHATBOT.md`, Agent Asset runtime contract를 documentation polish 명목으로 변경하지 않았다.
- [ ] unresolved design/contract 문제는 문구로 덮지 않고 follow-up 후보로 남겼다.
- [ ] 최종 diff가 documentation consistency와 readability라는 PR 목적 안에 머문다.

## L10 — Final Repository-Owned Validation

- [ ] Markdown formatter를 변경된 Markdown scope에 적용한다.
- [ ] docs-specific Markdown/link/frontmatter checks를 실행한다.
- [ ] docs index generator를 실행하고 idempotence를 확인한다.
- [ ] PR diff를 다시 읽어 accidental scope expansion과 semantic loss가 없는지 확인한다.
- [ ] PR body의 Changes와 Validation을 실제 최종 상태에 맞게 갱신한다.

# Cross-Folder Queue

현재 folder unit 밖에서 발견한 문제는 여기에만 기록한다. 해당 folder 차례가 오기 전에는 수정하지 않는다.

| Source unit | Target unit | Candidate | State |
| --- | --- | --- | --- |
| Baseline | `docs/` root | Analytical layer naming | queued |
| Baseline | `docs/` root + `docs/domains/` | Recovery proposal abstraction | queued |
| Baseline | Logical L1/L4 | AI delegation repetition | queued |
| Baseline | affected folders | Dense prose / manual wrapping | queued |

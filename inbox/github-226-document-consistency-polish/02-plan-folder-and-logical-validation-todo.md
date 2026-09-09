---
type: plan
title: "Four-Stage Documentation Work Todo"
description: "Use when reviewing or resuming PR #226 completion across consistency review, consistency improvement, readability polish, integrity review, folder units, and logical validation."
tags:
  - consistency
  - documentation
  - maintenance
  - readability
  - validation
---

# Four-Stage Documentation Work Todo

PR #226은 **정합성 검토 → 정합성 개선 → 가독성 다듬기 → 파괴 여부 검증**의 네 단계를 순서대로 수행했다. 각 단계는 folder unit으로 좁혀 진행하고, folder 작업 뒤에는 위치가 아니라 의미 단위의 logical validation으로 다시 검증했다.

> [!IMPORTANT]
> **Status: Complete.** 상세 finding과 변경 근거는 Stage별 sibling artifact가 소유하고, 이 문서는 작업 순서와 completion state를 추적한다.

## Stage Boundaries

| Stage | Main question | Mutation rule | Status |
| --- | --- | --- | --- |
| 1. Consistency Review | 문서들이 현재 owner, contract와 서로 일치하는가? | read-only review | ✅ Complete |
| 2. Consistency Improvement | 확정된 정합성 문제를 가장 작게 어떻게 고치는가? | Stage 1 finding만 수정 | ✅ Complete |
| 3. Readability Polish | 의미를 바꾸지 않고 더 쉽게 읽고 찾게 만들 수 있는가? | semantics frozen | ✅ Complete |
| 4. Integrity Review | 다듬기 과정에서 의미·계약·경계가 손상되지 않았는가? | regression 수정만 허용 | ✅ Complete |

## Scope Rules

- [x] 한 iteration의 writable scope를 현재 folder unit 또는 bounded final-validation artifact로 제한했다.
- [x] Canonical owner와 supporting evidence를 구분했다.
- [x] `INDEX.tsv`를 수동 편집하지 않았다.
- [x] `docs/development/dashboard.md`를 수정하지 않았다.
- [x] `AGENTS.md`, `CHATBOT.md`, `SKILL.md` 등 instruction/Agent Asset surface를 수정하지 않았다.
- [x] OpenSpec requirement, implementation, test 또는 runtime behavior로 scope를 확장하지 않았다.
- [x] `docs/documentation/**`, `.rulesync/rules/markdown.md`, `mols-documentation`의 문서 작성 경계를 적용했다.

## Folder Units

| Unit | Folder / surface | Stage result | Evidence |
| --- | --- | --- | --- |
| F0 | `docs/documentation/` | ✅ Reviewed · no change | Stage 1 report |
| F1 | `docs/` root | ✅ Reviewed · bounded consistency/readability edits | Stage 1–4 reports |
| F2 | `docs/domains/` | ✅ Reviewed · navigation fix/polish | Stage 1–4 reports |
| F3 | `docs/development/ai-agent/` | ✅ Reviewed · no change | Stage 1 report |
| F4 | `docs/development/tooling/` | ✅ Reviewed · no change | Stage 1 report |
| F5 | `docs/development/vcs-git/` | ✅ Reviewed · no change | Stage 1 report |
| F6 | `docs/development/` top level | ✅ Reviewed · no change | Stage 1/3 report |
| F7 | `docs/agents/` | ✅ Reviewed · no change | Stage 1 report |
| F8 | `docs/references/` | ✅ Reviewed · no change | Stage 1 report |
| F9 | repository root docs | ✅ Reviewed · root `README.md` consistency fix | Stage 1/2 report |
| F10 | generated projections | ✅ Validated · zero generated diff | Final validation closure |

# Stage 1 — Consistency Review

- [x] F0–F9 대상 inventory와 document role을 확인했다.
- [x] applicable ownership, canonical source와 supporting evidence를 확인했다.
- [x] stale 설명, owner drift, contradiction, missing mapping과 canonical duplication을 검토했다.
- [x] 표현 차이와 실제 의미 충돌을 구분했다.
- [x] C1–C3 finding을 근거와 affected file에 연결했다.
- [x] `Silver / Gold`와 `staging / marts` 등 intentional abstraction 차이를 protected non-finding으로 기록했다.
- [x] Stage 2 bounded change set을 C1–C3으로 고정했다.

## Stage 1 Exit Gate

- [x] F0–F9 consistency review 완료.
- [x] Finding owner/evidence 확인 완료.
- [x] Protected non-finding 정리 완료.
- [x] 미처리 cross-folder issue 없음.
- [x] Stage 2 change set 확정.

# Stage 2 — Consistency Improvement

- [x] Stage 1 findings만 수정했다.
- [x] 가장 좁은 canonical/entry owner에서 문제를 고쳤다.
- [x] Unrelated wording cleanup을 Stage 2에 섞지 않았다.
- [x] `RecoveryProposal`과 `SchemaRecoveryProposal`의 concrete distinction을 owner 문서에 보존했다.
- [x] Review AI / Runtime AI navigation과 LangGraph / OpenAI runtime ownership을 current owner와 맞췄다.
- [x] 수정 후 cross-document contradiction을 다시 검토했다.
- [x] Stage 2 semantic baseline `bc0914b7db4061fcb0aa6b89769324abd40cbe06`을 고정했다.

## Logical Consistency Validation

### L1 — Project Story and Lifecycle

- [x] `README.md` → `VISION.md` → `mvp.md` → `ARCHITECTURE.md`의 역할과 읽기 흐름을 확인했다.
- [x] Long-term vision, active MVP, durable architecture와 current capability contract를 구분했다.

### L2 — Data and Execution Flow

- [x] Source → Bronze → analytical layer → reliability evidence 흐름을 확인했다.
- [x] Data Platform, Data Operations와 Orchestration ownership을 구분했다.
- [x] Airflow scope가 data-plane orchestration에 머무는지 확인했다.

### L3 — Reliability and Recovery Authority

- [x] detection → incident → remediation draft → proposal → approval → recovery → re-validation 순서를 확인했다.
- [x] Advisory artifact와 executable mutation contract를 구분했다.
- [x] Generic recovery prose가 concrete proposal type 차이를 지우지 않는지 확인했다.

### L4 — AI Delegation and Runtime

- [x] Vision delegation principle과 MVP advisory-only boundary가 일치한다.
- [x] Review AI는 review semantics, Runtime AI는 bounded provider invocation을 소유한다.
- [x] AI output이 approval 또는 deterministic truth로 승격되지 않는다.

### L5 — Development and Documentation Ownership

- [x] root `DEVELOPMENT.md`와 detailed development guide의 owner가 일치한다.
- [x] README, guide, policy, reference와 generated projection의 역할을 구분했다.
- [x] Canonical owner가 있는 규칙을 competing 문서가 재정의하지 않는다.

## Stage 2 Exit Gate

- [x] Folder consistency gates 완료.
- [x] L1–L5 통과.
- [x] C1–C3 disposition 기록 완료.
- [x] Semantic baseline 고정.

# Stage 3 — Readability Polish

- [x] Stage 2 semantic baseline을 변경하지 않았다.
- [x] `docs/mvp.md`의 manual paragraph wrapping을 제거했다.
- [x] `docs/ARCHITECTURE.md`의 dense boundary prose를 의미 보존 상태로 paragraph split했다.
- [x] `docs/domains/README.md` navigation order를 conceptual flow에 맞췄다.
- [x] 새로운 fact, requirement, exception, authority 또는 architecture decision을 추가하지 않았다.
- [x] F0/F3/F4/F5/F6/F7/F8/F9는 불필요한 prose churn보다 no-change를 선택했다.

## Stage 3 Exit Gate

- [x] F0–F9 readability pass 완료.
- [x] Consistency fix와 readability edit를 구분해 기록했다.
- [x] Human-authored docs edit 종료.
- [x] Stage 4 baseline comparison 준비 완료.

# Stage 4 — Post-Polish Integrity Review

- [x] Stage 2 baseline과 Stage 3 결과의 fact/current-state claim을 비교했다.
- [x] Requirement, authority, ownership과 lifecycle 손실 여부를 확인했다.
- [x] 조건, 예외, 전제와 failure behavior 손실 여부를 확인했다.
- [x] Generic wording이 concrete recovery distinction을 지우지 않는지 확인했다.
- [x] Paragraph/navigation 이동이 scope 또는 관계를 바꾸지 않는지 확인했다.
- [x] Canonical owner link와 frontmatter responsibility가 보존되는지 확인했다.

## Logical Integrity Validation

- [x] 최종 결과에 대해 L1–L5를 다시 확인했다.

### L6 — Terminology Preservation

- [x] 같은 domain concept에 같은 용어가 사용된다.
- [x] 의도적으로 다른 abstraction은 다른 용어로 유지된다.
- [x] Readability edit가 contract identity를 손상하지 않았다.

### L7 — Navigation and Ownership Preservation

- [x] 중복 제거 후에도 canonical owner를 찾을 수 있다.
- [x] Entrypoint의 다음 행동과 문서 선택이 명확하다.
- [x] Generated projection/reference가 canonical source로 승격되지 않았다.

## F10 — Generated Projections and Final Validation

- [x] PR-head `scripts/generate_docs_indexes.py`를 generator input 재구성 환경에서 실행했다.
- [x] Generated `INDEX.tsv` expected diff가 zero diff임을 확인했다.
- [x] Generated output을 수동 편집하지 않았다.
- [x] Generate 후 6개 `INDEX.tsv` SHA-256이 모두 동일했고 재실행 `--check`가 통과했다.
- [x] Changed Markdown/docs validation은 CI Lite에서 통과했다.
- [x] Changed canonical docs의 repository-relative internal link target을 확인했다.
- [x] Changed `docs/**` frontmatter가 required `title` / `description`을 유지하는지 확인했다.
- [x] PR diff가 canonical docs 4개와 PR-specific Inbox artifact로 제한되는지 확인했다.
- [x] PR description에 consistency, readability, integrity와 final validation을 구분해 반영한다.

## Stage 4 Exit Gate

- [x] 변경된 모든 folder integrity review 완료.
- [x] L1–L7 최종 validation 통과.
- [x] Material polish regression 없음.
- [x] Generated projection과 deterministic Markdown/docs validation 완료.
- [x] Implementation, test, OpenSpec, dashboard, instruction surface scope 확장 없음.

# Cross-Folder Queue

추가 처리해야 할 in-scope cross-folder issue 없음.

# Progress

| Stage | Status | Completion evidence |
| --- | --- | --- |
| 1. Consistency Review | ✅ Complete | `03-report-stage1-consistency-review.md` |
| 2. Consistency Improvement | ✅ Complete | `05-report-stage2-consistency-improvement.md` |
| 3. Readability Polish | ✅ Complete | `06-report-stage3-readability-polish.md` |
| 4. Integrity Review | ✅ Complete | `07-review-stage4-integrity.md` |
| Final validation / F10 | ✅ Complete | `08-report-final-validation-closure.md` |

## References

- `03-report-stage1-consistency-review.md`
- `04-status-loops-run.md`
- `05-report-stage2-consistency-improvement.md`
- `06-report-stage3-readability-polish.md`
- `07-review-stage4-integrity.md`
- `08-report-final-validation-closure.md`

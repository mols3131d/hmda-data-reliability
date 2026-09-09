---
type: report
title: "Stage 1 Consistency Review"
description: "Use when continuing PR #226 Stage 1 folder-by-folder consistency review and reconciling confirmed findings before any canonical documentation edits."
tags:
  - consistency
  - documentation
  - review
---

# Stage 1 Consistency Review

Stage 1은 read-only consistency review다. 이 문서는 folder unit별 확인 결과, confirmed finding, protected non-finding과 다음 검토 지점을 누적한다. Canonical documentation은 Stage 2 전까지 수정하지 않는다.

## Review Contract

- 실제 contradiction, authority drift, stale contract, ownership duplication과 material terminology ambiguity만 finding으로 승격한다.
- 단순 표현 선호나 readability 문제는 Stage 3 후보로 분리한다.
- 다른 folder의 독립 문제는 즉시 수정하지 않고 cross-folder queue에 남긴다.
- `INDEX.tsv`, dashboard, instruction/Agent Asset surface는 기존 계획의 boundary를 따른다.

## F0 — `docs/documentation/`

Status: **Complete — no change required**

Reviewed:

- `docs/documentation/README.md`
- `docs/documentation/principles.md`
- `docs/documentation/frontmatter.md`
- `docs/documentation/readme-authoring.md`
- `frontmatter.json`
- `.rulesync/rules/markdown.md`

Findings:

- Confirmed material finding 없음.
- `README.md`는 policy entrypoint와 routing을 소유하고 세부 policy는 각 owner로 위임한다.
- `principles.md`는 일반 문서 품질·ownership·canonical-source 원칙을 소유한다.
- `frontmatter.md`는 metadata 적용과 `description` 작성 기준을 소유하며 schema ownership을 `frontmatter.json`에 둔다.
- `readme-authoring.md`는 README entrypoint 책임과 작성 기준만 소유한다.
- `frontmatter.json`의 required `title`/`description` 및 optional taxonomy가 문서 설명과 일치한다.
- Markdown rule의 paragraph line-break/readability 요구가 documentation policy와 충돌하지 않는다.

Protected non-findings:

- README와 세부 policy 사이의 짧은 요약·link는 navigation context이며 competing source of truth로 보지 않는다.
- generated `INDEX.tsv` 언급은 ownership boundary 설명이며 중복 policy가 아니다.

## F1 — `docs/` Root Documents

Status: **Complete — one material finding**

Reviewed:

- `docs/README.md`
- `docs/VISION.md`
- `docs/mvp.md`
- `docs/ARCHITECTURE.md`
- `docs/language.md`
- supporting `docs/AGENTS.md`
- supporting `DEVELOPMENT.md`
- supporting `docs/domains/data-platform.md`
- supporting Reliability contract/source evidence

Confirmed finding:

### C1 — MVP overuses concrete `RecoveryProposal` as the generic recovery proposal concept

`docs/mvp.md`의 System Proof, invariant와 Scope 일부는 recovery 전체의 승인 대상을 concrete `RecoveryProposal` 타입으로 표현한다. 그러나 `docs/ARCHITECTURE.md`, `docs/domains/reliability.md`와 implementation은 partition/freshness용 `RecoveryProposal`과 schema/table용 `SchemaRecoveryProposal`을 별도 contract 계열로 유지한다.

MVP는 current goal/scope/acceptance owner이지 exact contract type owner가 아니므로, recovery scope 전체를 설명하는 위치에서는 generic `validated recovery proposal` 수준으로 표현하고 concrete type을 하나로 일반화하지 않는 편이 owning boundary와 일치한다. Stage 2에서는 `mvp.md` 안에서 이 추상화 drift만 최소 수정한다.

Protected non-findings:

- `Silver / Gold`와 `dbt staging / marts`는 서로 모순된 layer 정의가 아니다. `DEVELOPMENT.md`가 `Silver / Gold`의 책임을 staging/mart로 명시하고 `docs/domains/data-platform.md`도 dbt Bronze-to-Gold 구조 안에서 staging/mart object를 설명한다. 필요하면 Stage 3 readability에서 mapping을 더 쉽게 보이게 할 수 있지만 Stage 2 consistency fix는 요구하지 않는다.
- `VISION.md`의 장기 delegation 확대 가능성과 `mvp.md`의 advisory-only Agentic boundary는 lifecycle/abstraction 차이다. 현재 MVP가 장기 vision을 위반하지 않는다.
- `docs/README.md`는 navigation과 ownership summary에 머물고 capability contract를 재정의하지 않는다.
- `language.md`는 current Markdown/documentation surface와 충돌하지 않는다.
- Airflow를 data-plane orchestration으로 제한하는 설명은 `mvp.md`와 `ARCHITECTURE.md`가 일치한다.

Next: F2 `docs/domains/`.

## Confirmed Findings

| ID | Owner / target | Finding | Planned Stage 2 action |
| --- | --- | --- | --- |
| C1 | `docs/mvp.md` | Generic recovery concept가 concrete `RecoveryProposal` type으로 과도하게 표현됨 | recovery-wide 문구만 generic validated recovery proposal로 최소 정리 |

## Cross-Folder Queue

아직 없음.

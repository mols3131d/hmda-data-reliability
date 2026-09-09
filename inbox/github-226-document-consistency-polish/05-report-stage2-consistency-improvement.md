---
type: report
title: "Stage 2 Consistency Improvement"
description: "Use when verifying the completed PR #226 consistency fixes and the semantic baseline that Stage 3 readability edits must preserve."
tags:
  - consistency
  - documentation
  - improvement
---

# Stage 2 Consistency Improvement

Stage 2는 Stage 1에서 확정한 C1–C3만 수정했다. 새 finding이나 readability-only edit를 섞지 않았다.

## Applied Changes

| Finding | Target | Applied change |
| --- | --- | --- |
| C1 | `docs/mvp.md` | recovery-wide `RecoveryProposal` 표기를 generic validated recovery proposal 개념으로 변경 |
| C1 | `README.md` | project summary, design boundary와 MVP diagram의 generic recovery 표기를 정리 |
| C2 | `docs/domains/README.md` | Review AI와 Runtime AI navigation link 추가 |
| C3 | `README.md` | LangGraph를 Remediation으로, OpenAI Python SDK를 AI runtime으로 표현해 current owner/source와 정렬 |

## Verification

### C1 — Recovery abstraction

Pass. Root README와 MVP는 generic recovery concept만 설명하고, `docs/ARCHITECTURE.md`와 `docs/domains/reliability.md`의 concrete `RecoveryProposal` / `SchemaRecoveryProposal` distinction은 변경하지 않았다. Exact contract owner를 상위 entry/MVP 문서가 다시 정의하지 않는다.

### C2 — Domain navigation

Pass. `docs/domains/README.md`는 기존 navigation 구조를 유지하면서 `Review AI`, `Runtime AI` 두 link만 추가했다. `OVERVIEW.md` ownership map을 복제하지 않았다.

### C3 — Toolchain ownership

Pass. Root README의 Toolchain은 `DEVELOPMENT.md`와 source evidence에 맞춰 LangGraph를 deterministic remediation draft workflow에, OpenAI Python SDK를 bounded AI runtime에 연결한다. `review_ai`의 semantic ownership이나 provider contract를 README가 새로 정의하지 않는다.

### Scope check

Pass. Canonical documentation changed files는 다음 세 개뿐이다.

- `README.md`
- `docs/mvp.md`
- `docs/domains/README.md`

Vision, Architecture, domain detail guides, development guides, OpenSpec, source/test, dashboard와 instruction surface는 Stage 2에서 수정하지 않았다.

## Semantic Baseline

Stage 3 readability polish가 보존해야 할 post-consistency baseline:

- Canonical-state commit: `bc0914b7db4061fcb0aa6b89769324abd40cbe06`
- `README.md` blob: `844d2b181e5cbd6611bd70469d6f37842abd9e9b`
- `docs/mvp.md` blob: `3c88390c70203d6f73829fa35e1cf10fac2637dc`
- `docs/domains/README.md` blob: `d8737f4e740e30c5b474c8362041d22b17c8b936`

이 baseline이 고정하는 의미:

- AI는 current MVP에서 advisory이며 mutation authority가 없다.
- Human approval은 validated recovery proposal에 결합된다. Concrete proposal type은 recovery scope owner가 구분한다.
- Airflow는 data plane을 소유하고 Reliability control plane/approval/recovery를 자동 결합하지 않는다.
- Review AI와 Runtime AI는 distinct current domains다.
- LangGraph는 remediation draft workflow, OpenAI Python SDK는 bounded provider runtime에 사용된다.

## Stage 2 Gate

- [x] C1 — `docs/mvp.md`
- [x] C2 — `docs/domains/README.md`
- [x] C1/C3 — root `README.md`
- [x] cross-document logical validation
- [x] semantic baseline recorded

Deterministic Markdown/docs validation은 Stage 3 authored edits와 generated projection 후 Stage 4에서 최종 실행·판정한다.

Next: **Stage 3 — Readability Polish**. 의미·authority·scope·acceptance를 변경하지 않는다.

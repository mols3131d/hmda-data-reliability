---
type: report
title: "Stage 2 Consistency Improvement"
description: "Use when verifying PR #226 Stage 2 fixes for the three Stage 1 consistency findings and establishing the post-consistency semantic baseline."
tags:
  - consistency
  - documentation
  - improvement
---

# Stage 2 Consistency Improvement

Stage 2는 Stage 1에서 확정한 C1–C3만 수정한다. 새 finding을 이유로 scope를 확장하지 않으며 readability-only edit는 Stage 3까지 보류한다.

## Accepted Work

| Finding | Writable target | Allowed change |
| --- | --- | --- |
| C1 | `docs/mvp.md`, `README.md` | recovery-wide 문구에서 concrete `RecoveryProposal`을 generic validated recovery proposal 개념으로 정리 |
| C2 | `docs/domains/README.md` | Review AI와 Runtime AI navigation link 추가 |
| C3 | `README.md` | LangGraph/AI runtime Toolchain label을 current owner와 source에 맞게 정리 |

## Pre-Change State

- `README.md`: `ee640e7dc897994daa0d046b083c70a8b9752b53`
- `docs/mvp.md`: `d8c7c81627d0344f614e01bc181d9088f0ecfcba`
- `docs/domains/README.md`: `de17d7daa3cd8316a4e5dd2ede63766951b24d29`

## Constraints

- `docs/ARCHITECTURE.md`와 `docs/domains/reliability.md`의 concrete proposal type distinction은 변경하지 않는다.
- Vision, OpenSpec, source/test, dashboard와 instruction surface는 수정하지 않는다.
- Stage 3 readability polish를 Stage 2에 섞지 않는다.
- 각 edit 뒤 target owner/evidence와 diff를 다시 확인한다.

## Progress

- [ ] C1 — `docs/mvp.md`
- [ ] C2 — `docs/domains/README.md`
- [ ] C1/C3 — root `README.md`
- [ ] cross-document logical validation
- [ ] semantic baseline recorded

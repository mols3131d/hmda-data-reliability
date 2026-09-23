# 00 — Revalidate OpenSpec Planning Before Remediation

## Goal

18번 review의 F1–F3을 current HEAD에서 다시 확인하고, active `review-ai-utility-evaluation` `spec-driven-tdd` Change의 planning/task state가 actual remediation을 올바르게 소유하게 한다.

## Freshness Check

구현 계획을 고치기 전에 PR head와 base `main`의 관계를 확인한다.

- `main`이 materially 움직여 current source/spec/test 판단에 영향을 줄 수 있으면 repository VCS policy에 따라 먼저 sync 필요성을 판단한다.
- sync가 필요하면 history rewrite 없이 현재 workflow가 허용하는 방식으로 처리하고 F1–F3 applicability를 다시 확인한다.
- base divergence가 immaterial하면 불필요한 sync만을 위해 작업을 중단하지 않는다.

## Why First

이 Change의 code-facing remediation은 active OpenSpec workflow가 lifecycle을 소유한다. `tasks.md`가 완료 상태라는 이유만으로 implementation defect를 planning 밖에서 바로 수정하지 않는다.

## Work

1. current HEAD에서 F1–F3이 여전히 재현 가능한지 source/spec/tests로 확인한다.
1. 각 finding을 다음 중 하나로 분류한다.
   - 기존 task의 implementation/test defect
   - planning artifact의 semantic defect
   - 이미 해결되어 더 이상 적용되지 않음
1. 기존 task가 owner이면 해당 task의 완료 상태를 다시 열거나 완료 조건을 current requirement에 맞게 수정한다.
1. Checklist 상태를 바꾸면 `tasks_completed`/`tasks_total` 같은 schema-owned progress metadata도 실제 상태와 일치시킨다. Review process 자체를 새 task로 추가하지 않는다.
1. Proposal/spec/design이 잘못된 경우 가장 이른 owning artifact를 먼저 수정하고 직접 영향받는 downstream만 다시 일치시킨다.
1. 새로운 독립 requirement를 만들지 않는다. Current Change 범위 밖이면 blocker/follow-up으로 분리한다.

## Boundaries

- 이 단계에서 application/runtime 구현을 수정하지 않는다.
- Review finding 번호 자체를 canonical requirement로 만들지 않는다.
- 과거 Inbox 설명보다 current canonical spec, active delta, source/tests와 schema workflow를 우선한다.

## Validation

- OpenSpec validation이 통과한다.
- F1–F3 각각에 current owner와 remediation path가 명확하다.
- task checkbox와 progress metadata가 actual state와 일치한다.
- implementation work를 시작할 수 있도록 task/dependency state가 actual state와 일치한다.

## Done When

F1–F3의 current applicability와 owning planning/task가 확인되고, 필요한 planning correction과 progress state가 implementation보다 먼저 정합화됐으면 Stage 0을 완료한다. 그 후에만 01로 이동한다.

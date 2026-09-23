# 05 — Reconcile OpenSpec with the Corrected Implementation

## Goal

Active `review-ai-utility-evaluation` OpenSpec change의 requirement, design, tasks와 현재 구현·tests가 같은 상태를 설명하게 한다.

## Scope

Stage 1 수정 후에만 수행한다.

현재 `tasks.md`가 완료로 표시되어 있다는 사실을 구현 완료의 근거로 사용하지 않는다. Stage 1에서 requirement interpretation이나 구현 shape가 바뀌었다면 proposal/design/spec/tasks를 필요한 최소 범위에서 맞춘다.

OpenSpec을 이용해 새 기능을 추가하거나 Langfuse scope를 끌어오지 않는다.

## Review Questions

- F1의 typed failure boundary가 현재 requirement/design과 일치하는가?
- F2의 세 semantic control role이 normative requirement와 implementation 모두에 명시되는가?
- F3의 bounded evidence boundary가 prompt와 validator에서 같은 의미인가?
- 완료 task가 실제 proof와 일치하는가?
- offline utility proof와 global Live Agentic proof의 경계가 유지되는가?

## Validation

- OpenSpec validation을 실행한다.
- spec scenario와 focused test를 대응시켜 빠진 requirement proof가 없는지 확인한다.
- 구현 세부를 normative spec에 불필요하게 고정하지 않는다.

## Done When

OpenSpec과 code/tests 사이에 알려진 semantic drift가 없고 task completion claim이 실제 current evidence와 맞으면 완료한다. 완료 후에만 06으로 이동한다.

# Research

`research`는 결정, specification 또는 구현 전에 중요한 질문에 근거를 바탕으로 답하는 것이 주된 목적일 때 사용한다.

Research는 working non-canonical artifact다. 이후 판단을 지원하지만 requirement, design, implementation 또는 project documentation 자체를 정본으로 확정하지 않는다.

## Contract

- 하나의 핵심 질문과 그 질문에 답하는 데 필요한 범위를 명확히 한다.
- 조사 순서가 아니라 현재 근거로 답할 수 있는 결론을 먼저 보여준다.
- Material한 경우 verified fact, inference, assumption, conflict와 unresolved uncertainty를 구분한다.
- 중요한 결론은 다시 확인할 수 있는 evidence와 연결한다.
- 답이나 후속 판단을 실질적으로 바꿀 수 있는 alternative, implication과 open question만 남긴다.
- 근거가 부족한 부분을 확신으로 채우지 않고 답의 중요한 한계를 드러낸다.

## Frontmatter

[`inbox/AGENTS.md`](../AGENTS.md)의 common artifact contract를 따른다. Research가 추가로 요구하는 frontmatter field는 `type: research` 외에는 없다.

`description`에는 조사 질문과 이 결과가 지원할 판단 또는 사용 목적을 적는다. 상단 답변을 다시 요약하는 용도로 사용하지 않는다.

`status`는 기본적으로 추가하지 않는다. Inbox는 canonical status projection이 아니며, research의 완료·차단 상태는 applicable workflow와 현재 답변이 소유한다. 다른 governing contract가 metadata를 명시적으로 요구할 때만 따른다.

`tags`는 optional이며 common Inbox contract를 따른다. 이 guideline은 research 전용 taxonomy를 별도로 정의하지 않는다.

## Structure

독자가 문서를 처음부터 끝까지 읽지 않아도 현재 답, 핵심 근거, 후속 의미와 중요한 불확실성을 복구할 수 있게 구성한다.

Template의 기본 순서는 다음과 같다.

1. leading answer callout
1. `Question`
1. `Scope`
1. `Findings`
1. optional `Options`
1. optional `Implications`
1. optional `Open Questions`

Leading callout이 현재 답의 단일 owner다. 같은 결론을 반복하는 별도 `Conclusion` section을 만들지 않는다.

표준 section으로 표현하기 어려운 material information에만 task-specific section을 추가한다. 기존 section의 책임을 중복하거나 특별한 이유 없이 이름을 바꾸지 않는다.

### Question and Scope

핵심 질문은 evidence로 답할 수 있을 만큼 구체적으로 작성한다. `Scope`에는 포함 경계를 적고, 제외 사실을 명시하지 않으면 incomplete research로 오해할 수 있을 때만 `Out of Scope`를 유지한다.

Investigation stop condition은 결과 문서의 section으로 출력하지 않는다. 조사 방법과 종료 판단은 research workflow가 소유한다.

### Findings

각 H3는 `Finding 1`, `Analysis` 같은 일반 label보다 finding 자체를 설명하는 제목을 사용한다.

`F1`, `F2` 같은 stable ID는 optional이다. 긴 artifact, discussion 또는 follow-up에서 finding을 반복 참조해야 할 때만 사용한다.

본문에서는 무엇을 확인했고 무엇을 추론했는지, 그리고 그것이 핵심 질문에 왜 중요한지 필요한 만큼 설명한다. 의미가 이미 분명한데 모든 finding에 `Evidence`, `Implication` 같은 subsection을 기계적으로 반복하지 않는다.

### Evidence

Evidence는 지원하는 claim 가까이에 두고, 중요한 결론을 다시 검증할 수 있을 만큼 locator를 남긴다.

단순한 finding은 inline link 또는 footnote만으로 충분할 수 있다. 여러 source, file, test, requirement, observation 또는 locator를 함께 보여주는 편이 더 읽기 쉬울 때만 `Evidence` H4를 사용한다.

`Evidence` section을 사용하면 다음 구조를 따른다.

- source, file, artifact, Pull Request, Issue 또는 external document를 top-level bullet로 둔다.
- symbol, test, requirement, section, line reference 또는 짧은 관찰을 해당 source의 nested bullet로 둔다.
- stable link가 있으면 직접 이동 가능한 target을 연결한다.
- path와 identifier spelling을 정확히 유지한다.
- 같은 사실을 반복 확인하는 데 그치는 source를 불필요하게 나열하지 않는다.

Footnote는 provenance, secondary evidence, exception 또는 본문 흐름을 끊는 보조 설명에 사용한다. Core evidence, material uncertainty 또는 result-changing conflict를 footnote에 숨기지 않는다.

### Options

여러 plausible alternative가 답이나 후속 판단을 실질적으로 바꿀 수 있을 때만 `Options`를 유지한다.

같은 criterion으로 비교할 수 있으면 table을 사용하고, 구조가 서로 다르거나 표가 오히려 이해를 어렵게 만들면 prose나 list를 사용한다. 강한 evidence로 질문에 이미 답했다면 완결성을 위해 option을 추가로 수집하지 않는다.

### Implications

Research 결과가 이후 decision, plan, specification, validation target 또는 work boundary를 실질적으로 바꿀 때만 사용한다.

Evidence가 다음 판단에 무엇을 의미하는지 설명하되 research artifact 자체를 canonical decision이나 requirement로 만들지 않는다. 의미 있는 다음 행동이 없으면 형식적인 `Next Step` section을 만들지 않는다.

### Open Questions

현재 답, confidence, scope 또는 후속 판단을 바꿀 수 있는 unresolved question과 conflict만 남긴다.

필요하면 각 question 아래에 무엇을 확인하거나 결정해야 해결되는지 nested bullet로 적는다. 관련 없는 개선 backlog로 사용하지 않는다.

## Investigation and Completion

Current behavior, scope, dependency, alternative 또는 failure를 evidence-backed 방식으로 조사할 때는 `prj-research-workspace`를 사용한다. Evidence search, rigor, conflict handling, stop condition과 completion semantics는 해당 workflow가 소유하고, 이 guideline은 Inbox research artifact의 content와 presentation contract를 소유한다.

Artifact에는 조사 활동 로그가 아니라 synthesized result를 남긴다. Raw log, large generated output, exhaustive link collection과 상세 activity history는 그 자체가 필요한 evidence가 아니면 포함하지 않고 reproducible locator, command 또는 supporting artifact를 우선한다.

## Resources

- Template: [`inbox/_templates/research.md`](../_templates/research.md)
- Skill: `prj-research-workspace`

질문에 도움이 되는 resource만 사용하고, optional template section은 결과를 개선하지 않으면 생략한다.

## Boundaries

- Investigation question이 없는 단순 reference dump나 summary를 `research`로 만들지 않는다.
- 관련 없는 repository-wide investigation으로 범위를 넓히지 않는다.
- Unverified assumption을 repository fact처럼 표현하지 않는다.
- 독자에게 synthesized answer가 필요한데 chronological work log로 바꾸지 않는다.
- Research artifact를 canonical requirement, design, implementation plan 또는 project decision으로 취급하지 않는다.
- Common artifact와 lifecycle rule은 `inbox/AGENTS.md`를 따른다.

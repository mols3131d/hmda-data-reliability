# Template Authoring

`inbox/_templates/**`의 템플릿을 새로 만들거나 구조·내용을 개선할 때 적용한다. 템플릿은 작성 양식을 통일하기 위한 목적이 아니라 **사람과 Agent가 작업 결과를 적은 비용으로 이해하고, 근거를 검토하며, 다음 판단이나 행동으로 이어가게 하는 출발점**이다.

## Purpose

- **Human decision support** — 상단에서 핵심 결과, 중요한 위험과 필요한 행동을 파악하고, 필요할 때 근거를 따라갈 수 있게 한다.
- **Context reuse** — 다른 session 또는 Agent가 전체 탐색을 반복하지 않고 현재 판단의 근거, 미해결 사항과 재개 지점을 찾게 한다.
- **Consistent evidence** — 같은 종류의 artifact에서 판단에 필요한 정보를 빠뜨리지 않되, 양식 충족 자체를 목적으로 삼지 않는다.

## Principles

- **Purpose before structure** — 해당 artifact를 읽는 사람이 답해야 할 질문과 해야 할 행동에서 section을 도출한다. 모든 템플릿에 동일한 구조를 강요하지 않는다.
- **Minimum sufficient context** — 의미와 중요한 제약을 보존하는 최소한의 내용을 요구한다. 단어 수나 토큰 수를 줄이기 위해 결정 근거, 불확실성 또는 필요한 조치를 생략하지 않는다.
- **Human-first readability** — 결론과 action을 앞에 두고 짧은 prose, list, table 중 가장 쉽게 읽히는 표현을 선택한다. 넓은 표, 과도한 heading 또는 Agent 전용 표현을 기본값으로 두지 않는다.
- **Progressive disclosure** — 빠른 판단용 요약과 필요한 경우에만 읽는 상세 근거를 분리한다. 한 사실이나 결론의 설명을 여러 section에서 반복하지 않는다.
- **Evidence and uncertainty** — 확인된 사실, 추론, 결정, 제안과 미검증 상태를 구분하고 material claim은 직접 확인 가능한 근거에 연결한다.
- **One owner per meaning** — 각 정보의 소유 section을 분명히 하고 canonical source, PR, 코드·테스트 또는 다른 artifact의 장문 내용을 복제하지 않는다. 링크와 작업에 특화된 delta를 우선한다.
- **Complement, do not replace** — 기존 템플릿의 유효한 contract와 독해 패턴을 유지한다. 반복적으로 필요한 별도 질문이 생겼을 때만 선택적 section이나 특화 템플릿을 추가한다.

## Patterns

### Select and Extend

- 기존 템플릿과 type guideline이 필요한 질문을 이미 해결하면 재사용한다.
- 새 템플릿은 기존 형식을 비대하게 만들지 않고 독립적으로 선택할 이유가 있을 때 추가한다.
- Required 항목은 owning contract가 요구하는 것만 유지한다. 선택적 section과 예시 행은 적용되지 않으면 제거하도록 표시한다.

### Lead and Expand

- 결과·판단·행동이 핵심인 artifact는 상단에 이를 먼저 두고 대상, 범위, 기준 revision처럼 해석에 필요한 맥락을 가까이 둔다.
- 반복 비교가 필요할 때만 짧은 summary table을 사용한다. 근거나 조건이 길어지면 세부 section 또는 링크로 분리한다.
- 여러 요약과 상세를 연결해야 할 때만 안정적인 ID를 사용한다. ID와 field가 독해보다 관리 부담을 늘리면 생략한다.

### Preserve Decisions

- 여러 후보나 의견을 종합한다면 최종적으로 채택한 결과와 제외·보류한 후보를 구별한다.
- 제외·보류한 판단이 후속 작업에 중요하다면 이유, 확인한 기존 safeguard 또는 부족한 evidence와 재검토 조건을 남긴다.
- 같은 결정을 summary, 후보 목록과 상세 설명에 반복하지 않고 ID 또는 직접 링크로 연결한다. 후보의 사실성 판단과 실제 조치·승인 권한을 혼동하지 않는다.

### Support Continuation

- 세션이나 Agent 간 이어받기가 필요한 경우 현재 goal과 scope에서 **달라진 결정, 미해결 blocker, 다음 action, exact reference와 재검증 조건**만 쉽게 추출할 수 있게 한다.
- 수신자가 repository나 정상적인 context discovery로 얻는 지침, 전체 로그, 대화 기록 또는 파일 목록을 템플릿에 재수록하지 않는다.
- 별도의 장황한 Handoff section을 일률적으로 추가하지 않는다. 실제 인계에서는 [Handoff](handoff.md)를, 인간의 결정이 필요한 인계에서는 [Human Handoff](handoff-human.md)를 따른다.

### Review and Trim

- 실제 사례로 템플릿을 채웠을 때 상단만으로 핵심 상태·필요한 결정이 보이는지 확인한다.
- 각 section이 독립된 질문에 답하는지, 중복과 넓은 표를 줄일 수 있는지, optional placeholder가 결과물에 남지 않는지 점검한다.
- 근거에 접근할 수 있고 미검증·미해결 상태가 가려지지 않는지 확인한다. 검증하지 않은 결과를 통과했다고 표현하도록 유도하지 않는다.

## Boundaries

- Artifact의 type, naming, frontmatter, ownership와 lifecycle은 [Inbox](../AGENTS.md)가 소유한다.
- Artifact별 필수 내용·판정 용어·validation 형식은 해당 `_guidelines/`가 소유한다. 이 가이드는 공통 schema나 범용 verdict를 새로 정의하지 않는다.
- 템플릿 개선은 canonical decision, 새로운 권한이나 추가 handoff artifact를 만드는 근거가 아니다.

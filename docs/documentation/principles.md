---
title: "Documentation Principles"
description: "문서를 새로 만들거나 구조·내용·배치를 바꿀 때 목적, ownership, 정본, 탐색성, 현재성과 유지보수성을 판단하는 공통 원칙입니다."
categories:
  - software-engineering
tags:
  - documentation
  - markdown
---

# Documentation Principles

## Purpose

문서는 사람이 필요한 정보를 찾고 이해하며 판단하고 행동하는 데 도움을 주는 것을 우선한다. LLM과 AI Agent도 중요한 독자이지만, agent routing이나 context 비용을 줄이기 위한 최적화가 사람의 이해를 해쳐서는 안 된다.

### Human

사람은 필요한 내용을 적은 부담으로 찾고 읽어 자신의 상황에 맞는 판단과 행동으로 이어갈 수 있어야 한다.

- **이해** — 의미, 맥락과 제약을 정확하고 쉽게 파악할 수 있어야 한다.
- **인지 부담** — 필요한 만큼만 읽어도 핵심을 파악할 수 있어야 한다.
- **탐색** — 필요한 문서와 다음 정보를 쉽게 찾을 수 있어야 한다.
- **접근성** — 사용 환경이나 도구가 달라도 필요한 정보에 접근하고 이해할 수 있어야 한다.
- **판단과 행동** — 읽은 뒤 무엇을 판단하거나 해야 하는지 분명해야 한다.

### LLM and AI Agent

LLM과 AI Agent는 사람을 위한 품질을 유지하면서 필요한 문서를 적은 비용으로 선택하고 해석할 수 있어야 한다.

- **맥락 비용** — 필요한 context만 불러오고 관련 없는 내용을 섞지 않는다.
- **탐색 비용** — path와 metadata만으로 후보를 빠르게 구분할 수 있게 한다.
- **추론 비용** — 관계, 범위, 전제와 ownership을 분명히 한다.
- **검증 비용** — current state, 근거와 정본을 구분할 수 있게 한다.
- **실행 비용** — 다음 행동과 owning source를 분명히 해 잘못된 선택과 불필요한 재시도를 줄인다.

## Principles

- **독자의 필요에서 시작한다.** 작성자가 설명하고 싶은 순서가 아니라 독자가 풀어야 할 질문, 내려야 할 판단과 해야 할 행동을 기준으로 구성한다. 이해·판단·행동에 도움이 되지 않는 내용은 관성적으로 추가하지 않는다.
- **책임과 범위를 분명히 한다.** 문서마다 주된 responsibility를 분명히 하고, 그 책임을 맡을 수 있는 가장 좁은 범위에 둔다. 파일이나 디렉터리가 있다는 이유만으로 문서를 만들지 않는다. 다만 선택한 범위 안에서는 오해하지 않을 만큼 필요한 맥락과 제약을 제공한다.
- **중요한 정보부터 보여준다.** 결론, 중요한 조건과 다음 판단에 필요한 정보를 먼저 둔다. 세부 설명과 참고 자료는 필요할 때 더 깊게 볼 수 있게 연결한다.
- **하나의 의미에는 하나의 정본을 둔다.** 같은 범위에서 같은 의미를 설명하는 owning source는 하나만 둔다. 다른 문서는 정본을 다시 정의하지 않고 필요한 안내, 짧은 맥락과 링크만 제공한다.
- **현재 상태를 믿을 수 있어야 한다.** 사실, 결정, 현재 상태와 불확실성을 구분하고 필요한 근거를 확인할 수 있게 한다. 오래된 상태나 추측을 현재 지침처럼 남기지 않는다.
- **찾을 수 있고 다음으로 이어져야 한다.** 독자가 문서를 발견하고 다른 후보와 구분해 선택할 수 있어야 한다. 읽은 뒤 필요한 다음 정보로 자연스럽게 이동할 수 있어야 한다.
- **유지하기 쉽게 설계한다.** 쉽게 다시 만들거나 owning source에서 도출할 수 있는 목록과 파생 정보는 사람이 정본처럼 중복 관리하지 않는다. 같은 로컬 규칙이 반복되면 더 적절한 공통 owner가 있는지 검토한다.

## Boundaries

이 문서는 일반 문서 품질과 ownership 원칙을 소유한다. 다음 concern은 더 구체적인 owner를 따른다.

- `docs/**`의 trust boundary, phase lifecycle과 subject ownership → [`../AGENTS.md`](../AGENTS.md)
- 일반 문서 frontmatter의 schema와 required field → [`../../frontmatter.json`](../../frontmatter.json)
- frontmatter 적용과 `description` 작성 → [Frontmatter](frontmatter.md)
- README 생성과 작성 → [README Authoring](readme-authoring.md)
- Markdown 문법·표현의 repository rule → [`.rulesync/rules/markdown.md`](../../.rulesync/rules/markdown.md)

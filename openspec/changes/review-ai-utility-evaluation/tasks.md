---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: "Review AI Utility Proof Tasks"
description: "Bounded context, utility output, rubric controls와 comparison evidence를 test-first로 구현한다."
tasks_completed: 5
tasks_total: 6
tags:
  - "capability:reliability-agentic-review"
---

## Tasks

- [x] 1. Bounded Review Context contract와 deterministic builder를 구현한다
  - **Covers:** Bounded review context
  - **Test first:** canonical target의 incident identity, 명시적으로 참조된 related evidence selection, source provenance, missing/unconfirmed gap, max evidence/payload와 stable digest를 검증한다.
  - **Done when:** canonical target은 incident identity에 고정되고, 참조된 contextual Evidence는 bounded projection/provenance에 포함된다.

- [x] 2. Review prompt/provenance에 context projection을 연결한다
  - **Covers:** Context projection is bounded and replayable
  - **Test first:** 같은 input의 canonical context replay, context overflow의 typed preflight rejection, provider-visible citable ID와 validator allowlist의 동일성, raw log/전체 payload 비노출, 기존 historical output/input 호환성을 검증한다.
  - **Done when:** context overflow가 `INPUT_REJECTED/context_too_large`로 닫히고 provider/store를 호출하지 않으며, prompt와 invocation evidence가 같은 bounded context를 사용하고 draft의 citable refs와 validator allowlist가 선택된 Evidence ID로 일치한다.

- [x] 3. Structured utility contribution과 deterministic reference guard를 추가한다
  - **Covers:** Structured agentic utility contribution
  - **Test first:** 네 contribution kind, priority invariant, bounded text, provided Evidence subset과 legacy output compatibility를 검증한다.
  - **Done when:** utility contribution이 advisory output에 표현되고 fabricated reference는 기존 validation boundary에서 거부된다.

- [x] 4. `rubric_v1` human rubric과 test-only positive/negative fixtures를 구현한다
  - **Covers:** Versioned human rubric and control discrimination
  - **Test first:** 다섯 criterion completeness, score/rationale bound와 fixture 사례에 대한 human score를 검증한다. Control 결과는 runtime model이나 durable hierarchy로 저장하지 않는다.
  - **Done when:** rubric identity와 complete human scores가 유지되고 restatement/hedging 사례는 test fixture로만 판별력을 확인한다.

- [x] 5. Baseline/candidate comparison evidence를 최소화한다
  - **Covers:** Baseline and candidate utility comparison evidence
  - **Test first:** exact baseline/candidate output roles, same case/rubric/revision comparison, criterion deltas, human decision/rationale, blocked/inconclusive fail-closed와 JSON round-trip을 검증한다.
  - **Done when:** comparison model이 evaluation identities와 change-under-test를 연결하고 역할 또는 attribution mismatch를 거부하며, 별도 proof bundle/store 없이 직렬화할 수 있다.

- [ ] 6. Representative fixtures, docs와 전체 검증을 연결한다
  - **Covers:** 네 Utility Proofs와 MVP acceptance evidence
  - **Test first:** representative positive/restatement/hedging fixtures의 human rubric score, comparison JSON/Markdown rendering과 기존 `tests/review_ai` 및 관련 suite 회귀를 검증한다. 고정 점수를 evidence로 만드는 standalone proof runner는 두지 않는다.
  - **Done when:** 같은 case/version/revision의 complete evaluation이 exact baseline/candidate roles로 비교되고, PR에 실제 validation과 미검증 live provider/human-evaluation 경계가 기록된다.

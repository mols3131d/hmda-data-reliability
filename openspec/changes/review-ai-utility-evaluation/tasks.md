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
  - **Test first:** canonical target 우선순위, related evidence selection, source provenance, missing/unconfirmed gap, max evidence/payload와 stable digest를 검증한다.
  - **Done when:** `BoundedReviewContext`가 immutable bounded projection을 만들고 prompt/provenance가 재사용할 수 있다.

- [x] 2. Review prompt/provenance에 context projection을 연결한다
  - **Covers:** Context projection is bounded and replayable
  - **Test first:** 같은 input의 canonical context replay, context overflow의 typed preflight rejection, provider-visible citable ID와 validator allowlist의 동일성, raw log/전체 payload 비노출, 기존 historical output/input 호환성을 검증한다.
  - **Done when:** context overflow가 `INPUT_REJECTED/context_too_large`로 닫히고 provider/store를 호출하지 않으며, prompt와 invocation evidence가 같은 bounded context를 사용하고 draft의 citable refs와 validator allowlist가 선택된 Evidence ID로 일치한다.

- [x] 3. Structured utility contribution과 deterministic reference guard를 추가한다
  - **Covers:** Structured agentic utility contribution
  - **Test first:** 네 contribution kind, priority invariant, bounded text, provided Evidence subset과 legacy output compatibility를 검증한다.
  - **Done when:** utility contribution이 advisory output에 표현되고 fabricated reference는 기존 validation boundary에서 거부된다.

- [x] 4. `rubric_v1` human rubric과 positive/negative controls를 구현한다
  - **Covers:** Versioned human rubric and control discrimination
  - **Test first:** 다섯 criterion completeness, score/rationale bound, compliant positive `PASS`, deterministic fact/draft restatement negative `FAIL`, actionability/prioritization이 없는 hedging negative `FAIL`, 누락·중복 role 및 case/revision/outcome mismatch rejection을 검증한다.
  - **Done when:** 명시적 semantic role을 가진 세 required control이 같은 case/version/revision에서 각각 `PASS`, `FAIL`, `FAIL`로 검증되고, quality basis가 case identity와 control 결과를 digest에 바인딩해 자동 judge 없이 durable evidence로 보존한다.

- [x] 5. Baseline/candidate comparison evidence와 create-only store를 구현한다
  - **Covers:** Baseline and candidate utility comparison evidence
  - **Test first:** same case/rubric comparison, criterion deltas, human decision/rationale, blocked/inconclusive fail-closed, duplicate ID와 JSON reload를 검증한다.
  - **Done when:** comparison이 invocation identities와 change-under-test를 연결한 사람이 읽을 수 있는 durable JSON evidence를 생성한다.

- [ ] 6. Representative fixture, proof runner, docs와 전체 검증을 연결한다
  - **Covers:** 네 Utility Proofs와 MVP acceptance evidence
  - **Test first:** network 없는 baseline/candidate fixture 실행, 세 control role 결과와 case-bound basis digest의 store/reload 보존, comparison의 동일 case 및 basis digest 연결, Markdown/JSON proof rendering 및 기존 `tests/review_ai`와 관련 suite 회귀를 검증한다.
  - **Done when:** matching case/version/revision에서 세 required control 결과와 identity-bound basis digest가 저장·재로드되고 comparison이 같은 identity와 digest를 참조하며, PR에 실제 validation과 미검증 live provider 경계가 기록된다.

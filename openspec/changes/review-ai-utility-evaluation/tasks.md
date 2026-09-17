---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: "Review AI Utility Proof Tasks"
description: "Bounded context, utility output, rubric controls와 comparison evidence를 test-first로 구현한다."
tasks_completed: 6
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
  - **Test first:** 같은 input의 canonical context replay, context가 raw log/전체 payload를 노출하지 않는지, 기존 historical output/input이 계속 읽히는지 검증한다.
  - **Done when:** provider user data와 invocation evidence가 같은 context projection을 사용하고 기존 review failure/read-only contract가 유지된다.

- [x] 3. Structured utility contribution과 deterministic reference guard를 추가한다
  - **Covers:** Structured agentic utility contribution
  - **Test first:** 네 contribution kind, priority invariant, bounded text, provided Evidence subset과 legacy output compatibility를 검증한다.
  - **Done when:** utility contribution이 advisory output에 표현되고 fabricated reference는 기존 validation boundary에서 거부된다.

- [x] 4. `rubric_v1` human rubric과 positive/negative controls를 구현한다
  - **Covers:** Versioned human rubric and control discrimination
  - **Test first:** 다섯 criterion completeness, score/rationale bound, compliant positive control `PASS`, restatement negative control `FAIL`, mismatch rejection을 검증한다.
  - **Done when:** control quality basis가 자동 judge 없이 deterministic하게 재검증 가능하고 durable evaluation model을 제공한다.

- [x] 5. Baseline/candidate comparison evidence와 create-only store를 구현한다
  - **Covers:** Baseline and candidate utility comparison evidence
  - **Test first:** same case/rubric comparison, criterion deltas, human decision/rationale, blocked/inconclusive fail-closed, duplicate ID와 JSON reload를 검증한다.
  - **Done when:** comparison이 invocation identities와 change-under-test를 연결한 사람이 읽을 수 있는 durable JSON evidence를 생성한다.

- [x] 6. Representative fixture, proof runner, docs와 전체 검증을 연결한다
  - **Covers:** 네 Utility Proofs와 MVP acceptance evidence
  - **Test first:** network 없는 baseline/candidate fixture 실행, Markdown/JSON proof rendering, 기존 `tests/review_ai`와 관련 suite 회귀를 검증한다.
  - **Done when:** `rubric_v1` controls와 baseline/candidate decision evidence가 matching revision에서 재실행되고, PR에 실행한 validation과 미검증 live provider 경계가 기록된다.

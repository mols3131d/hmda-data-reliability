# 10 — Review the Frozen Final Candidate

## Goal

Stage 1–3 수정이 끝난 frozen HEAD를 대상으로 fresh technical review를 수행해 과거 review의 stale 상태를 해소한다.

## Review Surface

Fresh review는 branch HEAD를 변경하지 않는 surface를 우선한다.

- GitHub PR review/comment 또는 equivalent non-mutating review surface를 사용한다.
- 새 tracked Inbox review artifact를 추가해 review 결과를 기록하지 않는다.
- review를 위해 tracked file을 수정해야 한다면 frozen HEAD가 깨지므로 08부터 다시 수행한다.

## Scope

Review는 diff 중심으로 수행한다. 최소한 다음을 다시 확인한다.

- F1 context overflow typed boundary
- F2 durable required-control quality basis
- F3 bounded evidence identity coherence
- OpenSpec ↔ implementation ↔ tests 정합성
- ELI5 또는 다른 unrelated scope가 남지 않았는지
- offline proof와 live-human proof 경계
- final PR description/validation evidence가 frozen HEAD에 적용되는지
- future Langfuse integration을 이유로 불필요한 evaluator/store/CLI/vendor abstraction이 들어오지 않았는지

Self-review는 independent approval로 부르지 않는다. 독립 reviewer/orchestration이 실제로 사용 가능하면 current repository workflow에 따라 사용하고, 사용할 수 없으면 limitation을 명시한다.

## Finding Disposition

각 finding은 바로 수용하지 않는다.

1. current code/spec/evidence로 finding이 실제인지 확인한다.
1. 수용 시 얻는 correctness/readability/scope 이득과 복잡도·중복 비용을 비교한다.
1. unsupported, duplicate, immaterial 또는 future integration convenience만을 위한 finding은 기각한다.
1. generic abstraction, 새 persistence layer, evaluator framework처럼 현재 defect보다 큰 구조를 요구하면 더 작은 대안이 없는지 먼저 확인한다.
1. 수용한 finding은 가장 이른 실제 owner로 돌린다. Code/spec/test defect는 Stage 0–2, validation freshness 문제는 08, PR description 문제는 09가 owner다.

Langfuse 관련 finding은 다음 조건을 모두 만족할 때만 #245에 수용한다.

- Langfuse가 없어도 현재 #245 contract의 correctness 문제다.
- current requirement 또는 reachable runtime/test evidence로 재현된다.
- 가장 작은 수정이 #245의 기존 scope 안에 있다.

그 외에는 14의 follow-up research 대상으로만 넘긴다.

## Result Handling

- blocking finding 없음 → 11로 진행
- blocking finding 수용 → 가장 이른 owning stage로 돌아가 수정하고, tracked file이 바뀌었으면 08부터 validation/review chain을 다시 수행
- finding 기각 → 근거를 review surface에 남기고 frozen HEAD 유지
- evidence 부족 → `not_ready` 상태로 유지하고 부족한 proof를 먼저 확보

## Done When

Frozen final HEAD에 적용되는 fresh review에서 unresolved blocking finding이 없고 accepted/rejected finding의 근거와 remaining limitation이 명확하며, speculative Langfuse preparation이 merge blocker로 승격되지 않았으면 완료한다.

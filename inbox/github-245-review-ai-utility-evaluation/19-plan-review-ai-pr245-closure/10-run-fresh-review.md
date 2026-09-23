# 10 — Review the Exact Final Candidate

## Goal

Stage 1–3 수정이 끝난 exact HEAD를 대상으로 fresh technical review를 수행해 과거 review의 stale 상태를 해소한다.

## Scope

Review는 diff 중심으로 수행한다. 최소한 다음을 다시 확인한다.

- F1 context overflow typed boundary
- F2 durable three-role quality basis
- F3 bounded evidence identity coherence
- OpenSpec ↔ implementation ↔ tests 정합성
- ELI5 또는 다른 unrelated scope가 남지 않았는지
- offline proof와 live-human proof 경계
- final PR description/validation evidence가 current state에 적용되는지

Self-review는 independent approval로 부르지 않는다. 독립 reviewer/orchestration이 실제로 사용 가능하면 current repository workflow에 따라 사용하고, 사용할 수 없으면 limitation을 명시한다.

## Result Handling

- blocking finding 없음 → 11로 진행
- blocking finding 있음 → 해당 01–07 작업으로 돌아가 수정 후 08–10을 다시 수행
- evidence 부족 → `not_ready` 상태로 유지하고 부족한 proof를 먼저 확보

## Done When

Exact final HEAD에 적용되는 fresh review에서 unresolved blocking finding이 없고 remaining limitation이 명확히 분리되면 완료한다.

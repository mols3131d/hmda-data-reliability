# 09 — Refresh the Pull Request Description

## Goal

PR #245 body가 오래된 완료 주장이나 revision을 제거하고 final candidate HEAD의 실제 scope, validation과 limitation을 설명하게 한다.

## Preconditions

08의 final validation이 완료된 뒤 작성한다. 이후 material change가 생기면 revision/validation section을 다시 갱신한다.

## Requirements

Repository Pull Request template과 language policy를 따른다. PR description은 영어로 작성한다.

반드시 현재 사실로 갱신할 항목:

- Summary
- 실제 Changes
- final Validation
- Review Focus
- remaining `Not Verified` boundary
- References
- exact `revision.base` / `revision.head` metadata

다음 stale claim은 현재 evidence 없이 유지하지 않는다.

- 과거 blocker가 모두 해결됐다는 주장
- 과거 `review-lead` 결과가 final HEAD에도 그대로 적용된다는 주장
- 과거 test count/CI가 current validation이라는 주장
- offline `compared / accept`가 실제 live human utility를 증명한다는 인상

Langfuse는 후속 PR이며 #245 change summary에 구현된 기능처럼 넣지 않는다.

## Done When

Reviewer가 PR body만 읽어도 current diff의 목적, 검증된 범위, 미검증 범위와 exact revision을 잘못 해석하지 않을 수 있으면 완료한다. 완료 후에만 10으로 이동한다.

# 12 — Merge PR #245 after Explicit Approval

## Goal

PR #245를 안전하게 `main`에 반영하고 Langfuse 후속 PR이 시작할 안정된 baseline을 만든다.

## Authorization Gate

이 파일이 존재한다는 사실은 merge 권한이 아니다. 사용자가 해당 시점에 PR #245 merge를 명시적으로 요청한 뒤에만 실행한다.

## Pre-Merge Check

Merge 직전에 mutable state를 다시 확인한다.

- PR이 open인지
- exact head SHA가 08–11의 evidence와 같은지
- base `main`이 material하게 움직이지 않았는지
- required/current CI가 성공했는지
- mergeability가 clean인지
- unresolved review thread/review가 있는지
- Draft/Ready lifecycle이 repository policy와 사용자 요청에 맞는지

Base/head가 바뀌어 evidence가 stale해지면 merge하지 않고 필요한 sync/validation/review 단계로 돌아간다.

## Merge

Repository가 허용하고 현재 history에 적합한 merge strategy를 사용한다. Public branch history를 merge 전에 임의로 rewrite하지 않는다.

Expected-head guard를 사용할 수 있으면 사용해 검증한 HEAD와 다른 commit이 병합되지 않게 한다.

## Post-Merge Check

- PR이 merged/closed인지 확인한다.
- resulting main commit SHA를 기록한다.
- #245가 실제로 `main`에 포함됐는지 확인한다.
- 이 시점 이후에만 `13-langfuse-next-pr.md`를 활성화한다.

## Done When

PR #245가 검증한 final change로 `main`에 반영되고 resulting revision을 식별할 수 있으면 closure가 완료된다.

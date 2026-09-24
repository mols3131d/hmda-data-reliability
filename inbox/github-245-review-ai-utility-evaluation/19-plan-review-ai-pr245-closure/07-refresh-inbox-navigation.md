# 07 — Refresh Inbox Navigation if It Blocks Handoff

## Goal

PR #245 Inbox의 stale navigation이 다음 작업자를 실제로 혼란스럽게 할 때만 최소 정리한다. 이 작업은 correctness나 merge readiness의 필수 gate가 아니다.

## Trigger

다음 중 하나가 실제로 확인될 때 수행한다.

- `17-brief-review-ai-artifact-index.md` 때문에 18번 current review 또는 19번 closure plan을 찾기 어렵다.
- 오래된 proposal/archive가 current verdict처럼 보인다.
- handoff 시 next action을 잘못 선택할 현실적인 위험이 있다.

그렇지 않으면 아무 repository change 없이 건너뛴다.

## Scope

정리가 필요하면 가장 작은 navigation change만 한다.

- 18번 high-confidence review를 latest correctness review entry로 찾을 수 있게 한다.
- 19번 staged closure bundle을 next-action entry로 찾을 수 있게 한다.
- stale artifact를 current truth로 표현하지 않는다.
- 쉽게 재생성할 수 있는 전체 status/history table을 만들지 않는다.
- Container root README나 directory 재편은 별도 필요성이 없으면 하지 않는다.

## Validation

- 링크가 current branch에서 유효하다.
- navigation이 canonical spec/code 상태를 재정의하지 않는다.
- 변경했다면 Markdown/Inbox validation을 통과한다.

## Done When

Material handoff risk가 있으면 최소 navigation correction과 validation이 완료되었을 때 끝난다. Risk가 없으면 repository를 바꾸지 않고 이 단계를 생략한다. 어느 경우에도 이 단계 자체가 merge readiness를 증명하지 않는다.

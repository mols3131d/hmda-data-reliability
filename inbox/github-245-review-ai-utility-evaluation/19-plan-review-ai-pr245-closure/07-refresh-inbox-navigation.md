# 07 — Refresh Inbox Navigation without Owning Status

## Goal

PR #245 Inbox에서 최신 review와 closure plan을 쉽게 찾을 수 있게 하되, navigation 문서가 authoritative status나 history를 소유하지 않게 한다.

## Scope

현재 `17-brief-review-ai-artifact-index.md`는 #15 시점의 gap tracking을 중심으로 되어 있어 18번 review bundle과 19번 closure bundle을 충분히 반영하지 않는다.

가장 작은 방식으로 navigation을 정리한다.

- 18번 high-confidence review를 최신 correctness review entry로 찾을 수 있게 한다.
- 19번 staged closure bundle을 next-action entry로 찾을 수 있게 한다.
- 15번 archive와 과거 proposal이 현재 verdict처럼 보이지 않게 한다.
- 쉽게 재생성할 수 있는 전체 status table을 새로 만들지 않는다.

Container root README로 navigation을 옮기는 것은 필요성이 명확할 때만 별도로 판단한다. 이 작업의 완료를 위해 directory 구조를 추가로 재편할 필요는 없다.

## Validation

- 링크가 현재 branch에서 유효하다.
- navigation이 canonical spec/code 상태를 재정의하지 않는다.
- Markdown/Inbox validation을 통과한다.

## Done When

다음 작업자가 18번 review와 19번 closure plan을 먼저 찾을 수 있고 stale artifact를 current truth로 오해할 가능성이 낮아지면 Stage 2를 완료한다.

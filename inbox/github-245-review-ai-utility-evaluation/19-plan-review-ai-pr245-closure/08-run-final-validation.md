# 08 — Freeze and Validate the Final Candidate HEAD

## Goal

Stage 1과 Stage 2가 끝난 exact candidate HEAD를 freeze하고 merge/readiness 판단에 사용할 새 validation evidence를 만든다.

## Preconditions

00–06의 blocking work가 완료되어야 한다. 07은 navigation hygiene이 실제 handoff를 방해할 때만 선행한다.

## Freeze Rule

이 단계가 성공한 뒤에는 tracked repository file을 변경하지 않는다.

- PR body, review/comment처럼 branch HEAD를 바꾸지 않는 metadata는 갱신할 수 있다.
- code/spec/test/docs/inbox 등 tracked file이 하나라도 바뀌면 freeze가 깨진 것으로 보고 이 단계부터 다시 수행한다.
- base `main`이 material하게 움직여 prospective merge state가 바뀌면 필요한 sync 여부를 판단하고, 영향을 받으면 다시 validation한다.

## Validation Set

Repository의 현재 guidance와 change impact를 기준으로 실제 명령을 선택하되 최소한 다음 범위를 포함한다.

- focused Review AI tests
- utility proof script tests
- relevant runtime/dependency boundary tests
- OpenSpec validation
- Python lint/type/format checks applicable to changed code
- Markdown/Inbox validation
- prospective-merge CI 또는 repository가 요구하는 current PR CI

과거 test count나 CI run을 현재 결과로 복사하지 않는다.

Langfuse service, Langfuse SDK integration 또는 새 live-human-eval transport는 #245 final validation의 필수 조건이 아니다. Existing opt-in live provider proof도 current #245 acceptance가 요구하는 범위만 정확히 기록하며, 외부 서비스를 추가로 호출해 merge evidence를 만들지 않는다.

## Scope Assertion

Final candidate에서 다음이 참인지 함께 확인한다.

- F1–F3 remediation이 current contract만 닫는다.
- offline proof를 live human evaluation으로 과장하지 않는다.
- future Langfuse convenience를 위한 evaluator/store/CLI/vendor abstraction이 추가되지 않았다.
- Langfuse가 없어도 모든 deterministic/core validation이 실행 가능하다.

## Record

다음 identity를 정확히 남긴다.

- base SHA
- frozen head SHA
- prospective merge SHA가 제공되면 해당 SHA
- CI run ID/status
- 실행한 focused validation과 결과
- 의도적으로 실행하지 않은 live provider/external-service 범위

## Done When

Frozen candidate HEAD와 prospective merge state에 직접 적용 가능한 green evidence가 있고 알려진 validation failure가 없으며 #245가 external evaluation platform 없이 설명·검증 가능하면 완료한다. 이후 tracked file이 바뀌지 않는 한 09로 이동한다.

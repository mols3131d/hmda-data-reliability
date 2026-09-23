# 06 — Remove Unrelated ELI5 Repository Scope

## Goal

PR #245의 제품 변경과 직접 관련 없는 repository-wide agent asset 변경이 diff에 남아 있지 않게 한다.

## Scope

현재 PR은 `dreambigou/eli5` source, generated route entry와 managed lock state를 함께 변경한다. 먼저 이 asset이 PR #245의 runtime/evaluation capability에 계속 필요한 repository-level dependency인지 현재 canonical evidence로 확인한다.

명시적인 지속 사용 근거가 없다면 #245에서 제거한다. 과거 ELI5 보고서는 working artifact로 남아도 되며, 그 문서를 읽기 위해 repository skill을 영구 설치할 필요는 없다.

## Managed-State Rule

`rulesync.lock`과 generated route는 직접 손으로 편집하지 않는다.

- source declaration을 repository의 정상 Rulesync workflow로 변경한다.
- local Rulesync workflow가 generated route와 lock state를 갱신하게 한다.
- Chatbot이나 원격 편집만으로 managed state를 흉내 내지 않는다.

현재 runtime에서 정상 Rulesync workflow를 실행할 수 없다면 임의 수정하지 말고 handoff/blocker로 남긴다.

## Validation

- `rulesync.jsonc`에 unrelated source가 남지 않는지 확인한다.
- generated route와 lock이 local workflow 결과와 일치하는지 확인한다.
- chatbot route validation과 관련 CI를 실행한다.
- Review AI tests가 asset 제거와 무관하게 그대로 통과하는지 확인한다.

## Done When

PR #245의 diff가 ELI5 repository capability 도입 없이 설명 가능하거나, 유지해야 할 구체적 repository-level 근거가 새로 확인되어 그 판단이 별도 evidence로 명시되면 완료한다. 완료 후에만 07로 이동한다.

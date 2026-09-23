# 06 — Resolve the ELI5 Repository Scope

## Goal

PR #245의 목적과 직접 관련 없는 repository-wide agent asset 변경이 diff에 섞이지 않게 하되, 실제 repository-level 필요성이 확인되면 근거와 함께 유지한다.

## Scope

현재 PR은 `dreambigou/eli5` source, generated route entry와 managed lock state를 함께 변경한다. 먼저 이 asset이 PR #245의 runtime/evaluation capability 또는 유지보수에 지속적으로 필요한 repository-level dependency인지 current evidence로 판단한다.

- 구체적 지속 사용 근거가 없으면 #245에서 제거한다.
- current repository-level 필요성이 확인되면 유지하되 PR 목적과의 관계를 명확히 설명한다.
- 과거 ELI5 보고서가 존재한다는 사실만으로 permanent skill installation을 정당화하지 않는다.

## Managed-State Rule

`rulesync.lock`과 generated route는 직접 손으로 편집하지 않는다.

- source declaration 변경은 repository의 정상 Rulesync workflow로 처리한다.
- generated route와 lock state는 해당 workflow 결과로 갱신한다.
- 현재 runtime에서 정상 workflow를 실행할 수 없다면 managed state를 흉내 내지 않고 blocker/handoff로 남긴다.

## Validation

- `rulesync.jsonc`, generated route, lock state가 같은 결정과 일치한다.
- chatbot route validation과 관련 CI가 통과한다.
- Review AI tests는 ELI5 유지/제거 결정과 독립적으로 통과한다.
- PR body가 실제 유지/제거 결과를 정확히 설명할 수 있다.

## Done When

ELI5 변경을 유지할지 제거할지가 current repository need와 PR coherence를 기준으로 결정되고, managed state와 validation이 그 결정과 일치하면 완료한다.

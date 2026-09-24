# 06 — Resolve the ELI5 Repository Scope

## Goal

PR #245의 목적과 직접 관련 없는 repository-wide agent asset 변경이 diff에 섞이지 않게 한다.

## Decision Rule

`dreambigou/eli5`가 repository에 일반적으로 유용하다는 사실만으로 #245 scope에 남기지 않는다.

#245에 유지하려면 다음을 모두 설명할 수 있어야 한다.

- #245의 implementation/validation/maintenance 결과에 실제로 필요하다.
- 별도 PR로 분리하면 #245의 검증 가능한 결과가 깨지거나 의미 있게 불완전해진다.
- repository-wide permanent dependency를 추가하는 비용이 그 필요성에 비례한다.

하나라도 성립하지 않으면 #245에서는 제거하고, 지속적인 repository capability가 필요하면 별도 work unit 후보로 분리한다. 과거 ELI5 보고서가 존재한다는 사실은 permanent skill installation 근거가 아니다.

## Managed-State Rule

`rulesync.lock`과 generated route는 직접 손으로 편집하지 않는다.

- source declaration 변경은 repository의 정상 Rulesync workflow로 처리한다.
- generated route와 lock state는 해당 workflow 결과로 갱신한다.
- 현재 runtime에서 정상 workflow를 실행할 수 없다면 managed state를 흉내 내지 않고 blocker/handoff로 남긴다.

## Validation

- `rulesync.jsonc`, generated route, lock state가 같은 결정과 일치한다.
- chatbot route validation과 관련 CI가 통과한다.
- Review AI tests는 ELI5 유지/제거 결정과 독립적으로 통과한다.
- PR body가 실제 결과를 정확히 설명할 수 있다.

## Done When

ELI5 변경이 #245에 필수·비분리적이라는 근거가 있으면 최소 범위로 유지되고, 그렇지 않으면 #245에서 제거되며 managed state와 validation이 그 결정과 일치하면 완료한다.

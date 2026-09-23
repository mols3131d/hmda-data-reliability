# 08 — Run Final Validation on the Candidate HEAD

## Goal

Stage 1과 Stage 2가 끝난 exact candidate HEAD에 대해 merge/readiness 판단에 사용할 새 validation evidence를 만든다.

## Preconditions

01–07이 완료되기 전에는 이 작업을 시작하지 않는다. 이후 material code/spec/scope change가 생기면 이 validation은 stale로 간주하고 다시 실행한다.

## Validation Set

Repository의 현재 guidance와 change impact를 기준으로 실제 명령을 선택하되 최소한 다음 범위를 포함한다.

- focused Review AI tests
- utility proof script tests
- relevant runtime/dependency boundary tests
- OpenSpec validation
- Python lint/type/format checks applicable to changed code
- Markdown/Inbox validation
- prospective-merge CI 또는 repository가 요구하는 current PR CI

과거 `113 passed`, `314 passed`, CI #1052/#1055 같은 숫자를 현재 결과로 복사하지 않는다.

## Record

다음 identity를 정확히 남긴다.

- base SHA
- head SHA
- prospective merge SHA가 제공되면 해당 SHA
- CI run ID/status
- 실행한 focused validation과 결과
- 의도적으로 실행하지 않은 live provider 범위

## Done When

현재 candidate HEAD와 prospective merge state에 직접 적용 가능한 green evidence가 있고 알려진 validation failure가 없으면 완료한다. 완료 후에만 09로 이동한다.

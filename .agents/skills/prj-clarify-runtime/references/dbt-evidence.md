# dbt Runtime Evidence

dbt 실행을 이해할 때는 log부터 늘리지 않는다. **실행 후 사실은 artifact를 우선하고, 시간적 흐름이나 artifact가 남기지 못한 실패 맥락만 dbt event/log로 보완한다.**

Project Pivot은 `dbt Core`를 사용한다. dbt의 event와 log 형식은 engine/version에 따라 달라질 수 있으므로 구조를 가정하기 전에 실제 사용 version과 공식 문서를 확인한다.

## Evidence Order

| Evidence | Prefer when |
| --- | --- |
| `run_results.json` | 실행된 node의 결과, status, timing 등 완료된 invocation 결과를 복원한다 |
| `manifest.json` | node identity, config, dependency/lineage 같은 project context를 복원한다 |
| dbt event / log | 실행 순서, node-level 진행, artifact가 남기지 못한 실패 맥락을 복원한다 |
| Project Pivot wrapper result / exception | subprocess boundary의 성공·실패와 caller가 알아야 할 최소 context를 전달한다 |

artifact가 존재하고 질문에 답할 수 있으면 같은 사실을 wrapper log에 다시 복제하지 않는다.

## Correlation

가능하면 dbt가 이미 제공하는 identity를 사용한다.

- artifact의 `metadata.invocation_id`로 같은 dbt invocation의 evidence를 연결한다.
- node event의 stable `unique_id`가 제공되면 `manifest.json`의 node context와 연결한다.
- 별도 correlation ID는 기존 identifier로 관계를 복원할 수 없을 때만 추가한다.

field 위치와 event schema는 dbt version에 따라 달라질 수 있으므로 hard-code하기 전에 현재 schema를 확인한다.

## Structured Logs

dbt는 console과 log file에 event를 출력하며 structured format을 지원한다. machine parsing이나 event correlation이 실제 복원 질문에 필요할 때만 structured format을 선택한다.

- 사람이 보는 기본 실행에 debug/structured output을 무조건 강제하지 않는다.
- log level과 format을 바꾸기 전에 기존 `logs/dbt.log`와 artifact로 충분한지 확인한다.
- human-oriented message text를 machine contract로 파싱하지 않는다. structured field나 artifact schema를 우선한다.
- engine/version마다 structured logging 방식이 달라질 수 있으므로 현재 dbt의 공식 설정을 확인한다.

## Failure Boundary

Project Pivot wrapper는 dbt의 모든 output을 다시 logging하지 않는다.

실패 시 caller가 필요한 최소 boundary context만 projection한다.

- command 또는 operation
- return code
- run/target path
- artifact 존재 여부
- 필요할 때 bounded stderr 또는 failure summary

node-level 원인과 상세 실행 흐름은 dbt artifact/log가 이미 소유하면 그 evidence를 유지하고 참조한다. 무제한 stdout/stderr를 exception이나 log에 복제하지 않는다.

artifact가 생성되기 전에 process가 실패했거나 artifact만으로 원인을 복원할 수 없을 때 log가 더 중요한 evidence가 될 수 있다.

## Project Pivot Check

현재 `run_dbt_build()`처럼 invocation별 target path를 사용하는 경계에서는 다음을 우선 확인한다.

1. 해당 run의 artifact가 독립된 target path에 남았는가?
1. `run_results.json`과 `manifest.json`으로 복원 질문에 답할 수 있는가?
1. 실패가 artifact 생성 전이라면 dbt log 또는 bounded process output이 원인을 보완하는가?
1. wrapper가 dbt가 이미 소유한 detail을 중복하고 있지 않은가?

## References

- dbt events and logs: <https://docs.getdbt.com/reference/events-logging>
- dbt log configuration: <https://docs.getdbt.com/reference/global-configs/logs>
- dbt artifacts: <https://docs.getdbt.com/reference/artifacts/dbt-artifacts>

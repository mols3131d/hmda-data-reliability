## Context

dbt foundation은 `manifest.json`, `run_results.json` artifact를 생성한다. incident detection은 `Incident`를 만들지만 `affected_assets`는 아직 비어 있다.

이번 변경은 dbt manifest의 `depends_on.nodes`를 역방향 그래프로 바꿔 incident asset의 downstream 영향을 계산한다.

## Goals / Non-Goals

**Goals:**

- dbt manifest의 nodes/sources를 파싱한다.
- source/model id, node name, relation name 형태의 incident asset을 dbt node id로 해석한다.
- downstream node를 transitive로 탐색한다.
- `LineageEvidence`와 affected assets가 반영된 `Incident`를 반환한다.

**Non-Goals:**

- BI dashboard/file-level lineage
- column-level lineage
- dbt artifact 생성 실행
- impact severity 계산

## Decisions

### manifest parser는 repo 내부 Python 모듈로 둔다

`project_pivot.reliability.impact`에 둔다. dbt CLI wrapper가 아니라 artifact parser만 책임진다.

### downstream은 transitive graph로 계산한다

직접 후속 모델만이 아니라 stg -> mart -> downstream chain 전체를 반환한다. 영향 범위 누락을 줄이기 위함이다.

### Incident는 immutable contract 유지 후 copy한다

기존 `Incident`는 frozen Pydantic 모델이다. `model_copy(update=...)`로 affected assets가 채워진 새 incident를 반환한다.

## Risks / Trade-offs

- [Risk] asset_name 표현이 다양할 수 있다. -> node id/name/relation name을 모두 index한다.
- [Risk] manifest schema가 바뀔 수 있다. -> MVP는 dbt standard `nodes`, `sources`, `depends_on.nodes`만 사용한다.

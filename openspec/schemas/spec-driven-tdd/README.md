# Spec-Driven TDD

OpenSpec의 artifact dependency를 사용해 필요한 계획만 만들고 TDD-compatible implementation으로 연결하는 재사용 가능한 custom schema다.

```mermaid
flowchart LR
    subgraph planning ["Planning Artifacts"]
        proposal["Proposal<br/>why + scope"] --> specs["Specs<br/>observable behavior<br/>or skipped for spec-free change"]
        specs --> design["Design<br/>technical delta only"]
        design --> tasks["Tasks<br/>verifiable outcomes"]
    end

    tasks --> apply["Apply<br/>test-first implementation"]
```

Spec-level behavior가 바뀌지 않는 pure refactor, tooling 또는 docs Change는 `.openspec.yaml`에 `skip_specs: true`를 설정한다. OpenSpec은 이 경우 Specs artifact를 완료로 취급하므로 artifact DAG를 바꾸거나 placeholder Capability와 Requirement를 만들지 않는다.

Design은 Proposal과 Specs의 요약본이 아니다. 다른 planning artifact가 소유하지 않으며 Tasks에 필요한 non-obvious technical delta만 추가한다.

| Path | Responsibility |
| --- | --- |
| [`schema.yaml`](schema.yaml) | 범용 workflow, artifact 의존성, 완료 조건과 Apply 계약 |
| [`templates/`](templates/) | artifact 구조·필드·parser contract와 구조에 종속된 작성 안내 |
| [`docs/`](docs/) | schema 설계 근거와 유지보수 기록 |

Schema는 특정 project, domain, 기술 stack이나 application/source layout을 가정하지 않는다.

활성 workflow와 작성 규칙은 위 owning file을 따르고, 설계 근거와 장기 보존 계약은 [`docs/`](docs/)에서 설명한다.

# Spec-Driven TDD

OpenSpec의 artifact dependency를 사용해 TDD-compatible implementation을 준비하는 재사용 가능한 custom schema다.

```mermaid
flowchart LR
    P[Proposal] --> S[Specs]
    S --> D[Design]
    D --> T[Tasks]
    T --> A[Apply]
```

| Path | Responsibility |
| --- | --- |
| [`schema.yaml`](schema.yaml) | 범용 workflow, artifact 의존성, 완료 조건과 Apply 계약 |
| [`templates/`](templates/) | artifact 구조·필드·parser contract와 구조에 종속된 작성 안내 |
| [`docs/`](docs/) | schema 개발·유지보수 문서 |

Schema는 특정 project, domain, 기술 stack이나 application/source layout을 가정하지 않는다. Template이 소유하는 문서 surface의 세부 규칙도 반복하지 않는다.

자세한 설계와 유지보수 기준은 [`docs/`](docs/)를 따른다.

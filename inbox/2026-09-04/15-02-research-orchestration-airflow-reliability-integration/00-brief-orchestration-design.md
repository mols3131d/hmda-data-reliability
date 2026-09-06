---
type: brief
title: "Orchestration Design Brief"
description: "오케스트레이션 설계의 현재 방향과 남은 결정만 빠르게 확인한다."
tags:
  - orchestration
  - airflow
  - reliability
---

# Orchestration Design Brief

## Current Direction

```text
Trusted State
    ↓
Candidate DuckDB
    ↓
Ingestion → dbt build/tests → Reliability
    ↓
PASS / CLEAR → Publish
INCIDENT      → Publish 안 함
실행 오류     → FAILED
```

| ID | 현재 선택 |
| --- | --- |
| D1 | Airflow는 실행 순서와 task 상태만 조율한다. |
| D2 | 같은 batch 흐름은 하나의 DAG로 구성한다. |
| D3 | Reliability는 publish 전에 실행한다. |
| D4 | 운영 baseline은 동일 asset·partition의 마지막 trusted snapshot을 사용한다. |
| D5 | `INCIDENT`는 `SUCCESS + INCIDENT`로 표현하고 publish하지 않는다. |
| D6 | 최초 baseline은 deterministic bootstrap으로 만든다. |
| D7 | Bootstrap PASS 후 별도 사람 승인 없이 채택한다. |
| D8 | Trusted state는 실제 데이터, dbt artifact, reliability evidence를 함께 포함한다. |
| D9 | MVP candidate는 run-scoped DuckDB로 격리한다. |
| D10 | 데이터 변경은 Write-Audit-Publish로 처리한다. |

각 결정에서 검토한 옵션과 트레이드오프는 `01-discussion-orchestration-design.md`에만 기록한다.

## Open Questions

1. Bootstrap minimum gate
2. Trusted generation identity와 저장 방식
3. Candidate assessment result contract
4. Publish 실패와 recovery 처리
5. Airflow task 간 outcome 전달
6. Candidate cleanup

다음 논의는 **Bootstrap minimum gate**부터 진행한다.

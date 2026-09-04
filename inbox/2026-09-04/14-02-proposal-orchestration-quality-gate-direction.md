---
type: proposal
title: "Airflow Quality Gate Architecture Direction"
description: "PR #205의 코드 상태와 분리하여, Airflow data plane의 blocking quality gate 배치와 domain ownership 방향을 제안한다."
tags:
  - orchestration
  - airflow
  - data-quality
  - reliability
---

# Airflow Quality Gate Architecture Direction

## Status and Scope

이 문서는 PR #205의 구현 코드에 대한 리뷰 결과가 아니다.

작성 시점에 논의 중인 quality gate 관련 최신 소스 코드가 PR head에 모두 반영되었다고 확인할 수 없는 상태이므로, 코드의 정확성·테스트 통과 여부·구체 구현 위치를 판정하지 않는다. 대신 현재 canonical architecture와 OpenSpec 계약, 그리고 quality gate의 운영 목적을 기준으로 향후 구현이 따라야 할 방향만 제안한다.

## Recommendation

Airflow `hmda_data_plane`의 critical path에 blocking quality gate stage를 두는 방향을 채택하는 것이 적절하다.

권장 실행 순서는 다음과 같다.

```text
Source
  ↓
Bronze ingestion
  ↓
Quality admission gate
  ↓
dbt analytics build
  ↓
validated artifact promotion
```

Quality gate의 목적은 Bronze 적재 자체를 거부하는 것이 아니라, 적재된 raw partition이 trusted downstream으로 진행할 수 있는지를 판정하는 것이다. 따라서 결함이 있는 데이터도 조사·replay·recovery를 위해 Bronze에는 남을 수 있으며, gate 실패는 downstream analytics 진행을 차단하는 방식으로 표현한다.

## Ownership Boundary

Airflow는 quality rule의 구현자가 아니라 orchestration owner로 유지한다.

Airflow가 소유할 책임은 다음과 같다.

- raw load 이후 quality gate를 실행하는 순서
- gate 성공/실패를 task state로 표현하는 것
- gate 실패 시 downstream analytics 실행을 차단하는 것
- 실행 evidence와 failure context를 관찰 가능하게 남기는 것

Airflow가 직접 소유하지 않을 책임은 다음과 같다.

- nullability, uniqueness, relationship 같은 deterministic data contract
- baseline, threshold, anomaly semantics
- incident lifecycle, impact analysis, remediation proposal
- approval, recovery, evaluation, AI review

즉 architecture 경계는 다음과 같이 보는 것이 적절하다.

```text
Airflow
  └─ 언제 검사하고, 실패 시 무엇을 막는가

Quality implementation
  ├─ dbt tests: deterministic data contracts
  └─ Reliability: baseline/anomaly/incident semantics
```

## dbt Test Integration

Quality gate가 Airflow task로 존재하더라도 실제 검사 로직은 dbt test로 구현할 수 있다.

예를 들어 deterministic admission contract는 다음과 같이 실행할 수 있다.

```text
load_raw
  ↓
Airflow quality_gate task
  ↓
dbt test --select <admission tests>
  ↓
PASS → analytics build
FAIL → downstream blocked
```

이 경우 `quality gate`는 Airflow의 orchestration concept이고, `dbt test`는 그 gate가 사용하는 validation implementation이다. 둘은 경쟁하는 개념이 아니다.

다만 동일 test를 별도 gate에서 실행한 뒤 `dbt build`가 같은 test를 다시 실행하지 않도록 selector/tag boundary를 명확히 해야 한다.

## Reliability Detector Integration

모든 quality rule을 dbt test로 옮길 필요는 없다.

`not_null`, `unique`, `relationships`, `accepted_values`처럼 현재 row/model 상태에 대한 deterministic contract는 dbt test가 자연스럽다.

반면 `null_spike`, `volume_drop`, freshness anomaly처럼 baseline 또는 과거 상태와 비교하는 reliability detection은 Reliability domain에 두는 편이 더 적절하다. Synthetic evaluation과 production gate가 같은 detector semantics를 공유해야 평가한 로직과 실제 차단 로직 사이의 drift를 줄일 수 있다.

따라서 장기적으로 quality gate는 다음처럼 여러 validation implementation을 조합할 수 있다.

```text
Airflow quality_gate
  ├─ dbt deterministic tests
  └─ Reliability anomaly checks
```

MVP에서는 필요한 검사만 사용하고, 단순성을 위해 불필요한 다중 엔진 orchestration은 추가하지 않는다.

## Quality Gate vs. Reliability Control Plane

Blocking quality gate와 Reliability lifecycle을 구분해야 한다.

Quality gate는 data-plane admission decision이다.

```text
profile / test
  ↓
deterministic decision
  ↓
PASS or BLOCK
```

반면 Reliability control plane은 실패 이후의 분석과 복구 판단을 담당한다.

```text
incident evidence
  ↓
impact / remediation analysis
  ↓
validated proposal
  ↓
external approval
  ↓
recovery
```

따라서 Airflow에 quality gate를 배치하는 것은 incident lifecycle, approval, recovery 또는 evaluation 전체를 Airflow에 자동 결합한다는 의미가 아니다.

## Canonical Contract Changes

이 방향을 채택하면 현재 canonical 문서의 Airflow boundary를 갱신해야 한다.

현재 architecture는 Airflow data plane을 Bronze ingestion과 dbt analytics만 연결하는 것으로 설명하고 있으며, reliability control-plane 자동 결합을 금지한다. 후자의 원칙은 유지하되, 전자의 경계는 blocking admission gate를 허용하도록 확장하는 것이 적절하다.

권장 계약은 다음 의미를 가져야 한다.

> Airflow data plane은 Bronze ingestion, read-only deterministic quality admission gate, dbt analytics 실행 순서를 조율할 수 있다. Incident lifecycle, remediation, approval, recovery, evaluation 및 LLMOps orchestration은 data-plane workflow에 자동 결합하지 않는다.

이에 따라 구현을 진행할 때 최소한 다음 canonical owner의 정합성을 함께 확인해야 한다.

- `docs/ARCHITECTURE.md`
- `docs/domains/orchestration.md`
- `openspec/specs/orchestration-pipeline/spec.md`
- 해당 변경을 소유하는 active OpenSpec change

## Suggested Design Constraints

구현 단계에서는 다음 제약을 유지하는 것을 권장한다.

1. Airflow DAG task는 thin adapter로 유지한다.
2. Quality policy나 detector business rule을 DAG 파일에 복제하지 않는다.
3. Quality gate는 기본적으로 read-only validation이어야 한다.
4. Gate 실패는 downstream analytics를 차단하되 raw Bronze evidence는 보존한다.
5. Incident lifecycle, remediation, approval, recovery는 gate 성공/실패 path에 자동 결합하지 않는다.
6. dbt test와 Reliability detector 중 어떤 validation mechanism을 사용할지는 rule의 성격에 따라 선택한다.
7. 동일 rule을 dbt와 Reliability 양쪽에 중복 구현하지 않는다.
8. 통계적 anomaly를 장기적으로 운영할 경우 `FAIL`, `WARN`, `OBSERVE` 같은 enforcement policy 분리를 검토한다.
9. Hardcoded baseline은 synthetic/MVP proof에는 사용할 수 있으나 durable production contract로 간주하지 않는다.

## PR #205 Guidance

PR #205에서 quality gate 관련 작업을 계속 포함한다면 PR 설명은 실제 의도를 명시해야 한다.

단순히 2026 synthetic evaluation 보완으로 설명하기보다 다음 연결 관계를 드러내는 것이 좋다.

```text
synthetic defect evaluation
  → detector behavior 검증
  → 검증된 detection boundary를 production data-plane gate에서 재사용
```

이 연결이 실제 구현에서도 성립한다면 synthetic evaluation과 Airflow gate를 같은 PR에서 다루는 것은 가능하다. 반대로 production gate가 별도 dbt rule 등 전혀 다른 semantics를 사용한다면 두 변경의 결합 근거가 약해지므로 분리를 다시 검토하는 편이 낫다.

## Decision Summary

현재 제안 방향은 다음과 같다.

- Airflow critical path의 quality gate: **채택 권장**
- 위치: **Bronze load 이후, analytics build 이전**
- Airflow의 quality business rule 소유: **지양**
- dbt test의 gate implementation 사용: **가능하며 deterministic contract에 권장**
- Reliability detector의 gate implementation 사용: **baseline/anomaly rule에 권장**
- incident lifecycle / approval / recovery의 Airflow 자동 결합: **비권장**
- 기존 architecture/OpenSpec 경계: **quality admission gate를 허용하도록 갱신 필요**

최종 구현 리뷰는 관련 소스 코드가 PR head에 반영된 뒤 별도로 수행한다.

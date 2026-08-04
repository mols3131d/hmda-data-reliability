---
type: openspec-rpi
category: research
title: "Foundation exit gate"
description: "현재 Foundation을 종료하고 MVP로 전환하기 위한 최소 evidence와 validation gate를 정의한다."
status: "completed"
tags:
  - "foundation"
  - "readiness"
  - "validation"
  - "data-reliability"
---

## Summary

> [!NOTE]
> Foundation은 새로운 capability를 더하는 단계가 아니라, 이미 구현된 경계를 반복 가능한 evidence로 닫는 단계다. 현재 남은 gap은 대부분 EDA runtime, 실제 source observation, pipeline evidence와 최종 ready 판정이다. 따라서 **기능 수가 아니라 하나의 재현 가능한 release gate가 통과하는지**로 종료해야 한다. 새로운 observability platform이나 production SLO는 MVP 이후로 미룬다.

## Question

- **Primary:** Project Pivot의 Foundation을 어떤 기준으로 종료하고 MVP reliability 개발로 전환해야 하는가?
- **Scope:** 현재 `main`의 Foundation capability, EDA extension, dbt test, Dagster execution evidence와 로컬 validation만 포함한다. cloud deployment, 장기 monitoring, 운영 SLO는 제외한다.
- **Stop Condition:** 각 capability의 ready 여부를 동일한 형식으로 판정할 수 있고, Foundation 종료를 재현하는 단일 validation flow를 제안할 수 있으면 종료한다.

## Findings

### F1. 남은 작업은 capability 부족보다 evidence closure 문제다

`docs/development/foundation/readiness.md`의 2026-08-03 snapshot은 구현 185/192, 검증 184/190으로 기록되어 있다. 남은 항목은 deterministic EDA expected value, notebook runtime smoke, actual-source observation, Bronze→dbt pipeline evidence와 Foundation completion decision이다.

- **Evidence** - `docs/development/foundation/readiness.md`, `openspec/changes/hmda-eda-foundation-extension/tasks.md`
- **Implication** - 새 subsystem을 추가하면 종료 조건이 다시 움직인다. 현재 gap을 닫고 evidence를 고정하는 것이 우선이다.

### F2. dbt와 Dagster의 공식 test model은 명시적 assertion과 추적 가능한 결과를 중심으로 한다

dbt data test는 model·source에 대한 assertion이며 실패 row를 반환한다. dbt는 primary key의 `unique`·`not_null`, source assumption 검증과 transformation 실행 시 test 수행을 권장한다. `manifest.json`은 model, test, source, parent/child map을 포함하므로 현재 프로젝트의 lineage와 contract evidence에 충분하다.

Dagster asset check는 한 check가 한 asset property를 검증하도록 권장하며, 실패 시 downstream materialization을 차단할지 명시적으로 선택할 수 있다. Project Pivot은 Dagster를 data plane에 한정하므로 asset check를 새 reliability control plane으로 확장하기보다 pipeline evidence 연결에만 사용해야 한다.

- **Evidence** - dbt Data Tests, dbt Manifest JSON, Dagster Asset Checks 공식 문서
- **Implication** - Foundation gate는 외부 dashboard가 아니라 기존 pytest, dbt artifact와 Dagster run evidence를 조합해 구성할 수 있다.

### F3. ready 판정에는 결과뿐 아니라 provenance가 필요하다

`pass`만 기록하면 어떤 source, code revision, command와 artifact로 통과했는지 재현할 수 없다. 최소 gate record는 다음을 포함해야 한다.

| Field | Required Evidence |
| --- | --- |
| Revision | Git commit SHA 또는 branch head |
| Source | dataset year, dataset class, source path와 checksum |
| Command | 실제 실행한 validation command |
| Result | pass/fail, 주요 count와 known anomaly |
| Artifact | pytest report, dbt artifact, notebook smoke output 또는 run metadata |
| Timestamp | 실행 시점과 timezone |

- **Evidence** - 현재 readiness의 actual-source observation gap, dbt artifact 구조
- **Implication** - readiness dashboard의 수동 진행률과 별도로 machine-readable evidence inventory가 canonical 판정 근거가 되어야 한다.

### F4. Foundation exit gate는 다섯 영역을 모두 통과해야 한다

| Gate | Minimum Ready Criteria | Blocking Failure |
| --- | --- | --- |
| Source & Bronze | representative source 적재 성공, partition 재실행 시 중복 없음 | schema mismatch, row loss, duplicate partition |
| dbt Silver & Gold | build/test 성공, core field contract와 mart grain 일치 | data test error, grain drift, lineage 누락 |
| EDA Evidence | valid·malformed runtime smoke, deterministic expected value, actual-source observation 기록 | partial evidence, notebook execution failure |
| Pipeline Boundary | Bronze→dbt 실행 evidence와 제외 범위 확인 | reliability lifecycle 자동 결합, 단계 누락 |
| Reliability Boundary | read-only lifecycle, approval-gated recovery, evaluation boundary regression 없음 | 승인 없는 write, contract regression |

- **Evidence** - `docs/ARCHITECTURE.md`, Foundation readiness, active EDA OpenSpec change
- **Implication** - 모든 test를 무조건 하나로 합칠 필요는 없지만, 최종 판정은 동일한 evidence inventory를 통해 한 번에 확인 가능해야 한다.

## Options

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| 문서 checklist만 사용 | 빠르고 수정이 쉽다 | 실행 결과와 쉽게 분리되고 stale해진다 |
| 단일 local release gate + evidence inventory | 재현 가능하고 현재 stack을 재사용한다 | command orchestration과 artifact 규격을 정해야 한다 |
| production SLO·observability까지 완료 | 운영 기준이 강하다 | local MVP 범위를 넘어 Foundation 종료를 지연한다 |

## Conclusion

- **Answer** - Foundation은 현재 active EDA change와 readiness gap을 닫고, 다섯 영역의 evidence를 한 revision에서 재현할 수 있을 때 종료한다.
- **Recommendation** - `hmda-eda-foundation-extension`의 미완료 task를 먼저 완료한 뒤, machine-readable readiness inventory와 이를 검증하는 단일 local release command를 추가한다. readiness 문서는 이 inventory의 사람이 읽는 projection으로 유지한다.
- **Next Step** - 다음 OpenSpec change는 `foundation-readiness-gate`처럼 좁게 잡고, 새로운 capability 없이 evidence schema, validation entrypoint와 final ready 판정만 정의한다.

## Validation Candidates

1. clean checkout 또는 고정된 local environment에서 representative source를 준비한다.
2. focused pytest, dbt build/test, notebook smoke와 Dagster pipeline validation을 실행한다.
3. source identity, revision, command, result, artifact location을 machine-readable inventory에 기록한다.
4. 모든 blocking gate가 pass이고 known anomaly가 명시됐을 때만 Foundation을 ready로 판정한다.
5. 같은 revision과 source에서 재실행해 결과가 안정적인지 확인한다.

## Evidence

| Evidence | Supports | Location |
| --- | --- | --- |
| Foundation readiness snapshot | F1, F3, F4 | `docs/development/foundation/readiness.md` |
| Active EDA tasks | F1, F4 | `openspec/changes/hmda-eda-foundation-extension/tasks.md` |
| Architecture boundaries | F4 | `docs/ARCHITECTURE.md` |
| dbt data tests | F2 | https://docs.getdbt.com/docs/build/data-tests |
| dbt manifest artifact | F2, F3 | https://docs.getdbt.com/reference/artifacts/manifest-json |
| Dagster asset checks | F2 | https://docs.dagster.io/guides/test/asset-checks |

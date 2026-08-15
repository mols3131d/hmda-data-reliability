---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-evaluation-report
description: Single-column null-spike recovery의 deterministic acceptance와 quality false-green 차단을 정의한다.
tags:
  - "domain:reliability"
  - "capability:reliability-evaluation-report"
  - "null-spike"
---

## ADDED Requirements

### Requirement: Null-spike recovery vertical-slice evaluation

시스템은 deterministic fixture identity, target column과 defect parameters로 clean baseline과 controlled single-column `null_spike` case를 서로 다른 isolated disposable target, clean과 candidate database에서 실행하고 detection, candidate validation, approval, recovery, replay와 downstream verification 결과를 case evidence로 집계할 수 있어야 한다(SHALL). Expected recovery identity와 target column null rate는 clean fixture baseline에서 직접 유도해야 한다(SHALL). Evaluation은 recovery executor의 stable content validation과 별도로 baseline target column null-rate의 exact restoration 및 post-recovery incident 해소를 판정해야 한다(SHALL).

#### Scenario: Existing evaluation database

- **GIVEN** evaluation target, workspace clean 또는 candidate database path 중 하나가 이미 존재할 때
- **WHEN** controlled `null_spike` evaluation을 요청할 때
- **THEN** workspace directory 또는 file 생성, source load, synthetic defect 적용, candidate validation과 approval 전에 요청을 거부해야 한다.
- **AND** 기존 database content를 변경해서는 안 된다.

#### Scenario: Aliased evaluation database paths

- **GIVEN** target, workspace clean과 candidate database path 중 둘 이상이 같은 physical path를 식별할 때
- **WHEN** controlled `null_spike` evaluation을 요청할 때
- **THEN** workspace directory 또는 file 생성, source load와 external callback 전에 요청을 거부해야 한다.
- **AND** target mutation 또는 recovery evidence를 생성해서는 안 된다.

#### Scenario: Evaluation path preflight

- **GIVEN** target, workspace clean과 candidate database path가 모두 존재하지 않을 때
- **WHEN** controlled `null_spike` evaluation entry가 path를 검증할 때
- **THEN** 세 path가 pairwise distinct physical path인지 하나의 preflight에서 확인해야 한다.
- **AND** preflight가 성공한 뒤에만 workspace directory, synthetic artifact와 evaluation database를 생성할 수 있다.

#### Scenario: Controlled single-column null spike

- **GIVEN** profiled target column과 고정된 null fraction이 주어질 때
- **WHEN** controlled `null_spike` case를 생성해 평가할 때
- **THEN** row count를 감소시키지 않고 해당 target column의 `null_spike` incident 하나를 식별해야 한다.

#### Scenario: Ambiguous incident set

- **GIVEN** controlled target lifecycle에서 target-column `null_spike`가 없거나 다른 incident를 포함해 둘 이상의 incident가 탐지될 때
- **WHEN** recovery proposal을 생성하려 할 때
- **THEN** candidate validation, approval과 target mutation 전에 evaluation을 실패로 종료해야 한다.
- **AND** detected incident types와 cardinality를 evidence로 포함해야 한다.

#### Scenario: Approved null-spike recovery

- **WHEN** controlled `null_spike` case가 valid clean candidate와 complete approval로 실행될 때
- **THEN** expected incident와 impact가 관찰되고 target content identity와 target column null rate가 clean fixture baseline과 정확히 일치해야 한다.
- **AND** incident resolution과 downstream dbt verification이 모두 성공해야 한다.

#### Scenario: Independent null-rate acceptance evidence

- **WHEN** approved recovery와 replay가 expected content identity를 복원할 때
- **THEN** evaluation case evidence는 baseline, recovery와 replay target-column null rate를 포함해야 한다.
- **AND** recovery 또는 replay의 content validation이 실패하거나 null rate가 baseline과 다르면 downstream success로 판정해서는 안 된다.
- **AND** content validation은 성공하고 null rate만 baseline과 다르면 `resume_verification`을, content validation이 실패하면 새 validation과 approval 필요성을 evidence에 포함해야 한다.
- **AND** recovery와 replay quality acceptance가 완료된 뒤 post-recovery lifecycle 또는 target validation이 실패해도 이미 확정한 baseline/recovery/replay null-rate evidence를 case result에 보존해야 한다.

#### Scenario: Residual-null candidate rejection

- **GIVEN** candidate target column null rate가 detection threshold 아래이지만 clean fixture baseline과 다르고 candidate identity도 clean expected identity와 다를 때
- **WHEN** recovery proposal을 생성하려 할 때
- **THEN** approval과 target mutation 전에 candidate를 거부해야 한다.
- **AND** candidate/expected identity와 candidate/baseline null-rate evidence를 case result에 포함해야 한다.

#### Scenario: Null-spike replay stability

- **GIVEN** 첫 approved recovery가 clean expected state와 null-rate를 복원했을 때
- **WHEN** 같은 approval과 fixture identity로 recovery를 반복 평가할 때
- **THEN** partition overwrite를 반복하지 않고 verification을 재개해야 한다.
- **AND** duplicate, semantic drift 또는 null-rate drift 없이 stable evidence를 재현해야 한다.

#### Scenario: Null-spike safety failure evidence

- **WHEN** candidate validation, approval, target freshness 또는 downstream verification 중 하나가 실패할 때
- **THEN** evaluation은 failure stage, target mutation 여부와 reconciliation action을 기존 recovery safety evidence 형식으로 식별해야 한다.
- **AND** candidate 또는 target validation callback의 `ValueError`를 raw exception으로 노출해서는 안 된다.

#### Scenario: Read-only lifecycle preservation

- **WHEN** controlled `null_spike` target에 read-only incident lifecycle만 실행할 때
- **THEN** incident와 remediation draft를 반환하되 approval, partition overwrite, evaluation report write를 실행해서는 안 된다.

---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-evaluation-report
description: Clean baseline과 volume-drop recovery vertical slice의 deterministic acceptance를 정의한다.
tags:
  - "domain:reliability"
  - "capability:reliability-evaluation-report"
  - "mvp"
  - "volume-drop"
---

## ADDED Requirements

### Requirement: Recovery vertical-slice evaluation

시스템은 deterministic fixture identity와 defect parameters로 clean baseline과 controlled `volume_drop` case를 실행하고 detection, candidate validation, approval, recovery와 downstream verification 결과를 case evidence로 집계할 수 있어야 한다(SHALL).

#### Scenario: Deterministic fixture state

- **GIVEN** 같은 fixture identity와 defect parameters가 주어질 때
- **WHEN** expected recovery state를 반복 생성할 때
- **THEN** source physical order와 관계없이 같은 partition content identity와 expected recovery evidence를 생성해야 한다.

#### Scenario: Clean baseline

- **WHEN** defect가 없는 deterministic fixture를 평가할 때
- **THEN** incident와 remediation draft가 생성되지 않아야 한다.

#### Scenario: Approved volume-drop recovery

- **WHEN** controlled `volume_drop` case가 valid candidate와 complete approval로 실행될 때
- **THEN** expected incident와 impact가 관찰되고 target content, incident resolution과 downstream dbt verification이 모두 성공해야 한다.

#### Scenario: Replay stability

- **WHEN** 같은 approved recovery와 fixture identity를 반복 평가할 때
- **THEN** duplicate 또는 semantic drift가 생기지 않고 stable evidence projection을 재현해야 한다.

### Requirement: Evaluation workspace isolation

시스템은 synthetic defect와 recovery acceptance를 disposable evaluation workspace에서 실행해야 한다(SHALL). Caller의 일반 target database를 synthetic defect injection 대상으로 암묵적으로 재사용해서는 안 된다(MUST NOT).

#### Scenario: Default target preservation

- **GIVEN** caller request가 기존 target database를 가리킬 때
- **WHEN** volume-drop evaluation을 실행할 때
- **THEN** synthetic defect는 evaluation workspace의 disposable database에만 적용되고 caller target database는 변경되지 않아야 한다.

### Requirement: Source provenance preservation

시스템은 evaluation fixture와 synthetic defect를 requested partition scope에 맞게 구성하고 다른 source year의 row를 대상 `source_year` provenance로 재작성해서는 안 된다(MUST NOT). 같은 logical input과 defect parameters는 input file order와 무관하게 같은 expected content identity를 생성해야 한다(SHALL).

#### Scenario: Multi-year source isolation

- **GIVEN** 둘 이상의 source year를 포함한 input set과 하나의 requested `source_year`가 있을 때
- **WHEN** controlled defect와 expected recovery state를 생성할 때
- **THEN** requested year의 partition만 evaluation 대상이 되고 다른 year의 row가 target year provenance로 포함되어서는 안 된다.

#### Scenario: Stable tie ordering

- **GIVEN** defect sampling key가 같은 여러 logical row가 서로 다른 physical order로 주어질 때
- **WHEN** 같은 defect parameters로 fixture를 반복 생성할 때
- **THEN** 선택된 logical row multiset과 expected content identity가 같아야 한다.

### Requirement: Recovery safety case evaluation

시스템은 invalid candidate, stale target, incomplete approval, candidate dbt failure, recovery dbt failure와 diverged reconciliation을 각각 target mutation 여부와 preserved evidence로 판정해야 한다(SHALL). Failure stage, mutation state와 artifact preservation은 실제 실행 결과에서 관찰되어야 하며 caller가 제공한 검증되지 않은 label만으로 성공 evidence를 구성해서는 안 된다(MUST NOT).

#### Scenario: Pre-mutation safety failures

- **WHEN** invalid candidate, stale target 또는 incomplete approval case를 평가할 때
- **THEN** target mutation이 없고 차단 이유가 case evidence에 포함되어야 한다.

#### Scenario: Candidate dbt failure observation

- **WHEN** candidate dbt boundary에서 실제 process 또는 artifact validation failure를 발생시킬 때
- **THEN** evaluator는 current target과 prior current artifact가 보존된 실패 evidence를 실제 run result에서 구성해야 한다.

#### Scenario: Post-mutation recovery failure

- **WHEN** partition 변경 이후 실제 target dbt verification이 실패하는 case를 평가할 때
- **THEN** post-mutation failure, expected current partition과 prior last-known-good artifact가 evidence에 포함되어야 한다.

#### Scenario: Diverged reconciliation case

- **WHEN** current target이 approved before/after state 어느 쪽과도 다른 case를 평가할 때
- **THEN** 기존 approval의 추가 mutation이 차단되고 새 validation과 approval 필요성이 evidence에 포함되어야 한다.

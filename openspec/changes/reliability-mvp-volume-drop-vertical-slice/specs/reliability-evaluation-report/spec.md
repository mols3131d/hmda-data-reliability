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
- **THEN** 같은 partition content identity와 expected recovery evidence를 생성해야 한다.

#### Scenario: Clean baseline

- **WHEN** defect가 없는 deterministic fixture를 평가할 때
- **THEN** incident와 remediation draft가 생성되지 않아야 한다.

#### Scenario: Approved volume-drop recovery

- **WHEN** controlled `volume_drop` case가 valid candidate와 complete approval로 실행될 때
- **THEN** expected incident와 impact가 관찰되고 target content, incident resolution과 downstream dbt verification이 모두 성공해야 한다.

#### Scenario: Replay stability

- **WHEN** 같은 approved recovery와 fixture identity를 반복 평가할 때
- **THEN** duplicate 또는 semantic drift가 생기지 않고 stable evidence projection을 재현해야 한다.

#### Scenario: Replay verification failure after recovery

- **GIVEN** 첫 approved recovery가 target을 expected recovered state로 변경한 뒤 replay를 시작했을 때
- **WHEN** replay의 downstream verification이 실패할 때
- **THEN** evaluation은 완료된 첫 recovery와 target mutation을 보존하고 replay failure를 별도로 식별해야 한다.
- **AND** 다음 조치는 partition overwrite가 아니라 `resume_verification`이어야 한다.

### Requirement: Recovery safety case evaluation

시스템은 invalid candidate, stale target, incomplete approval, candidate dbt failure, recovery dbt failure와 diverged reconciliation을 각각 target mutation 여부와 preserved evidence로 판정해야 한다(SHALL).

#### Scenario: Pre-mutation safety failures

- **WHEN** invalid candidate, stale target 또는 incomplete approval case를 평가할 때
- **THEN** target mutation이 없고 차단 이유가 case evidence에 포함되어야 한다.
- **AND** stale target의 reconciliation action은 `request_new_validation_and_approval`이어야 한다.

#### Scenario: Post-mutation recovery failure

- **WHEN** partition 변경 이후 dbt verification이 실패하는 case를 평가할 때
- **THEN** post-mutation failure, expected current partition과 prior last-known-good artifact가 evidence에 포함되어야 한다.
- **AND** 다음 조치는 partition overwrite가 아니라 `resume_verification`이어야 한다.

#### Scenario: Artifact state after post-promotion domain failure

- **GIVEN** target artifact promotion이 current projection을 변경했을 때
- **WHEN** 이후 artifact observation이 data-operations domain failure로 종료될 때
- **THEN** evaluation은 prior projection이 유지됐다고 보고해서는 안 된다.
- **AND** locked re-observation으로 확인한 actual current projection 또는 관찰 실패를 evidence에 명시해야 한다.

#### Scenario: Diverged reconciliation case

- **WHEN** current target이 approved before/after state 어느 쪽과도 다른 case를 평가할 때
- **THEN** 기존 approval의 추가 mutation이 차단되고 새 validation과 approval 필요성이 evidence에 포함되어야 한다.
- **AND** reconciliation action은 `request_new_validation_and_approval`이어야 한다.

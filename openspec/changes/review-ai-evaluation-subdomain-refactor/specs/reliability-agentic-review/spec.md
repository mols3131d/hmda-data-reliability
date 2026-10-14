---
type: openspec-spec-driven-tdd-spec
category: spec
title: Review AI Human Evaluation
description: Review AI의 human utility evaluation과 baseline/candidate comparison contract를 유지하며 Review Value API 이름을 제공한다.
tags:
  - "capability:reliability-agentic-review"
---

## MODIFIED Requirements

### Requirement: Versioned human utility evaluation

시스템은 Review AI utility를 `rubric_v1`로 식별되는 immutable human rubric으로 평가해야 한다(SHALL). Python evaluation API는 이 human-rated review value 평가를 `ReviewValueRubric`과 `ReviewValueAssessment`로 제공해야 한다(SHALL). Rubric은 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`의 다섯 criterion을 모두 포함해야 하며(SHALL), 각 criterion의 human score는 0–2 범위이고 non-empty rationale을 가져야 한다(SHALL). 자동 LLM judge 또는 외부 평가 플랫폼은 quality evaluation authority로 사용해서는 안 된다(MUST NOT).

#### Scenario: Rubric scores all utility dimensions

- **WHEN** human evaluator가 representative output을 평가할 때
- **THEN** 다섯 criterion 각각에 bounded score와 non-empty rationale가 있어야 evaluation을 유효한 quality evidence로 취급할 수 있다(SHALL).

#### Scenario: Rubric fixtures distinguish utility from restatement and hedging

- **WHEN** positive, deterministic-fact restatement 및 actionable next step이 없는 hedging control을 rubric test fixture로 평가할 때
- **THEN** fixture score는 추가 가치와 행동 가능성의 차이를 구분해야 하고 control 결과는 runtime 또는 durable quality-basis contract로 취급되어서는 안 된다(MUST NOT).

### Requirement: Baseline and candidate utility comparison evidence

시스템은 동일한 retained representative case와 rubric identity에서 baseline 및 candidate output의 human evaluation을 비교하는 immutable `ReviewValueComparisonEvidence`를 생성할 수 있어야 한다(SHALL). Python comparison API는 `ReviewValueComparisonStatus`, `ReviewValueComparisonEvidence`, `compare_review_value()`와 `render_review_value_comparison_markdown()`을 통해 이를 제공해야 한다(SHALL). Comparison은 baseline/candidate invocation identity, case identity/version, rubric identity, change-under-test, criterion별 정확히 하나의 score delta와 human `accept`, `reject` 또는 `no_change` decision 및 rationale을 연결해야 한다(SHALL). Criterion delta aggregate는 recorded baseline/candidate total과 total delta에 일치해야 한다(SHALL).

Comparison은 baseline output role이 `baseline`, candidate output role이 `candidate`이고 둘이 동일 case/version/rubric/revision 및 deterministic facts에서 평가된 경우에만 valid로 표시해야 한다(SHALL). 비교 조건이나 attribution evidence가 맞지 않으면 candidate를 accept 또는 baseline promotion하지 않고 `blocked`/`inconclusive`로 기록해야 한다(MUST NOT).

#### Scenario: Same case and rubric are compared

- **WHEN** 명시적 baseline/candidate evaluation이 동일 case/version, `rubric_v1`, deterministic facts와 project revision을 사용해 생성될 때
- **THEN** criterion 및 total delta, invocation identity, change-under-test와 human decision/rationale을 복원할 수 있어야 한다(SHALL).

#### Scenario: Mismatched or incomplete comparison is blocked

- **WHEN** output role, case/version, rubric, criterion score, deterministic facts 또는 project revision이 비교 조건을 만족하지 않을 때
- **THEN** evidence는 invalid 또는 `blocked`/`inconclusive`로 남고 candidate acceptance나 baseline promotion을 허용해서는 안 된다(MUST NOT).

#### Scenario: Comparison records retain their serialized contract after API rename

- **WHEN** comparison evidence가 Review Value Python API로 serialize된 뒤 다시 읽힐 때
- **THEN** serialized field names, enum values, rubric identity, embedded outputs와 output digests는 기존 utility comparison contract와 동일하게 유지되어야 한다(SHALL).

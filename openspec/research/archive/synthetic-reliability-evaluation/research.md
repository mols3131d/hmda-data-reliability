---
type: openspec-rpi
category: research
title: "Synthetic reliability evaluation"
description: "Project Pivot reliability lifecycle을 synthetic case로 평가하기 위한 case model, oracle과 scorecard를 정의한다."
status: "completed"
tags:
  - "evaluation"
  - "synthetic-data"
  - "reliability"
  - "testing"
---

## Summary

> [!NOTE]
> MVP의 첫 evaluation system은 외부 platform이 아니라 **versioned synthetic case registry와 deterministic pytest runner**여야 한다. 작은 고정 case가 regression oracle을 제공하고, Hypothesis가 값과 operation sequence의 edge case를 확장한다. 평가는 하나의 종합 점수가 아니라 profile, detection, impact, remediation, recovery와 replay를 분리한 다축 scorecard로 기록한다.

## Question

- **Primary:** Project Pivot의 reliability lifecycle을 어떤 synthetic case와 oracle로 평가해야 하는가?
- **Scope:** local HMDA fixture, deterministic fault injection, current lifecycle contract와 approval-gated recovery를 포함한다. production traffic replay, model-based judge와 대규모 benchmark generation은 제외한다.
- **Stop Condition:** 최소 case schema, lifecycle별 metric, case catalog와 실행 경계를 OpenSpec으로 정의할 수 있으면 종료한다.

## Findings

### F1. 고정 example과 generated case는 서로 대체하지 않는다

Named fixture는 known incident에 대한 정확한 expected output을 고정하기 좋다. Property-based testing은 사람이 예상하지 못한 값 조합을 탐색하고 실패 example을 축소하는 데 강하다. Hypothesis stateful testing은 값뿐 아니라 operation sequence를 생성하므로 ingest→detect→approve→recover 같은 lifecycle invariant 검증에 적합하다.

- **Evidence** - Hypothesis 공식 documentation과 stateful testing guide
- **Implication** - core regression은 named case로, combinatorial edge는 Hypothesis strategy와 state machine으로 나눈다.

### F2. synthetic case는 defect보다 oracle을 먼저 정의해야 한다

단순히 null이나 outlier를 넣으면 어떤 결과가 정답인지 모호하다. 각 case는 fault injection과 함께 lifecycle stage별 expected evidence를 소유해야 한다.

```yaml
id: unknown-action-code
source_fixture: hmda-core-valid-v1
injection:
  field: action_taken
  operation: replace
  value: "999"
expected:
  profile: unknown_code_count == 1
  incident: rule_id == hmda.action-taken.unknown-code
  impact: affected_rows == 1
  remediation: raw_value_preserved == true
  recovery: requires_approval == true
oracle:
  type: exact
```

최소 metadata는 case version, source contract version, seed, injection, expected lifecycle output와 oracle type이다.

- **Evidence** - 현재 read-only lifecycle과 recovery boundary, Langfuse experiment dataset의 input·expected output model
- **Implication** - case registry가 test fixture와 evaluation dataset의 canonical source가 되어야 한다.

### F3. lifecycle stage별 metric이 필요하다

| Stage | Primary Metric | Guardrail |
| --- | --- | --- |
| Profile | exact field/count/summary match | raw source unchanged |
| Detection | TP, FP, FN by rule and severity | known-clean case incident 0 |
| Impact | affected row/partition/asset precision·recall | unrelated lineage excluded |
| Remediation draft | schema validity, evidence grounding, forbidden action count | write 실행 없음 |
| Recovery | approval enforcement, postcondition, idempotency | denied case mutation 0 |
| Replay | same case/version result stability | seed와 revision 기록 |

- **Evidence** - Project Pivot architecture boundaries와 existing incident lifecycle tests
- **Implication** - overall pass rate만으로는 어느 boundary가 약한지 알 수 없다. stage와 case family 단위 결과를 보존해야 한다.

### F4. 초기 catalog는 실제 failure mode를 작게 덮어야 한다

| Family | Minimum Cases |
| --- | --- |
| Schema | missing required column, extra column, malformed token |
| Codes | known code, documented NA, unknown code |
| Numeric | null spike, zero/negative rule, extreme but preservable value |
| Ingestion | duplicate partition replay, partial file, source checksum change |
| Freshness | stale activity period, revised dynamic source |
| Lineage | affected mart, unrelated mart, missing dbt artifact |
| Approval | approved, denied, missing approval identity |
| Recovery | successful backfill, postcondition failure, rerun idempotency |

- **Evidence** - active HMDA EDA cases, ingestion idempotency, reliability and recovery contracts
- **Implication** - 처음부터 exhaustive benchmark를 만들지 않고 각 boundary당 대표 positive·negative case를 먼저 둔다.

### F5. synthetic benchmark 자체도 다축으로 검증해야 한다

2026년 Microsoft Research의 SynAE는 tool-calling agent synthetic benchmark를 validity, fidelity, diversity와 downstream evaluation 축으로 평가하며 단일 metric으로 품질을 충분히 설명할 수 없다고 보고한다. Project Pivot의 case도 domain validity, failure coverage, 중복도와 실제 lifecycle discrimination을 별도로 봐야 한다.

- **Evidence** - Microsoft Research SynAE
- **Implication** - case 수를 늘리는 것보다 서로 다른 failure surface를 식별하고 false confidence를 줄이는 것이 중요하다.

## Options

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| pytest example만 사용 | 단순하고 oracle이 명확하다 | unexpected combination과 sequence coverage가 약하다 |
| named case + Hypothesis | deterministic regression과 exploration을 함께 제공한다 | seed·strategy·shrunk failure 관리가 필요하다 |
| 외부 eval platform 우선 | UI와 비교 기능이 빠르다 | case semantics와 oracle이 정리되지 않으면 platform만 남는다 |

## Conclusion

- **Answer** - 평가의 중심은 versioned case registry, deterministic oracle과 lifecycle stage별 scorecard다.
- **Recommendation** - 12~20개의 named case로 boundary를 먼저 고정하고, pure transformation에는 `@given`, lifecycle transition에는 제한된 stateful test를 추가한다. runner는 pytest 결과와 machine-readable evaluation report를 동시에 생성한다.
- **Next Step** - `synthetic-reliability-evaluation` OpenSpec change에서 case schema, initial catalog, evaluator interface와 report contract를 정의한다. Langfuse 같은 backend integration은 이 local runner가 안정된 뒤 adapter로 추가한다.

## Validation Candidates

1. clean case에서 모든 detector가 false positive를 만들지 않는지 확인한다.
2. 각 injected defect가 expected rule 하나 이상을 재현하고 unrelated rule을 오염시키지 않는지 확인한다.
3. approval denied/missing case에서 source와 target mutation이 0인지 확인한다.
4. 동일 case/version/seed를 반복 실행해 stable result를 확인한다.
5. mutation 또는 intentionally broken implementation이 대응 case를 실제로 실패시키는지 확인한다.
6. case family별 coverage와 중복도를 report에 기록한다.

## Evidence

| Evidence | Supports | Location |
| --- | --- | --- |
| Property-based testing | F1 | https://hypothesis.readthedocs.io/en/latest/ |
| Stateful testing | F1 | https://hypothesis.readthedocs.io/en/latest/stateful.html |
| Experiment dataset model | F2 | https://langfuse.com/docs/evaluation/experiments/data-model |
| Deterministic code evaluators | F2 | https://langfuse.com/docs/evaluation/evaluation-methods/code-evaluators |
| Synthetic benchmark quality axes | F5 | https://www.microsoft.com/en-us/research/publication/synae-a-framework-for-measuring-the-quality-of-synthetic-data-for-tool-calling-agent-evaluations/ |
| Runtime boundaries | F2, F3 | `docs/ARCHITECTURE.md` |
| Reliability contract | F3, F4 | `docs/domains/reliability.md` |
| Current lifecycle tests | F3 | `tests/data_operations/test_incident_lifecycle.py` |
| Active EDA cases | F4 | `openspec/changes/hmda-eda-foundation-extension/tasks.md` |

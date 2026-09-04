---
type: review
title: "PR 205 Review: 2026 Defect Evaluation and Orchestration Quality Gate"
description: "PR 205 최신 구현 헤드(00cd3eb4)의 synthetic 2026 평가와 Airflow quality gate를 재검토하고 남은 architecture, contract, validation 이슈를 기록한다."
status: completed
reviewed_revision: "00cd3eb4bf5d3a41cb9e0fd32f978ab3a0799df6"
tags:
  - reliability
  - orchestration
  - hmda-data
  - data-operations
  - openspec
---

# PR 205 Review: 2026 Defect Evaluation and Orchestration Quality Gate

> [!NOTE]
> 최신 구현을 다시 검토한 결과, 이전 리뷰의 0-row silent pass, 예외 chaining 단절, 느슨한 로그 assertion, OpenSpec task metadata, 단순 `case_name` 연도 누락 문제는 대부분 보완되었다. Airflow critical path에 `raw → quality gate → analytics`를 두는 방향도 유지하는 것이 적절하다. 다만 quality policy ownership, synthetic filename/ingestion contract, durable architecture 문서 정합성, tracked sandbox credential 및 현재 CI 상태가 남아 있어 판정은 **Revise**다.

## Overview

| Target | Reviewed revision | Scope | Verdict |
| --- | --- | --- | --- |
| PR #205 | `00cd3eb4bf5d3a41cb9e0fd32f978ab3a0799df6` | synthetic 2026 evaluation, Airflow quality gate, OpenSpec, orchestration tests, inbox operational guides | Revise |

## Review Direction

Quality gate 자체를 Airflow에서 제거하는 것은 권장하지 않는다. 실행 경계는 다음과 같이 유지하는 편이 적절하다.

```text
Bronze ingestion
  ↓
Airflow quality gate
  ↓
dbt analytics build
  ↓
validated artifact promotion
```

Airflow는 gate의 실행 시점, task state, downstream blocking을 소유하고, 실제 quality/reliability policy는 owning domain의 public boundary에 위임하는 방향을 기준으로 검토했다.

## Findings

### F1. Quality policy ownership이 orchestration domain에 남아 있음

- **Severity** - 🟠 High
- **Location** - [`src/hmda_reliability/orchestration/quality_gate.py`](../../src/hmda_reliability/orchestration/quality_gate.py), [`openspec/changes/orchestration-quality-gate/design.md`](../../openspec/changes/orchestration-quality-gate/design.md)
- **Evidence** - `orchestration/quality_gate.py`가 `_BASELINE_NULL_RATES`, `_GATE_THRESHOLDS`, 활성 detector 범위, unsupported profile column 정책, `empty_partition` blocking 조건과 baseline 조립을 직접 소유한다. 반면 canonical [`openspec/specs/orchestration-pipeline/spec.md`](../../openspec/specs/orchestration-pipeline/spec.md)의 Domain delegation requirement는 orchestration이 reliability business rule을 중복 구현하지 않고 Reliability public boundary에 위임하도록 요구하고, [`docs/domains/reliability.md`](../../docs/domains/reliability.md)는 profile/detection을 Reliability 책임으로 둔다.
- **Impact** - Airflow adapter와 reliability policy가 같은 orchestration package에 결합되어 threshold/baseline 변경이 orchestration 변경으로 번지고, 향후 dbt test 또는 다른 validation implementation을 gate에 조합할 때 ownership이 불명확해진다.
- **Required Change** - `evaluate_quality_gate_task()`와 DAG dependency는 orchestration에 유지하되, baseline/threshold/detection policy는 Reliability 또는 해당 application composition boundary로 이동한다. Airflow task는 request 구성, gate 호출, `PASS/BLOCK`을 Airflow task state로 번역하는 thin adapter 역할만 갖게 한다.

### F2. `case_name` 연도 검증이 실제 ingestion parser semantics와 일치하지 않음

- **Severity** - 🟠 High
- **Location** - [`src/hmda_reliability/hmda_data/synthetic/cases.py`](../../src/hmda_reliability/hmda_data/synthetic/cases.py), [`src/hmda_reliability/hmda_data/ingestion/_source_query.py`](../../src/hmda_reliability/hmda_data/ingestion/_source_query.py), [`tests/hmda_data/test_synthetic.py`](../../tests/hmda_data/test_synthetic.py)
- **Evidence** - 현재 `null_spike()`는 `target_year` 문자열이 `case_name` 어디엔가 포함되어 있으면 허용한다. 그러나 ingestion의 `_source_year_sql()`은 filename에서 첫 번째 `\d{4}`를 추출한다. 따라서 `target_year=2026`, `case_name="null_spike_2025_2026"`은 synthetic validation을 통과하지만 ingestion에서는 `source_year=2025`로 해석된다.
- **Impact** - synthetic output의 `activity_year`는 2026인데 ingestion partition discriminator는 2025가 되어 downstream `load_hmda_loans_partition(..., 2026)`에서 행이 선택되지 않거나 partition mismatch를 일으킬 수 있다. 즉 generator의 safety guard와 실제 ingestion contract가 서로 다른 성공 조건을 가진다.
- **Required Change** - `case_name`에서 ingestion이 추출할 첫 번째 4자리 연도가 `target_year`와 정확히 일치하도록 검증하거나, generator가 output filename의 연도 부분을 canonical하게 구성한다. `case_name="null_spike_2025_2026"`, `target_year=2026` regression test를 추가하고 관련 synthetic OpenSpec delta에도 filename/partition contract를 명시한다.

### F3. 3-stage DAG와 durable architecture 문서가 아직 동기화되지 않음

- **Severity** - 🟠 High
- **Location** - [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md), [`docs/domains/orchestration.md`](../../docs/domains/orchestration.md), [`openspec/specs/orchestration-pipeline/spec.md`](../../openspec/specs/orchestration-pipeline/spec.md), [`openspec/changes/orchestration-quality-gate/specs/orchestration-pipeline/spec.md`](../../openspec/changes/orchestration-quality-gate/specs/orchestration-pipeline/spec.md)
- **Evidence** - 구현과 active OpenSpec delta는 `raw → quality gate → analytics`를 정의하지만, durable architecture는 여전히 Airflow가 Bronze 적재 후 dbt 분석만 실행한다고 설명한다. `docs/domains/orchestration.md`는 DAG에 raw load와 analytics build 두 task만 등록된다고 명시한다. canonical orchestration spec도 workflow graph와 ordered execution을 raw/analytics 2-stage 기준으로 서술한다.
- **Impact** - merge 후 implementation, domain guide, architecture guide, durable spec의 시스템 경계가 서로 다르게 읽힌다. 특히 `run_dbt_build=false`에서 gate는 실행하고 analytics만 skip할 것인지, gate failure가 DAG 전체를 실패시킬 것인지 durable contract가 명확하지 않다.
- **Required Change** - quality gate를 허용하는 data-plane contract로 architecture를 갱신한다. 최소한 `docs/ARCHITECTURE.md`, `docs/domains/orchestration.md`, orchestration quality-gate OpenSpec delta가 `Bronze → read-only blocking admission gate → analytics`와 `run_dbt_build=false` semantics를 일관되게 설명해야 한다. Incident lifecycle, remediation, approval, recovery, evaluation은 계속 Airflow 자동 경로 밖에 둔다.

### F4. Sandbox guide에 generated Airflow credential literal이 tracked content로 포함됨

- **Severity** - 🟡 Medium
- **Location** - [`inbox/2026-09-04/07-12-guide-orchestration-sandbox-dag-testing.md`](07-12-guide-orchestration-sandbox-dag-testing.md)
- **Evidence** - 로컬 Airflow standalone이 생성한 admin password 값이 문서 본문에 literal로 기록되어 있다. 같은 문서는 해당 password를 local generated file에서 확인할 수 있다고도 안내한다.
- **Impact** - local-only credential이라도 generated secret material을 repository history에 고정하며, 환경이 외부에서 접근 가능하게 구성될 경우 불필요한 credential reuse 위험을 만든다.
- **Required Change** - 실제 password literal을 제거하고 local generated password file에서 확인하라는 안내만 남긴다. 이미 push된 history rewrite는 별도 승인 대상이며 이 리뷰의 required change에 포함하지 않는다.

### F5. 최신 head CI가 Markdown validation 단계에서 실패하여 Python/test validation이 수행되지 않음

- **Severity** - 🟡 Medium
- **Location** - CI Lite run `33840028830`, [`inbox/2026-09-04/14-02-proposal-orchestration-quality-gate-direction.md`](14-02-proposal-orchestration-quality-gate-direction.md), [`inbox/2026-09-04/07-12-guide-orchestration-sandbox-dag-testing.md`](07-12-guide-orchestration-sandbox-dag-testing.md)
- **Evidence** - 최신 reviewed revision의 CI Lite는 `Validate changed Markdown`에서 실패했다. `14-02-proposal...`의 ordered-list style이 `rumdl fmt`에 의해 변경되고, sandbox guide에는 repository에 존재하지 않는 local DB/password 파일을 relative Markdown link로 둬 MD057이 발생한다. 이 단계 실패로 Python validation과 selected tests는 실행되지 않았다.
- **Impact** - 현재 PR 본문의 `ruff`, `ty`, `rumdl`, tests 전체 통과 주장은 최신 head CI evidence와 일치하지 않으며, 코드 변경의 merge-candidate validation이 완료되지 않았다.
- **Required Change** - changed Markdown을 repository rule에 맞게 수정하고 CI를 다시 통과시킨 뒤 PR Validation 섹션을 실제 최신 결과로 갱신한다. Local-only 경로는 Markdown link가 아니라 code span/path text로 표현하는 편이 적절하다.

## Resolved Previous Findings

최신 구현에서 다음 이전 finding은 보완된 것으로 확인했다.

| Previous finding | Latest state |
| --- | --- |
| 0-row partition이 quality gate를 clean으로 통과 | `current.row_count == 0`에서 `QualityGateError` 발생으로 보완 |
| unexpected error의 exception chaining 단절 | `raise AirflowException(...) from exc`로 causal context 보존 |
| clean log assertion의 boolean precedence 문제 | message와 `status == clean`을 함께 검증하도록 보완 |
| orchestration quality-gate `tasks.md` metadata 누락 | frontmatter와 task count 보완 |
| 연도 없는 custom `case_name` 허용 | `target_year` 문자열 포함 guard 추가; 단 F2의 parser semantics mismatch는 잔존 |
| 최초 synthetic 2026 F1~F6 | REPLACE 충돌, 다중 연도, target year validation, 실제 ingestion E2E, strict assertions 등 주요 항목 보완 확인 |

## PR Scope Assessment

Synthetic evaluation과 Airflow gate를 반드시 별도 PR로 분리해야 한다고 보지는 않는다. 다음 연결이 실제 구현에서 유지된다면 하나의 coherent change로 설명할 수 있다.

```text
synthetic defect evaluation
  → detector behavior 검증
  → 동일 reliability detection semantics 재사용
  → production data-plane blocking gate
```

다만 현재 PR title/body는 여전히 synthetic 2026 평가를 중심으로 쓰여 있고 Boundaries에는 Airflow DAG 변경이 out of scope로 남아 있다. 단일 PR로 유지한다면 title, Summary, Changes, Boundaries를 실제 scope에 맞게 갱신해야 한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| 최신 PR metadata/diff 확인 | head `00cd3eb4`, 5 commits, 23 changed files | Pass |
| 이전 review remediation 정적 확인 | 0-row, chaining, assertion, tasks metadata, `case_name` guard | Pass |
| quality gate implementation 정적 검토 | baseline/threshold/detector ownership 및 task adapter 확인 | Finding F1 |
| synthetic filename/ingestion contract 대조 | `case_name` contains check vs first-4-digit parser | Finding F2 |
| architecture/OpenSpec 대조 | 3-stage implementation vs durable 2-stage documentation | Finding F3 |
| latest CI Lite | run `33840028830` | Fail at Markdown validation |
| Python static analysis / selected tests on latest head | Markdown failure 때문에 해당 CI 단계 미실행 | Not validated |
| independent subagent Quality + Adversarial review | 현재 runtime에서 subagent invocation unavailable | Not performed |

## Remaining Risks

- `_BASELINE_NULL_RATES`의 고정값은 MVP/synthetic proof에는 사용할 수 있으나 실제 2026 source 분포가 달라지면 false positive/negative 위험이 있다. F1 ownership을 정리할 때 baseline lifecycle도 같은 policy boundary에서 관리할 필요가 있다.
- 모든 detector 결과를 blocking으로 확장할 경우 통계적 anomaly가 availability incident를 만들 수 있다. 현재 MVP는 null-spike 중심이므로 허용할 수 있지만, 장기적으로 `FAIL`, `WARN`, `OBSERVE` 같은 enforcement policy 분리를 검토할 가치가 있다.
- Raw asset event는 gate보다 먼저 성공할 수 있으므로 향후 asset-driven downstream DAG를 추가한다면 raw/untrusted asset과 validated/trusted asset semantics를 분리해야 한다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | Airflow gate 방향은 유지 가능하지만 policy ownership(F1), filename/partition contract(F2), durable architecture 정합성(F3)과 현재 CI failure(F5)를 해결해야 함 | PR #205 브랜치에서 최소 수정 후 재검토 |

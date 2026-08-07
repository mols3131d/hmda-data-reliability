# Project Pivot Deep Review

- **Repository:** `mols3131d/project-pivot`
- **Baseline:** `main@8980e0956d6b70a7725d7f241d70caadc81189dd`
- **Reviewed:** 2026-08-07 (Asia/Seoul)
- **Method:** repository structure, canonical documents, core source, representative tests, active OpenSpec changes, dependency and automation configuration을 정적 교차검토했다.
- **Limitation:** 이 리뷰에서는 test suite, dbt build, 실제 HMDA source를 실행하지 않았다. 실행 통과 여부와 resource behavior는 별도 검증이 필요하다.

## Executive Verdict

**Foundation의 방향은 타당하지만, 아직 “신뢰 가능한 evidence-first system”이 완성됐다고 보기 어렵다.**

가장 좋은 부분은 data plane과 reliability control plane의 분리다. `hmda_data`, `data_platform`, `reliability`, `data_operations`, `orchestration`의 책임이 비교적 선명하며, 위험 작업을 read-only lifecycle과 분리한 architecture도 적절하다.

반면 현재 주요 위험은 기능 부족이 아니라 **실패 시 증거 보존**, **profile 비교 의미**, **완료 상태의 정합성**이다. 특히 dbt artifact를 새 build 전에 삭제하는 방식, 측정 불가능한 freshness를 정상 시각으로 대체하는 방식, 완료된 OpenSpec change와 제거된 Marimo의 잔재는 프로젝트가 주장하는 재현성·검증 가능성을 약화한다.

### Assessment

| Area | Assessment | Summary |
| --- | --- | --- |
| Product focus | Good | HMDA reliability demonstration이라는 목적이 명확하다. |
| Architecture | Good | data plane, lifecycle, approval/recovery 경계가 잘 분리됐다. |
| Domain contracts | Mixed | Pydantic contract는 강하지만 비교 fingerprint와 event identity가 부족하다. |
| Testing | Good locally | scenario별 test가 풍부하지만 자동 gate와 의미 검증이 부족하다. |
| Evidence integrity | Needs work | 실패 시 last-known-good artifact 보존과 temporal identity가 약하다. |
| Repository governance | Needs work | active change, metadata, dependency, 문서가 현재 상태와 어긋난다. |

## What Is Working

### 1. Architecture boundary가 목적과 맞는다

`docs/ARCHITECTURE.md`는 ingestion/dbt data plane, read-only reliability lifecycle, external approval, recovery/evaluation을 분리한다. 실제 package 구조도 이 경계를 대체로 따른다. 위험 작업을 lifecycle에 자동 결합하지 않은 결정은 local portfolio system에서도 설명 가능성과 안전성을 높인다.

### 2. Partition ingestion의 원자성과 identifier 처리가 좋다

`hmda_data/ingestion/partition.py`는 staging table 검증 뒤 delete/insert를 transaction으로 묶고, 실패 시 rollback한다. SQL value는 parameter binding을 사용하고 identifier는 공용 quoting helper를 거친다. 이 부분은 재실행 가능성과 SQL 안전성의 좋은 foundation이다.

### 3. Test suite가 domain contract 중심으로 구성됐다

`tests/`는 package 구조를 따라 data platform, operations, HMDA data, dbt, orchestration, reliability로 나뉜다. Reliability는 approval, profile, detection, impact, remediation, recovery, evaluation을 각각 검증한다. 단순 coverage 채우기보다 observable contract를 고정하려는 방향이 보인다.

### 4. Actual-source evidence 생성 경로가 재현성을 고려한다

`scripts/run_actual_source.py`는 source SHA-256, repository revision, observed time을 기록하고 portable JSON과 Markdown을 같은 observation에서 생성한다. dirty repository를 거부하는 정책도 provenance 관점에서 유효하다.

## Findings

## P1 — dbt build 실패가 last-known-good evidence를 제거한다

**Evidence:** `src/project_pivot/data_operations/runner.py`

`run_dbt_build()`는 process 실행 전에 기존 `manifest.json`과 `run_results.json`을 삭제한다. 이후 timeout, process failure, dbt test failure가 발생하면 직전 성공 build의 artifact도 사라진다.

이 artifact는 downstream impact analysis의 입력이다. 따라서 build 실패가 단순 실행 실패를 넘어 **이전 lineage evidence까지 소실시키는 결과**를 만든다. Evidence-first system에서는 실패한 시도와 마지막 성공 상태를 함께 보존해야 한다.

**Recommendation**

- build마다 별도 target directory를 사용한다.
- 성공 후에만 `current` pointer 또는 canonical artifact를 promote한다.
- `last_successful`과 `failed_attempt`의 revision, command, timestamp를 분리해 기록한다.

## P1 — Profile compatibility가 비교 의미를 충분히 검증하지 않는다

**Evidence:**

- `src/project_pivot/data_operations/incident_lifecycle.py`
- `src/project_pivot/reliability/detection/detector.py`
- `src/project_pivot/reliability/profiling/profile_snapshot_builder.py`

Lifecycle은 baseline과 current의 `asset_name`, `partition`만 비교한다. 그러나 detection 의미에는 최소한 다음이 함께 일치해야 한다.

- profile column set
- partition column과 normalization
- freshness column과 fallback policy
- schema hash algorithm/version
- metric definition version

현재 null spike detector는 baseline에 없는 current column을 baseline null rate `0.0`으로 간주한다. 같은 table schema에서 profile column 설정만 달라져도 false positive가 가능하다.

**Recommendation**

`ProfileSnapshot`에 `profile_contract_fingerprint`를 추가하고 lifecycle 진입 시 동일성을 강제한다. Fingerprint에는 metric version, selected columns, partition/freshness semantics를 포함한다.

## P1 — “측정 불가 freshness”가 정상 관측값으로 변환된다

**Evidence:**

- `profile_snapshot_builder.py`는 freshness 값이 없으면 `observed_at`을 사용한다.
- `tests/reliability/test_profile_snapshots.py`는 빈 partition에서 이 동작을 정답으로 고정한다.

빈 partition 또는 freshness column 미사용은 freshness가 최신이라는 뜻이 아니라 **측정되지 않았다는 뜻**이다. 이를 `observed_at`으로 대체하면 detector가 delay를 발견하지 못하거나 잘못된 정상 상태를 생성할 수 있다. `freshness_used_fallback` metric이 있어도 detector는 이를 고려하지 않는다.

**Recommendation**

- `freshness_at: datetime | None`으로 표현한다.
- 상태를 `measured | unavailable | empty_partition`으로 분리한다.
- detector는 unavailable을 skip이 아니라 명시적 inconclusive result로 반환한다.

## P2 — Snapshot, evidence, incident ID가 반복 실행을 구분하지 못한다

**Evidence:**

- snapshot ID: asset + partition
- incident/evidence ID: type + asset + partition + optional column

동일 partition을 여러 번 관측하면 ID가 반복된다. 현재 객체를 일회성으로만 전달할 때는 문제가 없지만, 향후 persistence, evaluation, replay를 도입하면 사건과 관측이 충돌한다.

**Recommendation**

- snapshot ID는 contract fingerprint + observed_at 또는 content digest를 포함한다.
- incident는 stable issue key와 occurrence ID를 분리한다.
- evidence는 immutable observation ID를 사용한다.

## P2 — EDA evidence contract가 reliability contract보다 약하다

**Evidence:** `src/project_pivot/hmda_data/eda/analysis.py`, `explorer.py`

EDA는 넓은 `dict[str, Any]`를 생산하고 explorer도 key 존재를 런타임에 추측한다. 반면 reliability layer는 Pydantic contract를 사용한다. 이 차이는 key rename, denominator 변경, serialization drift가 type/static check를 통과하게 만든다.

또한 analyzer의 `duration_seconds`는 source relation 생성과 schema inference 이후부터 측정되어 이름과 달리 전체 실행 시간이 아니다. Actual-source 문서는 이를 `Total Duration`으로 표시하므로 evidence semantics가 어긋난다.

**Recommendation**

- `HMDACoreEDAEvidence`와 하위 model을 도입한다.
- `total_duration_seconds`와 `aggregation_duration_seconds`를 구분한다.
- source fingerprint는 wrapper만이 아니라 canonical evidence envelope의 필수 field로 둔다.

## P2 — 자동 verification gate가 없다

**Evidence:** `.github/`에는 agents, hooks, instructions만 있고 `workflows/`가 없다.

Local test guide와 pytest configuration은 잘 정리되어 있으나 PR에서 강제되지 않는다. `pytest-cov`가 설치되어도 기본 suite에는 coverage 수집이나 minimum threshold가 없고, memory/stress test는 기본 제외다.

이는 개인 프로젝트에서 즉시 치명적이지 않지만 agent가 병렬로 변경하는 현재 workflow에서는 regression cost를 다시 사람의 심층 리뷰에 전가한다.

**Minimum gate**

1. Ruff format/check
1. 하나의 type checker만 선택해 strict check
1. unit/component pytest
1. deterministic dbt fixture build/test
1. Markdown lint

Memory/stress와 actual-source run은 별도 수동 또는 scheduled gate로 유지한다.

## P2 — Marimo 제거가 repository 전체에 반영되지 않았다

**Evidence:**

- Active change는 Marimo code/test 전면 제거를 완료했다고 기록한다.
- `pyproject.toml`에는 `marimo` dependency와 `[tool.marimo.runtime]`이 남아 있다.
- `DEVELOPMENT.md`는 Notebook layer를 Marimo로 설명한다.
- `scripts/stop_marimo_kernels.py`가 남아 있다.

이 상태는 dependency와 canonical documentation이 implementation보다 뒤처진 사례다. `PyIceberg`, OpenTelemetry 관련 dependency도 Foundation active scope와 분리 여부를 재검토할 필요가 있다.

**Recommendation**

- Marimo를 완전히 제거하거나 별도 optional group으로 격리한다.
- base runtime dependency는 실제 production import graph 기준으로 축소한다.
- 제거 change에 repository-wide residue test를 추가한다.

## P2 — OpenSpec 완료 상태가 서로 모순된다

**Evidence:**

- `hmda-eda-baseline-reduce-core-scope/tasks.md`: 모든 checkbox는 완료지만 `tasks_completed: 0`.
- `hmda-eda-reconcile-core-contract/tasks.md`: `16/16` 완료지만 active change로 남아 있다.
- 두 active change가 같은 EDA core contract를 연속으로 다룬다.
- reconcile tasks에는 설명 없는 `![alt text](image.png)`가 삽입되어 있다.

OpenSpec이 source of planning truth라면 완료 여부와 active set이 정확해야 한다. 지금은 agent가 오래된 change를 다시 적용하거나 두 contract 중 어느 것이 authoritative한지 추론해야 한다.

**Recommendation**

- 먼저 두 change의 관계를 확정한다: supersede 또는 sequential completion.
- metadata를 checkbox에서 자동 계산해 drift를 제거한다.
- 완료 change는 review gate 후 archive한다.
- active change 수를 가능한 한 1개 capability당 1개로 제한한다.

## P3 — README가 repository complexity를 설명하지 못한다

README는 한 문장으로 목적만 설명한다. 신규 reviewer는 실행 방법, data requirement, 핵심 flow, current status, 안전 경계를 찾기 위해 여러 문서를 탐색해야 한다.

**Recommendation**

README에는 다음만 추가한다.

- Why / scope
- 6단계 system flow
- synthetic fixture 기반 quickstart
- actual HMDA data는 repository에 포함되지 않는다는 안내
- canonical docs links

## P3 — Schema hash가 column order를 무시한다

`calculate_schema_hash()`는 column metadata를 name으로 정렬한다. 따라서 column order만 바뀐 schema는 동일 hash가 된다. 모든 downstream SQL이 name-based라면 허용 가능하지만, ingestion이 `INSERT ... SELECT *`를 사용하므로 order가 실제 호환성에 영향을 줄 수 있다.

**Recommendation**

Schema contract에 ordinal position을 포함하거나, ingestion을 명시적 column mapping으로 바꾼 뒤 order-insensitive 정책을 문서화한다.

## Priority Plan

### Gate 0 — Evidence semantics

1. dbt artifact last-known-good 보존
1. profile contract fingerprint 도입
1. freshness unavailable 상태 모델링
1. temporal evidence identity 설계

이 네 항목이 해결되기 전에는 reliability 결과를 durable audit evidence로 확장하지 않는다.

### Gate 1 — Foundation closure

1. 두 EDA OpenSpec change 정리·archive
1. Marimo와 inactive dependency residue 제거
1. minimal CI gate 추가
1. README quickstart 작성
1. canonical docs와 runtime dependency 재정렬

### Gate 2 — MVP proof

Synthetic source 하나로 다음 end-to-end scenario를 고정한다.

`clean baseline → injected defect → detection → dbt impact → remediation draft → approval rejection/acceptance → partition backfill → validation → evaluation report`

각 단계가 동일한 immutable evidence chain을 참조하면 이 프로젝트의 포트폴리오 가치가 가장 선명해진다.

## Final Assessment

Project Pivot은 과도하게 넓은 data platform이 아니라 **작고 설명 가능한 reliability case system**으로 수렴하고 있다. Architecture와 test decomposition은 이미 Foundation 수준에서 좋은 편이다.

다음 개선의 중심은 기능 추가가 아니다. **증거를 잃지 않는 실패 처리, 비교 가능한 profile contract, 현재 상태와 일치하는 repository governance**를 먼저 완성해야 한다. 이 세 축이 정리되면 MVP 개발은 새로운 framework를 더하는 작업이 아니라, 이미 존재하는 lifecycle을 하나의 검증 가능한 scenario로 연결하는 작업이 된다.

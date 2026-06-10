# Foundation Readiness

## 목적

MVP 구현 전에 고정된 기반 상태를 한 곳에서 확인한다. 이 문서는 scratch 입력 메모를 현재 repo 증거와 연결하는 체크포인트다.

## 입력 근거

| 문서 | 역할 |
|---|---|
| `proposal.md` | 프로젝트 문제와 incident lifecycle 정의 |
| `architecture.md` | 컴포넌트 책임과 승인 경계 |
| `tech_stack.md` | 기술 도입 기준과 책임 |
| `mvp_scope.md` | MVP 포함/제외 범위 |
| `foundation.md` | foundation 원칙과 완료 기준 |
| `memo.md` | OpenSpec 작업 순서 |

## 완료된 기반 증거

| Capability | 현재 Spec | 완료 Archive | 검증 |
|---|---|---|---|
| Reliability contracts | `../../openspec/specs/reliability-contracts/spec.md` | `../../openspec/changes/archive/2026-06-07-define-reliability-contracts/tasks.md` | `uv run pytest tests/reliability/contracts` |
| Taxi data foundation | `../../openspec/specs/taxi-data-foundation/spec.md` | `../../openspec/changes/archive/2026-06-08-implement-taxi-data-foundation/tasks.md` | `uv run pytest tests/taxi_data/test_database.py tests/taxi_data/test_synthetic.py` |
| Partition ingestion | `../../openspec/specs/partition-ingestion/spec.md` | `../../openspec/changes/archive/2026-06-08-implement-partition-ingestion/tasks.md` | `uv run pytest tests/taxi_data/test_ingestion_partition.py` |
| dbt analytics foundation | `../../openspec/specs/dbt-analytics-foundation/spec.md` | `../../openspec/changes/archive/2026-06-09-implement-dbt-analytics-foundation/tasks.md` | `uv run pytest tests/dbt` |

## Contract 기준

Foundation contract는 `Incident`, `Evidence`, `ProfileSnapshot`, `LineageEvidence`, `Approval`이다. 구현 위치는 `../../src/project_pivot/reliability/contracts/`다.

## Foundation 제외 범위

- detector 구현
- LangGraph RCA workflow 구현
- Dagster asset graph, schedule, backfill 구현
- 고급 dbt 모델 확장
- production 배포 구성
- dashboard UI 구현

## 다음 MVP 후보

| 순서 | 후보 | Backlog |
|---|---|---|
| 1 | Profile snapshot 생성 | `../../docs/backlogs/add-profile-snapshots.md` |
| 2 | 기본 incident detection | `../../docs/backlogs/add-basic-incident-detection.md` |
| 3 | dbt lineage 기반 impact analysis | `../../docs/backlogs/add-impact-analysis.md` |
| 4 | remediation draft 생성 | `../../docs/backlogs/add-remediation-draft.md` |
| 5 | approval 기반 backfill/validation | `../../docs/backlogs/add-approval-backfill-validation.md` |
| 6 | evaluation report 생성 | `../../docs/backlogs/add-evaluation-report.md` |

## 검증 명령

```bash
test -f openspec/specs/foundation-baseline/spec.md
test -f openspec/changes/archive/2026-06-10-complete-foundation-baseline/tasks.md
env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/reliability/contracts tests/taxi_data tests/dbt
```

위 명령이 통과하면 foundation baseline은 완료 상태로 본다. MVP 후보는 별도 OpenSpec change로 진행한다.

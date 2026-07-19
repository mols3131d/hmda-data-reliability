## Context

`run_incident_lifecycle()`은 metadata/profile, 합성 `volume_drop`, detection, impact, remediation, 자동 승인 backfill, evaluation report를 함께 수행한다. Dagster asset은 baseline 없이 이를 호출해 과거 baseline과 current snapshot을 비교하지 못한다. reliability 하위 API에 탐지, 승인 기반 recovery, evaluation이 이미 분리돼 있다.

`remove-pipeline-cli` change의 단계 함수 유지를 전제로 새 lifecycle 계약을 정의한다. 해당 change archive 후 적용한다.

## Goals / Non-Goals

**Goals:**

- lifecycle 단계가 caller-supplied baseline과 DB에서 측정한 실제 current snapshot만 비교한다.
- 탐지된 모든 incident의 impact와 remediation을 결과에 보존한다.
- 탐지, 승인/recovery, synthetic evaluation의 실행 경계를 분리한다.
- baseline 공급 경로가 없는 Dagster pipeline에서 lifecycle asset을 제거한다.

**Non-Goals:**

- baseline 저장소나 최초 baseline 생성 정책 추가.
- 새 approval UI, recovery wrapper, evaluation runner 추가.
- 기존 reliability detector, recovery, evaluation 내부 동작 변경.
- 호환 shim 또는 deprecation 기간 제공.

## Decisions

### Caller가 baseline을 제공한다

`run_incident_lifecycle(request, baseline)`을 공개 계약으로 삼는다. 자동 조회는 file 또는 DuckDB 저장 정책을 숨은 책임으로 추가한다. 호출자가 baseline 소유권과 시점을 결정하고 lifecycle은 비교·분석만 담당한다.

JSON 자동 관리와 DuckDB Control table은 baseline 승격 정책·동시성·migration이 필요해 제외한다.

### current snapshot은 함수가 DB에서 측정한다

`create_profile_snapshot()`과 `ProfileSnapshotRequest`를 재사용한다. `simulate_row_count_ratio`와 `model_copy()` 기반 합성 current는 삭제한다. baseline과 current의 asset 또는 partition 불일치 시 문맥을 담은 `DataOperationError`를 반환한다.

### 모든 detection을 처리한다

`detections[0]` 선택을 제거하고 각 detection에 기존 impact/remediation API를 적용한다. 요약은 detector 순서를 유지하며 `dict.fromkeys()`로 중복을 제거한다. 별도 collection class는 만들지 않는다.

### recovery와 evaluation은 독립 capability로 남긴다

lifecycle은 approval 생성, partition 변경, evaluation 파일 작성을 하지 않는다. `execute_approved_backfill()`, `build_evaluation_report()`, `write_evaluation_report()`는 독립 reliability API와 단위 테스트로 유지한다.

### Dagster lifecycle asset을 제거한다

Dagster baseline 공급 계약이 없으므로 임시 기본값·합성값을 만들지 않는다. `pipeline_job`은 `raw_hmda_loans`, `dbt_loan_analytics`만 materialize한다. baseline source 정의 후 Control asset을 재추가할 수 있다.

## Risks / Trade-offs

- [공개 API 파손] 단일 인자 호출과 기존 결과 필드가 실패한다. 저장소 호출부·문서를 함께 갱신하고 호환 shim은 두지 않는다.
- [Control plane 통합 신호 감소] Dagster lifecycle end-to-end 검증이 사라진다. lifecycle 직접 테스트와 reliability 단위 테스트를 유지한다.
- [baseline 공급자 부재] 함수는 직접 호출하지만 표준 pipeline에 연결되지 않는다. 잘못된 baseline 생성 대신 후속 capability가 저장·승격 정책을 정의한다.
- [다중 incident 비용] incident마다 dbt artifact를 분석한다. MVP에서 단순 반복하고 측정된 병목 발생 시 artifact parsing API를 확장한다.
- [OpenSpec change 중첩] `remove-pipeline-cli`가 같은 orchestration capability를 수정한다. 기존 change archive 후 적용한다.

## Migration Plan

1. `remove-pipeline-cli` change를 archive해 main specs와 이력을 확정한다.
2. lifecycle 단계 API와 결과 계약을 즉시 변경한다.
3. 합성 평가·복구 설정과 Dagster lifecycle asset을 제거한다.
4. OpenSpec main specs, README, architecture, private guide를 새 경계에 맞춘다.
5. 단계·orchestration·reliability 검증을 통과시킨 뒤 이 change를 archive한다.

Rollback: 이전 commit의 함수 시그니처, 결과 필드, Dagster asset·설정 복원. 데이터 migration 없음.

## Open Questions

없음.

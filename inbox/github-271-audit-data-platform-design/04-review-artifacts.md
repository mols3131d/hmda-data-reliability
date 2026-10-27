---
type: review
title: Artifact Primitive Test Audit
description: Artifact pair identity와 projection lock의 현행 테스트, 독립 oracle 보강과 promotion composition의 인계 경계를 검토합니다.
---

# Artifact Primitive Test Audit

> [!NOTE]
> Artifact primitive의 production defect는 재현하지 않았다. 기존 3개 테스트가 직접 구별하지 못하던 pair identity와 lock mode·오류 우선순위를 12개 case로 보강했다. Promotion composition의 historical result-only drift 항목은 #270/#277 소유로 유지한다.

- **Target:** Data Platform artifact identity와 projection lock primitive.
- **Revision:** 기준 main `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`, 최초 PR head `f1cf36e5baf74f356333c7a7ff70240287e27c55`. 실행은 main 병합 뒤 `4f2bebb4d5a5a6e64336e5df3c9c11b5da65f4ae`에 이 문서와 테스트의 working-tree 변경을 더한 상태에서 수행했다.
- **Scope:** [test_artifacts.py](../../tests/data_platform/test_artifacts.py) 전체와 [artifacts.py](../../src/hmda_reliability/data_platform/artifacts.py) 전체. [historical Data Platform review](01-review-historical/data-platform/README.md), [domain ownership](../../docs/domains/data-platform.md), 관련 Spec 및 Data Operations caller/test는 책임 경계 확인을 위해 읽었다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Minor | Pair identity의 결과 파일 단독 변경·순서·byte 경계·경로 독립성을 직접 구별하는 oracle 부재 | `accepted → resolved`: 독립 입력 쌍과 경로 이동 invariant, 누락 파일별 typed error를 추가 |
| F2 | Minor | Lock의 SH/EX 동작과 body/unlock 동시 실패의 우선순위가 기존 테스트에서 미확인 | `accepted → resolved`: 실제 OS lock contention 4종과 원래 body exception 보존을 추가 |

F1과 F2는 **test oracle gap**이다. 현재 source는 보강된 case를 통과하며 source defect로 분류하지 않는다. 현재 Data Platform의 두 canonical Spec은 artifact primitive의 세부 identity encoding이나 lock을 직접 선언하지 않는다. 이번 테스트는 [domain ownership](../../docs/domains/data-platform.md#scope)과 [기존 public primitive contract](../../src/hmda_reliability/data_platform/artifacts.py)를 보호하며, 없는 normative JSON validation 요구를 새로 만들지 않는다.

## Details

### F1 — Minor: Pair Identity Oracle

#### F1 Locations

- [test_artifacts.py](../../tests/data_platform/test_artifacts.py)
  - `test_projection_identity_distinguishes_artifact_pairs`
  - `test_projection_identity_depends_on_bytes_instead_of_paths`
  - `test_projection_identity_reports_the_unreadable_artifact`
- [artifacts.py](../../src/hmda_reliability/data_platform/artifacts.py)
  - `artifact_projection_id`, `ArtifactProjectionReadError`
- [Lifecycle result requirement](../../openspec/specs/data-operations-incident-lifecycle/spec.md#requirement-lifecycle-result)
  - Downstream에서 판단에 사용한 projection identity를 recovery 입력으로 식별한다.

#### F1 Evidence

기존 파일에는 lock 오류 테스트 3개만 있었으며 `artifact_projection_id`를 직접 호출하는 case가 없었다. 새 테스트는 manifest 고정/result 단독 변경, result 고정/manifest 단독 변경, 두 파일의 순서 교환, 같은 연결 byte를 갖는 `("{} ", "{}")`와 `("{}", " {}")`를 서로 다른 identity로 판정한다. Expected digest를 production 알고리즘으로 다시 계산하지 않는다.

같은 opaque byte pair를 다른 파일명으로 이동하면 identity가 같아야 한다. 비 UTF-8 manifest와 빈 result를 사용해 JSON 해석과 byte identity의 책임을 구별한다. 각 파일을 실제 삭제하면 `ArtifactProjectionReadError.artifact_path`가 삭제 경로와 일치하고 원래 `FileNotFoundError`가 cause로 남아야 한다.

별도 Python process에서 테스트 module의 함수 참조만 바꾸는 transient negative control 4종을 실행했다. Manifest만 해시, result만 해시, 단순 byte 연결, pair 정렬 후 연결은 각각 새 inequality assertion에 의해 거부됐다. Source 파일과 저장소 상태를 mutation하지 않았다.

#### F1 Impact

Manifest만으로 identity를 계산해 result-only 변경을 놓치거나 두 파일 경계를 지워도 기존 primitive 테스트가 green일 수 있었다. 이는 promotion이 잘못된 pair를 채택한다는 재현 결과와 구별된다.

#### F1 Action

위 7개 component case를 추가했다. SHA-256 자체의 암호학적 안전성이나 문서화되지 않은 JSON schema는 이 테스트의 acceptance로 삼지 않는다.

### F2 — Minor: Lock Mode And Error Precedence

#### F2 Locations

- [test_artifacts.py](../../tests/data_platform/test_artifacts.py)
  - `test_projection_lock_enforces_shared_and_exclusive_access`
  - `test_artifact_body_failure_takes_precedence_over_unlock_failure`
- [artifacts.py](../../src/hmda_reliability/data_platform/artifacts.py)
  - `artifact_projection_lock`

#### F2 Evidence

기존 setup/release 오류 case는 typed error를, body의 파일 read 실패 case는 원래 오류를 확인했다. 다만 `exclusive` flag가 실제 reader/writer exclusion을 만드는지, body와 unlock이 동시에 실패하면 어떤 오류가 남는지는 직접 구별하지 않았다.

새 matrix는 실제 `fcntl.flock`을 사용한다. Holder를 먼저 얻고 contender의 OS 호출에만 `LOCK_NB`를 더해 sleep 없이 충돌을 관찰한다. Reader/reader는 함께 진입하고 reader/writer, writer/reader, writer/writer는 body에 진입하지 못하며 원래 `BlockingIOError`가 typed lock error의 cause다. Holder 종료 뒤 exclusive 진입도 성공한다. Domain lock 함수를 mock으로 대체하지 않는다.

별도 case는 body의 `FileNotFoundError` 객체와 unlock의 `OSError`를 함께 발생시켜 caller가 정확히 원래 body exception 객체를 받는지 확인한다.

#### F2 Action

위 5개 component case를 추가했다. 동시 promotion의 pair consistency와 reader가 같은 physical projection lock을 쓰는지는 caller composition의 검증 경계로 남긴다.

## File Review And Contract Boundary

| File Or Contract | Review Outcome | Oracle Or Exclusion |
| --- | --- | --- |
| [test_artifacts.py](../../tests/data_platform/test_artifacts.py) | 전체 검토, 수정 | 기존 3 case 유지, 새 12 case. 각 case는 `tmp_path`와 scoped monkeypatch로 격리 |
| [artifacts.py](../../src/hmda_reliability/data_platform/artifacts.py) | 전체 읽기, 변경 없음 | 길이 framing을 포함한 ordered byte pair, read error path/cause, shared/exclusive lock, body failure 우선 계약 대조 |
| [Data Platform ownership](../../docs/domains/data-platform.md) | 읽기, 변경 없음 | Pair identity/lock은 Data Platform, candidate 선택/promotion은 Data Operations |
| [dbt analytics Spec](../../openspec/specs/data-platform-dbt-analytics/spec.md) | 전체 읽기, 변경 없음 | dbt model/lineage 계약. Primitive의 JSON parsing 요구는 소유하지 않음 |
| [DuckDB access Spec](../../openspec/specs/data-platform-duckdb-access/spec.md) | 전체 읽기, 변경 없음 | DB mutation lock 계약을 artifact lock의 정본 요구로 혼동하지 않음 |
| [Stage execution Spec](../../openspec/specs/data-operations-stage-execution/spec.md#requirement-dbt-build-execution)와 [runner.py](../../src/hmda_reliability/data_operations/runner.py) | 관련 build·promotion·pair validation 경계 검토 전용 | 필수 파일 존재와 현재 실행 성공, candidate identity recheck는 #270/#277 |
| [Lineage artifact validation](../../openspec/specs/reliability-impact-analysis/spec.md#requirement-lineage-artifact-validation) | Spec 전체 읽기, 변경 없음 | 해석 불가능한 manifest·누락 run-results의 성공 거부는 Reliability impact consumer 계약. Opaque identity 함수에 JSON rejection을 추가하지 않음 |
| [test_dbt_runner.py](../../tests/data_operations/test_dbt_runner.py) | 관련 promotion/read 실패·boundary collision·lock recheck case 읽기 전용 | 기존 drift case는 manifest만 바꾼다. Operations suite를 여기서 수정하거나 실행하지 않음 |

## Legacy Adoption And Handoff

| Historical Item | Decision | Current Evidence And Owner |
| --- | --- | --- |
| [Artifact assessment의 result-only drift 메모](01-review-historical/data-platform/README.md#subdomain-assessment) | `accepted` for primitive gap; `deferred` for composition | 새 F1은 result-only byte change를 직접 구별한다. Operations D1의 동일 결함 수를 Data Platform production defect로 중복 계산하지 않는다 |
| Primitive hash 변경이 promotion에서 거부되는가 | `deferred` to #270/#277 | [기존 drift test](../../tests/data_operations/test_dbt_runner.py)는 manifest만 변경한다. #270은 result만 변경한 candidate, 보존해야 할 current pair의 고정 원문을 사용해 `DataOperationError`와 두 current 파일의 불변을 함께 확인한다. #277은 primitive mutant를 소비 경계까지 연결해 독립성을 재확인한다 |
| Malformed 또는 missing evidence의 의미 | `rejected` as primitive JSON defect | 실제 누락은 primitive의 typed read failure로 추가했다. JSON schema·successful current run·lineage failure 의미는 해당 consumer Spec을 따른다 |

이 하위 검토에서 재현된 production defect나 source 수정 요청은 없다. #277에 넘기는 항목은 위 composition 검증 범위와 primitive의 상세 계약이 canonical Spec에 직접 기술되지 않은 점이다. Spec 보강이 필요하다고 판단하면 owning change에서 결정하며, 이번 test-only PR에서 정본을 수정하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Focused artifact suite | `uv run --no-sync pytest tests/data_platform/test_artifacts.py -q`: 15 passed in 0.21s. 환경 준비 뒤 실제 수집·실행, skip 없음 |
| ✅ Pass | Independent oracle negative controls | 4개 transient identity mutant가 각각 새 assertion에서 거부됨. 전체 mutation coverage를 의미하지 않음 |
| ✅ Pass | Python static checks | `uv run --no-sync ruff check tests/data_platform/test_artifacts.py`, `ruff format --check`와 `ty check` 통과 |
| ✅ Pass | Patch whitespace | `git diff --check -- tests/data_platform/test_artifacts.py` 통과 |
| ✅ Pass | Review artifact checks | 이 문서의 `rumdl check`, `scripts/validate_inbox_artifacts.py`와 `git diff --check` 통과 |
| ⚪ Not Verified | Integrated suite, CI, independent final review | PR 담당자가 최종 diff를 모은 뒤 별도 실행·판정. 이 하위 작업은 commit/push와 Ready 전환을 수행하지 않음 |

## Risks And Limits

Lock matrix는 단일 host/process에서 독립 open-file description을 통해 실제 flock의 mode와 해제를 관찰한다. 별도 process의 scheduling, blocking 대기 시간, external/multi-host writer까지 검증하지 않는다. Close 자체의 I/O failure 주입은 별도 case로 추가하지 않았으며, body/unlock 우선순위 결과를 모든 cleanup failure의 실행 근거로 확대하지 않는다. Identity와 파일 읽기는 caller가 적절한 lock으로 묶어야 하며, primitive 테스트만으로 전체 promotion의 원자성·후속 evidence의 신뢰성을 확정할 수 없다.

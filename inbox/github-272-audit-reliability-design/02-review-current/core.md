---
type: review
title: Reliability Core Test Design Audit
description: Contracts, metadata, profiling, detection, impact, remediation 및 support의 현행 테스트와 보강 근거를 검토합니다.
---

# Reliability Core Test Design Audit

19개 파일 전체를 읽고 현재 source·Spec과 대조했다. 현재 구현이 정상인 네 가지 oracle gap을 최소 반례로 보강했다. Individual manifest node/edge shape 정책은 #277의 명세 판단으로 보류한다.

- **Target:** contracts·metadata·profiling·detection/quality policy·impact·remediation와 공통 support.
- **Revision:** `b16ad5734b4a5a35c1db3d12fe03124438e71348` + 아래 T1–T4 테스트 변경.
- **Scope:** 계약 테스트 8개, 그 외 테스트 8개, fixture 1개, package marker 2개. 모든 body를 검토했으며 package marker는 수정에서 제외했다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| T1 | Minor | 비교 대상의 partition 거부만 있고 asset 거부 반례가 없음 | 기존 population 거부 테스트를 asset/partition으로 parameterize |
| T2 | Minor | 빈 partition 외의 측정 불가 freshness 반례가 없음 | nonempty all-NULL·미지정 column을 기존 unavailable 테스트에 추가 |
| T3 | Minor | column 추가만으로는 이름·타입 각각의 hash 민감도를 구별하지 못함 | 동일 column 수의 rename/type 변경을 기존 schema 테스트에 추가 |
| T4 | Minor | rejected gate와 거부자·시각의 개별 누락을 관측하지 않음 | 기존 gate에 rejected 추가, 잘못된 rejection metadata 3종 검사 |

T1–T4는 production 결함 주장이 아니다. 현재 정상 동작을 보호하는 테스트 gap이며 모두 이 PR의 test-only 수정으로 수용했다.

## Contract Basis

- T1: [Profile comparison compatibility](../../../openspec/specs/reliability-incident-detection/spec.md), [DetectionRequest](../../../src/hmda_reliability/reliability/detection/request.py)의 asset·partition 동등성.
- T2/T3: [Freshness metric / Deterministic schema hash](../../../openspec/specs/reliability-profile-snapshots/spec.md), [profile builder](../../../src/hmda_reliability/reliability/profiling/profile_snapshot_builder.py)의 실제 SQL·schema metadata.
- T4: [Approval contract](../../../openspec/specs/reliability-data-contracts/spec.md)의 pending/rejected 실행 차단과 [Approval](../../../src/hmda_reliability/reliability/contracts/approval.py)의 기존 rejection metadata 검증. Status gate는 exact recovery proposal에 대한 mutation authority가 아니다.

## Full File Coverage

| File | Contract, scenario and independent oracle | Assessment and exclusion |
| --- | --- | --- |
| [contracts/test_approval.py](../../../tests/reliability/contracts/test_approval.py) | 실제 Pydantic review field 거부와 approved/pending gate. T4가 rejected gate·거부자/시각 개별 누락을 보강 | 실제 사람 승인이나 target mutation 권한의 증거가 아님 |
| [contracts/test_evidence.py](../../../tests/reliability/contracts/test_evidence.py) | 고정 payload·vendor-neutral source serialization, airflow/dagster source 거부 | 실제 orchestration 실행 제외 |
| [contracts/test_incident.py](../../../tests/reliability/contracts/test_incident.py) | 빈 evidence_refs의 실제 validation 거부 | 정상 필드·JSON은 fixture가 보완; lifecycle state transition 제외 |
| [contracts/test_lineage.py](../../../tests/reliability/contracts/test_lineage.py) | authored downstream과 affected_assets의 exact list 연결 | Graph traversal은 impact 테스트 소유 |
| [contracts/test_profile.py](../../../tests/reliability/contracts/test_profile.py) | invalid null rate·freshness status 조합 거부, unavailable JSON, UTC 정규화 | 실제 SQL 계산은 profiling 테스트 소유 |
| [contracts/test_recovery_proposal.py](../../../tests/reliability/contracts/test_recovery_proposal.py) | 고정 before timestamp, freshness binding 필수/금지, non-stale before 거부 | Candidate·mutation·replay는 recovery 검토 소유 |
| [contracts/test_schema_recovery.py](../../../tests/reliability/contracts/test_schema_recovery.py) | observation/전체 table scope 구분, 잘못된 identity·actions·candidate/after·proposal·false success의 실제 model/request/result 거부 | 실제 replacement·rollback·population composition은 recovery 소유 |
| [contracts/test_validation.py](../../../tests/reliability/contracts/test_validation.py) | invalid Incident의 ContractValidationError와 contract/field detail | 전체 Pydantic 오류 문구를 고정하지 않음 |
| [conftest.py](../../../tests/reliability/conftest.py) | 고정 UTC·asset·partition·evidence ID를 공유하는 NamedTuple fixture | 매 호출 새 model/collection; pending approval이며 사람/live evidence가 아님 |
| [test_fixtures.py](../../../tests/reliability/test_fixtures.py) | exact evidence/lineage links, pending gate, authored JSON enum/time, NaN profile 거부 | 전체 serialization compatibility golden은 아님 |
| [test_table_metadata_evidence.py](../../../tests/reliability/test_table_metadata_evidence.py) | 실제 DuckDB column name/type/nullability·count 1·identity·고정 time, missing-table domain error | Hash prefix는 profiling의 schema-change oracle이 보완; adapter/규모 일반 보장 제외 |
| [test_profile_snapshots.py](../../../tests/reliability/test_profile_snapshots.py) | 다른 날짜 sentinel을 둔 실제 SQL count 2·null 0.5·max timestamp·JSON, 반복 hash·empty/future freshness. T2/T3 반례 보강 | Recovery caller의 approved population 선택은 별도 책임 |
| [test_table_state_identity.py](../../../tests/reliability/test_table_state_identity.py) | 실제 multi-year 정렬·count 합계·frozen field, duplicate/file scope·NULL year 거부, 누락 partition·equal-count changed digest 불일치 | Unit digest는 authored 값; 실제 content hashing의 모든 조합은 HMDA 검증과 구분 |
| [test_basic_incident_detection.py](../../../tests/reliability/test_basic_incident_detection.py) | 정상·4 incident·exact payload/link, inclusive equality, zero threshold 양의 악화·zero baseline·독립 규칙/column. T1로 population 거부 양쪽 검사 | 실제 SQL profile 생성과 구분하는 unit 계약 |
| [test_quality_gate.py](../../../tests/reliability/test_quality_gate.py) | authored baseline·5%p equality·null spike·empty·unsupported column, exact log/error field, non-blocking types | 대부분 실제 detector; non-blocking fake는 policy 분리 증거이며 E2E가 아님 |
| [test_impact_analysis.py](../../../tests/reliability/test_impact_analysis.py) | 실제 JSON source→staging→mart exact traversal, name/node ID·paths/ref, syntax·missing file, invalid containers 10종·valid-empty 4종 | Historical I1 해결; node/edge shape는 아래 H1. 빈 run-results fixture는 실제 dbt 성공 증거가 아님 |
| [test_remediation_draft.py](../../../tests/reliability/test_remediation_draft.py) | 실제 LangGraph의 4 incident별 action·suggestion·lineage·JSON·approval flag | Human usefulness/approval 제외; 직접 DB 입력이 없고 외부 lifecycle 테스트가 mutation 부재를 보완 |
| [__init__.py](../../../tests/reliability/__init__.py) | 빈 package marker 전체 확인 | 동작/fixture 없음, 수정 제외 |
| [contracts/__init__.py](../../../tests/reliability/contracts/__init__.py) | 설명 docstring 전체 확인 | 동작/fixture 없음, 수정 제외 |

## Historical Disposition

| Historical item | Disposition | Current evidence |
| --- | --- | --- |
| I1 / L3 malformed manifest containers | `obsolete` | #268 `e9a738c5`의 [container guard](../../../src/hmda_reliability/reliability/impact/manifest.py)와 [invalid/valid-empty 반례](../../../tests/reliability/test_impact_analysis.py)가 과거 `nodes`/`sources` null/list/string/number/bool 사례를 직접 보호 |
| Detection zero-threshold false positive | `obsolete` | 현재 [positive degradation matrix](../../../tests/reliability/test_basic_incident_detection.py)가 무변화/개선·독립 규칙을 exact incident 목록으로 보호. 완료된 active Change의 후속 구현으로 확대하지 않음 |
| Contracts/metadata/profiling/detection/remediation의 historical 본문 | `accepted` (현재 평가 근거) | 별도 material finding 없음. 위 19-file 대조로 평가 범위를 재확인했고 metadata hash prefix·builder/caller scope·read-only composition 한계는 유지 |
| Remediation 단독 테스트의 직접 mutation 관측 부족을 별도 결함으로 승격 | `rejected` | [lifecycle state preservation](../../../tests/data_operations/test_incident_lifecycle.py)과 [system recovery content 재확인](../../../tests/data_operations/test_system_recovery_e2e.py)을 targeted read-only 대조. 두 외부 파일은 이 PR의 전수 inventory/수정/새 실행 근거에 포함하지 않음 |

R2 profile population 문제는 [Recovery disposition](recovery.md)으로 연결하며 중복 finding으로 세지 않는다.

## H1: Deferred Manifest Node And Edge Policy

**Disposition:** `deferred` to #277; 현 단계의 확정 production defect나 #272 blocker로 승격하지 않는다.

[Lineage artifact validation](../../../openspec/specs/reliability-impact-analysis/spec.md)은 readable/valid artifact와 uninterpretable manifest의 실패를 요구하지만, individual node/adjacency shape와 누락 허용 정책을 정의하지 않는다. [현재 parser](../../../src/hmda_reliability/reliability/impact/manifest.py)는 non-object node와 non-object `depends_on`, non-list `depends_on.nodes`를 건너뛴다.

Baseline에서 별도 `TemporaryDirectory`의 manifest/run-results를 사용한 실제 analyzer probe를 실행했다. 정상 source→model graph의 해당 field만 바꿨다.

| Input delta | Observed result |
| --- | --- |
| 정상 source와 이에 의존하는 model | 성공, downstream/affected `['stg_loans']` |
| model entry를 `null`로 변경 | 성공, 두 목록 `[]` |
| model의 `depends_on=null` | 성공, 두 목록 `[]` |
| `depends_on.nodes`를 source ID 문자열로 변경 | 성공, 두 목록 `[]` |

영향은 손상된 개별 node/edge가 영향 없음과 구분되지 않을 수 있다는 점이다. #277은 이 shape의 거부/허용 정책을 먼저 결정하고, 거부가 계약이면 parser·normative Spec·failure regression을 함께 소유한다. 권장 oracle은 정상 graph의 exact downstream 목록을 유지하면서 invalid shape가 식별 가능한 impact failure로 종료하는지 검사하는 것이다. 과거 I1의 container-level 결함을 다시 열지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Full-body static audit | 19/19 file, 해당 source·canonical Spec·historical 6개 보고서 대조 |
| ✅ Pass | 기존 domain baseline | `b16ad573`에서 `uv run --no-sync pytest tests/reliability -q`: 258 passed |
| ✅ Pass | T1–T4 focused | 변경 3개 module의 42 tests passed |
| ✅ Pass | H1 bounded probe | 정상 graph와 field 변경 3종, 위 actual result; repository 파일 변경 없음 |
| ✅ Pass | T1–T4 검출력 | 6개 subprocess에서 기존 oracle PASS, 보강 oracle assertion FAIL. [통합 근거](README.md#negative-controls) |
| ✅ Pass | 최종 domain | 268 passed in 22.97s. 독립 리뷰는 [통합 근거](README.md)에 별도 기록 |

## Risks And Limits

정적 coverage는 각 파일의 contract와 oracle을 읽었다는 의미이며 가능한 모든 입력 조합을 실행했다는 뜻이 아니다. 사람의 승인·효용, 운영 장애 빈도와 실제 외부 dbt/Airflow 실행을 이 테스트 묶음으로 일반화하지 않는다. 공용 configuration/production/타 도메인 수정은 수행하지 않았다.

---
type: review
title: PR 258 Domain And Subdomain Test Design Review
description: PR 258 브랜치의 도메인별 테스트 설계 강점·검출 공백·후속 보강안과 변경 범위의 관계를 확인합니다.
tags:
  - testing
  - review
---

# PR 258 Domain And Subdomain Test Design Review

> [!IMPORTANT]
> 이 묶음은 아래 `3ab89910`의 historical review다. 2026-10-25 최신 main과의 통합 상태에서는 inventory 94개 중 10개가 변경됐다. 현재 적용 범위와 G1–G6 후속 수정의 확인 결과는 [최신 readiness 보고서](../05-report-review-readiness.md#prior-review-applicability)를 따른다. 아래 당시 실행 수와 finding을 현재 main의 상태로 해석하지 않는다.

> [!NOTE]
> 독립 검토를 완료했다. 실제 파일·DB와 고정 값 oracle의 기반은 좋지만, 현재 테스트가 놓치는 계약 위반과 회귀 공백을 확인해 보강이 필요하다.

- **Target**: [PR #258](https://github.com/mols3131d/hmda-data-reliability/pull/258) 브랜치의 제품 도메인 7개와 공통 개발 지원 영역 테스트 설계.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: tracked test module 74개·support 17개·design 3개, 총 94파일을 quality/adversarial 두 관점에서 각각 전체 검토했다. Source·Spec은 관련 계약을 대조했다. 구현 수정은 포함하지 않으며, 후속 사용자 요청에 따라 보고서와 연결 문서를 같은 PR로 전달한다.

## PR Context

이 보고서 묶음은 PR #258 작업을 지원하는 artifact이며 해당 PR의 Inbox에 귀속된다. 검토 대상은 PR #258 브랜치의 전체 테스트 snapshot이다. PR의 코드 변경은 [SDK 오류 분류·재시도 회귀 5개](../00-plan-sdk-retry-classification.md)이고, 그 범위의 [독립 구현 리뷰](../02-review-sdk-retry-implementation.md)와 [Runtime AI 설계 리뷰](runtime-ai/README.md)에서는 추가 material finding을 확인하지 못했다.

아래 Major·Minor는 전체 snapshot에서 확인한 문제와 검출 공백의 등급이다. 다른 도메인의 항목은 후속 보강 제안으로 기록했으며, PR #258이 새로 만든 결함이나 이 PR의 필수 수정 항목으로 일괄 분류한 결과가 아니다.

## Findings

현재 suite는 **954 passed, 2 skipped**지만 아래 조건의 오동작은 검출하지 못한다. 우선 볼 Major 항목을 정리했다. 각 도메인 보고서에는 기존 보호장치·구체적 반례·최소 보강안과 Minor 항목도 있다.

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| G1 | Major | 합성 출력이 원본 경로와 겹치면 원본 삭제 | [원본 보존 회귀](hmda-data/synthetic.md#f1--major-overlapping-input-and-output) |
| G2 | Major | 여러 원천 중 필수 컬럼이 없는 파일도 적재 성공 | [파일별 구조 검증](hmda-data/ingestion.md#f1--major-mixed-source-schema) |
| G3 | Major | 복구는 반영됐지만 cleanup 오류에 완료 상태가 빠짐 | [실제 상태와 실패 증거 연결](reliability/recovery.md#r1--major-staging-cleanup-after-commit) |
| G4 | Major | 다른 범위의 빈 profile이 복구 성공 증거로 붙음 | [관찰 범위 정렬](reliability/recovery.md#r2--major-profile-population-binding) |
| G5 | Major | 손상된 lineage 구조를 영향 없음으로 성공 처리 | [구조 오류 거부](reliability/impact.md#i1--major-malformed-graph-shape) |
| G6 | Major | 복구 후 검증 실패가 Action PASS·100%로 집계 | [실패→보고서 FAIL 연결](reliability/evaluation.md#e1--major-failed-recovery-action-pass) |
| G7 | Major | 정상 evidence 입력의 크기 초과가 raw 예외로 노출 | [typed 입력 거부](review-ai/README.md#ai1--major-per-evidence-preflight-failure) |
| G8 | Major | 관련 Change가 불확실해도 OpenSpec 검증이 좁게 유지됨 | [불확실한 선택의 fail-safe](cross-cutting/ci.md#c1--major-uncertain-openspec-inventory) |

현재 구현이 정상인 주요 회귀 공백도 별도로 있다. [Partition 교체 중 실패·같은 연도 sibling 보존](hmda-data/ingestion.md), [run-results만 바뀐 artifact identity](data-operations/README.md), [workflow 생성·검사 revision](cross-cutting/ci.md)이 대표적이다. Service handoff·bootstrap·workflow의 잘못된 구현 5개는 **관련 focused 기존 tests가 통과하고 새 witness가 실패**함을 격리 복사본에서 확인했다. 전체 suite에 모든 mutant를 실행했다는 주장은 아니다.

모든 finding은 후속 제안이다. **현재 동작 재현 / 격리 negative control / 정적 설계 공백**을 구분하며, 영향이 다른 경우 같은 수정 규칙을 일괄 적용하지 않는다.

## Reports

| Domain | Subdomain Or Responsibility Views | Key Result | Review |
| --- | --- | --- | --- |
| HMDA Data | contracts, ingestion, EDA, synthetic | 원본·구조·교체 실패 경계 보강 | [도메인·하위 리뷰](hmda-data/README.md) |
| Data Platform | DuckDB, SQL, artifacts, dbt analytics | metric 분기를 구별하는 fixture 보강 | [영역별 리뷰](data-platform/README.md) |
| Data Operations | quality gate, dbt/promotion, lifecycle, system recovery | result-only artifact oracle 보강 | [영역별 리뷰](data-operations/README.md) |
| Reliability | contracts, metadata, profiling, detection, impact, remediation, recovery, evaluation | 복구 증거·범위·실패 집계 보강 | [도메인·하위 리뷰](reliability/README.md) |
| Review AI | contracts/context, prompt/service/validator/store, evaluation | preflight와 service 연결 보강 | [도메인·하위 리뷰](review-ai/README.md) |
| Runtime AI | settings/contracts, SDK/retry | 과거 SDK retry 공백 해소, 추가 material finding 없음 | [영역별 리뷰](runtime-ai/README.md) |
| Orchestration | config, execution, DAG/DAGRun | 실제 5경로 검증, 추가 material finding 없음 | [도메인·DAG 리뷰](orchestration/README.md) |
| Common Support | CI, tools, agent assets, docs, architecture guard, telemetry | CI 진입·fallback·local guard 보강 | [영역별 리뷰](cross-cutting/README.md)·[CI](cross-cutting/ci.md) |

실제 source 하위 패키지는 별도 리뷰로 연결하고, 평면 package의 영역은 각 domain 보고서 표에서 구분한다. 이 review view는 [canonical domain ownership](../../../docs/domains/OVERVIEW.md)을 변경하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 현재 테스트 실행 | [954 passed / 2 skipped](validation.md#test-execution) |
| ✅ Pass | Batch A–E 독립 검토 | 94파일 전체, [파일별 inventory](inventory.md) |
| ✅ Pass | 계약 반례·negative control 대조 | [주체·대상·결과·제한](validation.md#confirmed-counterexamples) |
| ✅ Pass | 문서·대상 최종 검증 | [27문서 metadata/링크·94개 target blob 동일](validation.md#artifact-and-snapshot-checks) |
| ⚪ Not Verified | 실제 외부 서비스·운영·모든 mutant | fixture·로컬 실행과 구분한 명시적 한계 |

## Risks And Limits

제품 도메인 7개·공통 지원 1개와 별도 하위 리뷰 15개를 포함한다. [진행 계획](plan.md)과 [실행·문서 검증 기록](validation.md)을 함께 남겨 다음 세션에서도 대상과 남은 후속 항목을 재구성할 수 있다.

이 보고서는 결정론적 테스트 설계를 검토한다. 실제 LLM 리뷰의 유용성·품질은 제외했다. Static source review·fixture·로컬 실행을 원격 ingestion·실제 사람의 승인·운영 배포 또는 모든 변경의 인간 검토 생략 근거로 확대하지 않는다.

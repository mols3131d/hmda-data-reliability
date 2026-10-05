---
type: plan
title: CI Cost and Complexity Improvement Plan
description: CI 필수 검증을 보존하면서 중복 실행을 줄이는 구현 순서, 환경 비용 측정과 단계별 완료·중단 조건을 정의한다.
tags:
  - ci
  - testing
  - optimization
---

# CI Cost and Complexity Improvement Plan

> [!IMPORTANT]
> **F1 구현·전달과 F2 초기 측정은 완료했다.** F1 로컬 검증은 [Execution Record](#execution-record), 2026-10-05의 비용 실측은 [F2 Measurement](research.md#f2-measurement)가 소유한다. 현재는 전체 환경 유지를 권고하며 별도 환경 도입과 F3는 진행하지 않는다.

[조사](research.md)는 HEAD `6251c91aafd2a2db0d41d2136ff6f773f02df03e`의 선택 계약과 [원 보고서](../06-review-ci-cost-and-complexity.md)의 과거 비용 표본을 구분한다. F1은 같은 PR #253 branch에서 이 HEAD에 대한 로컬 후속 변경으로 구현한다. 별도 branch·change를 만들지 않으며 remote delivery는 별도 요청을 따른다.

## Goal and Scope

`main` admission에 필요한 검증 범위와 실패 의미를 유지하면서 동일 revision의 동일 검사 반복만 제거한다. 개선의 일차 결과는 중복 범위 축소이며, 성능 개선은 같은 조건의 before/after 측정이 있을 때만 주장한다.

| Item | Planned Treatment |
| --- | --- |
| F1 AST guard | 앞선 boundary 성공 근거가 있을 때 일반 suite의 guard 재실행만 제외 |
| F1 runtime smoke | 전체 non-resource suite에 두 smoke target이 포함되고 성공하면 별도 반복 생략 |
| F2 full environment | Cold/warm 비용을 측정; 결과에 따른 분리 설계·도입은 별도 판단 |
| F3 wheel build | 비용 또는 조건 명료화 필요가 확인될 때만 작은 조건 분리 |
| F4 mapping | 기존 module·fixture와 대표 입력 검사를 유지; framework 추가 없음 |

애플리케이션, Tach dependency 모델, OpenSpec capability, pre-push hook, 권한·branch protection, provider·runner 변경은 범위 밖이다. 새 lock·cache 체계·workflow·job·scheduled suite·benchmark framework는 만들지 않는다. 현재 GitHub Actions의 prospective merge, read-only 권한, credential 비보존, timeout·concurrency·캐시는 유지한다.

## Failure and Evidence

[CI 계약](../../../docs/development/ci/README.md)과 [테스트 설계](../../../docs/development/test-design.md)가 admission·oracle의 owner다. 아래는 이번 변경에서 보존할 항목만 연결한다.

| Failure | Required Evidence | Role |
| --- | --- | --- |
| 필수 boundary 검사 누락 | 실제 YAML 실행의 `tach check`와 세 pytest target 독립 argv oracle | Blocking PR |
| 성공 근거 없이 AST guard 제외 | boundary 성공·skipped·독립 local 실행별 선택 계약과 실제 collection | Blocking PR |
| Unit-only 실행이 runtime smoke를 잘못 대체 | Dependency-only와 full-tests 혼합 입력의 별도 기대값 | Blocking PR |
| 외부 명령 실패를 성공·skip으로 전환 | boundary·selected tests·smoke의 실패 주입과 nonzero 전파 | Blocking PR |
| CI non-unit 계약이나 consumer coverage 누락 | 기존 full-unit 보완·domain closure·marker 회귀 | Blocking PR |
| 시간 절감의 과장 | 동일 조건의 전후 실행 또는 unknown 명시 | 비용 판단 근거; correctness gate 대체 불가 |

## Implementation Sequence

### 1. Fix the Coverage Oracle Before Deduplication

기존 [workflow tests](../../../tests/scripts/ci/test_ci_workflow.py), [pytest tests](../../../tests/scripts/ci/test_ci_pytest.py), classifier tests와 fake CLI fixture를 재사용한다. 정상 구현에서 기존 coverage가 성립함을 먼저 확인하고, 새 중복 제거 기대값은 명령·선택 assertion에서 RED가 되도록 작성한다. Import·fixture 실패를 RED로 세지 않는다.

[Verification](#verification)의 대표 조합마다 필요한 test target과 marker를 독립적으로 적는다. 현재 YAML이나 classifier 출력에서 기대값을 자동 복사하지 않는다. AST guard·두 smoke target은 실제 pytest collection으로 경로와 marker 범위가 맞는지 확인한다.

**Done When:** 기존 필수 target oracle을 유지하고, 새 회귀는 정상 수집 후 의도한 중복 조건에서만 실패한다. Coverage baseline이 불명확하면 수정하지 않고 그 경계를 먼저 해결한다.

### 2. Remove Only the Proven F1 Overlap

[Workflow](../../../.github/workflows/ci-lite.yml)와 [pytest script](../../../scripts/ci/pytest.sh)의 실행 책임에서 처리한다. Classifier의 `tach`·`runtime_smoke` 요구 의미, domain closure와 fallback flag는 바꾸지 않는다.

- **AST guard:** 기존 boundary step에 `id: boundaries`를 두고 selected-tests step에 `BOUNDARIES_CHECKED`를 이전 step의 `outcome == 'success'`로 전달하는 작은 연결을 우선한다. pytest script의 기본값은 false다. True일 때만 일반 scoped/full-tests 실행에서 AST guard 파일을 `--ignore` 대상으로 삼는다. 전체 boundary 단계와 세 target은 그대로 유지한다. 독립 local 실행·boundary skip에서는 guard를 계속 포함하며, full-unit 뒤 CI non-unit 보완에도 영향을 주지 않는다.
- **Runtime smoke:** `runtime_smoke=true` 중 `full_tests=true`인 조합에서만 별도 smoke 반복을 생략한다. 앞선 전체 실행이 실제로 선택되고 두 target을 포함한다는 계약, step 순서와 실패 시 job 중단을 함께 보호한다. Dependency-only의 `full_unit=true`에서는 smoke를 유지한다. Flag만으로 coverage를 증명하지 못하면 생략하지 않는다.

새 환경값 이름과 step id는 위의 국소 제안이다. 구현 시 더 작은 동등한 연결을 선택할 수 있지만 **선택됐다는 사실이 아니라 앞선 성공과 실제 coverage**가 제외 근거여야 한다. `continue-on-error`, 실패를 false로 바꾸는 fallback, 전체 domain 제외는 허용하지 않는다.

**Done When:** 관련 focused 검사가 GREEN이고 F1 두 조합의 반복만 사라진다. 필수 target·marker·timeout·병렬 threshold·오류 계약은 동일하다. 이후 [Verification](#verification)의 관련 suite와 필요한 독립 리뷰를 수행한다.

### 3. Measure F2 Before Splitting the Environment

먼저 native Actions step 시각과 uv 출력으로 환경 준비 비용을 분리한다. 자료가 부족하면 repository의 주 `.venv`나 공유 캐시를 지우지 않고, 격리된 checkout·새 venv·분리된 uv cache에서 수동 측정한다. 새 자동화는 추가하지 않는다.

| Condition | Control | Record |
| --- | --- | --- |
| Cold | 같은 revision·lock·runner에서 새 venv와 빈 격리 cache | sync 경과 시간, 설치·다운로드 증거, 실패 |
| Warm | 같은 조건의 새 venv에서 준비된 cache 재사용 | sync 경과 시간과 cache 재사용 근거 |
| CI overhead | uv 도구 설치·cache restore·runner 대기를 sync와 구분 | step/job 시각; 분리 불가능한 부분은 unknown |

각 조건을 반복해 표본 수와 분산·범위를 남긴다. 단일 로컬 실행을 GitHub runner의 성능이나 비용으로 일반화하지 않으며, 실제 과금을 조회하지 않았다면 금액 절감을 주장하지 않는다.

**Decision Gate:** full sync가 중요한 반복 비용이고 작은 locked 환경에서 동일 fixture·pytest plugin·정적 검사 계약을 보존할 수 있다는 근거가 있을 때만 분리 설계를 별도로 제안한다. 그 전에는 기존 환경을 유지한다. 별도 lock·`uvx pytest` 대체·cache 체계는 측정만으로 자동 승인되지 않는다.

### 4. Keep F3 Optional and F4 Local

F3는 packaging 조건 명료화가 필요하거나 build 비용이 의미 있게 측정됐을 때만 별도 작은 수정 단위로 다룬다. Test/script-only에서는 정적 Python·필요 테스트를 유지하고, source·build metadata·dependency/runtime 변경과 영향 불명확 입력에서는 build를 유지하는 oracle을 먼저 정의한다. 비용 근거도 명료화 필요도 없으면 보류한다.

F4는 새 domain·capability·파일 이동 시 기존 mapping과 대표 입력·consumer target 테스트를 함께 갱신하는 방식으로 반영한다. 범용 router나 추가 job을 만드는 단계가 아니다. 과거 시간 표본과 파일 수·줄 수만으로 구조 변경을 정당화하지 않는다.

## Verification

기존 [Testing Guide](../../../docs/development/testing.md)의 좁은 실행부터 시작한다. 아래는 acceptance를 보호할 검증 기준이며 실제 실행 결과는 [Execution Record](#execution-record)에 구분한다.

| Scenario | Expected Evidence |
| --- | --- |
| Runtime/reliability source; 앞선 boundary 성공 | Consumer target 유지; AST guard는 boundary에서 실행되고 selected suite에서만 제외 |
| `tests/review_ai` 단독 또는 독립 local script; 성공 근거 없음 | AST guard 포함; default false로 보수적인 선택 |
| Boundary skipped/failed | Skipped이면 제외 없음; 실패는 nonzero와 job 중단으로 남음 |
| Dependency + unmapped Spec | 전체 non-resource suite에 두 smoke target 포함; 후속 smoke 반복 없음 |
| Dependency only | 전체 unit과 두 runtime smoke target 모두 유지 |
| Dependency + CI helper | 전체 unit 뒤 CI non-unit 보완과 runtime smoke 유지 |
| CI helper only / docs·Inbox only | 각각 기존 CI 계약 범위 / unrelated Python·Tach·tests 미선택 |
| 필수 target 하나 제거 또는 실제 coverage 누락 | 독립 oracle·collection 검사 실패; silent skip 불가 |
| Boundary·selected·smoke 명령 실패 | Nonzero 전파; 후속 실행으로 실패를 숨기지 않음 |

F1의 좁은 실행 예시는 다음과 같다. 테스트 배치를 바꾸지 않는다면 같은 파일에서 시작하고 필요한 범위만 넓힌다.

```bash
uv run --no-sync pytest \
  tests/scripts/ci/test_ci_workflow.py \
  tests/scripts/ci/test_ci_pytest.py \
  -q -p no:sugar -p no:cacheprovider --color=no --tb=short
uv run --no-sync pytest tests/scripts/ci \
  -q -p no:sugar -p no:cacheprovider --color=no --tb=short
bash -n scripts/ci/pytest.sh
```

수정한 Python test의 Ruff·format·ty 검사와 관련 canonical CI 설명의 정합성도 확인한다. Fake CLI의 call log는 wiring·marker·실패 전파의 근거이지 실제 dependency/runtime 성공의 증명이 아니다. Guard·smoke의 실제 collection과 실행은 변경 위험에 필요한 가장 좁은 경계에서 확인한다.

Before/after 비교에는 같은 target·marker·환경·revision 관계를 남긴다. 실행 수가 줄어도 시간 개선이 유의미하지 않으면 그 사실을 기록한다. 승인된 delivery 이후에는 최종 base/head의 prospective merge CI를 확인하며, local hook·과거 success로 대체하지 않는다.

## Acceptance and Stop Conditions

- AST guard와 runtime smoke의 확인된 중복만 제거되며 필수 boundary·consumer·CI non-unit·dependency smoke coverage가 보존된다.
- 성공이나 coverage 근거가 불명확하면 제외하지 않고, 명령·분류 실패는 nonzero로 남는다.
- 대표 입력의 선택과 실제 target collection, focused suite와 관련 검증에서 미해결 실패가 없다.
- 영향 있는 canonical 설명만 실제 구현과 함께 갱신한다. 기존 06번 보고서의 과거 snapshot을 새 결과로 덮어쓰지 않는다.
- 환경 분리·build 조건 확장·추가 machinery는 별도 근거나 판단 없이 실행하지 않는다.
- 검증 범위를 줄여야만 절감이 성립하거나 복잡성이 이득보다 커지면 변경을 축소·보류한다. 안심을 위한 무관한 전체 suite·리뷰 반복은 추가하지 않는다.

## Execution Boundary

사용자 실행 요청으로 단계 1과 F1 구현을 진행했다. 2026-10-05 종료 요청으로 해당 변경을 commit·push하고 PR 본문을 갱신했다. 같은 날 재개 요청은 최신 상태 확인, F2 측정과 결과 기록으로 수행했다. 이후 병합 전 준비 요청에서 사용자는 로컬 보완·검증만 선택했다. 전체 PR 독립 리뷰의 필수 root blob lock 보완과 검증은 [Merge Preparation](../08-agent-routes-skills-lock-compatibility/02-report.md#2026-10-05-merge-preparation)에 구분한다. 환경 분리·F3·추가 delivery·Ready 전환·승인·merge는 수행하지 않는다. PR #253의 기존 완료 작업과 이 개선 단위의 evidence를 섞지 않는다.

## Execution Record

**F1 local implementation verified; independent review clear.** 아래는 기준 HEAD `6251c91aafd2a2db0d41d2136ff6f773f02df03e` 위의 F1 구현 검증 snapshot이다. 검증 당시 변경은 미커밋 상태였으며 실제 전달 revision은 최신 PR와 Git history에서 확인한다. 과거 remote CI 성공을 이번 변경의 실행 근거로 사용하지 않는다.

### Implementation

- Boundary step은 세 필수 pytest target과 `tach check`를 그대로 실행한다. `boundaries`의 성공 여부를 전달받은 scoped/full-tests만 AST guard 파일을 제외하며 missing/false 상태와 전체 unit 뒤 CI 보완은 기존 범위를 유지한다.
- Runtime smoke는 `runtime_smoke=true`이고 앞선 full-tests 성공이 확인되지 않았을 때 실행한다. `selected_tests` 성공 여부도 검사해 선택 flag만으로 coverage를 대신하지 않는다. Step 순서와 nonzero 실패 의미를 유지한다.
- Classifier·domain closure·fallback·dependency 환경·package build 조건은 수정하지 않는다. 현재 실행 규칙은 [Testing Guide](../../../docs/development/testing.md#pull-request-ci)에 반영한다.

### Validation

| Evidence | Observed Result | Limit |
| --- | --- | --- |
| Guard RED → GREEN | 성공 확인 scoped/full-tests 2개만 RED; 수정 후 동일 6개 GREEN | 이후 parallel·unit/failure 사례를 관련 suite로 확장 |
| Workflow RED → GREEN | 성공 env·step id 2개 RED; target·failure baseline 2개 GREEN; 연결 후 4개 GREEN | 실제 Actions runner 실행은 아님 |
| CI package | `tests/scripts/ci`: 161 passed | Fake CLI는 선택·argv·오류 계약의 근거 |
| Actual collection | Non-resource 819 → 817; guard 2개만 제외; dbt·Airflow smoke 5개 모두 유지 | 수집 결과이며 전체 817개 실행 성공을 주장하지 않음 |
| Actual boundary/runtime | `tach check`와 세 boundary 파일·두 smoke 파일: 16 passed | 로컬 Python 3.13 환경의 결과 |
| Negative control | Guard·dbt·Airflow target을 하나씩 제거한 임시 YAML이 독립 oracle에서 모두 실패 | 원본 파일 변경 없이 시행 |
| Static | Bash syntax, 변경 test Ruff·format·ty, editor diagnostics 통과 | Formatter는 새 test 두 파일만 정리 |
| Documentation | Testing Guide·번들 4개 문서의 rumdl·링크 검사와 세 Inbox artifact validator 통과 | Current workflow·guide와 historical research의 역할을 구분 |
| Independent review | `review-lead`의 quality·adversarial 통합 결과 `clear`; 필수 수정 없음 | Exact baseline과 현재 파일을 정적으로 대조; 제공된 실행 근거는 reviewer 재실행 결과가 아님 |

Collection은 동일 worktree·환경·`not memory and not stress` marker로 guard 제외 전후를 비교했다. Smoke 5개는 component/integration이며 unit-only suite가 대체할 수 없다. 실행 수 감소는 확인했지만 동일 조건 runtime 전후 측정, Actions latency와 과금 절감은 unknown이다.

F1 로컬 완료 gate와 승인된 delivery를 완료했다. Head `ec81d5d`의 새 prospective merge CI와 본문도 확인했으며 해당 외부 상태는 최신 PR가 소유한다. F2 cold/warm 세 쌍의 측정과 별도 offline cache 확인은 [F2 Measurement](research.md#f2-measurement)에 기록한다. 새 환경의 이득·검증 동등성은 미확인이며 기본 권고는 전체 환경 유지다. 다음 판단은 [Next Session](README.md#next-session)을 따른다.

---
type: research
title: CI Cost and Complexity Improvement Research
description: 현재 CI에서 필수 검증을 보존하며 제거할 중복과 추가 측정이 필요한 비용을 구분해 후속 개선 범위를 판단한다.
tags:
  - ci
  - change-impact
  - performance
---

# CI Cost and Complexity Improvement Research

> [!IMPORTANT]
> **F1의 중복 선택은 현재 구현에서도 확인됐다. 환경 분리와 packaging 축소의 실익은 아직 미확인이다.** 가장 작은 후보는 이미 성공한 AST guard의 재실행과 전체 non-resource suite 뒤의 runtime smoke 반복을 제거하는 것이다. 필수 검증 범위는 유지하며, 시간 절감이나 과금 절감은 아직 주장하지 않는다.

## Question

현재 CI Lite에서 `main` admission에 필요한 검증을 유지하면서 어떤 반복 실행을 제거할 수 있고, 환경·빌드 범위 축소는 어떤 추가 근거가 있어야 선택할 수 있는가?

## Scope

2026-10-04, branch `agent/research-ci-script-separation`의 HEAD `6251c91aafd2a2db0d41d2136ff6f773f02df03e`와 조사 시작 시 clean 작업 트리를 기준으로 한다. [원 보고서](../06-review-ci-cost-and-complexity.md)는 과거 비용 표본의 근거로, 현재 workflow·classifier·pytest script는 선택 계약의 근거로 사용했다.

F1의 두 중복 조합, F2의 환경 준비, F3의 wheel build 조건과 F4의 영향 매핑만 포함한다. 애플리케이션 변경, Tach boundary 재설계, 전체 CI 재설계, provider 이전과 권한 변경은 제외한다. 새 pytest suite·원격 실행 통계·cold install·과금·before/after benchmark는 수집하지 않았다.

## Findings

### AST Guard Is Selected Twice in Some Source Changes

[Workflow](../../../.github/workflows/ci-lite.yml)의 `Check Python dependency boundaries`는 `tach check`와 세 필수 pytest target을 실행한다. 그중 [AST guard](../../../tests/review_ai/test_dependency_boundaries.py)는 `component` marker를 가지며 일반 non-resource 테스트에도 포함된다.

[Classifier](../../../scripts/ci/classify_changes.sh)의 `runtime_ai`·`reliability` consumer closure는 `tests/review_ai`를 선택한다. [pytest script](../../../scripts/ci/pytest.sh)는 현재 별도의 제외 없이 해당 directory를 실행하므로 같은 guard가 다시 포함된다. 이는 대표 입력의 선택 결과와 코드의 연결로 확인한 반복이며, 실제 추가 시간은 측정하지 않았다.

제거 후보는 **앞선 boundary 단계가 성공한 경우의 AST guard 재실행만**이다. Boundary 단계 자체와 세 필수 target은 유지해야 한다. 앞선 성공 근거 없이 일반 실행에서 guard를 제외하면 검증 누락이므로, 독립적인 local script 실행의 기본값은 제외하지 않는 방향이어야 한다.

### Full Tests and Runtime Smoke Can Overlap

Dependency 변경은 `full_unit=true`, `runtime_smoke=true`를 선택한다. 여기에 미매핑 canonical Spec 변경이 겹치면 `full_tests=true`도 선택된다. pytest script는 `FULL_TESTS`를 우선해 `tests/`의 전체 non-resource suite를 실행하지만 workflow의 runtime smoke 조건은 여전히 `runtime_smoke=true`만 본다.

별도 smoke target은 [dbt foundation](../../../tests/dbt/test_analytics_foundation.py)과 [Airflow DAG](../../../tests/orchestration/test_airflow_dag.py)다. 이 경로들은 전체 suite의 test root 아래에 있으며 두 실행은 같은 `not memory and not stress` 범위를 사용한다. **전체 suite가 이 target의 검사를 실제로 포함하고 성공한 경우**에만 뒤의 반복 실행을 생략할 수 있다.

`FULL_UNIT`만 실행하는 경우는 다르다. Unit filter는 component·integration smoke를 대체하지 않으므로 dependency-only 변경의 runtime smoke는 유지해야 한다. 실제 collection과 성공·실패 wiring은 [계획서의 검증](plan.md#verification)에 포함하며, 이번 조사에서 새 pytest 실행으로 증명한 것으로 취급하지 않는다.

### Representative Inputs Preserve the Narrow Selection

현재 repository root에서 다섯 입력 조합을 `bash scripts/ci/classify_changes.sh --stdin`으로 실행했다. 아래 source와 Spec 경로는 분류 규칙을 확인하기 위한 합성 입력이며 실제 파일을 만들지 않았다. Boolean과 target은 classifier 출력에서 직접 확인했다.

| Input | Observed Selection | Meaning |
| --- | --- | --- |
| `src/hmda_reliability/runtime_ai/ci_cost_probe.py` | `tach=true`; targets는 `tests/runtime_ai tests/review_ai`; full flags는 false | 전용 boundary와 consumer suite에 AST guard가 함께 들어갈 조건 |
| `uv.lock` + `openspec/specs/unmapped-ci-cost-probe/spec.md` | `full_unit=true`, `full_tests=true`, `runtime_smoke=true` | 전체 non-resource suite와 별도 smoke가 함께 선택되는 조건 |
| `uv.lock` | `full_unit=true`, `full_tests=false`, `runtime_smoke=true` | 별도 smoke를 유지해야 하는 반례 |
| `scripts/ci/pytest.sh` | targets·ci_targets는 `tests/scripts/ci`; `python=false`, `tach=false`, full flags·runtime smoke는 false | CI-only 선택을 domain 전체로 넓힐 필요 없음 |
| `docs/development/ci/README.md` + 원 보고서의 Inbox 경로 | `tests=false`, `python=false`, `tach=false`, runtime smoke는 false | 문서-only 환경 준비를 새로 추가할 이유 없음 |

합성 입력 검사는 routing의 근거다. 실제 domain test 실행, dependency semantics 또는 CI 시간 측정을 대신하지 않는다.

### Environment and Build Savings Remain Unmeasured

현재 workflow는 CI helper-only 변경에서도 `tests=true`를 통해 `uv sync --locked`를 실행한다. [프로젝트 설정](../../../pyproject.toml)은 pytest·PyYAML 외에도 Airflow·dbt·Arrow와 dev plugin을 포함한다. 더 작은 환경의 후보는 있지만 CI 계약의 fixture·plugin·타입 검사까지 필요한 의존성이 무엇인지는 축소 환경에서 검증하지 않았다.

원 보고서의 성공 실행 41회는 중앙값 58초, 범위 12~117초였다. 관측된 sync는 1~2초, uv setup은 7~10초였지만 캐시·설치·runner 대기를 분리하지 않았다. 이 과거 표본을 현재 revision의 cold install 비용이나 환경 분리의 절감량으로 해석할 수 없다. Lock record 226개도 실제 설치 수나 다운로드 크기가 아니다.

모든 Python 변경이 `python=true`를 만들며 wheel build도 같은 조건을 사용한다. Test/script-only 변경의 build 분리는 가능하지만 원 보고서의 build 시간은 초 단위 기록상 0초였다. 비용이 없다는 뜻도, 중요한 병목이라는 근거도 아니다.

### Existing Contract Tests Are the Smallest Verification Surface

[Workflow tests](../../../tests/scripts/ci/test_ci_workflow.py)는 실제 YAML의 boundary 명령을 fake CLI로 실행해 세 필수 target과 실패 전파를 확인한다. [Pytest step tests](../../../tests/scripts/ci/test_ci_pytest.py)는 marker·병렬 threshold·full-unit 뒤 CI non-unit 보완을 검사한다. 기존 fixture와 module을 확장하는 편이 새 routing framework나 테스트 패키지보다 작다.

이 검사는 명령·환경 전달과 실패 계약을 보호한다. 실제 target collection과 runtime 호환성은 별도 근거가 필요하다. F4의 유지보수 위험은 mapping·workflow·marker 계약을 함께 갱신하는 것으로 다루며, 줄 수만으로 과설계라고 판단하지 않는다.

## Options

| Option | Benefit | Cost or Limit | Recommendation |
| --- | --- | --- | --- |
| 현 상태 유지 | 새 검증 누락 위험 없음 | 확인된 반복은 남음 | 개선 이득이 작거나 복잡성이 커지면 중단할 수 있는 기준선 |
| F1 두 중복만 제거 | 환경·dependency 변경 없이 반복 범위를 축소 | 성공 조건·실제 coverage의 회귀 검사 필요 | 먼저 준비 |
| F2 환경 분리 | Cold setup 비용을 줄일 가능성 | plugin·lock·cache 유지 부담; 현재 절감 미측정 | 측정 후 별도 판단 |
| F3 build 조건 분리 | packaging 영향이 더 명확해짐 | 새 분류 조건과 회귀 검사 필요 | 낮은 우선순위의 선택 항목 |

## Implications

후속 계획은 F1의 coverage 보존을 먼저 고정하고 실행 책임이 있는 workflow·pytest script에서만 반복을 줄이는 것이 적절하다. F2는 측정 결과가 환경 준비를 중요한 비용으로 지목할 때만 설계·승인으로 이어진다. F3는 조건 명료화의 필요가 있을 때 선택하고 F4를 이유로 새 framework·matrix·job을 추가하지 않는다.

이 조사는 기존 PR의 검증 완료와 다른 작업이다. 이전 follow-up을 새 blocker로 만들거나 이번 문서 작성만으로 구현·commit·push를 승인하지 않는다.

## Open Questions

- F1의 실제 반복 시간은 어느 정도인가? 수정 전후 같은 target·marker·환경의 실행 기록으로 확인해야 하며 target 수 감소를 시간 절감으로 대체하지 않는다.
- Cold/warm 환경의 설치·다운로드 비용과 uv setup·runner 대기를 구분할 수 있는가? 확인하지 못한 cache 상태는 unknown으로 남겨야 한다.
- 환경 분리의 이득이 추가 dependency·plugin·cache 계약을 유지할 비용보다 큰가? 측정 전에는 분리하지 않는 것이 기본값이다.

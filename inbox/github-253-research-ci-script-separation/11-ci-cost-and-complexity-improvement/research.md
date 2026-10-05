---
type: research
title: CI Cost and Complexity Improvement Research
description: F1 중복 선택의 과거 근거와 F2 cold·warm 측정으로 CI 환경 분리의 실익과 추가 검증 필요성을 판단한다.
tags:
  - ci
  - change-impact
  - performance
---

# CI Cost and Complexity Improvement Research

> [!IMPORTANT]
> **F2 측정은 완료했으며 현재는 전체 환경 유지가 적절하다.** 로컬 full sync의 cold 중앙값은 25.64초, warm은 0.23초였다. 현재 Actions는 cache hit이며 uv setup 13초 중 cache 복원이 약 10초, sync는 3초다. 작은 환경의 비용·검증 동등성은 측정하지 않았으므로 환경 분리의 실익과 과금 절감은 아직 미확인이다. 아래 `Findings`는 F1 구현 전 snapshot이며 현재 F1 결과는 [Execution Record](plan.md#execution-record)를 따른다.

## Question

현재 CI Lite에서 `main` admission에 필요한 검증을 유지하면서 어떤 반복 실행을 제거할 수 있고, 환경·빌드 범위 축소는 어떤 추가 근거가 있어야 선택할 수 있는가?

## Scope

2026-10-04, branch `agent/research-ci-script-separation`의 HEAD `6251c91aafd2a2db0d41d2136ff6f773f02df03e`와 조사 시작 시 clean 작업 트리를 기준으로 한다. [원 보고서](../06-review-ci-cost-and-complexity.md)는 과거 비용 표본의 근거로, 현재 workflow·classifier·pytest script는 선택 계약의 근거로 사용했다.

F1의 두 중복 조합, F2의 환경 준비, F3의 wheel build 조건과 F4의 영향 매핑만 포함한다. 애플리케이션 변경, Tach boundary 재설계, 전체 CI 재설계, provider 이전과 권한 변경은 제외한다. 위 snapshot에서는 새 pytest suite·원격 실행 통계·cold install·과금·before/after benchmark를 수집하지 않았다. 2026-10-05의 [F2 Measurement](#f2-measurement)는 전달된 HEAD `ec81d5d3abb27b036a50ed79e73b18565199f394`와 해당 CI 로그를 사용한 별도 후속 근거다.

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

## F2 Measurement

### State Basis

2026-10-05 재개 시 worktree는 clean이었고 로컬·원격 head는 `ec81d5d3abb27b036a50ed79e73b18565199f394`, base는 `5532dca2fd93696d40ba870471fa2359c5662335`였다. [PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253)은 Open·Draft, mergeable이며 본문의 revision·Validation은 최신 CI와 일치했다. 조회한 review·review thread에는 feedback이 없었다. 이 상태의 review readiness는 `ready`이며 correctness approval이나 merge permission은 아니다. Required approval·protection 설정의 미확인 상태를 무승인 merge 허용으로 해석하지 않는다.

[CI Lite run 37216063423](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37216063423)은 success다. Checkout 로그와 commit parents로 prospective merge `0b02ef08a69e2e5b1992fb5dffe579a605e04f3e`가 위 base/head 조합임을 확인했다. F1 구현·독립 리뷰는 반복하지 않았으며 새로운 CI 실행도 요청하지 않았다.

### Actions Cache Restore Is Separate from Sync

현재 revision의 [job 111476703631](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37216063423/job/111476703631)의 native step 시각과 로그를 사용했다. Runner는 Ubuntu 24.04 x86_64, Python 3.13.15, uv 0.11.32다.

| Stage | Observed Time | Evidence and Limit |
| --- | --- | --- |
| Run creation → job start | 3초 | `16:15:00Z → 16:15:03Z`; scheduling·runner 준비 원인은 분리 불가 |
| Python setup | 같은 초 내 완료 | Runtime은 이미 hosted tool cache에 존재; 실제 비용 0을 뜻하지 않음 |
| uv setup | 13초 | `16:15:09Z → 16:15:22Z`; uv 설치와 dependency cache 복원 포함 |
| Cache restore | 약 10초 | 로그 `16:15:12.141Z → 16:15:22.273Z`; exact-key hit, 348,447,326 B archive, extraction 포함 |
| Full sync | 3초 | `16:15:22Z → 16:15:25Z`; 프로젝트 1개 준비 241ms, 223개 설치 1.97초 |
| Job total | 49초 | `16:15:03Z → 16:15:52Z`; 테스트와 다른 검증 포함 |

uv 다운로드는 `16:15:10.175Z`, 설치 완료는 `16:15:11.437Z`이며 cache 복원과 다른 비용이다. Sync는 새 `.venv`를 만들었지만 package cache는 warm이었다. 따라서 이 실행을 cold install 표본으로 세지 않는다. 직전 run의 로그는 조회에서 비어 있어 추가 표본으로 사용하지 않았다. 위 시각이나 캐시 크기를 과금 절감액 또는 환경 축소로 줄일 수 있는 시간으로 환산하지 않는다.

### Local Cold and Warm Samples

같은 HEAD의 `git archive`를 저장소 밖 임시 영역에 풀고, 각 cold마다 빈 uv cache를 만들었다. 그 cache를 재사용하는 warm도 별도의 새 venv에서 실행했다. 같은 cache를 사용하는 cold → warm 순서의 세 쌍을 순차 실행했으며 warm이 이미 설치된 venv의 audit으로 끝나는 경우는 없었다.

| Condition | Value |
| --- | --- |
| Date / Host | 2026-10-05, Linux WSL2 x86_64, ext4 disk; GitHub runner 아님 |
| Toolchain | uv 0.11.32, CPython 3.13.15; Python build·filesystem은 hosted runner와 다름 |
| Source | HEAD `ec81d5d3abb27b036a50ed79e73b18565199f394`; CI는 위 prospective merge 사용 |
| Lock SHA-256 | `9ee5ff429ffeb5ef6b140d6bb173595c7c290bf51167eced72fa960077de0221` |
| Project SHA-256 | `25cb277ce7cb00497175c53b703cdd445c77fc525691ea8d8f6610f34d5bd0a8` |
| Command | `uv sync --locked --project "$checkout" --no-progress`; root dependencies와 default dev group 유지 |
| Controls | `UV_CACHE_DIR`, `UV_PROJECT_ENVIRONMENT`, `UV_PYTHON`을 명시; ambient `UV_ENV_FILE`, `PYTHONPATH`, `VIRTUAL_ENV`, `UV_OFFLINE`, `UV_NO_CACHE` 제거; Python 자동 다운로드 비활성화 |
| Timing | GNU `/usr/bin/time`의 wall clock; tool·runtime 준비와 cache 복사·복원은 제외 |

공식 uv 0.11.32 archive의 SHA-256 `aab924fd522efd06f1c5f3b93a243864fc453132c94b2dc49f1371b528a4b967`을 확인했다. 이 uv의 Python catalog에는 3.13.15가 없어 runtime만 별도 uv 0.12.5로 준비했으며 실제 sync는 모두 0.11.32로 실행했다. 주 `.venv`와 공유 cache를 삭제·교체하지 않았고, repository source·lock·workflow·test는 변경하지 않았다.

| Pair | Cold Wall (s) | Cold Prepare (s) | Cold Install (ms) | Warm Wall (s) | Warm Install (ms) |
| --- | --- | --- | --- | --- | --- |
| 1 | 27.26 | 26.89 | 163 | 0.23 | 162 |
| 2 | 25.64 | 25.41 | 115 | 0.25 | 174 |
| 3 | 25.31 | 25.09 | 114 | 0.18 | 112 |

Cold는 중앙값 **25.64초**, 범위 **25.31~27.26초**이고 warm은 중앙값 **0.23초**, 범위 **0.18~0.25초**다. 모든 sync exit code는 0이며 226개 resolution record 중 실제 설치는 223개였다. 여섯 환경의 정렬된 `name==version` 목록은 동일했고 SHA-256은 `4d5e4f775b0937eb82e683b064bdde7fd9b4eded27814ed9b74d41540ada5a6f`였다. 이는 설치 목록의 일치이지 pytest plugin·fixture 실행 동등성의 증명은 아니다.

Cold에는 다운로드·build·unpack이 포함됐다. Warm에는 download·prepare 로그가 없으며, 마지막 cache에서 `--offline`과 새 venv로 추가 실행해 223개 설치 성공을 확인했다. Offline 검사는 시간 표본에서 제외했다. Pair별 cache의 디스크 사용량은 약 1.09GiB로, Actions의 압축 archive 크기와 직접 비교하지 않는다. OS page cache·DNS·upstream cache는 초기화하지 않았으므로 cold는 **빈 uv cache**를 뜻하며 완전히 cold인 host나 network를 뜻하지 않는다.

재현할 때는 같은 source·lock·toolchain으로 pair별 빈 cache와 새 cold/warm venv를 만들고, 위 환경값으로 GNU time을 감싼 sync를 실행한다. Raw log는 repository에 추가하지 않는다. 이번 임시 근거는 `/home/mols3131d/.cache/hmda-pr253-f2.PgXHZ7/pair-{1,2,3}/{cold,warm}.{time,log}`와 `offline.log`에 남아 있으며 임시 자료이므로 지속 보존을 보장하지 않는다.

### Decision Gate Remains Open

빈 cache에서의 준비 비용과 Actions의 cache 복원 비용은 확인됐지만 **작은 locked 환경의 전후 비교·fixture/plugin·정적 검사 동등성은 확인하지 않았다.** 현재 evidence만으로 별도 lock·cache·workflow를 도입할 근거는 부족하다. 기본 권고는 기존 전체 환경을 유지하고 F2를 PR 완료 blocker로 만들지 않는 것이다.

추가 개선을 선택한다면 먼저 기존 성공 Actions 표본으로 cache hit/miss 빈도와 복원 시간을 확인하고, 절감 후보가 유지 비용을 감당할 때만 작은 환경의 계약 동등성·전후 비용을 별도 범위로 제안한다. F3 build 조건과 금액 절감은 이번 측정의 결론이 아니다. 추가 구현·commit·push·본문 갱신·Ready 전환·승인·merge는 수행하지 않았다.

## Open Questions

- 작은 환경이 cold 준비와 Actions cache 복원에서 실제로 얼마나 줄이며, fixture·pytest plugin·정적 검사 계약을 유지할 수 있는가? 비교 환경은 아직 만들지 않았다.
- 현재 lock/runtime의 Actions cache hit·miss 빈도와 비용 분포는 어떤가? 이번 관측은 exact-key hit 한 회이며 cold hosted-runner 표본·실제 과금은 없다.
- F1의 실제 반복 시간은 어느 정도인가? 수정 전후 같은 target·marker·환경의 실행 기록이 없으므로 target 수 감소를 시간 절감으로 대체하지 않는다.

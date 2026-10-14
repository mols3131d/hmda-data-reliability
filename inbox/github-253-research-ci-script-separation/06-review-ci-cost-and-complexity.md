---
type: review
title: CI Cost and Complexity Review
description: CI Lite의 최근 실행 시간, 환경 준비 범위, 중복 검증과 유지보수 복잡성을 검토하고 병합 기준을 유지하는 경량화 우선순위를 제안한다.
tags:
  - ci
  - github-actions
  - testing
---

# CI Cost and Complexity Review

> [!IMPORTANT]
> **실행 시간 기준으로 CI가 과도하게 무겁다는 근거는 부족하다. 다만 좁은 검증에도 전체 환경을 준비하고 일부 검사를 중복 선택하는 구조는 개선 여지가 있다.** 최근 성공 실행 41회의 중앙 완료 시간은 58초, 최장 시간은 117초였다. 대대적인 재설계보다 확인된 중복부터 제거하고, 환경 분리는 실제 비용을 더 측정한 뒤 결정하는 편이 낫다. 이번 결과는 비용 진단이며 PR 승인이나 구현 변경 요청이 아니다.

- **Target**: [CI Lite](../../.github/workflows/ci-lite.yml), [CI scripts](../../scripts/ci/), [Python configuration](../../pyproject.toml), 관련 계약 테스트와 [CI policy](https://github.com/mols3131d/hmda-data-reliability/blob/63535f6d46c7735777a942fd7bbb906889fc45c6/docs/development/ci.md).
- **Revision**: 2026-10-04, `Asia/Seoul`. [PR #253](https://github.com/mols3131d/hmda-data-reliability/pull/253)의 branch `agent/research-ci-script-separation`, 검토 시작 시 HEAD `63535f6d46c7735777a942fd7bbb906889fc45c6` 위의 미커밋 작업 트리. 종료 전 HEAD가 `cf9c1384bdd9c8c8cedc01c001f0806095ff766e`로 갱신된 것을 확인했다. 독립 검토의 대상은 최초 로컬 상태이며 원격 실행 통계는 각 실행 당시의 별도 리비전이다.
- **Scope**: PR 검증의 시간, 환경 준비 비용, 선택 범위와 유지보수 부담을 평가한다. 기존 classifier 수정, CI 테스트 패키지 분리와 Testing Guide 수정은 보존했다. Workflow, script, test, dependency, branch rule은 변경하지 않았다.

## Findings

모든 항목은 현재 상태의 `follow_up`이다. 새로운 correctness blocker나 PR #253이 도입한 성능 회귀를 입증한 것은 아니다. `Minor`는 확인된 제한적 중복, `Note`는 선택적 개선 후보를 뜻한다.

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Minor | 일부 source 변경에서 AST boundary guard가 두 단계에 포함되고, 전체 suite와 dependency smoke도 특정 조합에서 겹친다. | 같은 검사·marker 범위가 이미 포함된 조합에서만 중복 실행을 제거한다. |
| F2 | Note | CI-only 계약 검사도 애플리케이션 전체 locked environment를 준비한다. | Cold setup 비용을 측정하고, 절감이 유의미할 때만 locked tooling 환경 분리를 검토한다. |
| F3 | Note | Test/script-only Python 변경에도 애플리케이션 wheel을 빌드한다. | Packaging 영향 조건을 분리할 수 있으나 현재 시간 절감 우선순위는 낮다. |
| F4 | Note | 실행 시간보다 수동 영향 매핑을 유지하는 부담이 더 중요한 장기 위험이다. | 기존 경로별 계약을 유지하고 새로운 분류 framework나 job을 추가하지 않는다. |

## Details

### F1: Overlapping Test Selection

#### F1 Locations

- [Dependency boundary step](../../.github/workflows/ci-lite.yml#L115)
- [Domain consumer selection](../../scripts/ci/classify_changes.sh#L150)
- [AST boundary guard](../../tests/review_ai/test_dependency_boundaries.py#L11)
- [Full test execution](../../scripts/ci/pytest.sh#L15)
- [Dependency runtime smoke](../../.github/workflows/ci-lite.yml#L150)

#### F1 Evidence

`reliability`와 `runtime_ai` source 변경은 `tach=true`인 동시에 consumer인 `tests/review_ai`를 선택한다. 전용 boundary step이 실행하는 AST guard는 이 directory에도 들어 있으므로 일반 selected tests에서도 다시 포함된다. 로컬 classifier의 두 대표 source 입력에서 이 선택을 확인했다. Guard의 `component` marker는 selected tests의 `not memory and not stress` 조건에서도 제외되지 않는다.

Dependency 변경과 미매핑 canonical Spec 변경을 함께 입력하면 `full_tests=true`와 `runtime_smoke=true`가 동시에 선택된다. 전체 non-resource suite에는 별도 smoke 대상인 dbt/Airflow 테스트도 포함된다. 반대로 dependency 단독 변경의 `full_unit=true`는 component/integration smoke를 포함하지 않으므로 별도 실행이 필요하다.

#### F1 Impact

같은 리비전의 동일 검증을 반복하는 제한적 낭비다. 실제 중복 구간의 추가 시간은 측정하지 않았다. Boundary step 전체의 11~12초를 AST guard 중복 비용으로 간주해서는 안 된다. 그 step은 별도의 Tach 실행과 negative-path 테스트도 수행한다.

#### F1 Action

이미 실행된 검사와 marker 범위가 같다는 조건을 명시한 뒤 해당 조합만 한 번 실행하도록 조정한다. 전용 Tach 검사, 전체 unit fallback 뒤 component 보완과 dependency runtime smoke의 필수 범위는 유지한다. 기존 [CI contract tests](../../tests/scripts/ci/test_ci_workflow.py)에서 필수 target 누락과 실패 전파를 계속 검출해야 한다.

### F2: Broad Environment Preparation

#### F2 Locations

- [Dependency sync](../../.github/workflows/ci-lite.yml#L111)
- [CI-only selection](../../scripts/ci/classify_changes.sh#L248)
- [Project dependencies](../../pyproject.toml#L7)
- [CI fake-tool fixture](../../tests/scripts/ci/conftest.py#L33)

#### F2 Evidence

CI helper만 바뀌어도 `tests=true`를 통해 `uv sync --locked`를 실행한다. 현재 CI 계약 패키지의 직접 요구는 pytest, PyYAML과 표준 라이브러리이며 외부 CLI는 fake executable로 검증한다. 그러나 준비되는 프로젝트 환경에는 Airflow, dbt, Arrow 등도 포함된다. Lock inventory의 package record는 226개다. 이는 optional 항목 등을 포함한 inventory이며 실제 설치 패키지 수나 다운로드 크기를 뜻하지 않는다.

#### F2 Impact

검증의 직접 요구보다 준비 범위가 넓고 cache miss 시 비용이 커질 가능성이 있다. 다만 확인한 원격 실행의 sync 단계는 1~2초였다. `Set up uv`는 7~10초였지만 도구 설치·캐시 처리 등 내부 비용을 분리하지 않았으므로 그 전부가 full environment 때문이라고 볼 수 없다. Cache hit 여부와 cold install 시간은 확인하지 못했다.

#### F2 Action

먼저 CI-only 실행의 cold/warm 환경 준비 시간을 구분해 측정한다. 효과가 입증될 때만 같은 lock으로 관리하는 작은 tooling 환경을 검토한다. Timeout, strict marker, 필요한 pytest plugin과 Python 정적 검증을 보존해야 하며, 기존 locked-environment 계약을 함께 갱신해야 한다. 검증되지 않은 `uvx pytest` 대체나 별도 lock·캐시 체계 추가는 권고하지 않는다.

### F3: Unscoped Package Build

#### F3 Locations

- [Python change classification](../../scripts/ci/classify_changes.sh#L210)
- [Wheel build](../../.github/workflows/ci-lite.yml#L122)
- [Build module](../../pyproject.toml#L85)

#### F3 Evidence

모든 `.py` 변경이 `python=true`를 만들고 wheel build도 같은 flag를 사용한다. 따라서 애플리케이션 package와 관계없는 CI test 수정에도 `hmda_reliability` wheel을 빌드한다. 로컬 입력 `tests/scripts/ci/test_ci_classifier_python.py`에서도 `python=true`를 확인했다. 확인한 원격 build 시간은 모두 초 단위 기록상 0초였다. 작업이 없었다는 뜻이 아니라 측정 해상도보다 짧았다는 뜻이다.

#### F3 Action

정적 Python 검증과 packaging 영향을 구분하는 작은 조건 분리는 가능하다. Source, build metadata, runtime/dependency 변경과 영향 불명확 시의 build는 유지한다. 현재 주요 병목이라는 근거는 없으므로 속도 개선만을 위해 먼저 구현할 필요는 없다.

### F4: Routing Maintenance Cost

#### F4 Locations

- [Domain closure](../../scripts/ci/classify_changes.sh#L127)
- [OpenSpec capability mapping](../../scripts/ci/classify_openspec.sh#L78)
- [CI test package](../../tests/scripts/ci/)

#### F4 Evidence

현재 CI Bash 스크립트는 7개, 714줄이며 로컬 CI Python 테스트·helper는 9개, 1,400줄이다. 줄 수 자체는 과설계의 증거가 아니다. 실제 유지보수 지점은 domain consumer closure, OpenSpec capability mapping, workflow 조건과 pytest marker 조합을 함께 맞추는 부분이다. 현재 계약 테스트는 이 복잡성을 보호하며 136개가 로컬에서 통과했다.

#### F4 Action

새 domain/capability 또는 파일 이동 시 대표 입력의 선택 결과와 필수 target 계약을 함께 갱신한다. 기존 스크립트 분리는 로컬 재현과 실패 추적에 유용하므로 다시 inline으로 합치지 않는다. 전체 검증으로 되돌리거나 범용 router, 큰 matrix, 추가 job·cache를 도입할 근거는 없다.

## Runtime Evidence

GitHub Actions API에서 최근 50회 실행을 조회했다. 표본 생성 시각은 UTC `2026-09-26T15:12:51Z`부터 `2026-10-04T02:51:02Z`까지다. 성공 41회, 취소 7회, 실패 2회다. 성공 실행의 중앙값은 58초, 범위는 12~117초다. 여러 workflow 리비전과 변경 종류가 섞인 convenience sample이며 전체 변경 유형의 성능이나 장기 SLA를 대표하지 않는다.

전체 시간은 `updated_at - run_started_at`, job 시간은 `completed_at - started_at`으로 계산했다. 전체 시간에는 runner 대기 등이 포함된다. 실제 과금 시간이나 금액은 조회하지 않았다.

| Run | Context | Overall | Job | Selected Observations |
| --- | --- | --- | --- | --- |
| [37172302815](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37172302815) | 현재 원격 HEAD, PR #253 | 48초 | 26초 | Job 시작 전 22초, uv setup 7초, sync 2초, selected tests 9초 |
| [37017544922](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37017544922) | 문서 검증만 수행 | 12초 | 7초 | Python·uv·pytest 단계 미실행 |
| [37007476889](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37007476889) | Source/spec 등 복합 검증 | 59초 | 53초 | OpenSpec 10초, uv setup 10초, sync 1초, boundary 11초, tests 8초 |
| [36252052637](https://github.com/mols3131d/hmda-data-reliability/actions/runs/36252052637) | 표본 중 최장 성공 실행 | 117초 | 113초 | uv setup 7초, sync 2초, boundary 12초, tests 14초, runtime smoke 20초 |

설정상 PR당 job 한 개, 10분 timeout, superseded run 취소, uv 캐시가 이미 있다. Markdown·Inbox 변경은 Python 환경을 준비하지 않으며 `memory`·`stress` 테스트도 기본 제외한다. 따라서 “매 PR마다 전체 suite와 비싼 runtime을 전부 실행한다”는 진단은 현재 구조와 맞지 않는다. 위 단계 시간은 GitHub의 초 단위 기록이며 합산값이 전체 job 시간과 정확히 일치하지 않을 수 있다.

## Admission Evidence to Preserve

| Failure | Cheapest Existing Evidence | Boundary |
| --- | --- | --- |
| 변경 Python의 정적 오류 | Changed-file Ruff와 영향 범위의 `ty check` | Blocking PR |
| 금지된 runtime dependency | `tach check`, negative-path test, AST guard | Blocking PR, 중복만 제거 |
| Domain/consumer 동작 회귀 | 해당 domain과 consumer의 unit/component/integration test | Blocking PR |
| Dependency/runtime 호환성 실패 | 전체 unit/type 검사와 dbt/Airflow runtime smoke | Blocking PR, 포함 범위가 같을 때만 중복 제거 |
| Spec 또는 artifact 계약 위반 | OpenSpec strict validation, 변경된 Inbox root metadata 검사 | Blocking PR |
| 영향 범위를 결정할 수 없음 | 기존 fallback 확대 또는 selector 실패 | Silent skip 금지 |

Prospective merge 검증, 항상 생성되는 PR check, 최소 읽기 권한과 credential 비보존은 유지한다. Local hook 통과로 CI를 대체하지 않는다. Formatting을 이유로 전체 문서 lint나 write-back을 추가하지 않으며 기존 docs lint 계약을 임의로 완화하지 않는다.

## Recommended Sequence

1. **Low-risk deduplication**: F1의 두 중복 조건만 기존 계약 테스트로 고정하고 한 번 실행한다. Consumer coverage와 unit fallback 보완은 유지한다.
1. **Measure setup before splitting**: CI-only 변경에서 cold/warm setup을 구분한다. 의미 있는 시간·다운로드 절감이 없으면 F2는 보류한다.
1. **Optional packaging scope**: F3는 조건 명료화가 필요할 때만 진행한다. 현재 0초 단위 관측을 큰 절감 효과로 포장하지 않는다.
1. **Stop expanding machinery**: F4의 mapping을 기존 테스트로 보호한다. 새 framework, provider 이전, 대형 matrix와 scheduled full suite를 이 보고서만으로 추가하지 않는다.

후속 변경의 acceptance는 같은 대표 입력에서 필수 검사 누락이 없고, 모르는 영향 범위는 fail-safe이며, 동일 리비전·동일 marker 범위의 반복만 제거되는 것이다. 시간 개선은 같은 조건의 전후 실행으로 별도 입증한다. 지금 당장 CI 전체를 재설계하거나 검증을 끌 필요는 없다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| Pass | Configuration and contract inspection | Workflow, CI scripts, dependencies, test markers와 CI/testing 정책을 대조했다. |
| Pass | Remote execution sampling | 최근 50회 API 통계와 위 4회의 job/step 시각을 조회했다. 조회 명령은 `gh api 'repos/mols3131d/hmda-data-reliability/actions/workflows/ci-lite.yml/runs?per_page=50'`이다. |
| Pass | Local selector scenarios | Docs, CI helper, CI test, reliability source, runtime source, dependency, dbt, unknown Spec + dependency의 8개 입력을 `--stdin`으로 실행했다. |
| Pass | Bash syntax | CI Bash 스크립트 7개의 `bash -n`이 통과했다. |
| Pass | Current local CI contracts | `uv run --no-sync pytest tests/scripts/ci -q -p no:sugar -p no:cacheprovider --color=no --tb=short --durations=5`: 136 passed in 3.24s. |
| Pass | Independent diagnostic review | `review-lead`가 quality/adversarial 검토를 조정했다. 반환된 `clear`는 비용 진단의 완료이며 PR approval이 아니다. 독립 검토자는 정적 분석만 했고 위 실행 검증은 호출자가 수행했다. |
| Not Verified | Cold install, billing and optimization benefit | Cache hit, 다운로드 크기, 과금과 변경 전후 절감량은 확인하지 않았다. |
| Not Verified | Updated revision on GitHub | 확인한 최신 원격 success는 `63535f6`의 근거다. 이후 로컬 HEAD `cf9c138`의 원격 통과 여부는 확인하지 않았다. |

## Risks and Limits

대표 변경 조합과 설정 경로의 검토이며 애플리케이션 전체 correctness나 branch protection의 required-check 설정을 인증하지 않는다. 독립 검토자는 Git revision/diff와 executable validation을 직접 확인하지 못했으며 호출자가 확인한 상태·실행 근거와 구분했다. Full environment 축소의 plugin 호환성, cold runner 성능과 중복 제거의 실제 효과는 후속 검증 대상이다. 검토 중 HEAD 갱신은 이 작업에서 수행한 변경이 아니다. 이 보고서는 미커밋 상태로 남기며 본 작업에서는 commit, push, PR 상태 변경을 수행하지 않았다.

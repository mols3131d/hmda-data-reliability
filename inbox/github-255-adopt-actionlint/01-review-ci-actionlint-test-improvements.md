---
type: review
title: "Actionlint Test Improvement Review"
description: "PR #255의 actionlint 변경 경로 분류와 CI 실행 계약 테스트를 검토하고 실패 검출력을 높이는 최소 개선 범위를 제안한다."
tags:
  - ci
  - actionlint
  - testing
---

# Actionlint Test Improvement Review

> [!IMPORTANT]
> **Revise (non-blocking test improvements)** — 현재 actionlint 구현이 잘못 동작한다는 증거는 발견하지 못했고 실제 CI도 성공했다. 다만 추가된 계약 테스트는 Docker 명령의 전체 문자열을 고정하고, 검증 실패를 무시하도록 바뀌는 회귀를 놓칠 수 있으며, 기존 zizmor 경로 매트릭스와 중복된다. **새 테스트 프레임워크 없이 기존 테스트 2개 영역을 간결하게 재구성**하는 것을 권장한다.

- **Target** — [PR #255 — chore(ci): adopt actionlint](https://github.com/mols3131d/hmda-data-reliability/pull/255)
- **Revision** — base `5526c3b6cfc35e74a21ba848d390b814d0268406`; head `016fd6b4956ebc20162eb491d511414bcffec4f8` (2026-10-08 기준)
- **Scope** — `tests/scripts/ci/test_ci_classifier.py`, `tests/scripts/ci/test_ci_workflow.py`; 대조 대상 `scripts/ci/classify_changes.py`, `.github/workflows/ci-lite.yml` 및 [CI Lite 결과](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37775652983). 테스트 설계 개선 검토만 수행했으며 구현·테스트는 변경하지 않았다.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | 🟡 Minor | Docker 명령 전체와 digest를 테스트에 중복 고정해 동등한 구현 변경도 실패로 취급한다. | 전체 문자열 비교를 검사 의미·보안 invariant 중심으로 축소한다. |
| F2 | 🟡 Minor | `continue-on-error: true`가 추가되어도 신규 테스트가 통과할 수 있다. | Fail-closed 설정을 명시적으로 검증하고 필요시 외부 Docker 호출 실패만 fake executable로 확인한다. |
| F3 | 🔵 Note | Action 경로 선택에 대한 새 9개 parameter case가 기존 zizmor 경로 테스트를 상당 부분 반복한다. | 기존 경로 매트릭스에 `actionlint` 출력 검증을 합쳐 중복과 누락을 동시에 줄인다. |

## Details

### F1 · Full-command assertions bind tests to implementation text

🟡 **Minor**

#### Locations

- [`tests/scripts/ci/test_ci_workflow.py`](https://github.com/mols3131d/hmda-data-reliability/blob/016fd6b4956ebc20162eb491d511414bcffec4f8/tests/scripts/ci/test_ci_workflow.py#L491-L506)
  - `test_workflow_validates_actions_with_pinned_actionlint`, lines 496–503
- [`.github/workflows/ci-lite.yml`](https://github.com/mols3131d/hmda-data-reliability/blob/016fd6b4956ebc20162eb491d511414bcffec4f8/.github/workflows/ci-lite.yml#L36-L40)
  - `Validate GitHub Actions with actionlint`

#### Evidence

신규 테스트는 Docker 이미지의 **64자리 digest 전체**와 `docker run --rm -v ... -w ... -color`라는 **단일 문자열 전체**가 일치해야 통과한다. `assert "env" not in step`도 검증 결과가 아닌 구현 구조를 제한한다. 이미지 버전이나 digest 갱신, 동일한 효과의 인자 순서·출력 옵션 변경은 실제 회귀가 없어도 테스트와 함께 수정해야 한다.

반면 의미 있는 계약은 *조건부 선택, 전체 Workflow 검사, 이미지 digest pinning, checkout read-only, 실패 시 Job 차단*이다.

#### Impact

테스트와 Workflow의 이중 수정이 발생하고, 정상적인 유지보수 작업에서 불필요한 실패가 늘어난다. 명령 문자열을 완벽하게 맞춰도 실제 actionlint의 실패 검출 여부가 입증되는 것은 아니다.

#### Action

- `shlex.split(str(step["run"]))` 또는 최소한의 token 추출로 `docker run`, 이미지, mount와 작업 디렉터리를 분석한다.
- 이미지 참조는 공식 repository, 고정 버전 정책, `@sha256:[0-9a-f]{64}` 형식으로 검증한다. **digest 전체를 테스트에 복제하지 않는다.**
- `-v "$GITHUB_WORKSPACE:/repo:ro"`의 read-only 여부와 `-w /repo`, `Classify changes` 뒤 실행·정확한 `if` 조건을 유지해 검증한다.
- `-color`, 독립된 `env` 유무, 인자 표현 순서처럼 계약상 필수가 아닌 사항은 불필요하게 묶지 않는다. 보안 정책상 정확한 digest 문자열을 고정할 필요가 있다면 Workflow만 단일 owner가 되도록 한다.

### F2 · Fail-closed behavior has a specific false-green path

🟡 **Minor**

#### Locations

- [`tests/scripts/ci/test_ci_workflow.py`](https://github.com/mols3131d/hmda-data-reliability/blob/016fd6b4956ebc20162eb491d511414bcffec4f8/tests/scripts/ci/test_ci_workflow.py#L491-L506)
  - `test_workflow_validates_actions_with_pinned_actionlint`
- [`.github/workflows/ci-lite.yml`](https://github.com/mols3131d/hmda-data-reliability/blob/016fd6b4956ebc20162eb491d511414bcffec4f8/.github/workflows/ci-lite.yml#L36-L40)
  - 검사 단계에는 현재 `continue-on-error`가 없으므로 GitHub Actions 기본 실패 처리 동작을 사용한다.

#### Evidence

현재 테스트는 `if`, `run`, `env`, 단계 순서만 검사한다. 같은 Workflow Step에 `continue-on-error: true`를 추가해도 **테스트의 모든 기존 assertion은 그대로 충족**된다. 이 경우 실패한 검사 Step이 성공으로 취급될 수 있어 병합 차단 목적을 해친다. 이는 **현재 발견된 runtime defect가 아니라 테스트의 회귀 방어 공백**이다.

#### Impact

향후 Actionlint 실패를 무시하도록 변경해도 계약 테스트가 변경을 탐지하지 못한다.

#### Action

먼저 아래 한 줄로 가장 큰 공백을 막는다.

```python
assert step.get("continue-on-error", False) is False
```

동작 증거가 더 필요하다면, 기존 `tool_env` / fake CLI fixture를 재사용하는 **작은 negative-path 테스트 1개**만 고려한다. Workflow의 `run` 명령을 `bash -e -c`에서 실행하고 fake `docker`가 exit 17을 반환하게 해 exit code 전파를 관찰한다. 실제 Docker Hub 네트워크 또는 Docker daemon에 의존하는 테스트를 매 PR마다 추가하지 않는다.

실제 잘못된 Workflow를 탐지하는지 확인하려면 CI와 분리된 **일회성 수동 negative control**에서 공식 이미지를 사용할 수 있다. 이는 검증 강화 옵션이지 새 필수 프레임워크 도입 요구가 아니다.

### F3 · Consolidate the shared action-path matrix

🔵 **Note**

#### Locations

- [`tests/scripts/ci/test_ci_classifier.py`](https://github.com/mols3131d/hmda-data-reliability/blob/016fd6b4956ebc20162eb491d511414bcffec4f8/tests/scripts/ci/test_ci_classifier.py#L21-L42)
  - 기존 `test_actions_definitions_select_zizmor_even_when_deleted`: 허용, 삭제, 비대상, `inbox/**`을 포함한 12개 경로
- [같은 파일](https://github.com/mols3131d/hmda-data-reliability/blob/016fd6b4956ebc20162eb491d511414bcffec4f8/tests/scripts/ci/test_ci_classifier.py#L309-L331)
  - 신규 actionlint 전용 6개 positive 및 3개 negative case
- [`scripts/ci/classify_changes.py`](https://github.com/mols3131d/hmda-data-reliability/blob/016fd6b4956ebc20162eb491d511414bcffec4f8/scripts/ci/classify_changes.py#L105-L121)
  - 같은 파일 패턴 분기에서 `scope.zizmor`와 `scope.actionlint`를 함께 `True`로 선택

#### Evidence

현재 두 검사 flag는 같은 분기에서 결정된다. 새 테스트는 대표 사례를 다시 검증하지만, 기존 테스트의 `inbox/example/action.yml`, `.github/workflows/classify_changes.sh`, `tools/action.yaml.txt`, 삭제 경로까지 actionlint flag에 대해 확인하지는 않는다. 중복 테스트가 늘어난 반면 coverage matrix는 비대칭이다.

#### Impact

경로 매칭 정책이 바뀌면 양쪽 테스트의 기대값을 각각 유지해야 한다. 두 검사 flag가 같은 정책을 따른다는 사실도 하나의 matrix에서는 관찰되지 않는다.

#### Action

기존 `("path", "selected")` 테이블에서 `out = run_classifier([path])`를 한 번 호출하고, `("zizmor", "actionlint")` **두 flag 모두** `str(selected).lower()`와 비교한다. 새 테스트에만 있는 `.github/workflows/future.yaml`처럼 의미 있는 edge case만 기존 표에 합치고, 중복된 전용 테스트 두 함수를 삭제한다. 향후 두 도구의 선택 정책이 분리되면 그때 독립 매트릭스를 도입한다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 현재 base/head에 대한 CI Lite | [Run 37775652983](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37775652983): actionlint, zizmor, Python 검사와 selected tests 모두 성공 |
| ✅ Pass | CI 계약 suite의 기존 실행 근거 | 동일 Run 로그의 `238 passed in 11.55s`; 검토 과정에서 새로 pytest를 실행한 것은 아님 |
| ✅ Pass | 정적 테스트/Workflow 계약 대조 | 위 링크의 함수, matching branch, `continue-on-error` 누락과 중복 분기 직접 확인 |
| ⚪ Not Verified | Proposed changes 실행 | 현재 review-only 작업으로 테스트 수정·오류 주입 및 새 실행은 수행하지 않음 |
| ⚪ Not Verified | 독립 reviewer 검증 | 이 문서는 단일 맥락에서 작성한 test-focused review이며 별도 review-lead 판정이 아님 |

## Risks and Limits

- **Acceptance interpretation:** 현재 실제 Docker 기반 actionlint Step이 성공한다는 사실은 확인됐다. **차단 결함이 관찰된 것은 아니며**, 위 finding은 주로 향후 회귀 탐지와 유지보수 비용의 개선안이다. PR 전체의 merge approval을 대체하지 않는다.
- **Scope limit:** actionlint는 workflow에서 참조하지 않는 standalone local action 또는 모든 composite step의 검증을 보장하지 않는다. 이는 [기존 연구](00-research-ci-actionlint-adoption.md)의 도구 커버리지 경계이며 테스트를 과도하게 늘리는 이유가 되지 않는다.
- **Execution boundary:** CI Lite 자신의 YAML이 로딩 불가 상태이면 내부 actionlint Step도 시작하지 못할 수 있다. 이는 이 작은 테스트 변경만으로 해소할 수 없는 구조적 한계이므로 별도 scope 결정 없이 Workflow 아키텍처를 확대하지 않는다.
- **Recommended stop:** F1·F2를 최소 수정하고 F3의 중복을 정리한 후 `tests/scripts/ci`와 실제 CI Lite를 재실행한다. 충분한 증거가 나오면 추가 mock framework·반복되는 네트워크 E2E·별도 테스트 pipeline은 만들지 않는다.

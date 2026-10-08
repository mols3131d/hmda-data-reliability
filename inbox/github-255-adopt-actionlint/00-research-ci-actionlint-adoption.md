---
type: research
title: "Actionlint Adoption Research"
description: "GitHub Actions 정적 정확성 검증에 actionlint를 적용할 가치와 한계, 대안, PR #255의 구현·검증 근거를 조사한다."
tags:
  - ci
  - github-actions
  - actionlint
  - validation
---

# Actionlint Adoption Research

> [!NOTE]
> GitHub Actions의 정적 정확성 검증에는 **actionlint 도입이 적절하다**. YAML 문법뿐 아니라 Expression, Job 관계, 일부 Action 계약과 인라인 스크립트를 검증하며, 이미 도입된 zizmor의 보안 감사와 역할이 구분된다. 다만 **외부 Action의 SHA 고정 참조와 독립적인 local action, 실제 실행 결과까지 검증한다고 해석해서는 안 된다**. PR #255의 실제 CI는 성공했지만 오류 주입 negative control과 독립 리뷰 결과는 별도로 구분한다.

## Question

HMDA Data Reliability의 현재 CI 구조에서 actionlint가 해결하는 구체적인 검증 공백은 무엇인가? zizmor와 기존 결정론적 검사를 유지하면서 actionlint를 어떻게 적용하고, 어느 범위까지 신뢰해야 하는가?

## Scope

- **조사 기준:** 2026-10-08, actionlint **v1.7.12**(2026-03-30 공개), 공식 검사·사용·설정 문서
- **Repository:** `mols3131d/hmda-data-reliability`
- **PR #254:** zizmor 병합 후의 `main` (`5526c3b6cfc35e74a21ba848d390b814d0268406`)
- **PR #255:** `agent/chore/adopt-actionlint`, 조사 기준 head `2c6404a14945f1b7d45af3fb8818f2ad0845bbe6`
- **대상:** `.github/workflows/ci-lite.yml`, `scripts/ci/classify_changes.py`, `tests/scripts/ci/`, GitHub Actions 검사 역할과 실제 CI 근거
- **비교:** yamllint, zizmor, ghalint, ShellCheck, act, Super-Linter의 역할 차이

### Out of Scope

- 새로운 코드·테스트·CI 기능의 구현, 기존 보안 정책 변경, Lefthook 통합, repository ruleset 변경
- actionlint가 GitHub Actions 런타임 전체를 완전히 검증한다는 보장
- PR #255의 인간 승인 또는 merge-readiness 판정

## Findings

### Actionlint는 범용 YAML 파서가 아니라 GitHub Actions의 정적 의미 분석기다

[actionlint](https://github.com/rhysd/actionlint)은 Go로 작성된 MIT 라이선스 도구다. 공식 v1.7.12 문서가 제시하는 검사에는 Workflow 키·형식·중복, Expression 구문과 타입, context 접근, Matrix·Step·`needs` 관계, event·cron, runner label, 권한, reusable workflow 및 일부 Action 입력 계약이 포함된다. 잘못된 Job 참조나 존재하지 않는 Expression 속성은 YAML 자체가 유효하더라도 탐지할 수 있다.

예를 들어 `needs: build`를 쓰면서 `build` Job을 정의하지 않은 경우, 또는 Expression에서 `github.events`처럼 존재하지 않는 속성을 참조한 경우가 정적 검사 대상이다. 반면 **Job 관계가 설계 의도에 맞는지**, 조건부 실행이 모든 필요한 테스트를 수행하는지는 이 도구만으로 판단하지 못한다.

- 근거: [actionlint v1.7.12 — Checks](https://github.com/rhysd/actionlint/blob/v1.7.12/docs/checks.md), [Usage](https://github.com/rhysd/actionlint/blob/v1.7.12/docs/usage.md)
- 릴리스: [v1.7.12](https://github.com/rhysd/actionlint/releases/tag/v1.7.12); 조사 시점에 확인된 최신 GitHub release

### ShellCheck와 pyflakes는 내장 엔진이 아니라 선택적 연동이다

actionlint는 Bash/sh `run:`에 대해 **ShellCheck**, `shell: python`으로 실행하는 인라인 Python에 대해 **pyflakes**를 호출할 수 있다. 두 도구는 별도의 실행 파일이며, actionlint는 기본적으로 PATH에서 발견한 경우에만 연동한다. 발견하지 못하면 그 검사층이 빠질 수 있다.

또한 이 기능은 별도의 Python·Shell 파일을 직접 검사하는 용도가 아니다. Repository의 `scripts/ci/*.py`는 계속 **Ruff, ty, pytest**가 검증한다. PR #255는 actionlint 공식 Linux 바이너리를 호출하지만 ShellCheck·pyflakes 존재 여부를 별도의 필수 계약으로 고정하지는 않았다. 특히 pyflakes 검사를 항상 수행했다는 주장은 현재 근거로 뒷받침되지 않는다.

- 근거: [Checks — shellcheck integration](https://github.com/rhysd/actionlint/blob/v1.7.12/docs/checks.md#shellcheck-integration-for-run), [Checks — pyflakes integration](https://github.com/rhysd/actionlint/blob/v1.7.12/docs/checks.md#pyflakes-integration-for-run), [Usage](https://github.com/rhysd/actionlint/blob/v1.7.12/docs/usage.md)

### 외부 Action의 모든 입력값 검증을 기대하면 안 된다

actionlint는 local action의 `action.yml`을 Workflow의 `uses:`에서 참조할 때 입력 필수값·알 수 없는 입력과 메타데이터 구조를 분석한다. 유명한 외부 Action은 내장된 메타데이터 데이터베이스로 `with:` 오류를 검사하지만, 공식 문서는 **Major Version 표기(예: `actions/checkout@v4`) 중심**이라고 명시한다. 패치 버전 참조나 HEAD 참조는 지원 대상이 아니며, 전체 commit SHA 참조에도 같은 입력 검사를 기대할 수 없다.

우리 CI Lite는 공급망 통제를 위해 `actions/checkout`, `actions/setup-python` 등을 **full SHA로 고정**한다. 이 안전한 pinning 정책을 포기하지 말고, 외부 Action의 `with:` 입력 계약 검사가 제한된다는 사실을 검증 범위로 기록해야 한다.

- 근거: [Popular action inputs validation](https://github.com/rhysd/actionlint/blob/v1.7.12/docs/checks.md#popular-action-inputs-validation-at-with), [Local action inputs validation](https://github.com/rhysd/actionlint/blob/v1.7.12/docs/checks.md#local-action-inputs-validation-at-with)
- 현행 SHA 사용: [CI Lite in PR #255](../../.github/workflows/ci-lite.yml)

### Local Action의 검사 선택과 실제 수집 범위가 다르다

공식 문서에서 actionlint는 **Workflow가 실제로 참조하는 local action의 메타데이터**만 검사한다. 독립된 `action.yml`을 CLI 인자로 직접 넘겨 검사할 수 없고, Composite Action의 `runs.steps` 내용도 현재 정적 검사의 미지원 영역으로 명시되어 있다.

PR #255의 classifier는 workflow와 root/nested `action.yml`·`action.yaml` 변경 시 `actionlint=true`로 분류한다. 이 선택은 검사 실행의 트리거이지 변경된 모든 local action 파일이 actionlint에 의해 검증됐다는 뜻은 아니다. **참조되지 않은 독립 Action 정의의 보안 검증은 PR #254에서 도입한 zizmor가 담당**하며, local action 메타데이터 전체의 정적 정확성을 보장하려면 별도의 요구와 검증 설계가 필요하다.

- 근거: [Action metadata syntax validation](https://github.com/rhysd/actionlint/blob/v1.7.12/docs/checks.md#action-metadata-syntax-validation), [Classifier in PR #255](../../scripts/ci/classify_changes.py)
- 보안 검사 소유자: [PR #254](https://github.com/mols3131d/hmda-data-reliability/pull/254)

### Zizmor와의 조합은 역할 중복보다 검증 공백 보완 효과가 크다

| Validation concern | Primary owner | Boundary |
| --- | --- | --- |
| GitHub Actions 키·Expression·Job 관계 | **actionlint** | 실제 동작·모든 외부 Action 입력은 보장하지 않음 |
| 취약한 trigger, injection, token 권한, SHA pinning | **zizmor** | 현재 구성은 offline regular audit; 온라인 공급망 검사는 제외 |
| CI 변경 선택과 Python helper 실행 계약 | **pytest / Ruff / ty** | GitHub Actions 문법 전용 분석기는 아님 |
| 설치·외부 서비스·Step 실제 실행 | **GitHub Actions CI Lite** | 통과가 모든 경로 실행을 증명하지는 않음 |
| 필수 체크와 merge 차단 정책 | **GitHub Repository 설정** | YAML 정적 검사 대상이 아님 |

actionlint는 일부 script injection·credential 문제도 지적할 수 있으나 zizmor의 전용 보안 감사 범위를 대체하지 않는다. 반대로 zizmor가 통과해도 잘못된 Expression·Job 의존성이 모두 검출된다고 간주할 수 없다.

- 근거: [actionlint checks](https://github.com/rhysd/actionlint/blob/v1.7.12/docs/checks.md), [zizmor audits](https://docs.zizmor.sh/audits/), [CI ownership](../../docs/development/ci/README.md)

### PR #255는 현재 CI Lite 구조를 재사용하는 작은 도입이다

현재 [PR #255](https://github.com/mols3131d/hmda-data-reliability/pull/255)는 `main`을 기준으로 하는 별도 Draft PR이며, 다음 변경을 포함한다.

1. `classify_changes.py`의 `Scope.actionlint`와 workflow/action 경로 선택.
1. 기존 `check` Job에 조건부 **Validate GitHub Actions with actionlint** Step 추가.
1. 공식 `actionlint_1.7.12_linux_amd64.tar.gz`를 다운로드하고 고정 SHA-256을 확인한 후 전체 Workflow를 검사.
1. `tests/scripts/ci/test_ci_classifier.py`와 `test_ci_workflow.py`에서 검사 선택과 Step 연결을 보호.
1. 기존 zizmor, 별도 Python 검사, Lefthook 설정 및 `main` admission 방식을 유지.

릴리스 메타데이터의 Linux AMD64 asset digest는 다음과 일치한다.

```text
actionlint v1.7.12
actionlint_1.7.12_linux_amd64.tar.gz
sha256:8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8
```

이는 바이트 무결성을 검증하지만 다운로드 가용성, upstream 자체의 안전성 및 실제 실행의 완전성을 보장하지 않는다. 설치 방식은 새 GitHub Action과 별도 프로젝트 의존성을 추가하지 않는 대신 GitHub Release 다운로드에 의존한다.

- 근거: [PR #255 diff](https://github.com/mols3131d/hmda-data-reliability/pull/255/files), [v1.7.12 release](https://github.com/rhysd/actionlint/releases/tag/v1.7.12)

### 현재 PR의 CI 성공은 관찰됐지만 오류 탐지 범위 전부를 증명하지 않는다

2026-10-08 PR #255 head `2c6404a14945f1b7d45af3fb8818f2ad0845bbe6`에서 [CI Lite run 37760251837](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37760251837)이 **success**로 완료됐다.

| Check | Observed result | Evidence boundary |
| --- | --- | --- |
| actionlint Step | Pass | 실제 다운로드·checksum 검증 후 workflow scan 성공 |
| zizmor Step | Pass | 기존 보안 감사 실행 성공 |
| Ruff lint/format, ty | Pass | 변경 Python과 선택된 코드 검사 성공 |
| CI contract tests | **238 passed** | 변경 선택·wiring 계약 포함; 실제 오류 유형별 검증 전체는 아님 |
| Invalid Workflow negative control | **Not independently verified** | 오류를 주입했을 때 actionlint가 non-zero를 반환하는 실행 근거 없음 |
| Human approval / independent PR review | **Not verified** | 성공한 CI와 구분해야 함 |

CI가 성공했다는 것은 현재 Workflow가 이 도구 구성에서 통과했다는 뜻이다. 모든 잠재적 Expression·Action 입력·보안 위험이 검증됐다는 뜻은 아니다. 특히 **CI Lite YAML 자체가 실행 불가능할 정도로 잘못되면 그 안의 actionlint Step도 시작되지 않을 수 있다**. GitHub의 필수 체크/병합 정책과 조기 로컬 실행은 이런 자기 검증 한계를 보완하는 별도 경계다.

- 근거: [CI run](https://github.com/mols3131d/hmda-data-reliability/actions/runs/37760251837), [CI Admission Boundary](../../docs/development/ci/admission.md)

## Options

| Criterion | actionlint (preferred) | yamllint | act | Super-Linter |
| --- | --- | --- | --- | --- |
| Actions 구조·Expression 이해 | 전문 지원 | YAML 문법·스타일 위주 | 실제 실행으로 일부 확인 | 내부 구성 도구에 의존 |
| 일반 PR 검증 비용 | 낮음 | 낮음 | 상대적으로 높음 | 통합 오버헤드 |
| 기존 CI와 책임 중복 | 작음 | Actions 구조 검증에는 부족 | 실행 목적 다름 | 기존 lint stack과 중복 |
| Recommendation | **Adopt** | 현재 추가 불필요 | 디버깅 시 선택 | 현재 추가 불필요 |

`ghalint`는 Job permissions·timeout·SHA 고정 등 정책 강제가 주목적이며, `zizmor`는 보안 위험 탐지가 주목적이다. 어느 쪽도 actionlint의 정적 정확성을 직접 대체하지 않는다. 이 프로젝트에는 현재 **actionlint + zizmor + 기존 pytest/CI Lite** 구성이 합리적이다.

## Implications

- **도입 범위:** PR #255의 조건부 actionlint Step과 기존 classifier/계약 테스트 재사용을 유지하는 것이 현재 목적에 부합한다. 별도 workflow, 범용 YAML lint 체계나 wrapper 프레임워크는 필요하지 않다.
- **검사 정의:** "actionlint passed"는 Workflow 정적 검증 성공으로 기록한다. local action 전수 검사, ShellCheck·pyflakes 항상 실행, 외부 Action 전체 입력 계약 및 실제 CI 경로 검증으로 확장해 주장하지 않는다.
- **보안 구분:** SHA pinning과 zizmor 감사 정책을 actionlint 도입 때문에 약화시키지 않는다.
- **로컬 Hook:** Lefthook 통합은 초기 범위에서 제외한다. Workflow 변경이 잦아지거나 CI 실패 피드백 비용이 커질 때만 재검토한다.
- **버전 갱신:** GitHub Actions schema·context 변화로 false positive 또는 누락이 드러나면 upstream 릴리스 노트와 실제 Workflow baseline을 기준으로 고정 버전을 의도적으로 갱신한다.

## Open Questions

- **오류 주입 검증:** 잘못된 Expression, 존재하지 않는 `needs` 대상, malformed YAML, 다운로드/체크섬 실패를 실제로 재현해 실패 전파를 증명할 필요가 있는가?
  - 현재 계약 테스트 및 성공한 CI만으로는 모든 negative path가 실제 검증됐다고 볼 수 없다.
- **Local action scope:** 참조되지 않는 `action.yml` 파일의 *정적 정확성*까지 병합 조건으로 강제할 실제 요구가 있는가?
  - 필요한 경우 actionlint 선택 플래그와 실제 커버리지 차이를 명시적으로 해결해야 한다.
- **Optional script linters:** ShellCheck·pyflakes 실행을 환경 발견 방식으로 유지할 것인가, 해당 검사까지 필수 계약으로 만들 것인가?
  - 특히 Inline Python/조합 Shell 검사의 필요성과 운영 비용을 판단해야 한다.

핵심 근거는 상단의 공식 v1.7.12 문서, 실제 PR #255 코드 및 CI run에 연결했다. 이 문서는 **non-canonical research artifact**이며, PR 상태 또는 canonical CI 정책의 대체 정본이 아니다.

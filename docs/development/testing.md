---
title: "Testing Guide"
description: "Local pytest 실행 범위, marker, Git hook, PR CI와 추가 test evidence 수집 방법을 설명합니다."
categories:
  - software-engineering
tags:
  - ci
  - github-actions
  - lefthook
  - opentelemetry
  - pytest
  - testing
  - uv
---

# Testing Guide

로컬 runtime을 사용할 수 있는 사람과 agent가 pytest를 선택·실행하고 결과를 해석할 때 사용한다. Git hook과 PR CI가 어떤 검사를 실행하는지도 안내한다. 로컬 runtime을 사용할 수 없는 기여자에게 아래 명령은 필수 절차가 아니며, 병합에 필요한 repository-side 검증은 [Continuous Integration](ci/README.md)을 따른다.

테스트 시나리오와 oracle을 설계할 때는 [Test Design](test-design.md)을, `tests/` 파일을 수정하는 agent는 [`tests/AGENTS.md`](../../tests/AGENTS.md)를 참고한다.

## Start Here

변경과 직접 관련된 가장 좁은 범위부터 실행한다. 통과하면 관련 package suite로 넓히고, shared fixture·import·설정을 바꿨거나 영향 범위가 불확실할 때 전체 suite를 실행한다.

| Context | Command |
| --- | --- |
| 한 test | `uv run pytest tests/data_platform/test_sql.py::test_name` |
| test module | `uv run pytest tests/data_platform/test_sql.py` |
| domain directory | `uv run pytest tests/data_platform` |
| 현재 suite 전체 | `uv run pytest` |
| 이름으로 선택 | `uv run pytest -k "keyword"` |
| marker로 선택 | `uv run pytest -m unit` |

실패하면 먼저 원인을 조사한 뒤 같은 범위에서 다시 확인한다.

## Default Behavior

`pyproject.toml`의 pytest `addopts`는 모든 일반 실행에 필요한 correctness와 safety 기본값만 제공한다.

| Default | Meaning |
| --- | --- |
| `--timeout=60` | test 하나가 60초를 넘기면 실패시킨다. |
| `--strict-markers` | 등록되지 않은 marker를 오류로 처리한다. |
| `-m 'not memory and not stress'` | 비용이 큰 resource test를 기본 실행에서 제외한다. |

병렬 실행과 report 생성은 전역 기본값이 아니다. 넓은 suite에서 실행 시간을 줄일 때 `-n auto`를 명시하고, HTML report가 실제 evidence로 필요할 때만 `--html`을 사용한다.

## Git Hooks

Lefthook은 local Git hook을 실행할 수 있는 환경에서 빠른 feedback만 담당한다. Commit 전에는 staged file을 자동 수정하고, push 전에는 pushed Python의 정적 검사와 affected test, dbt test만 빠르게 확인한다. Hook을 사용할 수 없는 기여자에게 이를 병합 필수 검증의 유일한 실행 경로로 요구하지 않는다. `main` admission에서 CI가 소유하는 책임 경계는 [Admission Boundary](ci/admission.md)를 따른다.

| Hook | Trigger | Action |
| --- | --- | --- |
| `pre-commit` | staged Markdown | changed file rumdl fix 후 자동 stage |
| `pre-commit` | staged Python | changed file Ruff fix + format 후 자동 stage |
| `pre-push` | pushed Python | 존재하는 changed file Ruff check + format check, testmon affected tests |
| `pre-push` | pushed dbt SQL/YAML | `tests/dbt` |

`pre-commit`과 `pre-push`에는 project-wide type check나 full unit suite를 넣지 않는다. Project tool은 이미 준비된 `.venv`에서 `uv run --no-sync`로 실행해 매 hook마다 dependency sync를 확인하거나 별도 tool environment를 만드는 비용을 피한다. 삭제된 file은 fixer와 linter 대상에서 제외한다.

Python push에서는 `--testmon --testmon-forceselect`로 local `.testmondata`가 알고 있는 실제 dependency를 기준으로 affected tests를 선택한다. `.testmondata`는 Git에서 제외된 local selection cache이며 validation evidence가 아니다. Cache가 없으면 첫 testmon 실행의 선택 이점이 작고, 실행하면서 dependency data가 생성·갱신된다.

Git에는 모든 `git pull`을 실행 전에 차단하는 `pre-pull` hook이 없다. Pull 안전성은 불완전한 local hook 조합을 추가하는 대신 merge 대상 branch가 CI를 통과한 clean state라는 invariant로 관리한다.

## Pull Request CI

이 section은 `CI Lite`의 현재 validation behavior를 설명한다. Merge admission policy와 validation responsibility는 [Continuous Integration](ci/README.md)의 책임별 계약이 소유한다.

`CI Lite`는 `main` 대상 Pull Request마다 시작한다. Workflow-level path filter 없이 변경 범위에 따라 내부 step을 선택하므로 required check 자체가 누락되지 않는다. 검증 대상은 PR head 단독이 아니라 현재 base와 합쳐진 prospective merge다.

### Change Routing

- `inbox/**`는 확장자와 무관하게 CI 분류와 파일 수집에서 제외한다. Inbox-only 변경에도 workflow는 생성되지만 검증 단계는 선택하지 않는다. Markdown은 그 밖의 prospective change set에 포함된 현재 존재하는 changed file만 formatting한다. `docs/**`의 changed Markdown만 formatter 이후 `rumdl check`까지 수행하며, `docs/**` 밖의 선택된 Markdown은 lint를 merge admission 조건으로 사용하지 않는다.
- Python, `.python-version`, `pyproject.toml`, `uv.lock` 변경은 locked environment를 준비하고 changed Python file의 Ruff check + format check를 실행한다. 소스·의존성·일반 script와 영향이 불명확한 Python 변경은 project-wide `ty check`를 선택하고, CI 및 test directory 변경은 선택한 계약 범위와 changed Python file을 type-check한다.
- 명시적 `uv lock --check`는 `.python-version`, `pyproject.toml`, `uv.lock` 변경에 실행한다. Wheel 빌드는 해당 입력과 패키지 소스·리소스, root README·license 변경에 실행한다. 테스트나 CI script만 변경하면 두 검사를 선택하지 않으며 필요한 검증 환경의 `uv sync --locked`는 유지한다.
- JSON/JSONC와 TOML은 각각 Biome과 Tombi로 검증한다. 선택된 도구만 한 번의 npm 설치로 준비하며 TOML 대상이 없으면 버전 출력만을 위한 명령은 실행하지 않는다.
- CI 밖 repository Python script는 이름과 역할별 매핑 없이 전체 non-resource suite와 project-wide type 검사를 선택한다. 새 script나 rename된 entrypoint도 같은 기준을 사용한다.
- Canonical OpenSpec 변경은 capability별 테스트 매핑 없이 전체 non-resource suite와 project-wide type 검사를 선택한다. OpenSpec 구조 검증은 대상 Spec과 연결된 active Change를 선택하고, 유효한 신규 capability도 이름 등록 없이 같은 기준을 사용한다. Active Change와 archive만의 문서 변경은 기존 구조 검증 범위를 유지한다.
- CI workflow와 [`scripts/ci/`](../../scripts/ci/) helper, CI test 변경은 `tests/scripts/ci` 계약 suite를 선택한다. CI 파일이라는 이유만으로 Tach나 domain runtime suite를 선택하지 않으며 source·dependency 변경이 함께 있으면 해당 검증은 독립적으로 유지한다.
- 패키지 source·resource, dbt SQL/YAML, dependency state, root/shared test와 영향이 불명확한 Python 변경은 전체 non-resource suite를 선택한다. 수동 reverse-consumer 표를 관리하지 않는 대신 실행 범위가 넓어지는 정책이다.
- Python source, Tach configuration과 dependency state 변경은 [Tach](tooling/tach.md) runtime dependency check와 negative-path regression, source-level AST guard를 실행한다. Tach configuration 단독 변경도 locked environment를 준비한다. Boundary step이 성공한 경우에만 이후 scoped/full non-resource suite에서 AST guard 파일의 재실행을 제외한다. Boundary가 생략되거나 독립 local script에서 성공 근거가 없으면 guard를 유지한다.
- 전체 또는 선택 범위 모두 `unit`, `component`, `integration`을 유지하고 `memory`, `stress`만 제외한다. Dependency 변경의 전체 suite에 dbt·Airflow runtime smoke도 포함되므로 별도 smoke 단계는 두지 않는다. 전체 검사와 범위 검사가 겹치면 전체 suite를 한 번 실행한다.
- 전체 suite 또는 선택된 target이 3개 이상이면 xdist를 사용한다.
- Domain test 자체의 변경은 해당 test directory만 실행한다. 삭제·rename된 test도 남은 directory 계약을 선택하며, 디렉터리가 사라졌거나 root test 변경이면 전체 suite로 넓힌다.
- Lefthook 설정 변경은 `lefthook validate`로 configuration을 확인한다.
- Python dependency setup은 Python/test/dependency boundary validation이 필요할 때만 수행하고 uv cache를 재사용한다.

### Markdown Handling

CI는 prospective change set에서 현재 존재하는 Markdown만 disposable workspace에서 `rumdl fmt`로 formatting한다. 자동 수정 가능한 차이는 병합을 막지 않고 log와 step summary에 diff를 남긴다. `docs/**`의 변경 Markdown만 formatting 후 `rumdl check`를 실행하며, 남은 lint 위반은 실패한다. 일반 Inbox artifact 등 `docs/**` 밖의 Markdown은 Markdown lint를 merge admission 조건으로 사용하지 않는다.

CI는 formatting 결과를 branch에 write-back하지 않으며 별도의 post-merge Markdown autofix workflow도 두지 않는다. 로컬 runtime이 없는 기여자도 출력된 diff를 수정 근거로 사용할 수 있다.

### Local CI Steps

변경 경로 분류와 step 분기는 [`scripts/ci/`](../../scripts/ci/)에서 표준 라이브러리만 사용하는 Python script로 실행한다. [`classify_changes.py`](../../scripts/ci/classify_changes.py)는 선택 상태를 명시적으로 관리하고 [`classify_openspec.py`](../../scripts/ci/classify_openspec.py)에 전달한다. [`changed_files.py`](../../scripts/ci/changed_files.py)는 Git의 NUL 구분 출력을 사용해 파일 수집과 실패 전파를 담당한다. 두 helper는 직접 실행하지 않는다. 검사 실행은 [`run_checks.py`](../../scripts/ci/run_checks.py)의 `markdown`, `python`, `openspec`, `pytest`, `json`, `toml`, `tooling` 중 하나를 지정한다. Actions setup과 step 조건은 workflow에 유지한다. Python interpreter는 분류 전에 준비하며 프로젝트 의존성은 선택된 검증에 필요한 경우에만 설치한다. Local 실행도 필요한 도구와 locked 환경을 준비한 뒤 repository root에서 호출한다.

```bash
set -o pipefail
git -c core.quotePath=false diff --name-only <base> <head> | python3 scripts/ci/classify_changes.py --stdin
python3 scripts/ci/run_checks.py markdown
FULL_TYPE=false TYPE_TARGETS="src/hmda_reliability/review_ai tests/review_ai" python3 scripts/ci/run_checks.py python
BULK=false SPEC_TARGETS="reliability-agentic-review" python3 scripts/ci/run_checks.py openspec
FULL_TESTS=false TARGETS="tests/scripts/ci" python3 scripts/ci/run_checks.py pytest
JSON=true TOML=false python3 scripts/ci/run_checks.py tooling
```

파일을 수집하는 검사는 CI prospective merge의 `HEAD^1`과 `HEAD`를 비교하며 외부 revision 인자를 받지 않는다. 일반 local branch에서는 마지막 commit 변경만 비교하므로 전체 PR 검증으로 해석하지 않는다. 임의 범위의 분류는 위 `--stdin` 명령으로 확인하고, 해당 파일·도메인 검증은 도구나 pytest를 직접 호출한다. Git 비교 실패와 필수 도구 실패는 nonzero이며, Markdown formatter의 정보성 진단과 non-blocking diff는 docs lint 실패와 별도로 표시한다.

`pytest` 검사를 명시적으로 호출할 때는 `FULL_TESTS=true` 또는 하나 이상의 `TARGETS`가 필요하다. 전체 검사가 아니면서 대상이 비어 있거나 ASCII 공백·tab·newline만 있으면 외부 도구를 실행하지 않고 exit 1로 실패한다. CI의 tests=false 선택은 pytest step 자체를 호출하지 않는다.

`pytest` 검사의 `BOUNDARIES_CHECKED` 기본값은 false다. CI는 앞선 boundary step의 성공 여부를 전달하며, local에서 true로 지정하려면 같은 revision의 전체 boundary 검사가 먼저 성공했어야 한다.

## Select Tests

### Markers

`unit`, `component`, `integration`은 test가 연결하는 경계를 나타내는 primary level marker다. 일반 test는 requirement를 입증하는 가장 낮은 유효 경계 하나를 선택한다.

| Marker | Usage |
| --- | --- |
| `unit` | real I/O나 다른 component 연결 없이 isolated behavior를 검증할 때 |
| `component` | 하나의 component를 real local I/O 또는 tool boundary와 함께 검증할 때 |
| `integration` | 둘 이상의 project component 또는 system을 연결한 behavior를 검증할 때 |

`memory`와 `stress`는 test level을 대체하지 않는 resource marker다. 해당 contract를 검증하는 test의 primary level marker와 함께 사용할 수 있다.

| Marker | Usage |
| --- | --- |
| `memory` | 대표 input에서 process memory-budget contract를 검증할 때 |
| `stress` | 의도적으로 고비용인 worst-case resource behavior를 검증할 때 |

```bash
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m memory
uv run pytest -m stress
uv run pytest -m "not integration"
```

`memory`와 `stress`는 기본 filter에서 제외되므로 의도적으로 marker를 지정해야 한다.

### Rerun And Debug

직전 실패만 다시 실행하려면 다음 command를 사용한다.

```bash
uv run pytest --lf
```

병렬 실행 중 실패를 조사할 때는 병렬 실행을 끄고 상세 output을 확인한다.

```bash
uv run pytest -n 0 -vv -s tests/data_platform/test_sql.py
```

이 command는 빠른 기본 실행이 아니라 조사용이다. 문제를 확인한 뒤에는 원래의 focused command로 다시 검증한다.

## Additional Evidence

HTML report, coverage와 trace는 필요한 evidence가 있을 때만 수집한다.

```bash
mkdir -p artifacts
uv run pytest -n auto \
  --html=artifacts/pytest.html \
  --self-contained-html
```

```bash
uv run pytest --cov=src/hmda_reliability
```

Test별 trace가 필요하면 `--trace-per-test`를 사용한다. OTLP collector로 export할 때는 endpoint와 export option을 함께 지정한다.

```bash
uv run pytest --trace-per-test tests/data_platform/test_sql.py

OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
	uv run pytest --export-traces
```

`artifacts/pytest.html`과 같은 generated report는 local 실행 결과물이며 authored source가 아니다.

## HMDA EDA

HMDA EDA는 six-core descriptive evidence, YAML export, static chart와 controlled actual-source evidence를 검증한다. 작은 deterministic correctness suite부터 실행한다.

```bash
uv run pytest tests/hmda_data/eda/
```

실제 source의 portable JSON 및 Markdown evidence는 다음 command로 함께 생성한다.

```bash
uv run python scripts/run_actual_source.py
```

> [!WARNING]
> 이 observation은 성능 또는 OOM 안전성 보장이 아니다. source fingerprint, revision과 실행 시각이 일치하는지 확인한다.

## Review AI Evaluation

Review AI의 deterministic suite, 실제 제공자 통합 검증과 사람의 rubric 평가는 [Review AI Evaluation](review-ai-evaluation.md)을 따른다. 기본 pytest는 준비된 응답과 모의 전송으로 검증하며 실제 모델을 호출하지 않는다. 실제 단일 호출은 `hmda_reliability.review_ai.evaluation.live`, native Dataset 실험은 `hmda_reliability.review_ai.evaluation.experiment`에서 명시적으로 실행한다. Optional SDK 계약 검사는 `uv run --extra langfuse pytest tests/review_ai/evaluation`으로 실행하며 모의 HTTP와 메모리 exporter를 사용한다. SDK 미설치 시 해당 계약 검사만 생략하고 SDK-free 무결성·완비·격리 회귀는 계속 검증한다. 그 실행의 수집 완료와 진행 로그도 사람의 품질 평가를 대신하지 않는다.

이 문서는 일반 pytest 선택, CI behavior와 공통 test result 해석을 소유한다.

## Interpret Results

실행하지 않은 test는 통과했다고 기록하지 않는다. 실패가 나면 test 자체의 오류, production behavior 불일치, requirement의 빈틈, environment 문제, 현재 작업과 무관한 baseline failure를 구분한다. Test를 약화하거나 무조건 skip해 실패를 숨기지 않는다.

## Related Guides

- [Continuous Integration](ci/README.md): CI의 목적·원칙·패턴과 책임별 운영 계약
- [Test Design](test-design.md): requirement를 scenario와 oracle로 바꾸는 방법
- [`tests/AGENTS.md`](../../tests/AGENTS.md): `tests/` 파일을 수정할 때의 agent context
- [`pyproject.toml`](../../pyproject.toml): pytest correctness/safety defaults와 marker 등록
- [`lefthook.yml`](../../lefthook.yml): commit/push 실행 정책

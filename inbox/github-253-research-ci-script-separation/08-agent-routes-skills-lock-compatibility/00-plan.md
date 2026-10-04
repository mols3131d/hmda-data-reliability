---
type: plan
title: Agent Routes Bundle and Skills Lock Compatibility
description: PR 253에서 route generator를 단일 모듈 실행 경로를 가진 번들로 분리하고 실제 Skills CLI lock 형식과의 호환성을 수정하는 순서와 검증 기준을 정의한다.
---

# Agent Routes Bundle and Skills Lock Compatibility

PR [#253](https://github.com/mols3131d/hmda-data-reliability/pull/253)의 작업 branch `agent/research-ci-script-separation`에서 진행한다. 이 묶음은 [기존 CI 개선 계획](../00-plan-ci-validation-and-script-extraction.md)의 후속 작업이며, 사용자의 2026-10-04 요청에 따라 기존 범위 밖이었던 Skills lock 호환성 수정과 책임별 모듈 분리를 추가한다. 기존 실행 경로는 남기지 않는다는 후속 결정을 반영한다. 현재 원격 PR 본문의 제외 항목은 아직 수정하지 않았다.

사용자의 후속 실행 요청에 따라 로컬 구현·검증과 독립 리뷰를 완료했다. 실제 vendor 계약은 [Research](01-research.md), 구현 상태와 실행 결과는 [Report](02-report.md), 독립 리뷰와 해소한 finding은 [Review](03-review.md)에 기록한다. Local 변경을 commit하거나 push하지 않았으며 원격 CI는 새 구현을 검증하지 않았다.

## Goal

Route generator의 메타데이터 해석, 외부 source 해석과 index 생성을 책임별 모듈로 분리하고 실행 진입점을 하나로 통일한다. 이후 Skills CLI가 실제로 생성하는 lock 파일을 올바르게 처리하도록 개선한다. 구조 변경과 호환성 수정은 별도 단계로 검증하며, CI 검사를 끄거나 필요한 정보를 임의로 채워 성공시키지 않는다.

## Baseline

계획 작성 기준 local HEAD는 `cf9c1384bdd9c8c8cedc01c001f0806095ff766e`다. 이는 실제 Actions의 prospective merge SHA나 PR 본문에 기록된 head와 같다고 가정하지 않는다. 기존 미추적 Inbox 아티팩트는 그대로 보존한다.

| Evidence | Observation |
| --- | --- |
| [PR #251](https://github.com/mols3131d/hmda-data-reliability/pull/251)의 앞서 확인한 head `607a16cc32501f830bb8c89fe34728c170184e63` | 추가된 version 1 lock의 `langfuse` 항목은 `source`, `sourceType`, `computedHash`를 담고 `ref`, `skillPath`는 담지 않는다. |
| 기준 commit의 [Route generator](https://github.com/mols3131d/hmda-data-reliability/blob/cf9c1384bdd9c8c8cedc01c001f0806095ff766e/scripts/generate_agent_routes.py) | 당시 `skills_cli_dependency_sources()`가 `ref`와 `skillPath`를 필수로 요구했다. 실제 snapshot으로 `incomplete Skills CLI lock entry: langfuse`를 재현했다. |
| [기존 generator 테스트](../../../tests/scripts/test_generate_agent_routes.py) | `test_skills_cli_dependency_sources_use_locked_ref()`는 `ref`와 `skillPath`가 있는 fixture를 사용한다. 실제 version 1 lock의 호환성을 증명하지 않는다. |
| [CI classifier](../../../scripts/ci/classify_changes.sh)와 [workflow](../../../.github/workflows/ci-lite.yml) | lock 변경은 route 검증을 선택하며 workflow는 generator의 `--check`를 실행한다. CI 실행 코드 분리만으로 parser의 입력 가정은 바뀌지 않는다. |

현재 가설은 **실제 lock과 parser의 입력 계약 불일치가 실패 원인이고, 기존 fixture가 이를 검출하지 못했다**는 것이다. 가장 작은 판별 검사는 #251의 실제 lock snapshot을 입력해 현재 함수의 오류를 재현하는 것이다. 실제 vendor 계약과 CI 실패 로그까지 확인하기 전에는 해결 방식을 확정하지 않는다.

## Scope

- 구조 변경은 아래 번들로 책임을 옮기는 범위다. 구조 변경 단계에서는 lock 해석 규칙, 생성 출력과 실패 의미를 바꾸지 않는다.
- 호환성 수정의 중심은 `skills_cli_dependency_sources()`와 그 결과를 사용하는 `skill_entries()` 경로다. 실제 계약상 필요할 때만 인접한 metadata loading을 수정한다.
- 기존 generator 테스트를 재사용하되 import와 mock 대상은 실제 구현을 소유하는 모듈로 옮긴다. CLI 호출, Agent Assets 연동과 CI 경로 선택은 해당 기존 테스트로 보호한다.
- CI workflow, `scripts/agent_assets.py`, classifier와 현행 안내 문서의 실행 경로를 함께 이전한다. 과거 Inbox evidence를 새 실행 경로의 근거처럼 다시 쓰지 않는다.
- 생성 route는 호환성 수정으로 출력이 실제 달라질 때만 갱신한다. PR #251을 현재 branch에 통째로 병합하지 않는다.
- CI 검증 종류와 실패 전파는 유지한다. 애플리케이션 코드, 책임 분리와 무관한 정리, CI 재설계, 새 의존성, 권한과 branch protection 변경은 포함하지 않는다.

## Bundle

구현한 구조는 다음과 같다. 공유 경로와 error type은 `__init__.py`가 소유하며, 옛 import re-export는 제공하지 않는다.

```text
scripts/agent_routes/
	__init__.py
	__main__.py    # CLI, check/write mode and exit codes
	metadata.py    # frontmatter, JSONC and field validation
	sources.py     # external locks and remote metadata loading
	indexes.py     # local assets, index composition and JSONL output
```

저장소 루트에서 `python -m scripts.agent_routes`로 생성하고 `python -m scripts.agent_routes --check`로 검증한다. `__main__.py`가 유일한 실행 진입점이다. 기존 `scripts/generate_agent_routes.py`는 삭제하며 호환용 wrapper, 옛 import를 위한 re-export나 실행 alias를 만들지 않는다.

CI의 route step도 `uv run --no-project --with "PyYAML==6.0.3" python -m scripts.agent_routes --check`로 이전한다. Agent Assets 호출은 현재 Python interpreter와 `cwd=REPO_ROOT`를 유지하고 structured argv로 같은 모듈을 실행한다. 기존 스크립트가 제공하던 Python import 경로는 명시적으로 변경하되, 출력과 오류 계약은 보존한다.

공유 error type과 경로 설정의 위치는 module dependency를 확인해 최소한으로 정한다. 순환 import, `sys.path` 보정, 분산된 전역 설정과 함수별 파일 분리는 도입하지 않는다. 파일 수보다 책임을 찾기 쉬운 구조와 단순한 호출 흐름을 우선한다.

## Design Constraints

- Skills CLI의 실제 lock schema, `computedHash`의 의미와 설치 복원 동작을 해당 CLI 버전의 공식 source 또는 문서로 확인한다. CLI가 현재 `skills@latest`로 호출되는 점도 재현 조건에 기록한다.
- `computedHash`를 Git commit으로 취급하지 않는다. 누락된 정보를 `main`이나 추측한 `SKILL.md` 경로로 채우지 않는다.
- 원격의 현재 내용이 lock에 기록된 내용과 같은지 확인할 수 없는 경우 그 차이를 명시한다. 내용 고정이 필요한 기존 계약을 조용히 약화하지 않는다.
- 외부 Skill을 조용히 제외하거나 오류를 빈 결과로 바꾸지 않는다. lock 부재, 잘못된 lock, 미지원 형식, 외부 metadata 조회 실패를 구분하고 진단 가능한 오류를 유지한다.
- Rulesync 기반 locked source, Skill 이름 충돌 검사, 정렬, metadata 검증, `--check`의 read-only 동작과 exit code 의미를 보존한다.

### Resolved Contract

Skills CLI `1.7.0`의 version 1 lock은 `ref`와 `skillPath`를 optional로 정의한다. 구현은 GitHub commits API에서 선언된 ref 또는 실제 default revision을 해석하고, 그 commit의 archive에서 Skill 이름과 폴더 hash를 검증한 뒤 immutable raw URL을 만든다. `main`이나 Skill 경로를 추측하지 않는다. Folder hash의 경로 정렬은 vendor의 Node.js `localeCompare`를 그대로 사용하며 새 package dependency는 추가하지 않는다.

내용 불일치, 조회 실패와 이름 중복/부재는 실패다. 이 구현은 hash만으로 과거 revision을 검색·복원하지 않는다. Version과 hash가 없는 기존 explicit `ref`/`skillPath` 입력은 legacy 계약으로 유지하며, version 1 입력에는 유효한 `computedHash`가 필수다.

## Tasks

아래 1–9 단계의 로컬 작업은 완료했다. 범위 밖의 병행 문서 변경으로 관련 확장 suite에는 실패 두 건이 남으며, 이번 구현의 독립 리뷰는 최종 상태에서 `clear`다. 검증 범위와 delivery 제한은 [Report](02-report.md)를 따른다.

1. #251의 최신 lock과 관련 CI 실패 로그를 다시 확인한다. Skills CLI의 lock 작성·읽기 코드를 좁게 조사해 버전, source 표현, hash의 대상, Skill 경로와 revision을 얻을 수 있는 수단을 기록한다.
1. 실제 lock snapshot으로 현재 오류를 재현한다. 공급자 계약 확인 후 성공 시 route의 출처와 내용이 무엇에 고정되어야 하는지 정하고, 필요한 정보가 없을 때의 실패 조건을 결정한다.
1. 구조 변경 전 기존 generator 테스트와 통제된 입력의 생성 출력, check 동작과 오류를 baseline으로 확보한다. 이 단계의 기존 lock 오류는 구조 변경으로 우연히 해결하거나 숨기지 않는다.
1. 책임별 모듈과 새 실행 진입점으로 이전하고 기존 스크립트를 삭제한다. 같은 변경에서 CI, Agent Assets 호출, classifier path mapping, 테스트 import와 현행 문서 참조를 옮긴다. 새 번들 내부 파일만 바뀌어도 route 검증과 관련 테스트가 선택되게 한다.
1. 호환성 수정 전에 구조 변경만 검증한다. 새 모듈 실행과 CI의 no-project 호출에서 import가 성공하고 baseline의 출력, check/write 동작과 실패 전파가 유지되는지 확인한다. 옛 실행 경로가 삭제됐고 active caller가 남지 않았는지도 확인한다.
1. 계약에 맞는 회귀 테스트를 기존 모듈에 추가한다. 먼저 기존 코드에서 collection이 성공하고 기대 behavior에서 실패하는지 확인한다. 원격 조회는 통제된 loader 또는 fake boundary로 대체하고 실제 network에 의존하지 않는다.
1. parser와 필요한 인접 경로만 최소 수정한다. 정보 해석 규칙을 단순히 완화하는 대신 확인된 vendor 형식과 출처 계약에 맞춘다. 수정 직후 같은 focused test를 실행하고 local defect만 먼저 보완한다.
1. generator의 기존 테스트 전체와 필요한 인접 계약 테스트를 실행한다. 실제 파일을 사용하는 격리된 환경에서 생성과 `--check`를 함께 확인하며 기존 작업 트리에 외부 Skills를 설치하지 않는다.
1. 실제 lock 시나리오의 재현 결과, static check, route 검증과 남은 한계를 기록한다. 구현된 exact revision을 기준으로 독립 리뷰를 수행하고, 수정 후에는 해당 변경을 다시 검증한다.

## Acceptance

| Scenario | Expected Evidence |
| --- | --- |
| 책임별 번들 분리 | 메타데이터, source와 index 책임이 분리되고 통제된 입력의 기존 출력과 오류가 유지된다. 구조 변경과 lock 수정의 근거를 구분한다. |
| 단일 실행 진입점 | 모듈 실행으로 생성과 check를 수행한다. 기존 스크립트는 존재하지 않으며 wrapper, 옛 import alias와 active caller가 남지 않는다. |
| 새 module path 변경 | 번들 내부 Python 파일 변경도 route 검증과 관련 focused test를 선택한다. unrelated full-suite fallback에만 기대지 않는다. |
| 실제 version 1 lock 입력 | 누락 필드 때문에 무조건 실패하지 않으며, 확인된 출처·내용 계약에 맞는 route를 생성한다. 필요한 추가 조건은 조사 결과와 테스트에 명시한다. |
| hash와 source 정보 | hash의 실제 의미를 보존하고, 확인하지 않은 branch나 파일 경로로 내용을 대체하지 않는다. |
| lock 부재 또는 잘못된 입력 | 부재 시 기존 동작을 유지하고 malformed entry, 미지원 source, 필요한 정보 부족은 명확하게 실패한다. |
| metadata 조회와 이름 충돌 | 조회 실패와 다른 이름의 Skill을 성공으로 숨기지 않고, 로컬·Rulesync·Skills CLI 간 충돌을 계속 검출한다. |
| 기존 locked-ref 입력 | 유지 여부를 명시적으로 결정하고 그 결정을 테스트한다. 확인된 사용 계약을 설명 없이 제거하지 않는다. |
| 생성과 `--check` | 같은 입력에서 출력이 결정적이다. 일치 시 0, drift 시 1, 입력·조회 오류 시 2를 유지하며 check 모드는 파일을 쓰지 않는다. |
| CI와 bootstrap | 새 모듈 호출로 생성·검증하고 실제 lock을 포함한 route 검증 경로가 통과한다. 기존 실행 순서와 실패 전파를 유지하며 route 검사를 끄지 않는다. |

## Validation

구현 검증은 [Test Design](../../../docs/development/test-design.md)과 [Testing Guide](../../../docs/development/testing.md)를 따른다. 구조 변경에서는 baseline과 새 모듈의 동작을 비교하고 CLI, Agent Assets 호출과 classifier의 기존 계약 테스트를 실행한다. 호환성 수정에서는 가장 좁은 회귀 테스트부터 시작해 기존 generator 테스트 전체로 넓힌다. 변경된 파일에만 Ruff 등 해당 static check를 적용하며 불필요한 전체 suite 실행은 추가하지 않는다.

모듈 CLI와 CI의 no-project 호출은 실제 subprocess와 격리된 repository 입력으로 확인한다. Python path 주입이나 설치된 애플리케이션 package에 우연히 의존하는 import를 통과 근거로 삼지 않는다. 실행 경로 이전 후 현행 code, config, test와 안내 문서에 옛 경로가 남지 않았는지 검사한다. Baseline 설명과 과거 evidence의 옛 경로 기록은 이 검사에서 구분한다.

lock snapshot을 임시 입력으로 사용하는 generator 검증과 실제 원격 CI 실행은 별도 근거다. PR #253 branch에 lock이 없어서 통과한 결과를 #251과의 호환성 증거로 제시하지 않는다. 원격 검증이 불가능하면 미검증 범위를 남긴다.

계획서와 후속 Markdown 아티팩트에는 Inbox validator와 repository 설정을 따르는 `rumdl check`를 적용한다. 테스트 결과나 리뷰 통과는 실제 실행·확인한 revision에 대해서만 기록한다.

## Artifacts

이 하위 디렉터리에 작업 산출물을 모은다. 필요한 시점에만 파일을 추가하며 빈 placeholder는 만들지 않는다.

- `00-plan.md`: 현재 계획과 범위, 완료 기준. 조사 결과로 중요한 결정이 바뀌면 갱신한다.
- `01-research.md`: 확인된 vendor 계약, 오류 재현, 분리할 책임과 최소 수정 방향.
- `02-report.md`: 구현 요약, exact revision, 실행한 검증과 남은 제한.
- `03-review.md`: 구현 상태에 대한 독립 리뷰와 필요한 후속 조치.

## Delivery

구현은 PR #253의 같은 branch와 이 아티팩트 묶음에서 진행한다. commit, push, PR 본문 갱신, Ready 전환과 merge는 별도 요청 없이 수행하지 않는다. 향후 PR 본문을 갱신할 때는 기존 Skills lock 제외 항목과 실제 추가 scope를 일치시킨다. 병행 중인 07번 CI 문서 작업은 이번 08번 구현의 소유 범위가 아니며 변경을 보존한다.

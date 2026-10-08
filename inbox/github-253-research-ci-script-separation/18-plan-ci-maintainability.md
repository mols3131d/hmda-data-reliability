---
type: plan
title: "CI Maintainability Improvements"
description: "PR 253의 CI 선택 규칙과 테스트 중복 조사 결과 및 두 단계의 유지보수성 개선을 정리합니다."
tags:
  - ci
  - testing
  - maintainability
---

# CI Maintainability Improvements

2026-10-07 조사에 따른 PR 253 작업 기록이다. 현재 owning branch는 `agent/research-ci-script-separation`이다. 이 문서는 non-canonical이며 검증 선택 계약은 [Change Impact](../../docs/development/ci/change-impact.md), 실행 계약은 [Testing Guide](../../docs/development/testing.md#pull-request-ci)가 소유한다.

## Findings

| Priority | Evidence | Improvement |
| --- | --- | --- |
| 1 | [분류기](../../scripts/ci/classify_changes.py)는 Biome·Tombi·bootstrap 변경만으로 JSON/TOML을 선택하지만, [실행기](../../scripts/ci/run_checks.py)는 해당 changed file이 없으면 검사하지 않는다. wrapper 단독 변경의 플래그 활성화를 CLI로 재현했다. | 설치만 유발하는 Python 파일별 예외를 제거한다. 실제 JSON/TOML changed file 선택과 전체 Python 검증은 유지한다. |
| 2 | [라우트 분류 테스트](../../tests/scripts/ci/test_ci_classifier.py)는 실제 YAML을 읽지 않고 workflow 조건을 다시 계산한다. | 분류 출력은 해당 테스트가, 실제 setup·sync·검사 조건은 [workflow 테스트](../../tests/scripts/ci/test_ci_workflow.py)가 검증한다. |
| 3 | `FULL_TESTS=false`, `TARGETS=""`로 pytest runner를 호출하면 실행 없이 exit 0이다. 현재 분류기는 tests=true일 때 범위를 채우므로 현재 누락 결함으로 확인된 것은 아니다. | 별도 계약 강화 단계에서 명시적으로 호출된 빈 pytest 선택을 실패시킨다. 기존 성공 테스트와 실행 문서도 함께 변경한다. |
| 4 | pytest·step 테스트의 명령 assertion 4곳이 `[10:]` 위치에 의존한다. | 공통 명령은 대표 테스트에서 보호하고 나머지는 대상·marker·병렬 옵션의 의미를 검사한다. Production 상수를 oracle로 재사용하지 않는다. |
| 5 | 분류기 테스트 3개 파일의 unit-labelled 함수 37개가 실제 CLI subprocess를 사용한다. 일부는 파일시스템 fixture도 사용한다. | marker를 component로 바로잡고 동일 정책의 사례는 신규·삭제·rename·혼합 등 구별되는 실패 조건 중심으로 정리한다. |

wrapper의 argv·도구·cwd·종료 상태는 기존 [전달 계약 테스트](../../tests/scripts/test_tool_wrappers.py)가 보호한다. 실제 Node 도구 실행이나 설치 시간 절감량을 측정한 근거는 없다.

## Current Scope

첫 단계는 우선순위 1·2를 구현했다.

- Python wrapper 이름으로 JSON/TOML을 켜는 예외를 삭제한다.
- wrapper 단독 변경은 전체 non-resource suite와 project-wide type 검사를 유지한다.
- 실제 JSON/TOML 변경이 혼합되면 필요한 Node 도구와 해당 검사를 계속 선택한다.
- 라우트 분류 테스트에서 재계산한 workflow 조건을 제거한다.
- 실제 YAML의 uv setup, dependency sync, Python·test·route 단계 조건으로 라우트 격리를 검증한다.

사용자의 후속 요청에 따라 두 번째 단계는 우선순위 3·4·5를 구현한다.

- 전체 검사도 대상도 없는 명시적 pytest 호출은 도구 실행 전에 exit 1로 실패시킨다. ASCII 공백만 있는 선택도 같은 계약을 적용한다.
- `[10:]` assertion을 test-local literal 명령 또는 옵션 이름 기준으로 바꾼다. Pytest 선택·boundary 검사는 production과 독립적인 전체 argv oracle을 유지한다.
- 실제 CLI subprocess를 사용하는 분류기 테스트 37개의 unit marker를 component로 바로잡는다.
- 파일명만 다른 반복 사례를 줄이되 신규·삭제·rename·support·혼합 변경의 구별되는 계약은 유지한다.

새 설정 파일, 범용 규칙 엔진, Actions 표현식 해석기, 패키징 설정 parser, dependency 추가와 commit·push는 두 단계 모두 포함하지 않는다.

## Acceptance

1. Biome·Tombi·bootstrap 단독 변경은 json=false, toml=false이며 전체 Python 검증을 유지한다.
1. 현재 존재하는 JSON/TOML 변경이 섞이면 해당 selector가 true이고 도구 설치·검사 경로가 유지된다.
1. 라우트 전용 변경에서 실제 YAML 조건은 uv setup·route 검사를 선택하고 project dependency sync·Python·pytest를 선택하지 않는다.
1. 실제 YAML 조건을 의도적으로 잘못 바꾼 음성 대조에서 새 workflow assertion이 실패한다.
1. 관련 CI·wrapper 테스트, Ruff·format·type 검사와 독립 리뷰를 통과한다.
1. 빈 선택·ASCII 공백 선택은 boundary 성공 상태와 무관하게 pytest 도구 호출 없이 실패하고, 전체·범위 실행은 기존 계약을 유지한다.
1. 명령 assertion 4곳에서 고정 위치 `10`을 제거하고 명령 전달의 독립 oracle을 유지한다.
1. 세 분류기 파일의 모든 테스트가 component 선택에서 실행되고 unit 선택에서는 제외된다.

## First Stage

- [x] 현재 코드 조사와 CLI 재현을 완료했다.
- [x] 첫 구현 범위와 후속 항목을 분리했다.
- [x] 우선순위 1·2를 구현했다.
- [x] 집중 검증과 전체 CI 계약 검증을 완료했다.
- [x] 현재 변경의 독립 리뷰를 완료했다.

집중 테스트 149개가 통과했다. 전체 CI 계약과 기존 wrapper 전달 계약은 합계 225개가 통과했다. Ruff check, format check, CI source·test의 ty check와 diff whitespace 검사도 통과했다. 실제 YAML의 sync·pytest 조건을 routes=true로, route 조건을 python=true로 바꾼 메모리상 음성 대조는 모두 assertion 실패로 탐지했다. YAML 파일은 변경하지 않았다.

전체 application suite, 실제 Node 도구 실행과 remote Actions는 이번 단계에서 실행하지 않았다. 전체 non-resource suite의 선택 계약은 유지했지만 실제 domain runtime 통과를 주장하지 않는다. 변경 직전 스냅샷과 현재 네 Python 파일을 대조한 quality·adversarial 독립 리뷰의 최종 assessment는 clear다. 리뷰어는 보고된 실행 결과를 재실행하지 않았으며 필수 수정 사항은 없었다.

## Second Stage

- [x] 빈 pytest 선택 실패 계약과 실행 가이드를 반영했다.
- [x] 고정 위치 명령 assertion 4곳을 정리하고 리뷰에서 발견한 추가 제외 옵션 탐지 누락을 보완했다.
- [x] unit marker 37개를 component로 변경하고 중복 파일명 사례를 줄였다.
- [x] 집중 검증과 전체 CI·wrapper 계약 검증을 완료했다.
- [x] 현재 후속 변경의 독립 리뷰를 완료했다.

빈 선택 변경 직후 pytest 계약 25개, 명령·사례 정리 직후 관련 계약 152개가 통과했다. 세 분류기 파일의 component 선택은 97개가 통과했고 unit 선택은 97개 모두 deselect했다. 최종 CI·wrapper 계약은 합계 211개가 통과했으며 Ruff check와 ty check도 통과했다. 테스트 수 변화는 중복 파일명 사례 축소와 빈 선택 실패 사례 추가에 따른 것으로 검증 범위를 줄이는 CI 선택 정책 변경이 아니다.

첫 후속 리뷰는 boundary-confirmed 명령의 꼬리 앞에 예상하지 않은 제외 옵션이 추가되어도 통과하는 oracle 약화를 지적했다. Test-local literal prefix로 전체 argv를 검사하도록 보완한 뒤 pytest 계약 25개가 다시 통과했다. Guard 앞에 `--ignore=tests/runtime_ai`를 메모리상 주입한 음성 대조에서는 scoped·parallel-scoped·full-tests의 boundary-confirmed 3개 경우가 모두 assertion 실패로 탐지했다. 나머지 6개 경우는 통과했다. 소스나 fixture 파일을 변경하지 않았다.

보완 후 최종 CI·wrapper 계약 211개와 Ruff check·format check·ty check·rumdl·diff whitespace 검사가 다시 통과했다. 두 관점의 재리뷰는 후속 단계 직전 기준본과 현재 8개 파일을 비교해 최종 assessment clear, 필수 수정 사항 없음으로 완료했다. 리뷰어는 실행 결과를 재실행하지 않았고 실제 YAML 불변 여부는 기준본 사본이 없어 독립 확인하지 않았다. Workflow YAML은 이번 작업에서 편집하지 않았다.

전체 application suite, 실제 Node 도구 실행과 remote Actions는 후속 단계에서도 실행하지 않았다. 최종 clear는 지정된 8개 파일의 독립 검토 결과이며 이 미실행 검증을 대신하지 않는다.

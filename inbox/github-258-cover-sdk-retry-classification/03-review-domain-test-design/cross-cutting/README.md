---
type: review
title: Common Support Test Design Review
description: CI·bootstrap·도구·agent projection·문서 검증·architecture guard·telemetry 테스트의 설계와 한계를 검토합니다.
---

# Common Support Test Design Review

> [!NOTE]
> 실제 Git·CLI·파일 상태와 고정 argv/exit oracle은 강하다. CI 진입·불확실한 OpenSpec 범위, 일부 public entrypoint·artifact validation의 공백이 남는다.

- **Target**: 제품 domain을 지원하는 공통 개발·검증 도구.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: scripts·CI·root telemetry의 test 18개·support 5개 전체를 두 관점 독립 검토. Supporting source·설정은 관련 경로 대조.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| S1 | Major | 불확실한 active Change inventory에서 OpenSpec 범위가 넓어지지 않음 | [CI C1](ci.md#c1--major-uncertain-openspec-inventory) |
| S2 | Major | workflow 생성·prospective merge 정책을 test가 보호하지 못함 | [CI C2](ci.md#c2--major-workflow-entry-and-revision) |
| S3 | Minor | bootstrap `main()`의 실패 중단을 우회해 검사 | public entrypoint에서 nonzero·후속 미실행 검사 |
| S4 | Minor | Inbox comment-only null·빈 필수 값이 validator 통과 | 실제 YAML 빈 값의 negative oracle 추가 |
| S5 | Minor | Rule opt-out의 독립 기대값이 없음 | enabled/disabled fixture의 literal rows 비교 |
| S6 | Minor | xdist test가 주장한 per-test tracing을 선택·관찰하지 않음 | claim을 compatibility로 좁히거나 worker span 확인 |

S1·S4는 현재 실행의 반례다. S2·S3은 격리 mutant의 기존 test 통과와 새 witness 실패로 확인했다. S5·S6은 정적 설계 공백이며 현재 source가 잘못됐다고 재현한 결과가 아니다. 모두 후속 제안이다.

## Subdomain Assessment

| Area | Scenario And Independent Oracle | Boundary And Limit |
| --- | --- | --- |
| CI | missing test dir·invalid Git comparison·canonical pairing·guard dedup·명령 실패 전파 | 실제 Git/CLI; 외부 check 도구는 주로 argv/exit stub. [별도 CI 리뷰](ci.md) |
| Bootstrap/commands | action별 exact command/order/cwd, 명령 실행 경계 | 외부 설치는 fake; public main은 S3 |
| Clean | safe target만 삭제·protected data 보존, 확인 후 tracked index 재조회, ambient Git override 격리 | 실제 파일 삭제/보존; 단순 mock count가 아님 |
| Tool wrappers | 올바른 binary/args/cwd·failure propagation | 현재 플랫폼 경계; Windows 실제 npm/Node case skip |
| Agent projections/routes | module entrypoint·순서·실패, lock-bound URL/hash/collision, incomplete HTTP read에서 무작성 | HTTP/upstream fixture; host/model의 실제 routing·권한 증거 아님 |
| Event logging | sanitized field만 기록, context·error 분리 | 실제 ledger 출력; 모델 행동 품질을 측정하지 않음 |
| Docs/Inbox | exact TSV·frontmatter descriptions·drift check 무변경·bundle root 연결 | 의미 품질 평가 아님; scalar 누락은 S4 |
| Tach/dependency | 실제 금지 import 네 방향과 type-only·root 허용·unowned source 실패 | native graph와 별도 AST guard 책임을 구분; dynamic import 전체 증명 아님 |
| Telemetry | option 등록·serial console fixture/test/run span·xdist subprocess smoke | worker per-test span은 S6 |

근거는 [bootstrap](../../../../tests/scripts/test_bootstrap.py), [commands](../../../../tests/scripts/test_commands.py), [clean](../../../../tests/scripts/test_clean.py), [wrappers](../../../../tests/scripts/test_tool_wrappers.py), [agent assets](../../../../tests/scripts/test_agent_assets.py), [routes](../../../../tests/scripts/test_generate_agent_routes.py), [event log](../../../../tests/scripts/test_log_agent_event.py), [docs index](../../../../tests/scripts/test_generate_docs_indexes.py), [Inbox](../../../../tests/scripts/test_validate_inbox_artifacts.py), [Tach](../../../../tests/scripts/test_tach.py), [Tach config](../../../../tests/scripts/test_tach_config.py), [telemetry](../../../../tests/test_pytest_opentelemetry.py)다.

### S3 — Minor: Bootstrap Public Entrypoint

#### Locations: S3

- [test_bootstrap.py](../../../../tests/scripts/test_bootstrap.py)
  - `_steps()`를 직접 순회하고 모든 fake command가 0을 반환한다.
- [bootstrap.py](../../../../scripts/bootstrap.py)
  - `main()`이 실제 nonzero 중단·exit code를 소유한다.

#### Evidence: S3

현재 main은 정상이다. Nonzero 즉시 반환을 제거한 격리 mutant도 기존 bootstrap+workflow **58개를 통과**했다. [E1 witness](../validation.md#e1-bootstrap-and-workflow-negative-controls)는 main이 17 대신 0을 반환하고 후속 step까지 실행하는 회귀를 검출했다.

#### Action: S3

실제 main에 실패하는 선행 step을 주입해 원래 종료 코드와 후속 호출 부재를 함께 검사한다. 실제 설치를 실행할 필요는 없다.

### S4 — Minor: Empty YAML Scalar

#### Locations: S4

- [test_validate_inbox_artifacts.py](../../../../tests/scripts/test_validate_inbox_artifacts.py)
  - helper는 quoted scalar, negative case는 주로 missing field다.
- [validate_inbox_artifacts.py](../../../../scripts/validate_inbox_artifacts.py)
  - raw text의 `_has_value`가 inline comment를 값으로 취급한다.

#### Evidence: S4

Lead의 actual validator probe에서 `description: # TODO`와 `description: "" # TODO` 모두 `errors=[]`였다. Required nonempty 계약을 놓치지만 validator는 CI 제외이므로 local artifact 범위다. 단순 missing·empty 값 거부는 이미 보호된다.

#### Action: S4

Comment-only null·comment가 붙은 빈 scalar를 거부하는 사례를 추가한다. 문자열 안의 유효한 `#`는 보존한다. 이 보고서 묶음은 native 검사 외에 실제 YAML parser의 frontmatter 검사도 수행한다.

### S5 — Minor: Rule Opt-Out Oracle

#### Locations: S5

- [test_generate_agent_routes.py](../../../../tests/scripts/test_generate_agent_routes.py)
  - 709행 이후의 Rule fixture는 enabled Rule만 포함한다.
- [indexes.py](../../../../scripts/agent_routes/indexes.py)
  - `rule_entries`의 `route: false`·root 제외는 현재 정상이다.
- [mermaid Rule](../../../../.rulesync/rules/mermaid.md)
  - 실제 `route: false` 사용처.

#### Evidence: S5

Generator만 변경하면 committed index의 `--check`가 drift를 감지한다. 하지만 generator와 index를 함께 재생성하면 write/check가 같은 알고리즘을 사용한다. Opt-out 제거를 독립적으로 검출할 enabled/disabled literal expected rows가 없다. Mutant나 host/model routing은 실행하지 않았다.

#### Action: S5

작은 local Rule fixture에 enabled·disabled·root를 넣고 index의 exact 포함·제외 rows를 비교한다.

### S6 — Minor: Xdist Tracing Claim

#### Locations: S6

- [test_pytest_opentelemetry.py](../../../../tests/test_pytest_opentelemetry.py)
  - 67행 docstring은 worker per-test tracing을 주장하나 args는 `-n 2`, assertion은 passed 1뿐이다.

#### Evidence: S6

설치된 plugin의 per-test mode는 `--trace-per-test`에서 선택되지만 이 case는 flag·worker span 관측이 없다. Serial export case는 실제 span 속성을 검사하므로 그 보호를 무시하지 않는다. 현재 xdist case도 compatibility smoke로는 유효하다.

#### Action: S6

필요한 claim이 compatibility라면 설명 범위를 정확히 좁힌다. Worker per-test tracing을 보장해야 한다면 mode를 명시하고 로컬 sink의 span을 관찰한다. 외부 exporter·네트워크 호출은 요구하지 않는다.

## Placeholder Packages

[configs](../../../../src/hmda_reliability/configs/__init__.py)·[shared](../../../../src/hmda_reliability/shared/__init__.py)·[utils](../../../../src/hmda_reliability/utils/__init__.py)는 docstring placeholder다. 별도 executable contract의 테스트가 없다는 결함으로 세지 않는다. 실제 config 변환은 [Orchestration](../orchestration/README.md)에 매핑했다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 full-body·support 검토 | Batch E 두 관점 23/23, 미검토 target 없음 |
| ✅ Pass | 현재 정상 suite | [954 passed / 2 skipped](../validation.md#test-execution), 전체 기준 |
| ❌ Fail | 현재 validator·selector 계약 probe | Lead 직접 실행, caller 실행과 구분 |
| ✅ Pass | 격리 negative control 구별력 | caller baseline 58+2 통과, 3 mutant 기존 58 통과·witness 각 1개 실패 |
| ⚪ Not Verified | route opt-out mutant·worker per-test tracing | 정적 분석이며 실행하지 않음 |

## Risks And Limits

실제 hosted Actions·npm 설치·OpenSpec CLI validation·host/model 성능은 실행하지 않았다. 알려진 Windows·audit-cache skip은 [실행 근거](../validation.md#test-execution)에 남겼다. Local Skill 이름 충돌·bundle README 부재는 명시적 계약을 확보하지 못해 finding에서 제외했다.

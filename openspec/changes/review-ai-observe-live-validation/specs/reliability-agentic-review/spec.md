---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-agentic-review
description: 평가 모듈의 실제 provider 검증 진입점과 안전한 단계·대기 진행 표시를 정의합니다.
---

## ADDED Requirements

### Requirement: Evaluation-owned live validation entrypoint

실제 provider로 합성 사례를 검증하는 CLI는 `python -m hmda_reliability.review_ai.evaluation.live`로 제공해야 한다(SHALL). 기존 `scripts/run_agentic_review_live.py`와 그 호환 wrapper를 제공해서는 안 된다(MUST NOT). 검증은 실제 데이터 적재 없이 현재 한국어 세 단계·코드 JSON 취합을 사용하고 명시적 live opt-in·설정 검증·시간 예산·원문 보존·provenance 검사와 기존 종료 의미를 유지해야 한다(SHALL).

진행 표시는 표준 오류에만 기록하고 표준 출력의 최종 JSON shape와 의미를 변경해서는 안 된다(MUST NOT). 모듈 import 또는 비활성 실행만으로 provider를 호출해서는 안 된다(MUST NOT). 실행 완료와 진행 표시는 실제 출력의 정확성·한국어 준수·사람의 rubric 평가를 대신해서는 안 된다(MUST NOT).

자동 revision은 실제 import한 모듈이 속한 source checkout의 HEAD와 clean tracked tree를 검증해야 하며 caller의 다른 working directory를 그 source로 기록해서는 안 된다(MUST NOT). 배포 설치처럼 해당 checkout을 입증할 수 없으면 auto를 거부하고 명시적 revision을 요구해야 한다(SHALL).

#### Scenario: Module execution preserves the live result

- **WHEN** 사용자가 live opt-in과 유효 설정으로 새 모듈을 실행할 때
- **THEN** 현재 합성 사례의 세 단계 실행·저장·provenance 검증을 수행하고 기존 최종 JSON과 종료 의미를 유지해야 한다(SHALL).
- **AND** 기존 script 또는 wrapper를 실행 경로로 남겨서는 안 된다(MUST NOT).

#### Scenario: Import and disabled execution do not call a provider

- **WHEN** 모듈을 import하거나 live opt-in 없이 실행할 때
- **THEN** provider 호출과 heartbeat 실행을 시작해서는 안 된다(MUST NOT).

#### Scenario: Automatic revision identifies the loaded source checkout

- **WHEN** source checkout의 모듈을 다른 working directory에서 auto revision으로 실행할 때
- **THEN** 실제 모듈 소유 checkout의 HEAD·clean tree만 사용하고 다른 repository의 revision을 기록해서는 안 된다(MUST NOT).

#### Scenario: Installed code requires explicit revision provenance

- **WHEN** source checkout을 입증할 수 없는 배포 모듈에서 auto revision을 요청할 때
- **THEN** provider 호출 전에 정제된 설정 오류로 종료하고 명시적 revision을 요구해야 한다(SHALL).

### Requirement: Safe live stage progress

Live 검증은 표준 오류에 현재 단계의 한국어 이름·시작·완료 또는 실패·단계 경과 시간을 표시해야 한다(SHALL). 완료·실패 표시는 원문과 checkpoint 저장을 포함한 실제 단계 결과에 맞춰야 하며 provider 반환만으로 단계 완료를 표시해서는 안 된다(MUST NOT).

동기 provider 호출의 로컬 대기 중에는 기본 5초 간격으로 해당 단계와 로컬 경과 시간을 표시해야 한다(SHALL). 이 대기에는 logical call 내부의 bounded retry·backoff가 포함된다. 대기 표시는 provider 내부 진행률·생성 토큰 수·성공 예상이나 원격 추론 완료를 뜻한다고 표현해서는 안 된다(MUST NOT). Provider 호출 전 준비·후속 저장 및 실행 종료 후에는 provider 대기 heartbeat를 표시해서는 안 된다(MUST NOT).

진행 자료는 고정 단계·사건·상태와 로컬 경과 시간으로 한정해야 한다(SHALL). 원문·prompt·API key·사용자 설정값·개인 절대 경로·예외 문구를 진행 로그에 포함해서는 안 된다(MUST NOT). 일반 API는 관찰자를 명시하지 않으면 콘솔 출력과 heartbeat를 생성해서는 안 되며(MUST NOT), 관찰자 실패가 실행 결과·원문·provenance 보존을 변경해서는 안 된다(MUST NOT).

Provider 정상 반환·typed failure·예상하지 못한 예외·중단의 모든 종료 경로에서 대기 timer와 진행 자원을 정리하고 종료 후 로그가 계속 나와서는 안 된다(MUST NOT).

#### Scenario: Stage progress follows retained results

- **WHEN** 정상 단계가 시작되고 원문과 checkpoint 저장을 마칠 때
- **THEN** 한국어 단계 시작과 경과 시간을 포함한 완료를 순서대로 표시해야 한다(SHALL).
- **AND** provider 응답 이후 저장이 실패하면 완료 대신 실패를 표시해야 한다(SHALL).

#### Scenario: Heartbeats cover only synchronous provider waiting

- **WHEN** provider logical call이 기본 간격을 넘겨 계속 대기 중일 때
- **THEN** 5초마다 로컬 대기 시간을 표시하고 provider 호출 종료 시 heartbeat를 중단해야 한다(SHALL).
- **AND** 출력에 provider 내부 진행률이나 완료 예측을 포함해서는 안 된다(MUST NOT).

#### Scenario: Failed stage stops subsequent progress

- **WHEN** provider·응답 수집·시간 예산 또는 checkpoint 저장으로 단계가 실패할 때
- **THEN** 해당 단계 실패와 경과 시간을 표시하고 호출하지 않은 후속 단계의 시작·완료를 표시해서는 안 된다(MUST NOT).

#### Scenario: Unexpected exits release progress resources

- **WHEN** provider 대기 중 예외 또는 중단으로 제어가 빠져나갈 때
- **THEN** timer를 중지·정리하고 원문·예외 문구를 진행 로그에 추가하거나 종료 뒤 heartbeat를 출력해서는 안 된다(MUST NOT).

#### Scenario: Progress cannot leak input or alter evidence

- **WHEN** 원문·설정·오류에 민감한 문자열이 있거나 관찰자 자체가 실패할 때
- **THEN** 진행 로그는 고정 자료와 시간만 표시하고 관찰 실패로 provider 결과나 저장 근거를 바꾸어서는 안 된다(MUST NOT).

#### Scenario: Ordinary API calls stay silent

- **WHEN** 일반 검토 API를 관찰자 없이 실행할 때
- **THEN** 기존 결과와 저장 경계를 유지하고 단계 로그와 heartbeat 자원을 만들지 않아야 한다(SHALL).

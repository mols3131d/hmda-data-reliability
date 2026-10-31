---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-agentic-review
description: 단계 실행 예산과 전송 timeout의 관찰 가능한 계약을 정의합니다.
---

## ADDED Requirements

### Requirement: Staged execution time budgets

시스템은 유한하고 양수인 연결·읽기 대기 제한과 별도의 단계·전체 실행 시간 예산을 설정할 수 있어야 한다(SHALL). 기존 timeout 설정은 세부 전송 설정의 fallback으로 유지하고 명시적 세부 설정이 우선해야 한다(SHALL). 새 live staged 시작값과 기존 환경 변수의 우선순위를 문서화해야 한다(SHALL).

시스템은 monotonic 시간으로 예산을 확인하고 남은 예산을 넘는 후속 단계·전송 재시도·백오프를 시작해서는 안 된다(MUST NOT). 각 요청의 전송 대기 제한은 남은 예산 이하로 줄여야 한다(SHALL). 예산을 넘겨 반환된 응답을 완료 답변으로 채택해서는 안 되며(MUST NOT), 반환된 bounded 원문은 예산 실패 판정 전에 저장해야 한다(SHALL). 진행 중 동기 호출의 강제 취소나 원격 추론 종료를 보장한다고 표현해서는 안 된다(MUST NOT).

전송 timeout, 연결 오류, 단계 예산과 전체 예산 소진을 구분하고 실제 시도 수·경과 시간·적용 설정 및 이미 저장한 원문·checkpoint를 남겨야 한다(SHALL). 새 설정이 없는 과거 record를 읽을 수 있어야 하며(SHALL), 과거 미기록 값을 현재 기본값으로 소급 추정해서는 안 된다(MUST NOT). 시간 설정은 canonical input이나 프롬프트 내용을 바꾸어서는 안 된다(MUST NOT).

#### Scenario: Explicit phase settings override legacy fallback

- **WHEN** 기존 timeout과 새 연결·읽기 대기 설정을 함께 제공할 때
- **THEN** 명시된 각 세부 설정이 우선하고 생략된 전송 설정만 기존 timeout을 사용해야 한다(SHALL).
- **AND** 음수·0·비유한 예산은 provider 호출 전에 거부해야 한다(SHALL).

#### Scenario: Retries stop at the remaining budget

- **WHEN** 전송 실패 후 재시도 또는 백오프를 위한 시간이 남지 않았을 때
- **THEN** 새 시도를 시작하지 않고 실제 호출 수와 예산 소진을 반환해야 한다(SHALL).
- **AND** SDK 내부의 숨은 재시도를 사용해서는 안 된다(MUST NOT).

#### Scenario: Late text remains available for diagnosis

- **WHEN** 단계 또는 전체 예산을 넘긴 뒤 bounded 응답이 반환될 때
- **THEN** 원문과 실패 checkpoint를 보존하고 예산 소진을 기록하며 후속 호출과 completed 결과 채택을 중단해야 한다(SHALL).

#### Scenario: Workflow expires between stages

- **WHEN** 완료 단계의 저장 이후 전체 예산이 소진될 때
- **THEN** 이전 원문·checkpoint를 유지하고 다음 단계의 호출 횟수를 0으로 기록하며 provider를 호출하지 않아야 한다(SHALL).

#### Scenario: Transport timeout differs from a connection failure

- **WHEN** SDK가 timeout 예외를 반환할 때
- **THEN** 일반 연결 오류와 다른 provider_timeout 실패 코드로 기록해야 한다(SHALL).

#### Scenario: Historical evidence has no new time settings

- **WHEN** 새 전송·실행 예산 필드가 없는 기존 JSON record를 읽을 때
- **THEN** 기존 의미로 읽고 새 필드는 미기록 상태를 유지해야 한다(SHALL).

# reliability-ai-ingestion-investigation Specification

## Purpose

운영자가 HMDA 원천의 준비 상태와 실제 적재 단계의 결과를 근거와 함께 확인하고, 에이전트의 읽기 전용 조사를 통해 필요한 다음 조치를 결정할 수 있게 한다.

## Requirements

### Requirement: Scoped ingestion investigation and handoff

시스템은 권한 있는 호출자가 명시한 적재 요청의 `prepare` 조사와 허용된 `hmda_data_plane` 실행의 `review_run` 조사를 제공해야 한다(SHALL). 조사 결과는 조사 ID, 요청 범위, 관찰한 근거와 미확인 항목, 적용 가능한 다음 조치를 반환해야 한다(SHALL). 조사 도구는 호출자가 지정한 자료의 읽기 권한으로 제한하고, 실제 적재·재실행은 기존 권한을 가진 호출자가 별도로 요청해야 한다(SHALL).

#### Scenario: Preparation handed to the operator

- **WHEN** 호출자가 유효한 적재 요청을 조사할 때
- **THEN** 준비 상태, 원천 버전, 확인 근거와 다음 조치가 같은 조사에 연결되어야 함
- **AND** 조사 전후 원천과 Bronze 상태는 같아야 함

#### Scenario: Tool request outside the authorized scope

- **WHEN** 모델이 등록되지 않은 도구, 허용 범위 밖 자료 ID, 계약에 없는 인자 또는 한 응답에 여러 조회를 요청할 때
- **THEN** 시스템은 그 요청을 조회 전에 거절하고, 확인한 근거와 종료 사유를 반환해야 함

### Requirement: Source version bound readiness

시스템은 실제로 검사한 파일 집합과 내용의 버전을 준비 판정에 연결해야 한다(SHALL). 전체 검증 대상 파일의 필수 열과 요청 범위의 원천 파싱·대상 행을 기존 적재 규칙과 같은 기준으로 확인해야 한다(SHALL). 같은 범위와 버전의 필수 검사에 모두 통과하면 `ready`, 위반이 확인되면 `blocked`, 판정에 필요한 근거가 부족하면 `needs_human`을 반환해야 한다(SHALL). `continue_load` 권고는 `ready`에만 허용해야 한다(SHALL).

#### Scenario: Verified inputs are ready

- **WHEN** 고정한 원천 버전의 전체 검증 범위에서 필수 열과 파싱이 확인되고 요청 범위의 행 수가 양수일 때
- **THEN** 그 버전과 검사 근거를 담은 `ready`를 반환해야 함

#### Scenario: Confirmed input violation

- **WHEN** 실제 적재기가 검사할 파일의 필수 열이 누락되거나, 파싱 불가 또는 대상 범위가 0행임이 확인될 때
- **THEN** 확인된 위반과 근거를 담은 `blocked`를 반환해야 함

#### Scenario: Complete discovery confirms an empty source

- **WHEN** 요청에 해당하는 허용 원천 범위 전체의 발견을 마쳤고 지원하는 파일이 하나도 없음을 확인했을 때
- **THEN** 확인한 범위와 빈 파일 집합을 근거로 `blocked`를 반환해야 함

#### Scenario: Input identity or inspection is inconclusive

- **WHEN** 파일 버전 변경, 접근 실패 또는 시간 초과로 원천 발견이나 필수 검사를 마치지 못했고 유효한 위반 근거가 없을 때
- **THEN** 시스템은 미확인 이유를 담은 `needs_human`을 반환해야 함

### Requirement: Evidence driven model assistance

시스템은 확인한 규칙 결과와 근거 요약을 바탕으로 다음 조치를 평가해야 한다(SHALL). 추가 확인이나 해석이 필요한 때 모델은 허용된 조회 한 건 또는 근거를 인용한 권고를 제안할 수 있어야 한다(SHALL). 시스템은 승인된 조회로 새 근거를 얻으면 판정을 다시 계산하고, 검증된 관찰값과 모델의 해석을 각각 보존해야 한다(SHALL). 조회 결과를 후속 판단에 사용할 때는 승인된 제안 ID와 일치하는 관찰값만 사용해야 한다(SHALL).

#### Scenario: Deterministic result and next action

- **WHEN** 도메인 규칙으로 상태와 다음 조치가 모두 확정될 때
- **THEN** 규칙 근거만으로 결과를 반환해야 함
- **AND** 모델 호출 기록은 0건이어야 함

#### Scenario: Evidence changes the next step

- **WHEN** 초기 관찰값이 다른 두 조사에서 모델이 서로 다른 허용 조회나 권고를 선택할 때
- **THEN** 각 조사에 실제 선택과 사용 근거가 연결되고, 담당자는 각 결과에서 다른 다음 조치와 이유를 확인할 수 있어야 함

#### Scenario: Known verdict with unresolved follow-up

- **WHEN** 준비 판정은 확정됐지만 다음 조치를 정하려면 해석이 필요할 때
- **THEN** 모델 조사를 수행할 수 있어야 하며 같은 규칙과 근거에서 준비 판정은 동일해야 함
- **AND** 검증되지 않은 근거 ID를 인용한 권고는 채택 전에 보류해야 함

#### Scenario: Observation does not match the approved proposal

- **WHEN** 반환된 관찰값의 제안 ID가 승인된 조회와 다를 때
- **THEN** 불일치 사유를 기록하고 해당 관찰값을 판정이나 후속 모델 입력에 사용하지 않아야 함

### Requirement: Run scoped execution evidence

시스템은 지정한 Airflow 실행·태스크·시도의 관찰 상태와 확인된 데이터 갱신 근거를 반환해야 한다(SHALL). 행 수와 갱신 증거는 해당 시도에 연결할 수 있을 때 사용해야 한다(SHALL). 준비 조사와 실제 적재의 범위 및 원천 버전이 일치할 때만 결과를 비교하고, 비교에 필요한 값이 없으면 일치 여부를 `unknown`으로 보고해야 한다(SHALL).

#### Scenario: Stage observed without a verified update

- **WHEN** 해당 태스크 상태를 조회했고 같은 시도의 갱신 증거를 확인할 수 없을 때
- **THEN** 관찰한 단계 상태와 `unknown` 갱신 상태를 반환하고, 행 수를 미확인으로 남겨야 함

#### Scenario: Compare a verified pair of inputs

- **WHEN** 준비 조사와 실행 기록에서 대상 범위와 입력 버전이 각각 확인될 때
- **THEN** 두 값이 모두 일치할 때 비교 결과를 반환하고, 값이 다르면 비교할 수 없는 이유에 입력 차이를 명시해야 함

### Requirement: Bounded investigation and late responses

시스템은 모델 턴·도구 호출·기한을 제한하고 종료 이유를 기록해야 한다(SHALL). 호출 실패, 근거 부족 또는 예산 소진 시 이미 확인한 판정과 부족한 근거를 인계해야 한다(SHALL). 기한 이후 응답은 로컬 기록에 보존하고 새 조회나 판정에 반영하기 전에 조사를 종료해야 한다(SHALL).

#### Scenario: Model returns after the deadline

- **WHEN** 모델이 기한 이후에 추가 조회 요청을 반환할 때
- **THEN** 응답과 기한 소진 사유가 기록되고 추가 조회는 0건이어야 함
- **AND** 반환 판정은 기한 전에 확인한 근거에 기반해야 함

#### Scenario: Prompt or model unavailable

- **WHEN** 사용할 프롬프트를 확보하지 못하거나 모델 호출이 실패할 때
- **THEN** 기존 관찰과 판정, 실패 이유를 담은 인계를 반환해야 함

### Requirement: Local investigation evidence and offline replay

시스템은 조사 ID에 입력과 실행 조건, 초기 검사·조회 결과, 사용한 프롬프트·모델과 각 호출 결과를 연결해야 한다(SHALL). 재현은 원 조사 ID와 저장된 근거·상대 시각·종료에 영향을 준 저장 결과를 사용해 판정·인계·종료 사유를 다시 계산해야 한다(SHALL). 필요한 관찰값이 누락·손상됐거나 버전이 다르면 재현 불가 사유를 반환해야 한다(SHALL).

#### Scenario: Replay a successful or failed investigation

- **WHEN** 성공 또는 실패한 원 조사의 필수 기록과 사용 버전이 모두 존재할 때
- **THEN** 새 재현 ID에서 같은 판정·인계·종료 사유를 계산해야 함
- **AND** 실제 모델·프롬프트 호출, 원천·Airflow 조회 재실행, 원격 관측과 데이터 변경은 모두 0건이어야 함

#### Scenario: Recovery after process interruption

- **WHEN** 완료 기록이 없는 조사 뒤 호출자가 조사를 다시 요청할 때
- **THEN** 새 조사 ID에 이전 조사 ID를 연결하고 현재 범위와 버전을 확인해야 함

### Requirement: Investigation observation boundary

시스템은 원격 관측에 허용된 정보만 제공하고, 입력·출력 본문은 합성 사례의 허용된 필드로 제한해야 한다(SHALL). 관측 전송 장애의 상태는 로컬 결과와 별도로 기록해야 한다(SHALL).

#### Scenario: Observation transport fails

- **WHEN** 로컬 결과를 계산한 뒤 관측 전송이 실패할 때
- **THEN** 동일한 조사 결과와 전송 오류가 각각 기록되어야 함
- **AND** 전송 재시도에 따른 모델 재호출은 0건이어야 함

# Logging

Logging은 runtime clarification의 기본값이 아니다. **실행 후 중요한 사건을 복원하기 위해 필요한 최소 evidence**일 때 사용한다.

좋은 로그는 코드의 진행 상황을 중계하지 않는다. 나중에 로그만 읽고도 **무슨 일이 있었고, 무엇을 대상으로, 어떤 결과가 났으며, 왜 중요한지** 판단할 수 있는 사건을 남긴다.

## Good Log

좋은 log event는 다음 성질을 가진다.

| Quality | Question |
| --- | --- |
| 의미 있음 | 이 사건이 실행 이해에 실제로 필요한가? |
| 구체적임 | 무엇이 일어났는지 한 사건으로 식별되는가? |
| 맥락 있음 | 대상·결정·결과를 구분할 최소 context가 있는가? |
| 안정적임 | 메시지와 field의 의미가 구현 세부 변경에 쉽게 깨지지 않는가? |
| 검색 가능함 | 반복 실행에서 같은 종류의 사건을 비교·필터링할 수 있는가? |
| 비중복임 | 같은 사실을 다른 layer나 surface가 이미 충분히 소유하지 않는가? |
| 안전함 | secret, 민감 정보, raw payload, 과도한 크기를 남기지 않는가? |

모든 항목을 최대한 많이 기록하는 것이 아니라 **질문에 답하는 데 필요한 최소 정보**를 남긴다.

## Log Events, Not Narration

사건을 기록한다.

```text
HMDA 원천 적재 완료
artifact projection 승격 완료
recovery target 상태 불일치
승인되지 않은 backfill 거부
```

진행 상황을 문장처럼 중계하지 않는다.

```text
파일 읽기를 시작합니다
파일을 다 읽었습니다
다음 단계로 이동합니다
함수에 진입했습니다
```

함수 entry/exit, 모든 branch, loop iteration을 기계적으로 기록하지 않는다.

## Event Boundary

다음과 같이 **의미가 생기는 경계**를 우선한다.

- 외부 작업 또는 비용 있는 실행의 시작·완료·실패
- 중요한 상태 전이 또는 mutation
- approval, validation, reconciliation 같은 gate 결과
- 여러 가능한 경로 중 의미 있는 결정
- retry, fallback, skip처럼 정상 흐름과 다른 실행 선택
- 상위 layer가 알아야 하는 실패 원인

단순한 내부 함수 호출이나 값 계산은 그 자체로 event가 아니다.

## Message And Context

Message는 **사건의 종류**를 짧고 안정적으로 표현한다. 실행마다 달라지는 값은 context로 분리한다.

```text
message: "HMDA 원천 적재 완료"
context:
  table_name: raw.hmda_loans
  source_count: 3
  row_count: 120000
```

좋은 context 후보:

- stable identifier: `incident_id`, `approval_id`, `projection_id`
- operation target: table, asset, partition, artifact
- selected outcome: status, branch, action, reason
- bounded measurement: count, duration, return code
- correlation에 필요한 execution identifier

피한다:

- 전체 request/model dump
- raw row 또는 dataset sample
- secret, credential, token
- 무제한 stdout/stderr
- 쉽게 변하는 내부 object representation
- message에도 이미 들어 있는 값을 의미 없이 반복하는 field

## Stable Semantics

로그는 나중에 검색·비교될 수 있으므로 의미를 함부로 바꾸지 않는다.

- 같은 event는 가능한 한 같은 message와 field 의미를 유지한다.
- 같은 개념에 여러 동의어를 만들지 않는다.
- field 이름은 구현 단계가 아니라 domain/runtime 의미를 표현한다.
- formatter나 출력 모양보다 event semantics를 우선한다.

로그를 사실상 public API처럼 고정할 필요는 없지만, downstream 분석이나 사람이 반복적으로 의존하는 field는 변경 비용이 있다는 점을 고려한다.

## Level

level은 **사건의 심각도와 운영 의미**를 표현한다. verbosity 조절 수단으로만 사용하지 않는다.

| Level | Typical meaning |
| --- | --- |
| `DEBUG` | 정상 실행에서 숨겨도 되는 내부 진단 정보 |
| `INFO` | 정상적인 주요 실행 경계나 의미 있는 완료 결과 |
| `WARNING` | 실행은 계속되지만 예상과 다른 상태, fallback, degraded path |
| `ERROR` | 요청된 operation이 실패했거나 결과를 제공할 수 없음 |
| `CRITICAL` | process/system 수준에서 계속 진행하기 어려운 실패; 드물게 사용 |

level을 고르기 전에 **이 event 자체가 필요한지**를 먼저 판단한다.

## Failure Ownership

같은 failure를 여러 layer에서 반복 logging하지 않는다.

- 하위 layer가 context를 가진 exception을 올리고 상위 layer가 처리하지 않는다면 매 layer에서 다시 log하지 않는다.
- failure를 최종적으로 처리하거나 operator-visible 의미로 변환하는 boundary에서 기록하는 것을 우선한다.
- 상위 layer가 새로운 의미를 추가할 때만 별도 event를 고려한다.
- traceback은 원인 파악에 필요한 경계에서 한 번 충분히 남기는 것을 목표로 한다.

## Noise Budget

로그도 이해 부채를 만든다.

다음은 noise 신호다.

- 정상 실행 한 번에 같은 의미의 log가 반복된다.
- 한 사건을 이해하기 위해 지나치게 많은 line을 조합해야 한다.
- 대부분의 log가 항상 무시된다.
- 중요한 warning/error가 routine info/debug에 묻힌다.
- 로그 양 때문에 실제 문제 구간을 찾기 어려워진다.

새 event를 추가할 때는 기존 event를 제거하거나 합칠 수 있는지도 함께 본다.

## Final Check

로그를 추가·수정한 뒤 확인한다.

- 이 event는 어떤 runtime 질문에 답하는가?
- 사건의 owner와 기록 위치가 맞는가?
- message만 보고 event 종류를 이해할 수 있는가?
- context는 대상·결정·결과를 구분하는 데 충분한가?
- 기존 result, metadata, exception context 또는 다른 log와 중복되는가?
- 반복 실행에서 noise가 감당 가능한가?
- 민감도와 크기가 안전한가?
- 이 event를 제거해도 runtime 이해가 유지된다면 제거한다.

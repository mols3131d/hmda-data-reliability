# Logging

Logging은 runtime clarification의 기본값이 아니다. **기존 durable evidence만으로 복원되지 않는 사건의 흐름이나 결정을 남길 때** 사용한다.

## Good Log

좋은 log event는 나중에 다음 질문에 빠르게 답하게 한다.

- **무슨 사건이 있었는가?**
- **무엇을 대상으로 했는가?**
- **어떤 결과나 결정이 나왔는가?**
- **필요하다면 왜 그 결과가 났는가?**

그 질문에 답하지 않는 log는 추가하지 않는다.

## Event, Not Narration

의미가 생기는 사건을 기록한다.

```text
HMDA 원천 적재 완료
artifact projection 승격 완료
recovery target 상태 불일치
승인되지 않은 backfill 거부
```

코드 진행을 중계하지 않는다.

```text
파일 읽기를 시작합니다
다음 단계로 이동합니다
함수에 진입했습니다
```

함수 entry/exit, 모든 branch, loop iteration을 기계적으로 기록하지 않는다.

## Useful Boundaries

다음을 우선 검토한다.

- 외부 process, database 또는 framework 작업의 의미 있는 결과
- 중요한 mutation 또는 state transition
- approval, validation, reconciliation 같은 gate 결과
- retry, fallback, skip 같은 의미 있는 경로 선택
- 다른 evidence로는 사라지는 결정 근거
- 상위 경계가 처리해야 하는 실패

단순 함수 호출이나 값 계산 자체는 event가 아니다.

## Message And Context

Message는 **사건 종류**를 짧고 안정적으로 표현한다. 실행마다 달라지는 값은 structured context로 둔다.

```text
message: "HMDA 원천 적재 완료"
context:
  table_name: raw.hmda_loans
  source_count: 3
  row_count: 120000
```

Context는 필요한 것만 고른다.

- stable identifier: `incident_id`, `approval_id`, `projection_id`
- target: table, asset, partition, artifact
- outcome: status, action, reason, return code
- bounded measurement: count, duration
- 여러 evidence를 연결해야 할 때의 execution identifier

민감도와 크기 기준은 [Evidence](evidence.md#data-safety)를 따른다.

## Stable Semantics

- 같은 종류의 event는 message와 field 의미를 가능한 한 유지한다.
- 같은 개념에 여러 동의어를 만들지 않는다.
- field 이름은 구현 단계보다 domain/runtime 의미를 표현한다.
- formatter나 출력 모양보다 event semantics를 우선한다.

반복적으로 사람이 검색하거나 downstream 분석이 의존하는 field는 변경 비용이 있음을 고려한다. 그렇다고 log를 public API처럼 과도하게 고정하지 않는다.

## Level

| Level | Typical meaning |
| --- | --- |
| `DEBUG` | 정상 실행에서 숨겨도 되는 내부 진단 정보 |
| `INFO` | 정상적인 주요 실행 경계 또는 의미 있는 완료 결과 |
| `WARNING` | 실행은 계속되지만 예상과 다른 상태, fallback, degraded path |
| `ERROR` | 요청한 operation이 실패했거나 결과를 제공할 수 없음 |
| `CRITICAL` | process/system 수준에서 계속 진행하기 어려운 실패; 드물게 사용 |

level을 고르기 전에 event 자체가 필요한지 먼저 판단한다.

## Failure Ownership

같은 failure를 여러 layer에서 반복 logging하지 않는다.

- failure를 최종 처리하거나 operator-visible 의미로 바꾸는 boundary를 우선한다.
- 상위 layer가 새로운 의미를 추가할 때만 별도 event를 남긴다.
- traceback은 원인 파악에 필요한 경계에서 한 번 충분히 남기는 것을 목표로 한다.

## Noise Budget

로그도 이해 부채를 만든다. 다음 신호가 있으면 줄인다.

- 정상 실행마다 같은 의미의 event가 반복된다.
- 한 사건을 이해하려면 많은 line을 조합해야 한다.
- routine log가 중요한 warning/error를 가린다.
- 기존 result, artifact, metadata 또는 exception과 같은 사실을 반복한다.

새 event를 추가할 때 기존 event를 제거하거나 합칠 수 있는지도 본다.

## Final Check

- 이 event는 어떤 복원 질문에 답하는가?
- 사건의 owner와 기록 위치가 맞는가?
- message와 최소 context만으로 사건을 식별할 수 있는가?
- 기존 evidence와 중복되지 않는가?
- 반복 실행에서 noise와 데이터 크기가 감당 가능한가?

이 event를 제거해도 복원 질문에 답할 수 있다면 제거한다.

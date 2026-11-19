---
type: design
title: Ingestion Agent Decision and Tool Contract
description: 준비 판정은 코드가 확정하고 모델은 필요한 다음 조회와 후속 조치를 제안하도록 정의합니다.
---

# Ingestion Agent Decision and Tool Contract

## Delegation

운영자의 과제는 **지정한 범위로 적재를 요청할지, 입력을 바로잡을지, 어떤 확인을 더 해야 할지** 결정하는 것이다. 그래프는 이 과제를 기준으로 모델을 호출한다. 판정이 끝났더라도 다음 조치가 불분명하면 해석을 요청할 수 있다. [조사 흐름](architecture-plan.md#investigation-workflow)

| 알고 있는 상태 | 그래프가 취할 다음 행동 |
| --- | --- |
| 판정과 다음 조치가 규칙으로 정해졌다 | 코드가 판정과 근거를 반환한다. |
| 빠진 근거를 허용된 도구로 보충할 수 있고 어떤 조회가 필요한지 판단해야 한다 | 모델이 다음 조회를 한 건 제안한다. 검증된 응답을 받은 뒤 규칙과 후속 조치를 다시 평가한다. |
| 관찰할 사실은 확보했고 해석이나 후속 조치가 필요하다 | 관찰값을 제공하고 모델에 근거를 인용한 가설과 권고를 요청한다. |
| 필요한 근거를 확보할 수 없거나 실행 기한이 지났다 | 코드가 확인된 판정과 미확인 항목을 반환한다. 준비 판정을 못 내린 경우 `needs_human`으로 인계한다. |

## Tool Contract

모델은 **조회 한 건** 또는 **권고안**을 응답한다. 조회는 등록된 도구명과 허용된 자료 ID로 구성한다. 그래프가 모드, 자료 ID, 인자, 중복 호출과 예산을 확인하고 집행한다. 한 응답에 여러 조회가 있거나 인자가 계약과 다르면 오류를 기록하고 이미 확인한 근거로 인계한다. [허용 도구와 반환값](evidence-tool-schemas.md#tool-interfaces)

권고안에는 `evidence_ids`, `hypotheses`, `next_action`을 받는다. 기존 근거와 연결할 수 있는 제안만 반환한다. 관찰값과 규칙 결과는 코드가 구성하며, 모델의 원인 해석은 가설로 표시한다. 인용 근거가 부족하면 확인할 내용을 인계한다.

## Result Contract

| 준비 상태 | 코드가 적용하는 조건 |
| --- | --- |
| `blocked` | 고정된 범위와 버전에서 필수 규칙 위반이 하나 이상 확인됐다. |
| `ready` | 고정된 범위와 버전에서 모든 필수 검사를 마치고 통과했다. |
| `needs_human` | 확인된 위반이 없고 필수 근거가 부족하다. 검사 미완료·입력 변경·예산 소진은 이유로 기록한다. |

`prepare`는 조사 ID, 대상 범위, 입력 버전, 준비 상태, 확인 근거, 미확인 항목과 다음 조치를 반환한다. `ready`에서는 `continue_load`를 권고할 수 있다. `blocked`에서는 `correct_input` 또는 `request_confirmation`, `needs_human`에서는 `request_confirmation`을 사용한다. 권고에는 이유와 영향받는 원천·연도·파일·대상 범위를 붙인다. 실행 권한은 기존 적재 요청에서 확인한다.

`review_run`은 DAG 실행·단계 참조, 확인된 상태와 데이터 갱신의 근거, 입력 일치 여부를 반환한다. 다음 조치는 `inspect_execution`, `request_confirmation` 또는 `none` 중 하나다. 준비 판정의 근거는 이전 조사에, 실제 실행의 증거는 확인한 실행 기록에 연결한다. [실행 결과의 출처](evidence-tool-schemas.md#airflow-evidence)

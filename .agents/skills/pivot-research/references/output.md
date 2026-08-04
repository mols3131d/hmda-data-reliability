# Output

완료 상태, Chat 출력 또는 Artifact 작성 판단이 필요할 때 읽습니다.

## Completion

| 결과 | 조건 |
| --- | --- |
| 완료(Completed) | 핵심 질문에 근거 있는 답을 제시했고, 남은 충돌과 미확인 사항이 사용 목적을 막지 않습니다. |
| 진행 중(In Progress) | 답을 바꿀 수 있는 제한된 추가 조사 또는 결정이 남아 있습니다. |
| 차단(Blocked) | 필수 접근, 환경, 근거 또는 결정이 없어 신뢰할 수 있는 답을 만들 수 없습니다. |

Artifact의 실제 상태 값은 프로젝트 계약을 따릅니다.

## Output Selection

`output: auto`는 다음 기준을 사용합니다.

- 사용자가 Artifact를 요청하면 Artifact를 사용합니다.
- 다음 작업에서 지속적으로 참조해야 하는 근거면 Artifact를 사용합니다.
- 일회성 설명이나 제한된 확인이면 Chat을 사용합니다.
- Artifact 계약이 불명확하면 확인된 결과를 Chat으로 보고하고 Artifact 작성만 보류합니다.

## Chat

다음 네 항목을 필요한 만큼 간결하게 제공합니다.

- 현재 답 또는 결론
- 주요 근거
- 남은 충돌과 미확인 사항
- 다음 판단 또는 행동

빈 항목을 형식적으로 만들지 않습니다.

## Artifact

- 프로젝트에 이미 존재하는 Research 템플릿을 그대로 사용합니다.
- 저장 위치, front matter, 상태와 보관 규칙은 프로젝트 계약을 따릅니다.
- 템플릿, 저장 경로 또는 schema를 이 스킬에서 새로 정의하지 않습니다.
- 중요한 결론은 다시 확인할 수 있는 근거 위치와 연결합니다.
- 상세 활동 로그, 비공개 추론, cache, secret과 대용량 raw output은 저장하지 않습니다.

## Portability

특정 workflow, schema 또는 directory를 필수로 요구하지 않습니다.

적용 우선순위는 다음과 같습니다.

1. 명시된 argument
2. 프로젝트 규칙과 기존 템플릿
3. 기존 Research artifact
4. 일반적인 Chat 보고

프로젝트별 Research 자산이 없어도 Chat Research는 계속 수행할 수 있습니다.

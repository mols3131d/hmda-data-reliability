---
name: pivot-research
description: Conduct evidence-backed research before specification, implementation, or technical decisions. Use to understand current behavior, bound scope, verify dependencies, compare meaningful options, or investigate failures. Do not use for implementation, final requirements, or independent Review.
---

# Pivot Research

질문에 답할 근거를 조사하고 다음 판단에 사용할 수 있는 형태로 정리한다.

Research는 요구사항·설계·구현을 대신 결정하지 않는다.

## Arguments

```yaml
question: auto
scope: auto
exclude: []
rigor: auto
output: auto
```

| Argument | `auto` 동작 |
| --- | --- |
| `--question <text|auto>` | 핵심 목표와 필요한 하위 질문을 도출한다. |
| `--scope <value,...|auto>` | 직접 관련된 대상과 검증에 필요한 관계까지만 포함한다. |
| `--exclude <value,...>` | 지정한 대상을 조사하거나 근거로 사용하지 않는다. |
| `--rigor <auto|lite|standard|strict>` | 위험을 다루기에 충분한 가장 낮은 엄밀도를 선택한다. |
| `--output <auto|chat|artifact>` | 지속적인 기록이 필요할 때만 Artifact를 사용한다. |

명시된 argument를 우선한다. 충돌은 조용히 덮어쓰지 않는다.

## Workflow

1. 조사 목적, 핵심 질문과 범위를 정한다.
2. 기존 근거를 먼저 확인한다.
3. 답이나 주요 불확실성을 바꿀 수 있는 근거만 추가로 조사한다.
4. 중요한 결론을 다시 확인할 수 있는 근거 위치와 연결한다.
5. 근거 있는 답과 남은 불확실성을 Chat 또는 Artifact로 정리한다.

새로운 조사가 답이나 주요 불확실성을 실질적으로 바꾸지 않으면 중단한다.

## Progressive Disclosure

현재 판단에 필요한 문서만 읽는다.

| 필요 | Reference |
| --- | --- |
| 범위, 엄밀도, 조사 순서와 종료 기준 | [Workflow](references/workflow.md) |
| 근거 품질, 분류, 충돌과 추적성 | [Evidence](references/evidence.md) |
| 완료 상태, Chat·Artifact와 이식성 | [Output](references/output.md) |

Artifact는 프로젝트의 기존 Research 템플릿과 저장 규칙을 사용한다. 별도 형식이나 경로를 만들지 않는다.

## Completion

핵심 질문에 근거 있는 답을 제시했고, 남은 충돌과 미확인 사항이 사용 목적을 막지 않으면 완료한다.

## Boundaries

- 요구사항, 설계 또는 구현 계획을 Research 결과로 확정하지 않는다.
- 코드, 테스트 또는 설정을 구현 목적으로 수정하지 않는다.
- 근거 없는 확신으로 완료 처리하지 않는다.
- 질문과 무관한 전체 조사나 링크 수집을 하지 않는다.
- 사용자 의도와 활성 명세의 충돌을 조용히 해결하지 않는다.

# Pivot Research

질문에 답할 근거를 조사하고, 다음 판단에 사용할 수 있는 형태로 정리하는 Research 스킬입니다.

## Use Cases

다음과 같은 작업에 사용합니다.

- 현재 코드나 시스템이 어떻게 동작하는지 확인
- 변경 전 영향 범위와 의존 관계 조사
- 장애나 오류의 원인 분석
- 기술·도구·설계 대안 비교
- 명세 또는 구현 전에 필요한 사실 검증

요구사항·설계·구현 자체를 확정하거나 독립 Review를 수행하는 용도로는 사용하지 않습니다.

## Arguments

```yaml
question: auto
scope: auto
exclude: []
rigor: auto
output: auto
```

| Argument | 설명 |
| --- | --- |
| `--question <text|auto>` | 핵심 질문 또는 조사 목표 |
| `--scope <value,...|auto>` | 조사할 경로, 시스템, 버전 또는 주제 |
| `--exclude <value,...>` | 조사에서 제외할 대상 |
| `--rigor <auto|lite|standard|strict>` | 조사 엄밀도(Rigor) |
| `--output <auto|chat|artifact>` | 결과를 Chat 또는 Artifact로 남길지 지정 |

`auto`는 사용자 요청, 프로젝트 규칙과 기존 Research 자산을 바탕으로 가장 작은 합리적 값을 선택합니다.

## Examples

현재 동작을 가볍게 확인합니다.

```text
--question "이 설정은 어디에서 적용되는가?" --rigor lite
```

여러 코드 영역의 관계를 조사합니다.

```text
--question "EDA 실행 경계와 실패 전파 경로는 무엇인가?" --scope src/,tests/ --rigor standard
```

지속적으로 참조할 조사 결과를 요청합니다.

```text
--question "복구 절차의 데이터 손실 위험은 무엇인가?" --rigor strict --output artifact
```

## Output

Chat 결과는 현재 답, 주요 근거, 남은 불확실성과 다음 행동을 간결하게 제공합니다.

Artifact가 필요하면 프로젝트에 이미 존재하는 Research 템플릿과 저장 규칙을 사용합니다. 이 스킬은 별도 템플릿, 저장 경로 또는 front matter를 만들지 않습니다.

## Principles

- 기존 근거를 먼저 확인하고 부족한 부분만 조사합니다.
- 중요한 결론은 파일, 기호, 명령 결과 또는 URL과 연결합니다.
- 답이나 주요 불확실성을 바꾸지 않는 추가 조사는 중단합니다.
- 특정 workflow, schema 또는 directory에 종속되지 않습니다.

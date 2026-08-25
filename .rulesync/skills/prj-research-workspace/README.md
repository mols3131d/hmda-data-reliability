# Research Workspace

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
template: auto
scope: auto
exclude: []
rigor: auto
output: auto
```

| Argument | 설명 |
| --- | --- |
| `--question <text\|auto>` | 핵심 질문 또는 조사 목표 |
| `--template <path\|auto>` | 사용할 Research 템플릿 경로 |
| `--scope <value,...\|auto>` | 조사할 경로, 시스템, 버전 또는 주제 |
| `--exclude <value,...>` | 조사에서 제외할 대상 |
| `--rigor <auto\|lite\|standard\|strict>` | 조사 엄밀도(Rigor) |
| `--output <auto\|chat\|artifact>` | 결과를 Chat 또는 Artifact로 남길지 지정 |

`template: auto`는 프로젝트 설정, 기존 Research Artifact, 예상 보고서 저장 경로와 그 주변의 가까운 템플릿 후보만 짧게 확인합니다. 찾지 못하면 저장소 전체를 뒤지지 않고 템플릿 없이 계속합니다.

## Workflow

1. 핵심 질문을 정합니다.
1. 지정된 템플릿을 읽거나 가까운 후보를 짧게 찾습니다.
1. 템플릿과 주변 폴더의 로컬 지침에서 기대되는 내용을 파악합니다.
1. 질문과 템플릿을 바탕으로 조사 범위와 필요한 하위 질문을 정합니다.
1. 기존 근거를 확인하고 부족한 근거만 조사합니다.
1. 결과를 Chat 또는 Artifact로 정리합니다.

템플릿은 단순 서식이 아니라 Artifact에 기대되는 정보 구조입니다. `<...>`, `{...}`, `{{...}}` 플레이스홀더와 주석에도 작성 지침이 포함될 수 있습니다.

## Examples

현재 동작을 가볍게 확인합니다.

```text
--question "이 설정은 어디에서 적용되는가?" --rigor lite
```

템플릿을 직접 지정합니다.

```text
--question "변경 절차의 위험은 무엇인가?" --template docs/templates/research.md --rigor strict --output artifact
```

자동으로 가까운 템플릿을 찾습니다.

```text
--question "실행 경계와 실패 전파 경로는 무엇인가?" --template auto --scope src/,tests/
```

## Output

Chat 결과는 현재 답, 주요 근거, 남은 불확실성과 다음 행동을 간결하게 제공합니다.

Artifact가 필요하면 발견된 Research 템플릿과 프로젝트 저장 규칙을 사용합니다. 필수 항목과 조사 목표에 관련된 항목은 근거를 확보해 채웁니다. 템플릿을 찾지 못하면 템플릿 없이 작성합니다.

## Principles

- 기존 근거를 먼저 확인하고 부족한 부분만 조사합니다.
- 중요한 결론은 파일, 기호, 명령 결과 또는 URL과 연결합니다.
- 답이나 주요 불확실성을 바꾸지 않는 추가 조사는 중단합니다.
- 템플릿 탐색은 가까운 후보로 제한합니다.
- 템플릿은 조사에 필요한 내용을 확장할 수 있지만 핵심 질문을 대체하지 않습니다.
- 특정 workflow, schema 또는 directory에 종속되지 않습니다.

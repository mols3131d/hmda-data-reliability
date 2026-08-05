# MOLS Code Review

구현 코드와 테스트 코드의 correctness, regression, failure path와 validation evidence를 검토하는 범용 Review 스킬입니다.

특정 Agent, Review workflow, Git host 또는 artifact 형식에 의존하지 않습니다. 파일, diff, commit, pull request나 현재 작업 내용을 대상으로 사용할 수 있습니다.

## Use Cases

- 구현이 요구사항과 기존 contract를 충족하는지 확인
- 변경으로 인한 regression과 compatibility 문제 탐색
- error handling, state transition과 failure recovery 검토
- 테스트가 실제 behavior를 검증하고 false green을 만들지 않는지 확인
- 기존 validation 결과의 범위와 신뢰성 평가
- 여러 Review 결과의 evidence를 재검증

## Arguments

```yaml
target: auto
baseline: auto
contract: auto
scope: auto
exclude: []
focus: auto
validation: auto
```

| Argument | 설명 |
| --- | --- |
| `--target <value\|auto>` | 검토할 diff, file, directory, revision 또는 변경 대상 |
| `--baseline <value\|auto>` | 변경 전과 비교할 revision 또는 기준 |
| `--contract <value\|auto>` | 기대 동작을 정의하는 spec, 문서, issue 또는 사용자 지시 |
| `--scope <value,...\|auto>` | 포함할 path, component, behavior 또는 relation |
| `--exclude <value,...>` | 제외할 path, relation 또는 concern |
| `--focus <auto\|implementation\|tests\|all>` | 구현, 테스트 또는 둘 모두를 검토 |
| `--validation <command\|auto\|none>` | 실행할 검증 command 또는 자동 선택 여부 |

`auto`는 현재 요청과 repository context에서 가장 좁은 합리적 값을 선택합니다. 유효한 baseline이나 contract가 없으면 임의로 만들지 않고 해당 제한을 결과에 표시합니다.

## One Engine, Two Lenses

구현 코드와 테스트 코드는 별도 스킬로 나누지 않습니다.

두 대상은 공통으로 contract, 영향 범위, regression과 validation을 해석해야 합니다. 공통 엔진을 유지하되 다음 기준만 분리하여 적용합니다.

| Target | Primary questions |
| --- | --- |
| Implementation | 실제 동작, contract, boundary, state, failure와 compatibility가 올바른가? |
| Tests | scenario, oracle, isolation과 assertion이 실제 defect를 검출할 수 있는가? |

테스트 Review가 별도의 수명주기, 입력 또는 출력 계약을 갖게 될 때만 독립 스킬로 분리합니다.

## Examples

현재 변경 전체를 검토합니다.

```text
--target auto --focus all --validation auto
```

특정 구현 경로를 이전 revision과 비교합니다.

```text
--target src/pivot/reliability/ --baseline main --focus implementation
```

테스트의 설계와 false green 위험만 검토합니다.

```text
--target tests/reliability/ --focus tests --validation "uv run pytest tests/reliability -q"
```

## Output

결과는 중요한 finding과 불확실성을 근거 위치에 연결해 제공합니다. 각 finding은 무엇이 잘못되었는지뿐 아니라 어떤 조건에서 도달하며 어떤 영향을 만드는지 설명해야 합니다.

Severity, verdict와 저장 형식은 이 스킬을 사용하는 Review 계약을 따릅니다.

# Branches

브랜치는 하나의 변경 목적을 격리하고 검토 가능한 단위로 전달하기 위해 사용한다.

Research, Plan, Implementation, Review 같은 개발 단계는 branch 구조가 아니라 artifact와 commit으로 구분한다.

## Application

인간은 변경의 맥락과 위험에 따라 이 기준을 유연하게 적용할 수 있다. Agent는 공통 기준과 `Agent` section의 제약을 엄격하게 적용한다.

Repository protection, security policy와 권한은 항상 우선하며 우회하지 않는다.

## Naming

```text
[<owner>/]<type>/<topic>
```

| Part | Meaning |
| --- | --- |
| `owner` | 작업 주체를 나타내는 optional namespace |
| `type` | 변경 성격 |
| `topic` | 변경 목적 |

### Owner

Agent는 `agent` owner를 사용한다. 인간은 특별한 구분이 필요하지 않다면 owner를 생략할 수 있다.

```text
feat/reliability-profile
mols/feat/reliability-profile
agent/docs/vcs-git-guides
agent/feat/review-engine
```

Owner는 작업 출처를 나타낼 뿐 특정 제품이나 Git author identity를 보장하지 않는다.

### Type

[`.gitmessage`](../../../.gitmessage)의 Conventional Commit type을 사용한다.

```text
feat  fix  refactor  perf  docs  test  style  chore
```

### Topic

- 소문자 kebab-case를 사용한다.
- 구현 방법보다 변경 목적을 표현한다.
- 날짜, 모델 버전, 대화 ID와 의미 없는 번호를 넣지 않는다.
- 이름이 충돌하면 번호를 붙이지 말고 목적을 더 구체화한다.

## Change Unit

하나의 branch는 함께 검토하고 병합하며 되돌릴 수 있는 하나의 변경 목적을 가진다.

같은 목적의 설계, 문서, 구현과 검증 보강은 같은 branch에서 반복할 수 있다. 개별 file이나 대화 요청마다 branch를 분리하지 않는다.

독립적으로 검토하거나 되돌릴 가치가 있는 새 목적은 별도의 branch와 pull request로 분리한다.

## Base And Reuse

작업 branch는 원칙적으로 원격 저장소의 현재 `main` head에서 생성한다. 별도의 기준 branch가 지정되면 해당 원격 branch의 현재 head를 사용한다.

같은 이름의 branch가 있으면 관련 pull request와 작업 목적을 먼저 확인한다. 동일 작업의 후속 수정일 때만 재사용한다.

## Agent

- `agent` owner namespace를 사용한다.
- 새 변경 목적의 repository content 수정은 새 작업 branch에서 수행한다.
- 동일 작업의 후속 수정은 기존 pull request branch를 계속 사용할 수 있다.
- 자신의 branch 또는 사용자가 수정을 명시한 branch만 변경한다.
- `main`이나 보호 branch에 직접 commit하지 않는다.
- 사용자의 명시적 요청 없이 force-push, history rewrite 또는 미병합 branch 삭제를 수행하지 않는다.
- 규칙이나 권한이 충돌하면 임의로 우회하지 않고 중단하여 보고한다.

저장소 조회, 분석, review, 상태 확인과 GitHub metadata 변경에는 새 branch가 필요하지 않다.

## Related

- [Commits](commit.md): 변경을 commit으로 구성하고 기록하는 기준
- [Pull Requests](pull-request.md): branch를 검토와 채택 경계로 전달하는 기준

# Branch Strategy

## Purpose

브랜치는 변경을 격리하고 검토 가능한 단위로 전달하기 위해 사용한다.

개발 단계를 브랜치 구조로 표현하지 않는다. Research, Plan, Implementation, Review는 artifact와 commit으로 구분한다.

## Model

```text
main
└── [<owner>/]<type>/<topic>
```

- `owner`: 작업 주체
- `type`: 변경 성격
- `topic`: 변경 목적

## Naming

```text
[<owner>/]<type>/<topic>
```

예시:

```text
feat/reliability-profile
docs/eda-strategy

chatbot/docs/branch-strategy
agent/feat/review-engine
```

### Owner

Chatbot과 agent는 `owner`를 반드시 사용한다.

| Owner | Meaning |
| --------- | ---------------------------------------------- |
| `chatbot` | 대화형 환경에서 연결된 도구로 수행한 작업 |
| `agent` | repository 작업 환경에서 file 수정과 command 실행을 수행한 작업 |

인간은 특별한 구분이 필요하지 않다면 `owner`를 생략한다.

```text
feat/reliability-profile
mols/feat/reliability-profile
```

`owner`는 작업 출처를 나타내는 namespace다. 특정 제품이나 모델을 식별하지 않으며 Git commit의 author 또는 committer identity도 보장하지 않는다.

### Type

저장소의 Conventional Commit 유형을 사용한다.

```text
feat
fix
refactor
perf
docs
test
style
chore
```

### Topic

- 소문자 kebab-case를 사용한다.
- 구현 방법보다 변경 목적을 표현한다.
- 날짜, 모델 버전과 대화 ID는 넣지 않는다.
- 의미 없는 번호 접미사는 사용하지 않는다.
- 기존 branch와 이름이 충돌하면 목적을 더 구체화한다.

## Workflow

```text
원격 기준 브랜치 확인
→ 작업 브랜치 생성
→ 요청 범위 변경
→ 검증 및 diff 확인
→ Draft PR 생성
→ 필요한 후속 수정
→ 인간 검토
→ 병합 및 정리
```

작업 브랜치는 원칙적으로 원격 저장소의 현재 `main` head에서 생성한다.

별도의 기준 브랜치가 명시된 작업은 해당 원격 브랜치의 현재 head를 사용한다.

## Change Unit

하나의 branch는 함께 검토하고 병합하며 되돌릴 수 있는 하나의 변경 목적을 가진다.

개별 file이나 대화 요청마다 branch를 분리하지 않는다. 같은 목적의 설계 수정, 문서 보완, 구현 수정과 검증 보강은 같은 branch와 Draft PR에서 반복할 수 있다.

독립적으로 검토하거나 되돌릴 가치가 있는 새 목적은 별도의 branch와 PR로 분리한다.

## Human Work

인간은 변경의 맥락과 위험을 판단하여 이 전략을 유연하게 적용할 수 있다.

- 작은 변경을 기존 branch에 포함할 수 있다.
- 작업 목적이 응집되어 있다면 범위를 조정할 수 있다.
- 실험 중 임시 branch와 commit을 사용할 수 있다.
- repository policy와 책임 범위 안에서 직접 commit이나 history 정리를 판단할 수 있다.

다만 변경의 목적, 검증 상태와 주요 위험을 다른 작업자가 이해할 수 있어야 한다.

## Chatbot and Agent Work

Chatbot과 agent는 다음 규칙을 엄격하게 적용한다.

- 자신의 `owner` namespace를 사용한다.
- GitHub 쓰기 작업은 새 작업 branch에서 수행한다.
- 요청된 목적과 직접 관련된 범위만 변경한다.
- 서로 다른 변경 목적을 하나의 branch에 혼합하지 않는다.
- 인간이나 다른 작업 주체의 branch를 명시적 허가 없이 수정하지 않는다.
- 변경은 Draft PR로 전달한다.
- 수행한 검증과 수행하지 못한 검증을 구분한다.
- CI 또는 Review 실패를 조용히 무시하지 않는다.
- 예외를 스스로 추론하거나 확대 적용하지 않는다.

사용자의 명시적인 요청 없이는 다음 작업을 수행하지 않는다.

- `main` 또는 보호 branch 직접 commit
- PR Ready 전환
- PR 승인 또는 병합
- Auto-merge 설정
- Force-push 또는 history rewrite
- Review thread 해결
- 미병합 branch 삭제

규칙을 적용할 수 없거나 서로 충돌하면 임의로 우회하지 않고 작업을 중단하여 보고한다.

## Existing Branches

같은 이름의 branch가 존재하면 관련 PR과 작업 목적을 먼저 확인한다.

동일 작업의 후속 수정이라면 기존 PR branch를 계속 사용할 수 있다. 동일 작업이 아니면 branch를 재사용하지 않는다.

Chatbot과 agent는 자신의 `owner` branch이거나 사용자가 수정을 명시적으로 요청한 branch만 변경한다.

## Commits

- 하나의 commit은 하나의 논리적 변경을 표현한다.
- 관련 file은 가능한 한 작업 단위로 묶는다.
- file마다 기계적으로 commit을 생성하지 않는다.
- 요청 범위 밖의 변경을 같은 commit에 포함하지 않는다.
- 실행하지 않은 검증을 commit message나 PR에 기록하지 않는다.

작업 중 commit은 검토 가능한 진행 단위로 사용할 수 있다. 최종 history를 단순하게 유지할 필요가 있으면 merge 시 squash를 사용할 수 있다.

## Pull Request

GitHub 쓰기 작업은 원칙적으로 Draft PR로 전달한다.

PR에는 최소한 다음을 기록한다.

```markdown
## Summary

- 변경 내용
- 변경 목적

## Validation

- 수행한 검증
- 수행하지 못한 검증과 이유

## Notes

- 중요한 결정
- 남은 위험 또는 제한
```

검증과 Review는 변경의 위험과 영향 범위에 비례하여 적용한다. 모든 변경에 전체 test suite나 전체 Review를 요구하지 않는다.

## Cleanup

병합된 작업 branch는 repository의 자동 삭제 설정 또는 권한 있는 주체가 정리한다.

Chatbot과 agent는 사용자의 명시적인 요청 없이 미병합 branch나 다른 작업 주체의 branch를 삭제하지 않는다.

## Exceptions

다음 작업에는 새 branch가 필요하지 않다.

- 저장소 조회와 분석
- 코드 또는 문서 Review
- PR 상태와 CI 결과 확인
- 명시적으로 요청된 기존 PR 후속 수정

긴급 상황이라도 chatbot과 agent의 `main` 직접 commit은 사용자가 위험을 인지하고 명시적으로 요청한 경우에만 허용한다.

Repository protection, security policy와 권한은 항상 우선하며 우회하지 않는다.

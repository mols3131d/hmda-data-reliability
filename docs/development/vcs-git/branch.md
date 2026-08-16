# Branches

브랜치는 하나의 변경 목적을 격리하고 검토 가능한 단위로 전달한다.

Research, Plan, Implementation, Review는 branch 구조가 아니라 artifact와 commit으로 구분한다.

## Application

인간은 변경의 맥락과 위험에 따라 이 기준을 유연하게 적용할 수 있다. Agent는 `Agent Instructions` section의 제약을 따른다.

Repository protection, security policy와 권한은 항상 우선한다.

## Naming

```text
[<actor>/]<type>/<topic>
```

| Part | Meaning |
| --- | --- |
| `actor` | 작업 주체를 구분하는 optional namespace |
| `type` | 변경 성격 |
| `topic` | 변경 목적 |

Agent는 actor namespace로 `agent`를 사용한다. 인간은 특별한 구분이 필요하지 않다면 actor를 생략할 수 있다.

```text
feat/reliability-profile
mols/feat/reliability-profile
agent/docs/vcs-git-guides
agent/feat/review-engine
```

Type은 [`.gitmessage`](../../../.gitmessage)의 Conventional Commit type을 사용한다. Topic은 소문자 kebab-case로 변경 목적을 표현한다.

## Change Unit

하나의 branch는 함께 검토하고 병합하며 되돌릴 수 있는 하나의 변경 목적을 가진다.

같은 목적의 spec, 문서, test와 구현은 같은 branch에서 함께 변경할 수 있다. 독립적으로 검토하거나 되돌릴 새 목적은 별도의 branch와 pull request로 분리한다.

## Base And Reuse

작업 branch는 원칙적으로 원격 저장소의 현재 `main` head에서 생성한다. 별도의 기준 branch가 지정되면 해당 branch를 사용한다.

기존 branch는 동일 작업의 후속 수정일 때만 재사용한다. `inbox`는 반복되는 routine artifact 생성을 위한 장기 유지 예외다.

## Inbox Branch

`inbox`는 routine non-canonical artifact를 지속적으로 생성하고 보관하는 장기 유지 branch다. 날짜별 artifact와 archive의 owning location은 `inbox` branch이며, routine artifact는 `main`에 복제하지 않는다.

`inbox` branch가 없으면 current remote `main`에서 한 번 생성한다.

### Direct Push

Routine artifact direct push를 허용하는 경로는 다음뿐이다.

```text
inbox/YYYY-MM-DD/**
inbox/archive/**
```

- Routine artifact는 `inbox`에 직접 commit하고 push하며 Pull Request를 만들지 않는다.
- 하나의 commit에는 하나의 artifact 또는 함께 소비되는 하나의 bundle만 포함한다.
- Routine artifact push에는 routine artifact 변경만 포함한다.
- Merge base 기준 `inbox` 고유 content는 위 허용 경로에만 존재해야 한다.
- Commit message는 [Commits](commit.md) 규칙을 따른다.
- `inbox/AGENTS.md`, `inbox/README.md`, `inbox/_guidelines/**`, `inbox/_templates/**`는 운영 자산이며 direct push 예외에 포함하지 않는다.
- 운영 자산과 그 밖의 repository content는 최신 `main`에서 일반 작업 branch와 Draft Pull Request로 변경한다.

Push 전에는 다음만 확인한다.

1. Local branch와 push destination이 모두 `inbox`다.
1. Remote `inbox`를 갱신했고 push가 fast-forward다.
1. Push에 포함된 변경이 허용 경로 안에만 있다.
1. 예상하지 못한 변경이나 unresolved conflict가 없다.

Remote가 앞서 있으면 먼저 반영한다. Force-push, remote history rewrite, 다른 작업자의 변경을 덮어쓰기 위한 reset 또는 branch replacement는 금지한다.

### Formatting

Repository-managed automation은 routine artifact push 뒤 변경된 Markdown artifact에 `rumdl fmt`를 적용하고 필요한 formatting change를 `inbox`에 별도 commit할 수 있다.

- Formatting은 content validation gate가 아니라 mechanical normalization이다.
- Formatter는 해당 push에서 변경된 routine artifact만 수정하고 repository의 current Markdown formatter configuration을 따른다.
- 운영 자산이나 다른 repository path를 수정하지 않는다.
- Formatting commit에는 formatter가 만든 변경 외의 내용을 섞지 않는다.
- 동시 update는 직렬화하거나 push 직전 remote `inbox`를 다시 읽어 stale ref를 덮어쓰지 않는다. Force-push는 사용하지 않는다.
- Formatter 실패는 artifact의 의미를 승인하거나 거부하는 판단으로 해석하지 않는다.

Automation이 아직 구성되지 않았거나 일시적으로 실패한 경우에도 routine artifact delivery 자체를 별도 Pull Request로 우회하지 않는다.

### Main Sync

`inbox`가 최신 repository context를 필요로 할 때 `main`을 `inbox`에 merge한다. `main`에서 Inbox Branch 또는 `inbox/**` 운영 guidance가 변경되면 다음 routine artifact 작업 전에 sync한다. 방향은 항상 **`main` → `inbox`**이며, sync를 이유로 `inbox` content를 `main`에 merge하지 않는다.

- Sync commit에는 `main` 반영 외의 변경을 섞지 않는다.
- Conflict나 예상하지 못한 path가 생기면 자동으로 의미를 결정하지 않고 중단한다.
- Force-push, rebase, history rewrite 또는 branch replacement로 sync하지 않는다.
- Routine artifact writer는 `main` sync와 artifact commit을 하나의 commit에 섞지 않는다.

### Main Inbox Index

`main:/inbox/README.md`는 사람이 최근 inbox artifact를 찾기 위한 **human-only index**다. Artifact 자체를 저장하거나 canonical state를 나타내지 않는다.

Repository-managed automation은 index 갱신에 한해 `main:/inbox/README.md`를 직접 갱신할 수 있다. 이 예외는 다음 경계 안에서만 허용한다.

- 변경 대상은 `main:/inbox/README.md` 하나뿐이다.
- Index는 `inbox` branch의 artifact에 대한 link와 식별 metadata만 투영한다.
- Artifact content를 `main`에 복제하지 않는다.
- Index는 current implementation, validation evidence, normative contract 또는 project status의 source로 사용하지 않는다.
- Routine artifact writer는 artifact 작업의 side effect로 index를 수동 갱신하지 않는다.
- Direct update 직전에 current `main`을 다시 읽고, branch가 이동했으면 최신 `main` 기준으로 index commit을 다시 만든다. Force-push는 사용하지 않는다.

Index automation이 아직 구성되지 않았거나 실패한 경우에도 routine artifact는 `inbox` branch에서 유효하다. Index automation 자체의 구현과 변경은 일반 Draft Pull Request workflow를 따른다.

### Canonicalization And Legacy Promotion

Inbox artifact에서 장기적으로 유지할 결정이나 계약이 채택되면 해당 canonical owner에 필요한 내용을 다시 작성하고 일반 Draft Pull Request로 전달한다. Inbox artifact 자체를 `main:/inbox/YYYY-MM-DD/**` 또는 `main:/inbox/archive/**`로 promotion하지 않는다.

기존 `main:/inbox/YYYY-MM-DD/**`와 `main:/inbox/archive/**`는 이전 promotion workflow의 legacy artifact다. 새 artifact를 추가하지 않으며, 독립적인 작업·근거 가치가 사라진 legacy artifact는 별도 cleanup 작업에서 삭제하거나 archive 정책을 정리한다.

## Agent Instructions

- `agent` actor namespace와 자신의 작업 branch를 사용한다. Routine inbox artifact는 `Inbox Branch`의 direct push 예외를 따른다.
- 요청된 변경 목적과 범위만 수정한다.
- `main`, 보호 branch 또는 다른 작업 주체의 branch를 명시적 요청 없이 변경하지 않는다.
- Main Inbox Index의 direct-write 예외는 repository-managed automation에만 적용하며 agent가 `main` 직접 수정을 정당화하는 근거로 사용하지 않는다.
- 명시적 요청 없이 force-push, history rewrite 또는 미병합 branch 삭제를 수행하지 않는다.
- 규칙이나 권한이 충돌하면 우회하지 않고 보고한다.

## Related

- [Commits](commit.md): 변경을 commit으로 구성하는 기준
- [Pull Requests](pull-request.md): 변경을 검토와 채택 경계로 전달하는 기준

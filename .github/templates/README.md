# GitHub Templates

이 directory는 Pull Request와 Pull Request Review에 사용하는 project template을 관리한다. GitHub가 자동 해석하는 template 위치가 아니라 인간과 Agent가 공통 형식을 재사용하기 위한 source다.

## Metadata Header

Template 상단의 `yaml` code block은 Front Matter나 GitHub metadata가 아니다. GitHub가 제공하지 않는 정보만 보완하며, GitHub가 이미 소유하는 상태·작성 계정·review decision을 반복하지 않는다.

### `author`

`author`는 실제 작성 주체가 GitHub에 표시되는 계정과 다를 때 Agent 주도 작성을 식별하는 optional list다.

- 인간만 작성에 기여한 경우 생략한다.
- 인간이 작성을 주도하고 Agent가 보조한 경우 생략한다.
- Agent가 작성을 주도했지만 인간 계정의 권한으로 작성되어 GitHub만으로 실제 작성 주체를 구별할 수 없을 때 기록한다.
- 각 항목은 `<user-id>:<provider>-<service>` 형식의 scalar string을 사용한다.
- `provider-service`는 lowercase kebab-case를 사용한다.
- 여러 Agent가 작성에 주도적으로 참여했다면 복수 항목을 사용할 수 있다.

```yaml
author:
  - mols3131d:openai-chatgpt
```

## Writing Rules

- 현재 변경과 판단에 필요한 최종 정보만 남긴다. Agent의 상세 reasoning, 시행착오와 되돌린 시도는 기록하지 않는다.
- GitHub UI, CI 또는 다른 canonical artifact가 이미 소유하는 정보를 필요 없이 복제하지 않는다.
- optional section은 내용이 있을 때만 유지하고 빈 placeholder를 남기지 않는다.
- repository 내부 경로와 artifact는 repository-relative reference를 사용한다.
- 요구사항이나 결정의 source가 따로 있으면 내용을 다시 쓰기보다 해당 artifact를 연결한다.

## Templates

- [`pull-request.md`](pull-request.md): Pull Request description
- [`pull-request-review.md`](pull-request-review.md): Pull Request review body

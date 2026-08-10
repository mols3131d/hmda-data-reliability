# GitHub Templates

이 directory는 Pull Request와 Pull Request Review에 사용하는 project template을 관리한다. GitHub가 자동 해석하는 template 위치가 아니라 인간과 Agent가 공통 형식을 재사용하기 위한 source다.

## Metadata

GitHub가 제공하지 않는 정보만 optional metadata로 보완한다. Metadata를 사용하면 본문 맨 위에 `yaml` code block으로 두며, Front Matter나 GitHub metadata로 취급하지 않는다.

### `author`

`author`는 실제 작성 주체가 GitHub에 표시되는 계정과 다를 때 Agent 주도 작성을 식별하는 optional list다.

- 인간만 작성에 기여했거나 인간이 주도하고 Agent가 보조했다면 생략한다.
- Agent가 주도했지만 GitHub 작성자만으로 실제 작성 주체를 구별할 수 없을 때 기록한다.
- 각 항목은 `<user-id>:<provider>-<service>` 형식의 scalar string을 사용한다.
- `provider-service`는 lowercase kebab-case를 사용한다.

```yaml
author:
  - mols3131d:openai-chatgpt
```

Template에서는 기본 읽기 흐름을 방해하지 않도록 이 예시를 HTML comment 안에 둔다. 실제 사용할 때만 본문 맨 위로 옮긴다.

## Writing Rules

- 결론과 판단에 필요한 핵심 정보를 먼저 둔다.
- 작업 과정이나 시행착오보다 최종 결과와 근거를 기록한다.
- GitHub UI, CI 또는 canonical artifact가 이미 소유하는 정보는 필요 없이 복제하지 않는다.
- optional section은 판단 비용을 줄일 때만 사용하고 빈 placeholder는 제거한다.
- 상태는 `✅ Pass`, `❌ Fail`, `⚪ Not Verified`처럼 marker와 text label을 함께 적는다.
- Template의 `<status>`와 다른 placeholder는 실제 내용으로 교체하고 남겨두지 않는다.
- repository 내부 path와 artifact는 repository-relative reference를 사용한다.
- 요구사항이나 결정의 source가 따로 있으면 내용을 다시 쓰기보다 해당 artifact를 연결한다.

## Templates

- [`pull-request.md`](pull-request.md): Pull Request description
- [`pull-request-review.md`](pull-request-review.md): Pull Request review body

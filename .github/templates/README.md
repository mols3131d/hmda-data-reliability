# GitHub Templates

이 directory는 Pull Request와 Pull Request Review에 사용하는 project template을 관리한다. GitHub가 자동 해석하는 template 위치가 아니라 인간과 Agent가 공통 형식을 재사용하기 위한 source다.

## Metadata

GitHub가 제공하지 않는 정보만 optional metadata로 보완한다. Metadata를 사용하면 본문의 마지막에 하나의 `yaml` code block으로 두며, Front Matter나 GitHub metadata로 취급하지 않는다. Footnote 정의가 있으면 metadata를 그 바로 앞에 두고, 본문에는 별도 `Metadata` heading을 만들지 않는다.

Metadata field는 서로 독립적이며 필요한 field만 사용한다.

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

### `revision`

`revision`은 Pull Request description이나 review의 판단이 기준으로 삼은 exact repository revision pair를 식별하는 optional map이다.

- 사용하면 `base`와 `head`를 함께 기록한다.
- `base`는 비교 기준이 된 target branch commit이다.
- `head`는 description 또는 review가 설명·검토한 source branch commit이다.
- 값은 full commit SHA를 사용한다. Branch name처럼 움직이는 ref는 기록하지 않는다.
- Pull Request description에서 `revision`을 사용한 뒤 base 또는 head가 바뀐 상태로 본문을 갱신하면 `revision`도 함께 갱신한다.
- Pull Request review의 `revision`은 해당 review가 실제로 검토한 비교 기준을 고정하며, 이후 PR head가 바뀌어도 과거 review의 값은 바꾸지 않는다.

```yaml
revision:
  base: <full-base-commit-sha>
  head: <full-head-commit-sha>
```

Template에서는 기본 읽기 흐름을 방해하지 않도록 metadata 예시를 HTML comment 안에 둔다. 실제 사용할 때는 comment를 제거하고 본문 마지막에 두며, footnote 정의가 있으면 그 바로 앞에 둔다.

## Writing Rules

- 결론과 판단에 필요한 핵심 정보를 먼저 둔다.
- 작업 과정이나 시행착오보다 최종 결과와 근거를 기록한다.
- GitHub UI, CI 또는 canonical artifact가 이미 소유하는 정보는 필요 없이 복제하지 않는다.
- 구조화된 사실, 경로, 근거, 변경 항목처럼 독립적으로 훑어야 하는 값은 긴 문단보다 list를 우선한다.
- 하나의 field에 값이 하나면 inline으로 쓸 수 있고, 값이 여러 개면 nested list로 분리한다.
- List depth는 2단계를 권장하고 최대 3단계까지만 사용한다. 4단계가 필요하면 section이나 field 구조를 다시 나눈다.
- optional section과 metadata는 판단 비용을 줄일 때만 사용하고 빈 placeholder는 제거한다.
- `revision`을 기록했다면 본문의 validation, finding과 상태 설명이 해당 base/head 기준과 일치해야 한다.
- 상태는 `✅ Pass`, `❌ Fail`, `⚪ Not Verified`처럼 marker와 text label을 함께 적는다.
- Template의 `<status>`와 다른 placeholder는 실제 내용으로 교체하고 남겨두지 않는다.
- repository 내부 path와 artifact는 repository-relative reference를 사용한다.
- 요구사항이나 결정의 source가 따로 있으면 내용을 다시 쓰기보다 해당 artifact를 연결한다.

## Templates

- [`pull-request.md`](pull-request.md): Pull Request description
- [`pull-request-review.md`](pull-request-review.md): Pull Request review body

# GitHub Templates

GitHub가 인식하는 Issue와 Pull Request 템플릿은 각각 [`ISSUE_TEMPLATE/issue.md`](../ISSUE_TEMPLATE/issue.md), [`pull_request_template.md`](../pull_request_template.md)에 둔다. 이 directory는 공통 작성 규칙과 GitHub가 자동 제공하지 않는 Pull Request Review 템플릿을 관리한다. GitHub 템플릿은 default branch에 반영된 뒤 적용된다.

## Issue Composition

Issue는 문제 보고, 변경 제안, 조사 요청에 공통으로 사용한다. 필요한 정보만 작성하고 해당하지 않는 optional section과 빈 placeholder는 제거한다.

- **Objective:** 문제, 제안 또는 조사할 질문과 목적
- **Acceptance:** 완료를 판단할 결과·조건 또는 조사 산출물. 아직 결정되지 않았다면 미확정 사항을 명시한다.
- **Context:** 배경, 관련 문서·이슈 및 참고 정보
- **Evidence / Environment:** 현상·재현 근거와 관련 실행 조건. 필요할 때 별도 section으로 구분한다.
- **Boundaries / Open Decisions:** 제외 범위, 제약과 결정이 필요한 사항

확인한 사실과 추정·미확정 사항을 구분한다. 중복 설명, 불필요한 환경 정보 및 비밀 값은 제외하고, 별도 원본이 있는 요구사항과 증거는 링크로 연결한다.

## Metadata

GitHub가 제공하지 않는 정보만 optional YAML metadata로 보완한다. Metadata field는 서로 독립적이며 필요한 field만 사용한다.

- **Issue:** 템플릿의 YAML Front Matter에는 GitHub가 해석하는 `name`과 `about`을 둔다. 이 설정은 생성된 Issue 본문에 보존되지 않는다. `author`, `environment`, `source_revision`은 필요할 때만 본문 마지막의 `yaml` code block에 기록한다.
- **Pull Request / Review:** 기존과 같이 본문 마지막에 하나의 `yaml` code block으로 기록한다. PR의 `revision.base/head`는 비교 기준 commit pair이며 Issue의 `source_revision`과 다르다.

본문 YAML block은 GitHub metadata에 자동 연동되지 않는다. Footnote 정의가 있으면 바로 앞에 두고 별도 `Metadata` heading은 만들지 않는다.

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

### `environment`

`environment`는 Issue의 증상이나 결과에 영향을 주는 확인된 조건만 담는 optional map이다. 필요에 따라 runtime, model, hardware, data, configuration 등 관련 key만 기록한다. 비밀 값이나 확인하지 못한 추정은 넣지 않으며, 본문 Environment와 중복하지 않는다.

```yaml
environment:
  runtime: <runtime-and-version>
  configuration: <relevant-non-secret-settings>
```

### `source_revision`

`source_revision`은 Issue의 현상이 관찰된 정확한 repository commit을 식별할 때만 사용하는 optional full commit SHA다. Branch name이나 PR의 `revision.base/head`를 대신하지 않는다.

```yaml
source_revision: <full-commit-sha>
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

Template에서는 기본 읽기 흐름을 방해하지 않도록 optional metadata 예시를 HTML comment 안에 둔다. 실제 사용할 때는 comment를 제거하고 필요한 field만 본문 마지막에 둔다.

## Writing Rules

- 결론과 판단에 필요한 핵심 정보를 먼저 둔다.
- 작업 과정이나 시행착오보다 최종 결과와 근거를 기록한다.
- GitHub UI, CI 또는 canonical artifact가 이미 소유하는 정보는 필요 없이 복제하지 않는다.
- 구조화된 사실, 경로, 근거, 변경 항목처럼 독립적으로 훑어야 하는 값은 긴 문단보다 list를 우선한다.
- 하나의 field에 값이 하나면 inline으로 쓸 수 있고, 값이 여러 개면 nested list로 분리한다.
- List depth는 2단계를 권장하고 최대 3단계까지만 사용한다. 4단계가 필요하면 section이나 field 구조를 다시 나눈다.
- optional section과 metadata는 판단 비용을 줄일 때만 사용하고 빈 placeholder는 제거한다.
- PR/review에서 `revision`을 기록했다면 본문의 validation, finding과 상태 설명이 해당 base/head 기준과 일치해야 한다.
- 상태는 `✅ Pass`, `❌ Fail`, `⚪ Not Verified`처럼 marker와 text label을 함께 적는다.
- Template의 `<status>`와 다른 placeholder는 실제 내용으로 교체하고 남겨두지 않는다.
- repository 내부 path와 artifact는 repository-relative reference를 사용한다.
- 요구사항이나 결정의 source가 따로 있으면 내용을 다시 쓰기보다 해당 artifact를 연결한다.

## Templates

- [`.github/ISSUE_TEMPLATE/issue.md`](../ISSUE_TEMPLATE/issue.md): GitHub native Issue template
- [`.github/pull_request_template.md`](../pull_request_template.md): GitHub native Pull Request description
- [`pull-request-review.md`](pull-request-review.md): Pull Request review body

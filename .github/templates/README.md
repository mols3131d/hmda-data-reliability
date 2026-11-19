# GitHub Templates

Issue 작성 템플릿은 [`ISSUE_TEMPLATE/issue.md`](../ISSUE_TEMPLATE/issue.md), GitHub native Pull Request 템플릿은 [`pull_request_template.md`](../pull_request_template.md)에 둔다. 이 directory는 공통 작성 규칙과 GitHub가 자동 제공하지 않는 Pull Request Review 템플릿을 관리한다. GitHub native 템플릿은 default branch에 반영된 뒤 적용된다.

## Issue Composition

Issue는 문제 보고, 변경 제안, 조사 요청에 공통으로 사용한다. 다음 세 H2는 **필수**이며 아래 순서로 작성한다.

- **Summary:** 이슈의 핵심 문제·제안·조사 질문과 목적, 기대 결과를 요약한다.
- **Boundaries:** 해결·조사 대상, 명시적인 제외 범위, 제약 및 권한 경계를 구분한다.
- **Caveats:** 작성자가 독자의 오해 가능성, 확인되지 않은 가정, 불완전한 근거·재현·검증, 정보 부족과 해석의 한계를 드러낸다. 확인된 사항이 없다면 `N/A`와 그 이유를 적고 빈 섹션을 남기지 않는다.

그 외 H2/H3는 모두 **선택 사항**이다. `Acceptance`, `Context`, `Evidence`, `Environment`, `Open Decisions` 같은 이름은 예시일 뿐이며, 이슈의 작성 취지와 목적에 따라 제목·순서·하위 구성을 자유롭게 정한다. 불필요한 섹션과 placeholder는 제거한다.

확인한 사실과 추정·미확정 사항을 구분한다. 중복 설명, 불필요한 환경 정보 및 비밀 값은 제외하고, 별도 원본이 있는 요구사항과 증거는 링크로 연결한다.

## Metadata

GitHub가 제공하지 않는 정보만 optional YAML metadata로 보완한다. Metadata field는 서로 독립적이며 필요한 field만 사용한다.

- **Issue:** GitHub Markdown Issue 템플릿의 YAML Front Matter에는 필수 `name`과 `about`을 함께 둔다(`description`은 Issue Form 용도이므로 사용하지 않는다). `source_revision`, `author`, `environment`는 **완성된 이슈 본문 마지막의 단일 `yaml` code block**에 필요한 항목만 순서대로 기록한다. `environment`를 포함한 본문 metadata는 optional이며 미확인 값이나 placeholder는 제거한다. GitHub는 해당 YAML code block을 네이티브 이슈 속성으로 해석하지 않는다. 이미 생성된 이슈 본문에는 템플릿 전용 Front Matter(`name`, `about`)를 포함하지 않는다.
- **Pull Request / Review:** 기존과 같이 본문 마지막에 하나의 `yaml` code block으로 기록한다. PR의 `revision.base/head`는 비교 기준 commit pair이며 Issue의 `source_revision`과 다르다.

Markdown Issue 템플릿의 `name`·`about`은 템플릿 선택기에서 사용하는 설정이며, 생성된 이슈 본문으로 복사하는 metadata가 아니다. Issue/PR/Review 본문의 YAML code block은 GitHub metadata에 자동 연동되지 않는다. Issue 생성 도구는 기록할 metadata를 본문 마지막에 명시적으로 포함해야 한다. PR·Review에 footnote 정의가 있으면 metadata block 바로 앞에 두고 별도 `Metadata` heading은 만들지 않는다.

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

`environment`는 재현이나 판단에 영향을 주는 **확인된 실행 환경**을 기록하는 optional YAML map이다. 실행 환경이 이슈와 무관하거나 확인할 수 없으면 필드 자체를 생략하고, 필요한 미확정 사항은 `Caveats`에 설명한다.

`environment`를 사용하는 경우 다음 두 필드를 필수로 작성한다.

- **`runtime`:** 문제가 관찰된 주요 실행 엔진·서비스·플랫폼의 이름. 패키지나 관련 도구를 모두 나열하지 않는다.
- **`version`:** 해당 `runtime`의 확인된 버전. 추정값이나 임의 기본값은 사용하지 않는다.

그 외 `os`, `data`, `model`, `configuration` 등은 **이슈의 원인 분석·재현·판단에 영향을 미치는 경우에만** 추가한다. 추가 키의 이름과 구조는 관련 정보에 맞게 정하고, `configuration`을 사용할 때는 문자열 대신 개별 설정으로 구성한 map을 사용한다. 본문과 불필요하게 중복하거나 비밀 값을 노출하지 않는다.

```yaml
environment:
  runtime: Python
  version: "3.12"
  configuration:
    ingestion_mode: full
```

위 예시는 구조 설명용이며 실제 이슈에는 검증한 조건만 기재한다.

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

Issue 템플릿은 `name`·`about`을 Front Matter에 두고 optional metadata 예시를 본문 마지막 YAML code block에 둔다. 실제 Issue 작성 시 템플릿 Front Matter는 제거하고 필요한 metadata field만 남긴다. PR·Review 템플릿의 metadata 예시는 기본 읽기 흐름을 방해하지 않도록 HTML comment 안에 두며, 사용할 때는 comment를 제거하고 필요한 필드만 본문 마지막에 둔다.

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
- HTML tag로 해석될 수 있는 placeholder는 inline code나 escape로 표시한다.
- Template의 `<status>`와 다른 placeholder는 실제 내용으로 교체하고 남겨두지 않는다.
- repository 내부 path와 artifact는 repository-relative reference를 사용한다.
- 요구사항이나 결정의 source가 따로 있으면 내용을 다시 쓰기보다 해당 artifact를 연결한다.

## Templates

- [`.github/ISSUE_TEMPLATE/issue.md`](../ISSUE_TEMPLATE/issue.md): GitHub Markdown Issue 템플릿 (`name`·`about` 설정, 본문 YAML metadata)
- [`.github/pull_request_template.md`](../pull_request_template.md): GitHub native Pull Request description
- [`pull-request-review.md`](pull-request-review.md): Pull Request review body

<!--
관련 문서와 적용되는 에이전트 지침·Skill·Rule을 확인한다.
프로젝트 하네스: `CHATBOT.md`, `AGENTS.md`, `.agents/route/ROUTE.md` (연결된 `.agents/route/` 인덱스와 `.rulesync/` 포함).
사용자·로컬 환경의 별도 하네스도 있는지 확인하고, 적용되는 지침을 참고한다.
-->

## Summary

<!--
왜 이 변경이 필요한가? 병합 후 무엇이 달라지는가?
2~4문장으로 핵심부터 설명하고 구현 상세는 Changes에 둔다.
-->

<변경 이유와 기대 결과>

## Changes

<!--
검토자가 diff에서 확인해야 할 최종 변화는 무엇인가?
파일 목록보다 동작, 계약, 구조의 변화에 집중한다.
여러 하위 항목이 필요한 경우 nested list를 사용할 수 있으며 depth 2를 권장하고 최대 3까지만 사용한다.
-->

- <주요 변경>

## Validation

<!--
무엇을 확인했고 결과는 어땠는가?
실제로 수행한 검증만 기록한다. 중요한 미수행 검증은 ⚪ Not Verified로 남긴다.
상태: ✅ Pass / ❌ Fail / ⚪ Not Verified
-->

- `<status>` — `<check>`: <result 또는 evidence>

<!--
Optional — 판단 비용을 줄일 때만 해당 section을 추가한다.

- Boundaries — 범위를 오해하기 쉬울 때
  `## Boundaries` → `- **Out of Scope:** <의도적으로 제외한 범위>`
- Review Focus — 중요한 결정, trade-off, 가정을 집중 검토해야 할 때
  `## Review Focus` → `- <집중해서 검토할 결정, trade-off 또는 가정>`
- Risks — Validation과 별개로 병합 후에도 위험이나 제한이 남을 때
  `## Risks` → `- ⚠️ <위험 또는 제한>: <영향 또는 대응>`
- References — 요구사항이나 판단 근거를 다른 artifact가 소유할 때
  `## References` → `- <repository-relative path 또는 link>`

Validation 항목이 많고 Check / Result / Evidence 비교가 중요하면 table을 사용할 수 있다.

| Check | Result | Evidence |
| --- | --- | --- |
| `<check>` | `<status>` | `<evidence>` |
-->

<!--
Optional metadata — GitHub가 제공하지 않는 provenance가 판단에 필요할 때만 본문 마지막에 추가한다.
Footnote 정의가 있으면 metadata를 그 바로 앞에 두고 별도 Metadata heading은 만들지 않는다.
공통 규칙은 `.github/templates/README.md`를 따른다.

`author`는 Agent 주도 작성의 실제 작성 주체를 식별한다.
`revision`은 이 description의 validation과 상태 설명이 기준으로 삼은 exact base/head commit pair다.
`revision`을 사용한 뒤 base 또는 head가 바뀐 상태로 본문을 갱신하면 값도 함께 갱신한다.

```yaml
author:
  - <user-id>:<provider>-<service>
revision:
  base: <full-base-commit-sha>
  head: <full-head-commit-sha>
```
-->

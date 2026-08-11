## Summary

<!--
전체적으로 어떻게 판단했는가? 가장 중요한 근거는 무엇인가?
2~4문장으로 결론부터 쓰고 필요한 경우 다음 조치를 덧붙인다.
GitHub review decision은 본문에 반복하지 않는다.
-->

<검토 결론과 핵심 근거>

## Findings

<!--
수정하지 않으면 동작 오류, 위험 또는 저장소 계약 위반이 남는가?
확인된 문제만 finding으로 기록한다. 단순 선호나 근거 없는 가능성은 제외한다.
문제가 없으면 `✅ No findings`를 기록한다. 문제가 있으면 원인별로 F1, F2...를 작성한다.

중요도는 impact와 urgency를 기준으로 색 원형과 text label을 함께 표시한다.
🔴 Critical / 🟠 High / 🟡 Medium / 🔵 Low
-->

<finding 결과>

<!--
### <importance> — F1 · <finding title>

- **Location:** 어디에서 발생하는가?
- **Evidence:** 무엇으로 확인했는가?
- **Impact:** 수정하지 않으면 어떤 문제가 생기는가?
- **Required Change:** 무엇이 바뀌어야 해결되는가?
- **Uncertainty:** 중요한 미확인 전제가 있을 때만 추가한다.

예: `### 🟠 High — F1 · 검증 실패 전에 입력 기록이 생성됨`
-->

## Validation

<!--
무엇을 직접 확인했고 어떤 근거가 있는가?
diff, contract, test, command 등 실제 확인 결과만 기록한다.
중요한 미확인 영역은 ⚪ Not Verified로 남긴다.
상태: ✅ Pass / ❌ Fail / ⚪ Not Verified
-->

- <status> — `<check>`: <result 또는 evidence>

<!--
Optional — 판단 비용을 줄일 때만 해당 section을 추가한다.

- Scope — 일부만 검토했거나 특별한 기준을 적용했을 때
  `## Scope` → `- <검토 범위, 기준 또는 미검토 제한>`
- Remaining Risks — finding과 별개로 중요한 위험이나 후속 확인이 남을 때
  `## Remaining Risks` → `- ⚠️ <남은 위험 또는 후속 확인>`

Validation 항목이 많고 Check / Result / Evidence 비교가 중요하면 table을 사용할 수 있다.

| Check | Result | Evidence |
| --- | --- | --- |
| <check> | <status> | <evidence> |
-->

<!--
Optional metadata — GitHub가 제공하지 않는 provenance가 판단에 필요할 때만 본문 마지막에 추가한다.
Footnote 정의가 있으면 metadata를 그 바로 앞에 두고 별도 Metadata heading은 만들지 않는다.
공통 규칙은 `.github/templates/README.md`를 따른다.

`author`는 Agent가 review를 주도했지만 GitHub 작성자만으로 실제 작성 주체를 구별할 수 없을 때 사용한다.
`revision`은 이 review가 실제로 검토한 exact base/head commit pair를 고정한다. 이후 PR head가 바뀌어도 과거 review의 값은 바꾸지 않는다.

```yaml
author:
  - <user-id>:<provider>-<service>
revision:
  base: <full-base-commit-sha>
  head: <full-head-commit-sha>
```
-->

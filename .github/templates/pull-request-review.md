```yaml
# Optional: Agent가 주도했지만 GitHub 작성자만으로 실제 작성 주체를 구별할 수 없을 때 사용한다.
# author:
#   - <user-id>:<provider>-<service>
```

<!--
기본은 Summary, Findings, Validation이다.
Review 과정이 아니라 merge 판단에 필요한 결론, 확인된 문제, 검증 근거를 남긴다.
Optional section은 실제 판단 비용을 줄일 때만 추가하고, 사용하지 않는 placeholder는 제거한다.
-->

## Summary

<!-- 작성 질문: 전체적으로 어떻게 판단했는가? 가장 중요한 근거는 무엇인가? 필요한 경우 다음 조치를 덧붙인다. GitHub review decision은 반복하지 않는다. -->

<검토 결론과 핵심 근거>

## Findings

<!--
Finding 기준: 수정하지 않으면 동작 오류, 위험 또는 저장소 계약 위반이 남는 확인된 문제인가?
문제가 없으면 `None`. 문제가 있으면 원인별로 F1, F2...를 작성한다.
단순 선호나 근거 없는 가능성은 finding으로 만들지 않는다.
-->

None

<!--
### F1 — <finding title>

- **Location:** <문제가 있는 file, symbol, document 또는 behavior>
- **Evidence:** <문제를 확인한 code, contract, test 또는 관찰 결과>
- **Impact:** <수정하지 않을 때 발생하는 구체적인 영향>
- **Required Change:** <문제를 해소하기 위한 수정 또는 충족 조건>
- **Uncertainty:** <판단에 중요한 미확인 전제가 있을 때만 추가>
-->

## Validation

<!-- 작성 질문: 무엇을 직접 확인했고 어떤 근거가 있는가? 실제 확인한 diff, contract, test, command와 결과를 기록하고 중요한 미확인 영역은 Not Verified로 명시한다. -->

- **<Pass | Fail | Not Verified>** — <check>: <result 또는 evidence>

<!--
Optional — 필요한 section만 추가한다.

- Scope: 일부만 검토했거나 특별한 기준을 적용해 review 범위를 오해할 수 있을 때
- Remaining Risks: finding과 별개로 검토 후에도 중요한 위험이나 후속 확인이 남을 때

## Scope

- <검토 범위, 특별한 기준 또는 미검토 제한>

## Remaining Risks

- <남은 중요한 위험 또는 후속 확인>
-->

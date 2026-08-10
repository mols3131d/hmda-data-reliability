```yaml
# Optional: Agent가 주도했지만 GitHub 작성자만으로 실제 작성 주체를 구별할 수 없을 때 사용한다.
# author:
#   - <user-id>:<provider>-<service>
```

<!--
작성 순서: Summary → Findings → Validation.
결론을 먼저 쓰고, 확인된 문제와 검증 근거를 뒤에 둔다.
작성 후 빈 placeholder와 사용하지 않는 optional 항목은 제거한다.
-->

## Summary

<!--
전체적으로 어떻게 판단했는가? 가장 중요한 근거는 무엇인가?
2~4문장으로 요약하고 필요한 경우 다음 조치를 덧붙인다.
GitHub review decision은 본문에 반복하지 않는다.
-->

<검토 결론과 핵심 근거>

## Findings

<!--
수정하지 않으면 동작 오류, 위험 또는 저장소 계약 위반이 남는가?
확인된 문제만 finding으로 기록한다. 단순 선호나 가능성은 제외한다.
문제가 없으면 `None`. 있으면 원인별로 F1, F2...를 작성한다.
-->

None

<!--
Finding 형식:

### F1 — <finding title>
- **Location:** 어디에서 발생하는가?
- **Evidence:** 무엇으로 확인했는가?
- **Impact:** 수정하지 않으면 어떤 문제가 생기는가?
- **Required Change:** 무엇이 바뀌어야 해결되는가?
- **Uncertainty:** 중요한 미확인 전제가 있을 때만 추가한다.
-->

## Validation

<!--
무엇을 직접 확인했고 어떤 근거가 있는가?
diff, contract, test, command 등 실제 확인 결과만 기록한다.
중요한 미확인 영역은 Not Verified로 남긴다.
-->

- **<Pass | Fail | Not Verified>** — <check>: <result 또는 evidence>

<!--
Optional — 판단에 도움이 될 때만 추가한다.
- Scope: 일부만 검토했거나 특별한 기준을 적용했을 때
- Remaining Risks: finding과 별개로 중요한 위험이나 후속 확인이 남을 때
-->

```yaml
# Optional: Agent가 주도했지만 GitHub 작성자만으로 실제 작성 주체를 구별할 수 없을 때 사용한다.
# author:
#   - <user-id>:<provider>-<service>
```

<!-- 기본: Summary, Findings, Validation. Optional section과 빈 placeholder는 제거한다. -->

## Summary

<결론, 핵심 근거, 필요한 다음 조치>

## Scope

<!-- Optional: 일부만 검토했거나 특별한 기준을 적용했을 때만 유지한다. -->

- <검토 범위와 기준>
- <미검토 범위 또는 제한>

## Findings

<!-- 없으면 `None`. 있으면 문제별로 F1, F2... 반복하고 같은 root cause는 중복하지 않는다. -->

### F1 — <finding title>

- **Location:** <file, symbol, document 또는 behavior>
- **Evidence:** <확인된 code, contract, test 또는 관찰 결과>
- **Impact:** <수정하지 않을 때의 구체적인 영향>
- **Required Change:** <필요한 수정 또는 충족 조건>
<!-- Optional: 중요한 미확인 전제가 있을 때만 `- **Uncertainty:** <내용>`을 추가한다. -->

## Validation

<!-- 실제 확인한 것만 기록하고, 수행하지 않은 검증은 Not Verified로 구분한다. -->

- **<Pass | Fail | Not Verified>** — <check>: <evidence>

## Remaining Risks

<!-- Optional: 수정 후에도 남는 중요한 위험이나 후속 확인이 있을 때만 유지한다. -->

- <남은 위험 또는 후속 확인>

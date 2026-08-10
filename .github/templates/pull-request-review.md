```yaml
# OPTIONAL: Agent가 review 작성을 주도했으나 GitHub 계정만으로 실제 작성 주체를 구별할 수 없을 때만 사용한다.
# author:
#   - <user-id>:<provider>-<service>
```

<!--
작성 규칙:
- 결론 요약, Findings, Validation은 기본적으로 유지한다.
- Scope와 Remaining Risks는 필요한 경우에만 유지한다.
- 확인된 문제만 finding으로 기록하고 같은 root cause를 반복하지 않는다.
- GitHub가 소유하는 Approve / Comment / Request Changes decision은 본문에 반복하지 않는다.
- 빈 placeholder와 불필요한 안내 주석은 작성 후 제거할 수 있다.
-->

> [!NOTE]
> <!-- REQUIRED: 검토 결론과 가장 중요한 근거를 짧게 요약한다. 수정이 필요하면 필요한 다음 조치까지 포함한다. -->
> <검토 결론과 핵심 근거>

## Scope

<!-- OPTIONAL: 전체 PR이 아닌 일부만 검토했거나 특별한 기준을 적용했을 때만 유지한다. -->

- <검토한 범위와 기준>
- <판단에 영향을 주는 미검토 범위 또는 제한>

## Findings

<!--
REQUIRED:
- 발견 사항이 없으면 `None`만 기록한다.
- 발견 사항이 있으면 F1부터 독립적인 finding 단위로 반복한다.
- Location, Evidence, Impact, Required Change가 서로 같은 문제를 설명해야 한다.
- Uncertainty는 중요한 미확인 전제가 있을 때만 유지한다.
-->

### F1 — <finding title>

- **Location:** <file, symbol, document 또는 behavior>
- **Evidence:** <확인된 code, contract, test 또는 관찰 결과>
- **Impact:** <수정하지 않을 때의 구체적인 영향>
- **Required Change:** <필요한 수정 또는 충족 조건>
- **Uncertainty:** <남은 불확실성 또는 미확인 전제>

## Validation

<!-- REQUIRED: 실제 검토에 사용한 check와 evidence를 기록한다. 수행하지 않은 검증은 Not Verified로 구분한다. -->

| Check | Evidence | Result |
| --- | --- | --- |
| <검증 항목> | <실행 결과, 문서, diff 또는 관찰 근거> | <Pass / Fail / Not Verified> |

## Remaining Risks

<!-- OPTIONAL: finding 수정 후에도 남는 위험, 검토 범위 밖의 중요한 제한 또는 후속 확인이 있을 때만 유지한다. -->

- <남은 위험 또는 후속 확인>

```yaml
# OPTIONAL: Agent가 작성을 주도했으나 GitHub 계정만으로 실제 작성 주체를 구별할 수 없을 때만 사용한다.
# author:
#   - <user-id>:<provider>-<service>
```

<!--
작성 규칙:
- Summary, Changes, Validation은 기본적으로 유지한다.
- OPTIONAL section은 내용이 있을 때만 유지한다.
- 빈 placeholder와 불필요한 예시는 제거한다.
- 작업 과정이나 시행착오보다 최종 net change와 검증 근거를 기록한다.
-->

## Summary

<!-- REQUIRED: 왜 변경하는지와 변경 후 기대되는 결과를 짧게 설명한다. 구현 상세는 Changes에 둔다. -->

<변경 이유와 기대 결과>

## Changes

<!-- REQUIRED: 최종적으로 남은 주요 변경만 기록한다. 되돌린 시도나 임시 작업은 나열하지 않는다. -->

- <추가·수정·삭제된 핵심 변경>

## Boundaries

<!-- OPTIONAL: 의도적으로 제외한 범위나 scope 오해 가능성이 있을 때만 유지한다. -->

| In Scope | Out of Scope |
| --- | --- |
| <이번 PR이 책임지는 범위> | <의도적으로 다루지 않는 범위> |

## Validation

<!-- REQUIRED: 실제 수행한 검증과 그 근거를 기록한다. 수행하지 않은 검증은 숨기지 말고 Not Verified로 표시한다. -->

| Check | Evidence | Result |
| --- | --- | --- |
| <검증 항목> | <test, command, diff 또는 관찰 근거> | <Pass / Fail / Not Verified> |

## Review Focus

<!-- OPTIONAL: 인간 또는 다음 reviewer의 판단이 특히 필요한 부분이 있을 때만 유지한다. -->

- <설계 trade-off, 중요한 가정 또는 집중해서 볼 부분>

## Risks

<!-- OPTIONAL: 미검증 사항, 제한 또는 merge 후에도 남는 위험이 있을 때만 유지한다. -->

- <남은 위험 또는 제한>

## References

<!-- OPTIONAL: 변경 목적이나 검증 기준을 소유하는 OpenSpec, inbox artifact 또는 canonical document가 있을 때만 유지한다. -->

- <reference>

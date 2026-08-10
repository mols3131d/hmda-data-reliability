```yaml
# Optional: Agent가 주도했지만 GitHub 작성자만으로 실제 작성 주체를 구별할 수 없을 때 사용한다.
# author:
#   - <user-id>:<provider>-<service>
```

<!--
기본은 Summary, Changes, Validation이다.
작업 과정보다 reviewer가 변경 목적, 결과, 검증을 빠르게 이해하는 데 필요한 최종 정보만 남긴다.
Optional section은 실제 판단 비용을 줄일 때만 추가하고, 사용하지 않는 placeholder는 제거한다.
-->

## Summary

<!-- 작성 질문: 왜 이 변경이 필요한가? merge되면 무엇이 달라지는가? 보통 2~4문장이면 충분하다. -->

<변경 이유와 기대 결과>

## Changes

<!-- 작성 질문: reviewer가 diff에서 확인해야 할 핵심 변화는 무엇인가? 파일 목록보다 동작, 계약, 구조의 변화에 집중한다. -->

- <주요 변경>

## Validation

<!-- 작성 질문: 무엇을 확인했고 결과는 어땠는가? 실제 수행한 검증만 기록하고, 중요한 미수행 검증은 Not Verified로 명시한다. -->

- **<Pass | Fail | Not Verified>** — <check>: <result 또는 evidence>

<!--
Optional — 필요한 section만 추가한다.

- Boundaries: PR이 다루지 않는 범위를 오해하기 쉬울 때
- Review Focus: trade-off, 가정 등 인간 판단이 특히 필요한 부분이 있을 때
- Risks: Validation과 별개로 merge 후에도 위험이나 제한이 남을 때
- References: 요구사항이나 판단 근거를 다른 artifact가 소유할 때

## Boundaries

- **Out of Scope:** <의도적으로 제외한 범위>

## Review Focus

- <집중해서 검토할 결정, trade-off 또는 가정>

## Risks

- <merge 후에도 남는 위험 또는 제한>

## References

- <OpenSpec, inbox artifact 또는 canonical document>
-->

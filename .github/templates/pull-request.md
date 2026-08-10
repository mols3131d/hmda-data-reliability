```yaml
# Optional: Agent가 주도했지만 GitHub 작성자만으로 실제 작성 주체를 구별할 수 없을 때 사용한다.
# author:
#   - <user-id>:<provider>-<service>
```

<!--
작성 순서: Summary → Changes → Validation.
이 세 section으로 충분하면 나머지는 추가하지 않는다.
작성 후 빈 placeholder와 사용하지 않는 optional 항목은 제거한다.
-->

## Summary

<!--
왜 이 변경이 필요한가? 병합 후 무엇이 달라지는가?
2~4문장으로 설명하고 구현 상세는 Changes에 둔다.
-->

<변경 이유와 기대 결과>

## Changes

<!--
검토자가 diff에서 확인해야 할 최종 변화는 무엇인가?
파일 목록보다 동작, 계약, 구조의 변화에 집중한다.
-->

- <주요 변경>

## Validation

<!--
무엇을 확인했고 결과는 어땠는가?
실제로 수행한 검증만 기록하고 중요한 미수행 검증은 Not Verified로 남긴다.
-->

- **<Pass | Fail | Not Verified>** — <check>: <result 또는 evidence>

<!--
Optional — 판단에 도움이 될 때만 추가한다.
- Boundaries: 범위를 오해하기 쉬울 때
- Review Focus: 중요한 결정, trade-off, 가정을 집중 검토해야 할 때
- Risks: 병합 후에도 위험이나 제한이 남을 때
- References: 판단 근거를 다른 artifact가 소유할 때
-->

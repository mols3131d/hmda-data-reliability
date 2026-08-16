# MVP Domain Milestone: Reliability

## Goal

Data Lake의 실제 evidence로 incident를 결정론적으로 판단하고 안전하게 복구하며,
그 결과를 **제한된 LLM reviewer가 설명·검토**할 수 있게 한다.

## Outcomes

### Deterministic Reliability

- clean state와 최소 한 개 controlled incident를 재현 가능하게 구분한다.
- incident, impact와 `RemediationDraft`가 raw/dbt evidence를 참조한다.
- candidate validation과 approval 이전 단계는 current state를 변경하지 않는다.
- stale, diverged 또는 불완전한 approval은 mutation 전에 차단된다.
- 승인된 recovery 뒤 incident 해소와 downstream validation을 다시 확인할 수 있다.
- retry와 failure가 필요한 reconciliation action과 함께 evidence로 남는다.

### Minimal Agentic Review

- LLM reviewer는 `Incident`, evidence와 deterministic `RemediationDraft`를 입력으로 받는다.
- 결과는 summary, evidence used, likely cause, draft review와 warning을 구조화해 반환한다.
- 사용한 evidence는 실제 입력 evidence의 범위를 벗어나지 않는지 deterministic check가 가능하다.
- LLM은 detection 결과를 덮어쓰거나 approval/recovery action을 직접 실행하지 않는다.
- invocation은 incident/evidence identity, prompt/version, model과 structured output을
  다시 연결할 수 있는 최소 trace를 남긴다.

## Done When

하나의 synthetic incident에서 다음 흐름을 current revision으로 재현하면 완료한다.

```text
deterministic detection
→ evidence + RemediationDraft
→ real LLM invocation
→ structured review + safety checks
→ external human approval
→ approved recovery
→ deterministic re-validation
```

LLM review가 실패하거나 부적절한 action을 제안해도 mutation 권한을 얻지 못해야 한다.

## Non-Goals

- LLM 기반 incident detection
- LLM이 처음부터 자유롭게 recovery plan을 생성하거나 직접 실행
- 모든 incident type의 Agentic parity
- autonomous multi-agent RCA와 approval
- 특정 model provider 또는 LLMOps vendor를 MVP contract로 고정
- production prompt management와 online evaluation platform

## References

- [Reliability Domain](../../domains/reliability.md)
- [MVP](README.md)
- `src/project_pivot/reliability/`
- `tests/reliability/`

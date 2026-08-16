# MVP Domain: Reliability

## Mission

데이터 문제를 **결정론적으로 증명하고, AI가 그 evidence를 제한된 범위에서 해석하며,
사람이 승인한 recovery만 안전하게 실행되는 최소 Agentic Reliability lifecycle**을 제공한다.

Reliability domain은 Project Pivot MVP의 차별화 지점이다. LLM을 truth source나 execution
controller로 사용하지 않고, 검증 가능한 deterministic layer 위에 review capability로 배치한다.

## MVP Capability Layers

### Deterministic Truth

- clean state와 대표 synthetic incident를 재현 가능하게 구분한다.
- incident를 뒷받침하는 profile/evidence와 downstream impact를 만든다.
- deterministic `RemediationDraft`를 제공해 AI가 자유롭게 action space를 발명하지 않게 한다.
- candidate, approval, recovery와 post-recovery verification에 필요한 state identity를 유지한다.

### Bounded Agentic Review

- 실제 model invocation이 deterministic incident, evidence, impact와 `RemediationDraft`를 입력으로 사용한다.
- 결과는 사람이 검토하고 코드로 평가할 수 있는 structured contract로 반환한다.
- review가 사용한 evidence와 invocation 조건을 다시 식별할 수 있는 execution evidence를 남긴다.
- deterministic safety evaluation이 최소한 output structure, evidence reference와 금지된 action boundary를 확인한다.
- uncertainty나 근거 부족은 숨기지 않고 review 결과에 표현한다.

Agentic reviewer는 deterministic result를 **설명·검토·보강**한다. Detection rule, recovery
proposal identity 또는 approval decision을 대체하지 않는다.

### Human-Controlled Recovery

- recovery proposal은 검증한 target/evidence state와 결합된다.
- incomplete approval, invalid candidate, stale/diverged target은 mutation 전에 차단된다.
- 승인된 recovery만 expected state를 복원한다.
- recovery 뒤 같은 deterministic lifecycle을 다시 실행해 incident 해소를 검증한다.
- retry/replay는 duplicate mutation 없이 필요한 verification을 이어간다.

## Done When

대표 synthetic incident 하나가 다음 lifecycle을 **한 current revision에서** 재현하면 완료다.

```text
clean baseline
→ controlled incident
→ deterministic evidence + impact + RemediationDraft
→ bounded Agentic review
→ deterministic review evaluation
→ external human approval
→ approved recovery
→ deterministic re-validation
→ replay/failure evidence
```

이 proof에서 다음이 동시에 확인되어야 한다.

- Agentic review 없이도 incident의 핵심 사실과 safety gate를 deterministic하게 판단할 수 있다.
- 실제 Agentic invocation이 evidence-bound structured review를 생성한다.
- 어떤 evidence와 invocation 조건이 결과를 만들었는지 추적할 수 있다.
- Agentic output만으로 state mutation을 시작할 수 없다.
- approved recovery 뒤 incident가 해소되고 downstream validation이 정상 state를 확인한다.
- expected failure와 retry path가 검토 가능한 evidence로 남는다.

## Boundary

**Owns**

- profiling, incident detection과 impact evidence
- deterministic remediation baseline
- bounded Agentic review contract와 safety evaluation
- recovery proposal/approval boundary를 사용하는 recovery execution
- post-recovery evaluation과 replay evidence

**Does not own**

- 외부 인간의 approval decision 자체
- Dagster reliability control-plane
- LLM 기반 anomaly detection
- approval 없는 autonomous recovery
- 범용 autonomous RCA와 multi-agent planning
- 특정 model provider 또는 LLMOps vendor의 운영 방식

## Acceptance Evidence

- `src/project_pivot/reliability/`
- `tests/reliability/`
- incident lifecycle, recovery와 evaluation 관련 OpenSpec
- Agentic review가 구현되면 해당 structured contract, trace/evaluation test evidence

## References

- [MVP](README.md)
- [Reliability Domain](../../domains/reliability.md)
- [Architecture](../../ARCHITECTURE.md)

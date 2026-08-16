# MVP Domain: Reliability

## Mission

데이터 문제를 **결정론적으로 증명하고, AI가 그 evidence를 제한된 범위에서 해석하며,
사람이 승인한 recovery만 안전하게 실행되는 최소 Agentic Reliability lifecycle**을 제공한다.

Reliability domain은 LLM을 truth source나 execution controller로 사용하지 않는다.
Deterministic truth와 safety contract를 먼저 만들고 그 위에 Agentic review를 별도 layer로 배치한다.

## MVP Capability Layers

### Deterministic Truth

- clean state와 대표 synthetic incident를 재현 가능하게 구분한다.
- incident를 뒷받침하는 profile/evidence와 downstream impact를 만든다.
- 기존 `RemediationDraft`를 결정론적으로 생성해 AI가 action space를 자유롭게 발명하지 않게 한다.
- candidate, approval, recovery와 post-recovery verification에 필요한 state identity를 유지한다.

### Bounded Agentic Review

Agentic reviewer는 기존 read-only lifecycle의 detection/impact/remediation node를 LLM으로
대체하지 않는다. Lifecycle이 만든 deterministic 결과를 **소비하는 별도 review layer**다.

- 실제 model invocation은 deterministic incident, evidence, impact와 `RemediationDraft`를 입력으로 사용한다.
- 결과는 사람이 검토하고 코드로 평가할 수 있는 structured contract로 반환한다.
- review가 사용한 evidence와 model/prompt 조건을 다시 식별할 수 있는 invocation evidence를 남긴다.
- uncertainty나 근거 부족은 숨기지 않고 review 결과에 표현한다.

Agentic reviewer는 deterministic result를 **설명·검토·보강**한다. Detection rule,
`RemediationDraft`, recovery proposal identity 또는 approval decision을 대체하지 않는다.
Reviewer availability나 review 결과 자체는 기존 approval/recovery contract에 새로운 권한
조건을 추가하지 않는다.

### Human-Controlled Recovery

- recovery proposal은 검증한 target/evidence state와 결합된다.
- incomplete approval, invalid candidate, stale/diverged target은 mutation 전에 차단된다.
- 승인된 recovery만 expected state를 복원한다.
- recovery 뒤 같은 deterministic lifecycle을 다시 실행해 incident 해소를 검증한다.
- retry/replay는 duplicate mutation 없이 필요한 verification을 이어간다.

Agentic review는 MVP end-to-end proof에 포함되지만 recovery authorization의 source는 아니다.
Invalid/unavailable Agentic output은 review proof를 실패시키며 mutation permission을 만들거나
완화하지 않는다.

## Agentic Proof Model

Agentic MVP는 **deterministic contract proof**와 **live model proof**를 분리한다. 둘 다 필요하지만
같은 검증 성격으로 취급하지 않는다.

### Contract Proof

외부 model availability와 무관하게 반복 가능한 acceptance다.

- structured review schema와 validation
- 허용된 evidence만 참조하는 evidence binding
- approval/recovery authority를 만들지 않는 forbidden-action guardrail
- known synthetic case에 대한 deterministic evaluator
- invalid/unsupported output의 fail-closed behavior

이 proof는 regression과 CI에 적합해야 한다.

### Live Model Proof

실제 Agentic capability가 단순 mock이나 deterministic rule wrapper가 아님을 확인한다.

- current revision에서 실제 model invocation을 최소 한 번 수행한다.
- model과 주요 config, prompt identity/version, project revision, evidence references와
  structured output을 남긴다.
- latency와 provider가 제공하는 usage(token/cost)를 invocation evidence에 포함한다.
- contract proof가 정의한 validator와 safety evaluator를 통과한다.
- exact prose나 token sequence의 재현성은 요구하지 않는다.

Live proof는 configured provider와 network를 요구할 수 있다. Provider 자체는 MVP contract가
아니며, live proof의 non-determinism을 deterministic regression에 전파하지 않는다.

## Done When

대표 synthetic incident 하나가 다음 proof를 **한 current revision에서** 연결하고,
Agentic contract proof와 live model proof가 모두 확인되면 완료다.

```text
clean baseline
→ controlled incident
→ deterministic evidence + impact + RemediationDraft
├→ bounded Agentic review → contract validation / safety evaluation
└→ external human approval → approved recovery
→ deterministic re-validation
→ replay/failure evidence
```

다음 조건을 동시에 만족해야 한다.

- Agentic review 없이도 incident의 핵심 사실과 safety gate를 deterministic하게 판단할 수 있다.
- deterministic contract proof가 외부 model 호출 없이 반복 가능하다.
- 실제 model invocation이 evidence-bound structured review를 생성하고 observability evidence를 남긴다.
- Agentic review가 기존 approval/recovery authority를 획득하거나 변경하지 않는다.
- Agentic output만으로 state mutation을 시작할 수 없다.
- approved recovery 뒤 incident가 해소되고 downstream validation이 정상 state를 확인한다.
- expected failure와 retry path가 검토 가능한 evidence로 남는다.

## Boundary

**Owns**

- profiling, incident detection과 impact evidence
- deterministic `RemediationDraft`
- bounded Agentic review contract, validation과 safety evaluation
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
- Agentic review 구현 이후 structured contract, deterministic evaluator와 live invocation evidence

## References

- [MVP](README.md)
- [Reliability Domain](../../domains/reliability.md)
- [Architecture](../../ARCHITECTURE.md)

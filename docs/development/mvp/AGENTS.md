# MVP Documentation Instructions

이 directory는 Project Pivot MVP의 **목표, domain별 완료 gate, 현재 상태**를 관리한다.
구현 세부를 복제하는 문서 집합이 아니라, 무엇을 증명해야 MVP라고 부를 수 있는지
검토 가능한 수준으로 유지한다.

## Ownership

- [`README.md`](README.md)는 MVP의 가치 제안, system invariants, scope와 전체 완료 기준을 소유한다.
- Domain 문서는 해당 domain이 MVP에 기여해야 하는 결과와 완료 경계를 소유한다.
- `status.yml`은 domain state와 blocker의 구조화된 정본이다.
- `status.md`는 `status.yml`을 사람이 판단하기 쉽게 설명한다.
- 세부 runtime behavior, API와 requirement는 OpenSpec, `docs/domains/**`와 tests가 소유한다.

## Domain Gates

현재 canonical domain인 HMDA Data, Data Platform, Data Operations, Reliability,
Orchestration을 기준으로 문서 하나씩 둔다.

Domain 문서는 구현 순서나 task 목록이 아니다. 다음 질문에만 답한다.

1. 이 domain이 MVP에 왜 필요한가?
2. MVP에서 반드시 어떤 결과를 제공해야 하는가?
3. 무엇을 관찰하면 완료라고 판단할 수 있는가?
4. 어떤 책임은 의도적으로 소유하지 않는가?
5. 완료 판단은 어디의 evidence로 확인하는가?

API, class, fixture, test function과 세부 algorithm은 domain 문서에 복제하지 않는다.
Canonical domain ownership과 충돌하면 `docs/domains/**`를 우선하고 MVP 문서를 고친다.

## MVP Model

MVP는 두 capability를 함께 증명한다.

- **Minimal Data Lake** — HMDA Data가 Source→Bronze를 소유하고, Data Platform이 Bronze를
  dbt analytical layer로 변환하며, Orchestration이 data plane을 반복 실행한다.
- **Agentic Reliability** — deterministic reliability evidence와 기존 `RemediationDraft`를
  제한된 Agentic reviewer가 설명·검토하고, 실제 state change는 human approval 뒤에만 일어난다.

Reliability는 deterministic truth, Agentic review와 human-controlled recovery 사이의
evidence와 safety boundary를 소유한다.

## Agentic Boundary

- deterministic detection, impact와 `RemediationDraft`가 LLM 판단보다 먼저 존재한다.
- Agentic reviewer는 기존 deterministic lifecycle을 대체하지 않고 그 결과를 소비하는 별도 layer다.
- Agentic output은 deterministic fact나 `RemediationDraft`를 대체하지 않고 설명·검토·보강한다.
- Agentic output은 approval이나 recovery command가 아니다.
- Agentic review는 MVP proof에는 필요하지만 기존 approval/recovery authority에 새로운 권한
  조건을 추가하지 않는다.
- **Contract proof**는 structured schema, evidence binding, forbidden-action guardrail과
  deterministic evaluator를 외부 model 호출 없이 반복 검증한다.
- **Live model proof**는 같은 current revision에서 실제 model invocation과 observability
  evidence를 최소 한 번 확인한다.
- Live evidence에는 model/config, prompt identity, project revision, evidence refs, structured
  output, latency와 provider가 제공하는 usage(token/cost)를 포함한다.
- Live model proof의 non-determinism을 deterministic regression이나 CI의 전제조건으로 만들지 않는다.
- 특정 model provider나 LLMOps vendor는 MVP의 canonical dependency가 아니다.
- autonomous recovery, 범용 autonomous RCA와 multi-agent orchestration은 MVP 밖이다.

## Status Model

- task 수, test 수 또는 임의의 `x/y`를 MVP 진행률로 사용하지 않는다.
- canonical progress axis는 **domain state** 하나다.
- domain implementation state는 `implemented`, `partial`, `blocked`로 기록한다.
- implementation state와 current-revision validation을 분리한다.
- system-level capability/proof 상태는 domain state와 blocker에서 파생하며 독립 progress 표로 중복 관리하지 않는다.
- 실행하지 않은 validation을 `passing`으로 기록하지 않는다.
- `status.yml`과 `status.md`가 충돌하면 current evidence를 확인해 YAML을 먼저 갱신한다.
- MVP 전체는 모든 required domain gate가 구현되고 같은 current revision에서 system acceptance가 확인되어야 완료다.

## Writing

- 목표 → 필요한 결과 → 완료 evidence → boundary 순서로 작성한다.
- KISS와 DRY를 따른다.
- 목표, 현재 사실, 비목표와 미검증 상태를 구분한다.
- 외부 research는 판단에 참고할 수 있지만 이 directory의 canonical 목표는 자족적으로 설명한다.
- 특정 tool이나 구현 선택은 그것이 MVP의 본질적 contract일 때만 명시한다.
- 후속 roadmap을 현재 MVP 완료 조건에 섞지 않는다.

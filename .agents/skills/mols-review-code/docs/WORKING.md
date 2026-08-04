# Working

이 문서는 현재 작업 기준선이다. 과거 작업 로그가 아니라 현재 구조, 검증 상태와 남은 문제만 유지한다.

## Current State

`mols-review-code`는 구현 코드와 테스트 코드를 근거 중심으로 검토하는 범용 Code Review 엔진이다.

```text
mols-review-code/
├── README.md
├── SKILL.md
├── docs/
│   ├── DIRECTIVE.md
│   └── WORKING.md
└── references/
    ├── findings.md
    ├── implementation.md
    ├── tests.md
    └── workflow.md
```

특정 Agent, Review workflow, VCS와 Review artifact에 의존하지 않는다. 호출자는 자신의 권한, perspective, severity와 verdict 계약을 유지한다.

## Arguments

현재 지원하는 Argument는 일곱 개다.

- `target`
- `baseline`
- `contract`
- `scope`
- `exclude`
- `focus`
- `validation`

유효한 baseline이나 contract를 확인할 수 없으면 임의로 만들지 않고 Review 제한으로 보존한다.

## Review Model

```text
Target
→ Baseline and contract
→ Changed behavior and scope
→ Implementation and/or test lens
→ Focused validation
→ Candidate verification
→ Findings and uncertainty
```

- 공통 workflow는 대상과 기대 동작, 영향 범위와 evidence를 해석한다.
- Implementation lens는 runtime behavior, contract, state, failure와 regression을 검토한다.
- Test lens는 scenario, oracle, false green, isolation과 validation 신뢰성을 검토한다.
- Findings lens는 candidate를 reachability, safeguard, baseline과 impact로 재검증한다.
- Severity, verdict와 결과 저장 형식은 호출자의 Review 계약을 따른다.

## Split Decision

현재 구현 Review와 테스트 Review는 별도 스킬로 나누지 않는다.

| 기준 | 판단 |
| --- | --- |
| 공통 입력 | target, baseline, contract와 scope를 공유한다. |
| 공통 workflow | 영향 추적, regression과 evidence 검증이 동일하다. |
| 대상별 전문성 | `implementation.md`와 `tests.md`로 충분히 분리된다. |
| 분리 비용 | 공통 규칙 중복과 두 스킬의 판단 불일치 위험이 크다. |
| 독립 필요성 | 테스트 Review만의 별도 lifecycle과 출력 계약이 아직 없다. |

다음 조건이 실제로 생길 때만 `mols-review-tests` 같은 독립 스킬을 검토한다.

- 테스트 설계와 구현이 Code Review와 별개의 반복 workflow가 됨
- test artifact만을 위한 독립 입력, 완료 상태와 저장 계약이 생김
- test-specific 규칙이 공통 Code Review보다 커져 점진적 공개로도 관리하기 어려움
- 구현과 무관한 test suite audit가 주요 사용 사례가 됨

## Validation

### Structure

- `SKILL.md`에는 공통 workflow, Reference 선택과 boundary만 둔다.
- 구현, 테스트와 finding 기준은 서로 다른 Reference가 관리한다.
- 사용자 설명과 분리 결정은 `README.md`에 있다.
- 목적, 불변 조건과 설계 결정은 `DIRECTIVE.md`가 관리한다.
- Agent 이름과 Agent 간 실행 구조를 포함하지 않는다.

### Quality

- KISS: 하나의 engine과 네 개의 단일 책임 Reference로 구성한다.
- DRY: target, contract, scope와 validation workflow는 한 곳에서만 정의한다.
- 독립성: Agent, OpenSpec, pull request와 artifact format 없이 사용할 수 있다.
- 범용성: diff, file, revision, pull request와 current-state Review를 지원한다.
- Finding 품질: location, evidence, reachability와 impact를 요구한다.
- 비용 통제: 가장 작은 validation과 finding을 바꿀 수 있는 context만 탐색한다.
- 인간 편집성: 각 file의 책임과 변경 지점이 명확하다.

## Remaining Validation

- 실제 implementation-only Review로 scope와 baseline 자동 해석을 검증해야 한다.
- test-only Review로 oracle과 false green 기준을 도그푸딩해야 한다.
- 구현·테스트 혼합 변경에서 두 lens가 중복 finding을 만들지 않는지 확인해야 한다.
- 서로 다른 reviewer perspective에서도 같은 evidence가 과도하게 같은 결론을 강제하지 않는지 확인해야 한다.

정적 구조와 문서 간 책임 검증은 완료됐다. 현재 차단 요소는 없다.

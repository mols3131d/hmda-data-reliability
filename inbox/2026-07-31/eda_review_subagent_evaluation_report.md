---
title: "EDA Review Subagent 평가 보고서"
description: "2026-07-31 HMDA EDA review에 참여한 general-reviewer와 adversarial-reviewer의 역할 수행과 개선점을 평가한다."
date: 2026-07-31
---

# EDA Review Subagent 평가 보고서

## Summary

이번 HMDA EDA review에는 `general-reviewer`와 `adversarial-reviewer`를 병렬로
사용했다. 두 agent는 fixture contract가 실제 memory gate에서 충분히 강제되지
않는다는 P1 finding을 독립적으로 확인했다. 이는 최종 review의 신뢰도를 높인
가장 큰 기여다.

다만 두 결과 모두 정적 review 중심이었고, 실행 검증의 부재 또는 범위를 결과
형식에서 일관되게 분리하지 못했다. 또한 `adversarial-reviewer`는 유용한 추가
위험을 찾았지만 runner exception path의 실제 재현 증거는 남기지 않았다.

| Agent | Score | Verdict |
| --- | ---: | --- |
| `general-reviewer` | 8.0/10 | spec과 implementation의 직접적인 contract gap을 정확히 식별했다. |
| `adversarial-reviewer` | 8.5/10 | false pass, cleanup, evidence traceability 관점에서 review 범위를 효과적으로 확장했다. |
| Combined delegation | 8.5/10 | 공통 P1 finding을 독립적으로 재확인했고, 역할 중복은 제한적이었다. |

## Review Assignment

| Agent | Assigned focus | Expected contribution |
| --- | --- | --- |
| `general-reviewer` | correctness, regression, contract gap, missing validation | EDA baseline의 구현과 canonical spec 사이의 직접 불일치 식별 |
| `adversarial-reviewer` | reachable failure, false pass, resource cleanup, misuse of evidence | 정상 통과처럼 보이는 실패 조건과 운영상 회복성 위험 탐색 |

두 agent 모두 code 수정 없이 read-only review를 수행하도록 제한했다. main agent는
artifact, implementation, tests, canonical spec을 먼저 수집한 뒤 병렬 review를
시작했다.

## Agent Evaluation

### `general-reviewer`: 8.0/10

#### General Reviewer Strong Points

- fixture manifest의 느슨한 type과 validation 범위를 정확한 code 위치에 연결했다.
- manifest의 `schema_columns`, `row_width_bytes`, `null_rates`,
  `activity_year_cardinality`, `activity_year_skew`가 기록만 될 뿐 preflight에서
  검증되지 않는 점을 찾아냈다.
- `expected["null_counts"]`에 있는 column만 비교하므로 required column 전체의
  null invariant가 memory gate에 포함되지 않는 점을 명확히 설명했다.
- canonical OpenSpec의 fixture 필수 특성 및 required-column null invariant 요구와
  구현의 차이를 직접 연결했다.
- completion report가 fixture-level memory result를 full-source guarantee로
  확대하지 않았다는 점을 확인해, 근거 없는 finding을 추가하지 않았다.

#### General Reviewer Gaps

| Gap | Impact | Improvement |
| --- | --- | --- |
| P1 finding 하나에 집중돼 runner failure handling과 evidence traceability를 발견하지 못함 | review breadth가 adversarial reviewer에 의존 | contract review에서도 lifecycle, report provenance checklist를 포함 |
| 정적 분석과 실행 검증을 finding 본문에서 분리하지 않음 | finding의 확정 수준을 독자가 즉시 판단하기 어려움 | 각 finding에 `Validation: static inspection only` 또는 실행 결과를 명시 |
| fixture artifact의 실제 file hash를 대조하지 못한 한계를 언급했지만, artifact 부재 원인을 별도로 분류하지 않음 | artifact packaging 문제와 code contract 문제를 구분하기 어려움 | `code defect`, `artifact availability`, `unverified hypothesis`를 별도 field로 표기 |

#### General Reviewer Assessment

`general-reviewer`는 가장 중요한 spec-to-code gap을 정확히 찾아냈다. P1 finding의
근거는 manifest model, fixture validation, evidence validation, test scope와
canonical spec을 동시에 대조한 데 있다. 이 agent는 narrow correctness review에는
강했지만, runner lifecycle과 audit trail까지 넓히는 역할은 상대적으로 약했다.

### `adversarial-reviewer`: 8.5/10

#### Adversarial Reviewer Strong Points

- fixture가 full-source의 column 수와 type 다양성을 충분히 반영하지 못해
  3 GiB memory gate가 false pass할 수 있다는 위험을 제시했다.
- runner의 `mkdtemp()` 이후 exception path에서 cleanup과 final report write가
  보장되지 않는 점을 찾았다.
- memory report에 fixture version만 있고 manifest/fixture digest가 없어 결과를
  특정 fixture bytes와 독립적으로 결합하기 어렵다는 traceability 문제를 찾았다.
- full-source 12.44 GiB uncontrolled observation과 fixture 3 GiB 통과를
  구분한 completion report의 해석 경계는 문제로 삼지 않았다.
- finding마다 priority, reachability, impact, remediation을 포함해 운영 관점의
  판단에 필요한 형식을 갖췄다.

#### Adversarial Reviewer Gaps

| Gap | Impact | Improvement |
| --- | --- | --- |
| fixture representativeness finding은 spec의 최소 요구를 넘는 비교 가능성 요구를 포함 | 요구사항 위반과 개선 제안의 경계가 흐려질 수 있음 | `spec violation`과 `risk-based recommendation`을 분리 |
| runner cleanup finding은 exception 경로를 읽어 도출했지만 실제 malformed time report 또는 worker output으로 재현하지 않음 | severity의 신뢰도가 정적 reasoning에 머묾 | 최소 재현 test 또는 controlled artifact corruption check 제안 |
| fixture contract P1을 general reviewer와 독립적으로 재확인했지만, 그 finding의 exact spec clause를 결과에 포함하지 않음 | main agent의 reconciliation 비용 증가 | finding마다 code location과 requirement location을 모두 강제 |

#### Adversarial Reviewer Assessment

`adversarial-reviewer`는 general review와 다른 failure mode를 실질적으로
탐색했다. 특히 cleanup과 evidence traceability finding은 단순 code style 문제가
아니라 memory validation의 조사 가능성과 반복 실행 안정성에 영향을 준다.

다만 representativeness 문제는 “현재 canonical spec 위반”과 “full-source 보장
요구가 생길 때 필요한 stronger contract”를 구분해야 한다. 이 구분이 없으면
현재 scope 밖의 개선을 P1 defect처럼 보이게 할 위험이 있다.

## Finding Reconciliation

| Candidate finding | Source | Decision | Rationale |
| --- | --- | --- | --- |
| Fixture manifest contract is not enforced | Both | Accepted, P1 | canonical spec의 필수 manifest 특성과 required-column null invariant를 실제 preflight/evidence validation이 강제하지 않는다. |
| Fixture does not model full-source schema width/type diversity | Adversarial | Accepted as risk, not spec defect | full-source memory guarantee를 주장하지 않는 현재 boundary에서는 immediate contract violation이 아니다. 다만 representative label의 신뢰도를 낮춘다. |
| Runner exception path can leak temp artifacts and skip final report | Adversarial | Accepted, P2 | run directory cleanup과 report write가 exception-safe하게 보장되지 않는다. 실제 재현 test가 추가돼야 한다. |
| Memory report lacks fixture digests | Adversarial | Accepted, P3 | historical result의 replay/audit traceability가 약하다. |
| Completion report overclaims full-source memory safety | Both | Rejected | completion report가 fixture-level 3 GiB result와 full-source 12.44 GiB observation을 명시적으로 분리한다. |

## Combined Delegation Evaluation

### What Worked

- 동일한 target에 대해 일반 correctness와 adversarial failure analysis를
  분리해 확증 편향을 낮췄다.
- 두 결과가 독립적으로 P1 fixture contract gap에 수렴했다.
- adversarial reviewer의 추가 finding은 general reviewer의 범위를 보완했다.
- 두 reviewer 모두 full-source guarantee overclaim을 만들지 않아 completion
  report의 해석 경계를 존중했다.

### What Did Not Work Fully

- reviewer output에 공통 evidence schema가 없었다. 따라서 main agent가
  code defect, risk, unverified hypothesis를 후처리로 분류해야 했다.
- 어느 reviewer도 focused pytest 또는 controlled failure reproduction을
  실행하지 않았다. 이는 read-only delegation 제한과 별개로, 검증 가능 여부를
  결과에 더 명확히 남겨야 한다는 뜻이다.
- subagent 결과는 finding 중심으로는 충분했지만, 채택·기각 판단은 main agent가
  별도 matrix로 만들어야 추적 가능해진다.

## Improved Delegation Contract

다음 EDA review에서는 subagent에 아래 형식을 고정한다.

```text
Scope:
- files and artifacts to inspect
- whether execution is permitted

For every finding:
- Severity: P1/P2/P3
- Classification: spec defect / implementation defect / operational risk
- Reachability: concrete input or failure path
- Evidence: code path, artifact, test, or runtime output
- Validation: executed / static-only / not possible
- Requirement link: exact spec or project contract, if applicable
- Remediation: smallest scope-correct change

End with:
- Rejected hypotheses
- Unverified risks
- Validation gaps
```

### Recommended Assignment Split

| Role | Required question | Do not spend time on |
| --- | --- | --- |
| `general-reviewer` | What implementation behavior violates an explicit contract or can regress current behavior? | speculative performance improvements without a contract link |
| `adversarial-reviewer` | What reachable failure can produce false pass, leaked resources, stale evidence, or misleading operational confidence? | restating ordinary type or style issues |
| Main agent | Which claims are accepted, rejected, or residual risks, and what validation proves each decision? | rediscovering the same code paths already covered by reviewers |

## Final Judgment

이번 subagent delegation은 효과적이었다. 두 agent가 같은 P1 issue를 독립적으로
확인했고, adversarial reviewer가 cleanup과 report provenance라는 별도 위험을
추가했다.

다음 개선의 핵심은 reviewer 수를 늘리는 것이 아니다. 각 finding을 `spec defect`,
`operational risk`, `unverified hypothesis`로 구분하고, evidence와 validation
상태를 동일한 형식으로 강제하는 것이다. 그러면 main agent의 reconciliation이
짧아지고 최종 review report의 판단 근거도 더 견고해진다.

# Review

`review`는 식별된 대상을 의도된 contract, baseline 또는 quality expectation과 비교해 evidence-backed finding을 만드는 것이 주된 목적일 때 사용한다.

## Scope

Review는 code, test, documentation, architecture, workflow, process 또는 이들 사이의 consistency를 다룰 수 있다.

OpenSpec `plan-review.md`처럼 다른 workflow가 owning review artifact를 정의하면 competing Inbox authority를 새로 만들지 않고 해당 artifact를 사용한다.

## Contract

- 가능한 경우 target, scope와 reviewed revision 또는 baseline을 식별한다.
- Candidate finding은 실제 target과 기존 safeguard를 확인한 뒤 채택한다.
- Material finding은 location, evidence, impact와 required action으로 뒷받침한다.
- Material한 경우 verified fact, inference, defect, risk와 optional improvement를 구분한다.
- 수행한 validation, 수행하지 못한 validation과 remaining risk를 기록한다.
- 추측성 finding을 늘리기보다 적은 수의 잘 뒷받침된 finding을 우선한다.

## Frontmatter

[`inbox/AGENTS.md`](../AGENTS.md)의 common artifact contract를 따른다. Review가 추가로 요구하는 frontmatter field는 `type: review` 외에는 없다.

`description`에는 review target과 목적 또는 scope를 적는다. 현재 verdict는 leading result callout이 소유하므로 description에 반복하지 않는다.

`status`, `target`, `revision`, `scope`, `verdict`는 기본적으로 frontmatter에 추가하지 않는다. 본문과 중복되어 stale metadata가 되기 쉽다. 다른 applicable owner contract가 요구할 때만 추가한다.

`tags`는 classification이 search나 retrieval을 실질적으로 개선할 때만 유지한다. Namespaced tag와 plain tag를 함께 사용할 수 있다.

- `domain:<value>` — broad domain 또는 ownership context
- `capability:<value>` — specific capability
- `<tag>` — namespace가 필요하지 않은 cross-cutting search term

Standalone `subdomain:<value>`로 parent-child taxonomy를 암묵적으로 표현하지 않는다. Hierarchical classification이 필요하면 implicit tag pairing 대신 별도 canonical taxonomy가 관계를 소유한다.

Tag value는 lowercase kebab-case를 사용하고 적용되지 않는 placeholder는 제거한다.

## Severity

한 review 안에서는 동일한 severity vocabulary를 일관되게 사용한다.

| Severity | Meaning |
| --- | --- |
| 🔴 **Critical** | Safety, data integrity 또는 fundamental contract를 위반해 acceptance를 반드시 차단해야 한다. |
| 🟠 **Major** | Material defect 또는 evidence gap으로 acceptance 전에 수정해야 한다. |
| 🟡 **Minor** | 실제 문제이지만 일반적으로 단독으로 acceptance를 차단하지 않는다. |
| 🔵 **Note** | Defect가 아닌 observation, caution 또는 optional improvement다. |

Finding을 더 눈에 띄게 만들기 위해 severity를 과장하지 않는다. `Note`도 실제 판단에 도움이 될 때만 기록한다.

## Presentation

반복해서 읽는 사람이 문서를 처음부터 끝까지 읽지 않아도 result, finding severity, affected location과 required action을 빠르게 파악할 수 있게 구성한다.

Template의 기본 순서는 다음과 같다.

1. result callout과 target context
1. `Findings` summary
1. optional `Details`
1. `Validation`
1. optional `Risks and Limits`

Overall verdict는 leading callout이 한 번만 소유한다. 같은 verdict를 별도 summary나 closing section에서 반복하지 않는다.

Target context는 `Target`, `Revision`, `Scope`의 고정 3-item bullet list로 표현한다. 서로 다른 metadata field를 한 row의 table로 묶지 않는다.

### Findings Summary

Finding이 있으면 fixed `ID | Severity | Finding | Action` table을 사용한다. 각 row는 빠르게 훑을 수 있게 짧게 유지하고, 판단에 필요한 설명만 `Details`에서 확장한다.

`F1`, `F2`, `F3`처럼 stable ID를 사용한다. 같은 finding의 summary row와 detail section은 동일한 ID와 severity를 사용한다.

Material finding이 없으면 `Findings` heading은 유지하고 빈 placeholder row 대신 finding이 없음을 짧게 적는다.

### Finding Details

상세 설명이 필요한 finding만 H3로 확장하고 semantic part는 H4로 구분한다. `**Impact:**`, `**Next:**` 같은 repeated inline label로 대체하지 않는다.

Standard detail structure는 다음과 같다.

- `Locations`
- `Evidence`
- `Impact`
- `Action`

Summary만으로 판단할 수 있으면 해당 detailed finding 전체를 생략한다. Detail을 유지한 경우에도 적용되지 않는 subsection은 finding이 모호해지지 않을 때만 생략한다.

설명은 prose를 사용한다. 여러 file, test, requirement, evidence item, impact 또는 action처럼 동종 항목은 bullet로 표현하고, 순서가 의미 있을 때만 numbered list를 사용한다.

## Locations and Links

Location은 review에서 직접 탐색할 수 있게 표현한다.

- File, symbol, requirement와 section을 inline으로 이어 쓰지 않고 `Locations` H4 아래에 둔다.
- File 또는 artifact를 top-level bullet로 두고 symbol, test, requirement, section 또는 line reference를 nested bullet로 둔다.
- 여러 file이나 artifact에 걸친 finding은 각각 top-level bullet을 사용한다.
- Stable link가 있으면 repository file, artifact, Pull Request, Issue, commit 등 직접 이동 가능한 target을 연결한다.
- Raw URL보다 목적지를 알 수 있는 짧은 linked label을 우선한다.
- Path와 identifier spelling은 정확히 유지한다.

Example:

```markdown
#### Locations

- [`src/recovery/executor.py`](../../src/recovery/executor.py)
  - `execute_approved_backfill`
  - `_ensure_approved`
- [`tests/data_operations/test_system_recovery_e2e.py`](../../tests/data_operations/test_system_recovery_e2e.py)
  - `test_pre_approval_safety_rejected_approval_zero_mutation`
```

## Evidence and Footnotes

Evidence는 지원하는 finding 가까이에 둔다. Finding, impact와 action을 이해하는 데 필요한 핵심 사실은 본문에 남긴다.

Footnote는 provenance, secondary evidence, exception 또는 본문 흐름을 끊는 긴 보조 설명에만 사용한다. Core finding, material impact, required action 또는 중요한 uncertainty를 footnote에 숨기지 않는다.

Footnote가 repository artifact나 external GitHub object를 가리키면 가능한 경우 target을 직접 링크한다.

## Validation

Review artifact의 validation은 fixed `Result | Check | Evidence` table로 기록한다. 한 항목뿐이어도 같은 구조를 유지해 반복 review에서 scan pattern과 result vocabulary를 일관되게 한다.

Result label은 다음을 사용한다.

- ✅ `Pass`
- ❌ `Fail`
- ⚪ `Not Verified`

실제로 수행한 validation만 기록한다. 수행하지 못한 검증이 review confidence에 영향을 주면 이유와 함께 `Not Verified`로 남긴다.

## Risks and Limits

Material residual risk, review coverage limit, unresolved uncertainty 또는 re-review 조건이 있을 때만 유지한다. Finding이나 validation row를 다시 반복하지 않는다.

## Resources

- Template: [`inbox/_templates/review.md`](../_templates/review.md)
- Multi-perspective template: [`inbox/_templates/review-multi-perspective.md`](../_templates/review-multi-perspective.md) — 관점별 검토와 후보 의견의 수용·드랍·미해결 판단을 기록할 때 사용한다.
- Resolution template: [`inbox/_templates/review-resolution.md`](../_templates/review-resolution.md) — 기존 finding에 대한 대응과 검증을 기록할 때 사용하며 fresh review를 대체하지 않는다.
- Skill: implementation 또는 test review에는 `prj-review-code`; 그 밖의 target에는 이를 강제하지 않고 이 guideline을 적용한다.

Review target에 도움이 되는 resource만 사용하고 optional template section은 필요하지 않으면 생략한다.

## Boundaries

- Style preference만으로 finding을 만들지 않는다.
- 관련 없는 existing defect나 redesign으로 review scope를 넓히지 않는다.
- 수행하지 않은 validation, reproduction 또는 verification을 수행했다고 표현하지 않는다.
- Review artifact를 canonical fix, decision 또는 requirement로 취급하지 않는다.
- Common artifact와 lifecycle rule은 `inbox/AGENTS.md`를 따른다.

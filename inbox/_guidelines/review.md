# Review

Use `review` when the artifact's primary purpose is to evaluate an identified target against an intended contract, baseline, or quality expectation and produce evidence-backed findings.

## Scope

Review may cover code, tests, documentation, architecture, workflow, process, or consistency between them.

If another workflow defines an owning review artifact, such as an OpenSpec `plan-review.md`, use that artifact instead of creating a competing inbox authority.

## Contract

- Identify the target, scope, and reviewed revision or baseline when available.
- Verify candidate findings against the actual target and existing safeguards.
- Support material findings with location, evidence, impact, and required action.
- Separate verified facts, inference, defects, risks, and optional improvements when material.
- Record performed validation, omitted validation, and remaining risk.
- Prefer a small number of well-supported findings over speculative volume.

## Severity

Use one severity vocabulary consistently within the review.

| Severity | Meaning |
| --- | --- |
| 🔴 **Critical** | Safety, data integrity, or a fundamental contract is violated in a way that must block acceptance. |
| 🟠 **Major** | A material defect or evidence gap must be corrected before acceptance. |
| 🟡 **Minor** | A real issue is worth correcting but does not normally block acceptance by itself. |
| 🔵 **Note** | An observation, caution, or optional improvement that is not itself a defect. |

Do not inflate severity to make a finding more visible. Use `Note` only when recording it materially helps the reviewer; do not create notes to increase finding count.

## Presentation

Optimize the artifact for repeated human review. A reader should be able to determine the result, scan finding severity, open affected locations, and identify required actions without reading the document from start to finish.

Use the template's structure in this order:

1. result callout and target context
2. `Findings` summary
3. optional `Details`
4. `Validation`
5. optional `Risks and Limits`

State the overall verdict once in the leading callout. Do not repeat the same verdict in a second summary or closing verdict section.

### Findings Summary

Use the fixed `ID | Severity | Finding | Action` table when findings exist. Keep each row concise enough to scan; move explanation into `Details` only when the summary is insufficient for a decision.

Use stable finding IDs such as `F1`, `F2`, and `F3`. The summary row and detail section for the same finding must use the same ID and severity.

If no material finding exists, keep the `Findings` heading and state that no finding was identified instead of creating empty placeholder rows.

### Finding Details

Use an H3 for each detailed finding and H4 sections for its semantic parts. Do not express these parts as repeated inline labels such as `**Impact:**` or `**Next:**`.

The standard detail structure is:

- `Locations`
- `Evidence`
- `Impact`
- `Action`

Omit the entire detailed finding when the summary row is sufficient. Within a retained detail, omit a section only when it is genuinely not applicable and the finding remains unambiguous.

Use prose for explanation. Use bullets when the content is naturally a list of peer items, such as multiple files, tests, requirements, evidence items, impacts, or actions. Use numbered lists only when order or sequence is meaningful.

## Locations and Links

Make review navigation direct.

- Put location information under the `Locations` H4 instead of joining file, symbol, requirement, and section names inline.
- Use the file or artifact as the top-level bullet and its symbols, tests, requirements, sections, or line references as nested bullets.
- When one finding spans multiple files or artifacts, use one top-level bullet per file or artifact.
- Link repository files, artifacts, Pull Requests, Issues, commits, and other directly navigable targets whenever a stable link is available.
- Prefer concise linked labels over pasted raw URLs.
- Keep path and identifier spelling exact.

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

Keep evidence close to the finding it supports. The main text must contain the facts necessary to understand the finding, its impact, and its action.

Use footnotes only for supporting provenance, secondary evidence, exceptions, or longer explanation that would interrupt the main reading flow. Do not hide the core finding, material impact, required action, or an important uncertainty in a footnote.

When a footnote points to a repository artifact or external GitHub object, link the target directly where practical.

## Validation

Use the fixed `Result | Check | Evidence` table when multiple validation items need comparison.

Use these result labels consistently:

- ✅ `Pass`
- ❌ `Fail`
- ⚪ `Not Verified`

Record only validation actually performed. State important omitted validation as `Not Verified` with the reason when that omission affects confidence in the review.

## Risks and Limits

Use this optional section only for material residual risk, review coverage limits, unresolved uncertainty, or conditions that require re-review. Do not repeat findings or validation rows here.

## Resources

- Template: [`inbox/_templates/review.md`](../_templates/review.md)
- Skill: `prj-review-code` only for implementation or test review; broader targets use this guideline without forcing that skill.

Use only resources that serve the review target. Adapt or omit optional template sections that do not.

## Boundaries

- Do not create findings from style preference alone.
- Do not broaden the review into unrelated existing defects or redesign.
- Do not claim validation, reproduction, or verification that was not performed.
- Do not treat the Review artifact as the canonical fix, decision, or requirement.
- Follow the common artifact and lifecycle rules in `inbox/AGENTS.md`.

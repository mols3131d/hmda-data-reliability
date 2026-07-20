---
title: '{{Title}}'
date: 'yyyy-MM-dd'
type: 'code-review-summary'
---

<!--
Code review summary report template.
-->
## Summary

<!-- Summarize test results below -->

| 🟩 `PASS` | 🟥 `FAIL` | 🟧 `ERROR` | ⬜ `SKIP` |
| :---: | :---: | :---: | :---: |
| {{pass_count}} | {{fail_count}} | {{error_count}} | {{skip_count}} |

<!-- Write Summary -->

## Findings

| 🔴 `bug` | 🟡 `risk` | 🔵 `nit` | ❓ `question` |
| :---: | :---: | :---: | :---: |
| {{bug_count}} | {{risk_count}} | {{nit_count}} | {{question_count}} |

---

### {{severity_emoji}} [`{{domain}}-{{finding}}`]({{link}}) <!-- Link only if finding doc exists -->

[`{{file}}:{{start_line}}[-{{end_line}}]`]({{link}})

- **{{focus}} {{core}}**: {{observation}}

  ---> **{{action}} {{what}}**: {{recommendation}}

---

### {{additional_finding_heading}}    <!-- Write Another Finding -->

[`{{file}}:{{start_line}}[-{{end_line}}]`]({{link}})

- **{{focus}} {{core}}**: {{observation}}

  ---> **{{action}} {{what}}**: {{recommendation}}

---

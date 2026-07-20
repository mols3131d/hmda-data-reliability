---
title: '{{Title}}'
date: 'yyyy-MM-dd'
type: 'code-review-summary'
---

<!--
이 파일은 대한 리뷰 결과 보고서 요약 템플릿이다.
-->
## Summary

<!-- 아래 테이블에는 테스트 결과를 요약한다. -->

| 🟩 `PASS` | 🟥 `FAIL` | 🟧 `ERROR` | ⬜ `SKIP` |
| :---: | :---: | :---: | :---: |
| {{pass_count}} | {{fail_count}} | {{error_count}} | {{skip_count}} |

<!-- Write Summary -->

## Findings

| 🔴 `bug` | 🟡 `risk` | 🔵 `nit` | ❓ `question` |
| :---: | :---: | :---: | :---: |
| {{bug_count}} | {{risk_count}} | {{nit_count}} | {{question_count}} |

### `{{file}}:{{start_line}}[-{{end_line}}]`: {{severity}}: [`{{domain}}-{{finding}}`](/{{link}})

<!-- Write Findings Summary -->

### {{additional_finding_heading}}    <!-- Write Another Findings -->

{{additional_finding_summary}}

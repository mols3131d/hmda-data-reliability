# Development Documentation Rules

`docs/development/**`에 적용하는 scoped 규칙이다. 상위 [`../AGENTS.md`](../AGENTS.md)의 문서 공통 규칙을 함께 따르며, 이 파일은 **development guide와 dashboard에만 필요한 규칙**을 소유한다.

## Ownership

| Area | Owns |
| --- | --- |
| `README.md` | development 문서 navigation과 boundary 안내 |
| `testing.md` | test 실행 command, marker, report, coverage, tracing |
| `test-design-and-implementation.md` | observable contract, scenario와 oracle 설계 기준 |
| `vcs-git/**` | Git/GitHub workflow; 세부 규칙은 각 guide가 소유 |
| `dashboard.md` | human-only development status projection |

한 guide의 세부 규칙을 다른 development 문서에 복제하지 않는다. 필요한 경우 owning guide를 링크한다.

## Dashboard Policy

- Agent는 사용자가 dashboard 자체를 묻거나 task가 명시적인 dashboard refresh일 때만 `dashboard.md`를 상태 판단에 사용한다.
- Dashboard는 별도의 dashboard refresh 작업에서만 갱신한다. 일반 feature, fix, refactor, test, spec 또는 documentation 작업의 side effect로 수정하지 않는다.
- Refresh는 installed `mols-markdown-dashboard` skill을 사용해 current canonical Spec, source, tests와 matching-revision execution evidence를 다시 조사한다.
- Project dashboard 계약의 `Development Progress`, `Implementation Gaps`, `Verification Gaps`를 유지하고 Requirement와 Verification Target을 의미 단위로 집계한다.
- 근거 없는 status나 denominator를 추측하지 않는다.
- Dashboard에 canonical contract, acceptance definition 또는 project-wide machine-readable SSOT를 새로 만들지 않는다.
- Repository artifact는 Markdown을 기본으로 유지한다. Skill이 작업용 YAML을 사용하더라도 별도 요청 없이 dashboard SSOT로 저장하지 않는다.

## Guide Lifecycle

- Development guide는 특정 phase의 진행률이나 일회성 상태가 아니라 phase-independent 방법과 workflow를 설명한다.
- Current capability contract나 runtime implementation state를 development guide가 다시 소유하지 않는다.
- 완료된 phase bundle이나 historical readiness artifact를 이 directory에 보존하지 않는다.
- Tool, command 또는 workflow가 바뀌면 해당 내용을 실제로 소유하는 가장 가까운 guide만 갱신한다.

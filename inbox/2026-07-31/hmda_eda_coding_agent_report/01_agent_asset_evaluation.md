---
title: "Agent Asset 활용 평가"
description: "이번 HMDA EDA coding 작업에서 instruction, skill, agent asset의 사용 여부와 효과를 평가한다."
date: 2026-07-31
---

# Agent Asset 활용 평가

## 결론

이번 작업에서는 repository instruction과 관련 skill을 실제 구현과 검증 routing에
사용했다. 별도 subagent는 호출하지 않았으며, `Data Builder`, `general-reviewer`,
`adversarial-reviewer`가 작업에 적합한지 검토했지만 직접 조사·수정·검증하는
방식으로 진행했다.

## 사용한 instruction과 skill

| Asset | 사용 여부 | 평가 |
| --- | --- | --- |
| `AGENTS.md` | 사용 | project 구조, Korean 응답, 문서·코드 범위를 확인했다. |
| `docs/DEVELOPMENT.md` | 사용 | pytest marker, `uv`, formatting, memory test 분리 규칙을 적용했다. |
| `docs/ARCHITECTURE.md` | 사용 | read-only EDA와 resource/report 경계를 확인했다. |
| Python instruction | 사용 | Pydantic `extra="forbid"`, frozen model, domain package reuse를 적용했다. |
| Markdown instruction | 사용 | Korean 본문, technical term, GFM 문서 형식을 적용했다. |
| `openspec-apply-change` | 부분 사용 | `openspec list --json`으로 active change를 확인했으나 active change가 없어 첨부 task와 canonical spec을 직접 기준으로 삼았다. |
| `ponytail` | 사용 | 새 dependency와 불필요한 abstraction을 추가하지 않고 최소 변경으로 제한했다. |
| `prj-testing` | 사용 | 좁은 pytest slice부터 시작하고 `memory` marker를 일반 test와 분리했다. |
| `python-fact-grounded-coding` | 사용 | Python environment, Pylance diagnostics, runtime test, Ruff, mypy를 근거로 판단했다. |

## Agent 사용 평가

- `Data Builder`: 분석 artifact와 EDA 작업에 적합하지만 이번 세션에서는 호출하지 않았다.
- `general-reviewer`: correctness·regression 독립 review를 수행하지 않았다.
- `adversarial-reviewer`: false pass와 failure recovery를 별도 agent가 검토하지 않았다.
- 실제 subagent 미사용은 사실이며, 해당 agent가 작업했다거나 delegation 결과가 있었다고 볼 수 없다.
- 대신 malformed `time` report, malformed/missing worker JSON, cleanup, preflight
  failure를 직접 focused test로 고정했다.

## 평가

**장점:** instruction을 읽은 뒤 local hypothesis를 세우고, 첫 edit 직후 좁은
executable validation을 수행했다. 구현과 검증 범위를 HMDA EDA source/test에
제한했다.

**개선점:** 독립 reviewer의 second opinion이 없었다. 다음 유사 작업에서는
`Data Builder`에 fixture/test artifact construction을 위임하고, main agent가
contract integration과 최종 validation을 담당할지 먼저 비교하는 편이 좋다.

**종합:** 직접 구현과 validation routing에는 효과적이었지만, agent delegation과
독립 review는 사용하지 않은 부분적 asset 활용이었다.

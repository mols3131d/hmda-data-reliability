---
title: "Development"
description: "개발 환경, tooling, testing, CI, Git/GitHub workflow, AI agent asset policy와 development dashboard를 연결하는 docs/development directory의 entrypoint입니다."
categories:
  - software-engineering
tags:
  - ci
  - git
  - github
  - pytest
  - rulesync
  - testing
  - tooling
---

# Development

이 directory는 repository의 **phase-independent development guides**와 사람이 빠르게 보는 **development dashboard**를 둔다. Dashboard는 위치상 development에 속하지만 개발 규칙이나 canonical state를 소유하지 않는 human-only projection이다.

## Documents

| Document | Role | Use when |
| --- | --- | --- |
| [Development Dashboard](dashboard.md) | human-only development status snapshot | 사람이 개발 진행 상태와 gap을 빠르게 확인할 때 |
| [Environment Variables](environment-variables.md) | `.env` 설정, 표기 규칙, 도메인별 환경변수 소유권과 확장 원칙 | 로컬 환경변수를 설정하거나 새 환경변수를 추가·검토할 때 |
| [AI Agent](ai-agent/README.md) | instruction surface 선택과 agent asset 관리 정책 | Agent instruction 또는 asset의 owner와 관리 경로를 결정할 때 |
| [Tooling](tooling/README.md) | repository workflow를 지원하는 개발 도구의 project-specific usage | bootstrap, OpenSpec, Rulesync, Git hook 또는 formatter 사용 경로를 확인할 때 |
| [Continuous Integration](ci/README.md) | CI의 목적·원칙·패턴과 책임별 운영 계약의 진입점 | CI scope, change-impact routing 또는 merge gate를 설계·변경할 때 |
| [Testing Guide](testing.md) | pytest command, marker, report, coverage, tracing | 일반 test를 실행하거나 결과를 확인할 때 |
| [Review AI Prompt Composition](review-ai-prompts.md) | 프롬프트 모듈의 책임·재사용·조립과 모델 전달 경로 | 프롬프트를 분할·편집하거나 실제 주입 메시지를 확인할 때 |
| [Review AI Evaluation](review-ai-evaluation.md) | Review AI의 offline/live/human/Langfuse evaluation workflow | Review AI 품질과 LLMOps evidence를 실행하거나 해석할 때 |
| [Test Design](test-design.md) | requirement를 observable contract, scenario와 oracle로 변환하는 기준 | test를 설계하거나 requirement를 추적할 때 |
| [Version Control and GitHub](vcs-git/README.md) | branch, commit, Pull Request와 review 운영 규칙 | Git/GitHub 작업을 수행할 때 |

## Boundary

- Current capability의 normative contract는 [`../../openspec/specs/`](../../openspec/specs/)가 소유한다.
- 시스템 구조와 domain ownership guidance는 [`../ARCHITECTURE.md`](../ARCHITECTURE.md), [`../domains/**`](../domains/OVERVIEW.md)가 설명한다.
- Active product goal은 [`../mvp.md`](../mvp.md)가 소유한다.
- [`dashboard.md`](dashboard.md)는 위 source들을 대체하지 않는 human-only projection이다.
- [`../../DEVELOPMENT.md`](../../DEVELOPMENT.md)는 repository-wide 개발 환경과 active tool choice를 안내한다.

## Rules

`docs/**`의 agent 규칙과 dashboard policy는 [`../AGENTS.md`](../AGENTS.md)가 소유한다. Tooling, CI, Test와 Git/GitHub의 세부 workflow는 각각의 owning guide가 소유하며 이 README는 반복하지 않는다.

## Reading Order

1. Repository 개발 환경이 필요하면 [`../../DEVELOPMENT.md`](../../DEVELOPMENT.md)를 확인한다.
1. Tooling, CI, Agent instruction, Test 또는 Git/GitHub 작업이면 해당 owning guide를 읽는다.
1. Dashboard를 다루는 명시적 작업이면 [`../AGENTS.md`](../AGENTS.md#dashboard-policy)의 dashboard policy를 먼저 확인한다.
1. 제품 목표나 project document navigation이 필요하면 [`../README.md`](../README.md)에서 owning document를 찾는다.

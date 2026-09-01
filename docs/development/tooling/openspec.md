---
title: "OpenSpec"
description: "이 repository에서 OpenSpec을 실행·갱신하는 integration 방식과 project-specific owning source를 연결합니다."
categories:
  - software-engineering
tags:
  - openspec
  - tooling
---

# OpenSpec

OpenSpec의 일반 workflow, slash command와 CLI reference는 [OpenSpec 공식 문서](https://openspec.dev/docs/)를 따른다. 이 문서는 **HMDA Data Reliability repository의 integration과 owning source**만 설명한다.

## Repository Integration

- [`openspec/config.yaml`](../../../openspec/config.yaml)은 사용할 schema와 repository-specific context/rule을 소유하며 `spec-driven-tdd` schema를 선택한다.
- Project-local `spec-driven-tdd` workflow/schema contract는 [`openspec/schemas/spec-driven-tdd/`](../../../openspec/schemas/spec-driven-tdd/)가 소유한다.
- [`scripts/bootstrap.py`](../../../scripts/bootstrap.py)의 `setup`과 `update`는 `npm exec @fission-ai/openspec@latest`를 통해 `openspec update`를 실행한다. `session`은 OpenSpec integration을 갱신하지 않는다.
- Repository는 이미 OpenSpec project structure와 config를 소유한다. Routine bootstrap에서 `openspec init`을 다시 실행하지 않고 기존 integration만 `update`로 refresh한다.
- OpenSpec을 repository dependency로 별도 고정 설치하거나 global installation을 전제로 하지 않는다.

Bootstrap의 OpenSpec step은 installed instruction/integration surface를 refresh하는 경로다. Project-local config와 schema의 source ownership을 대체하지 않는다.

새로운 OpenSpec command, option 또는 tool 자체의 동작이 필요하면 repository 문서에 복제하지 않고 [공식 CLI reference](https://openspec.dev/docs/cli)를 확인한다.

## Artifact Authority

OpenSpec artifact authority와 instruction ownership map은 [`openspec/README.md`](../../../openspec/README.md)가 설명한다. Repository-specific context/rule은 [`openspec/config.yaml`](../../../openspec/config.yaml), workflow/schema contract는 [`openspec/schemas/spec-driven-tdd/`](../../../openspec/schemas/spec-driven-tdd/)가 소유한다. 이 tooling guide는 canonical boundary, naming rule 또는 artifact 작성 규칙을 다시 정의하지 않는다.

Current capability를 판단하거나 OpenSpec artifact를 작성할 때는 tooling 문서가 아니라 해당 OpenSpec owning source를 따른다.

## Boundary

- OpenSpec 일반 사용법과 CLI semantics → 공식 문서
- repository의 schema, artifact authority와 작성 규칙 → [`openspec/`](../../../openspec/README.md)의 owning source
- OpenSpec integration refresh 시점 → [Bootstrap](bootstrap.md)

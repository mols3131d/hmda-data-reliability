---
title: "OpenSpec"
description: "이 repository에서 OpenSpec을 사용하는 integration 방식, project config와 contract boundary를 설명합니다."
categories:
  - software-engineering
tags:
  - openspec
  - tooling
---

# OpenSpec

OpenSpec의 일반 workflow, slash command와 CLI reference는 [OpenSpec 공식 문서](https://openspec.dev/docs/)를 따른다. 이 문서는 **HMDA Data Reliability repository에서 달라지는 부분**만 설명한다.

## Repository Integration

[`openspec/config.yaml`](../../../openspec/config.yaml)은 이 repository의 OpenSpec project configuration을 소유하며 `spec-driven-tdd` schema를 사용한다.

OpenSpec integration은 [`scripts/bootstrap.py`](../../../scripts/bootstrap.py)가 관리한다.

- `setup`: clone 이후 OpenSpec integration을 현재 tool 상태에 맞춘다.
- `update`: external tooling 갱신과 함께 OpenSpec integration을 갱신한다.
- 실행은 `npm exec @fission-ai/openspec@latest` 경로를 사용하며 OpenSpec을 repository dependency로 고정 설치하지 않는다.

일반적인 OpenSpec 설치나 command 사용법을 repository 문서에 복제하지 않는다. 새로운 CLI 동작이나 option이 필요하면 [공식 CLI reference](https://openspec.dev/docs/cli)를 먼저 확인한다.

## Contract Boundary

이 repository에서는 OpenSpec artifact의 역할을 다음처럼 구분한다.

| Surface | Role |
| --- | --- |
| `openspec/specs/**` | current capability의 canonical contract |
| `openspec/changes/**` | planned/in-flight work와 archive history |
| `openspec/config.yaml` | schema, project context와 project-specific OpenSpec rule |

Change artifact만으로 current system behavior를 단정하지 않는다. Current capability를 판단할 때는 관련 Spec과 실제 source/test 또는 matching revision evidence를 함께 확인한다.

Spec ID, Change ID와 schema-specific 작성 규칙은 [`openspec/config.yaml`](../../../openspec/config.yaml)이 소유하므로 이 문서에서 반복하지 않는다.

## When to Use This Guide

OpenSpec 자체의 사용법이 궁금하면 공식 문서를 본다. 이 guide는 다음 질문에 답할 때만 사용한다.

- 이 repository가 어떤 OpenSpec schema와 config를 사용하는가?
- OpenSpec integration update는 어떤 repository entrypoint가 소유하는가?
- Spec과 Change 중 무엇이 current contract를 소유하는가?

Repository-wide documentation trust boundary는 [`docs/AGENTS.md`](../../AGENTS.md)를 따른다.

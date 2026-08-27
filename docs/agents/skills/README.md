---
title: "Agent Skill Maintainer Documentation"
description: "Repository-owned Agent Skill의 유지보수 문서와 훼손되면 안 되는 baseline을 배치하는 경계를 정의합니다."
categories:
  - agent-assets
tags:
  - skills
  - maintenance
---

# Agent Skill Maintainer Documentation

`docs/agents/skills/<skill-name>/`은 해당 Skill을 유지보수하기 위한 maintainer-only 문서를 둔다. Runtime에 필요한 source와 reference는 Skill package가 소유한다.

`baseline/`은 그중에서도 Skill의 원래 의도, protected requirement와 중요한 설계 결정처럼 후속 변경에서 훼손되면 안 되는 기준선을 둔다. Baseline은 일반 runtime guidance나 작업 기록을 대신하지 않는다.

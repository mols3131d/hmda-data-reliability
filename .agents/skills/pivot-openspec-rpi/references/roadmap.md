# Roadmap

## MVP Definition

| Capability | MVP criterion |
| --- | --- |
| Discoverable skill | 구체적인 trigger와 anti-trigger가 있는 valid `SKILL.md` |
| Progressive disclosure | core instruction은 `SKILL.md`, phase detail은 direct reference |
| Research | 충분성 판단, evidence order, status, handoff 정의 |
| OpenSpec integration | proposal·requirements·design·tasks·archive는 OpenSpec 소유 |
| Review | 독립적 evidence reconciliation과 status-based routing |
| Human readability | table, Mermaid, verdict-first template |
| Portability | relative reference와 Windows·WSL installation |
| Validation | deterministic package validator와 acceptance scenarios |

## Delivery

```mermaid
flowchart LR
    F[Foundation]
    C[Core workflow]
    T[Templates]
    V[Static validation]
    D[Dogfooding]
    A[Adoption]

    F --> C --> T --> V --> D --> A
```

| Phase | Deliverable | Exit signal |
| --- | --- | --- |
| Foundation | Vision과 Principles | responsibility boundary가 명시됨 |
| Core workflow | Skill, Research, Review, OpenSpec routing | 모든 verdict에 하나의 next route 존재 |
| Templates | Research와 Review artifact | 빈 template도 읽고 행동 가능 |
| Static validation | cross-platform validator와 scenarios | structure와 reference가 통과 |
| Dogfooding | Lite 1개, Standard 1개 change | rework와 duplicate planning을 정성적으로 확인 |
| Adoption | Copilot과 Codex 설치 | 두 환경에서 skill discovery 확인 |

## Post-MVP

| Priority | Candidate | Trigger |
| ---: | --- | --- |
| P1 | 별도 forked Research·Review skill | 더 강한 context isolation이 실제로 필요 |
| P1 | OpenSpec config example | 같은 project rule이 반복됨 |
| P2 | Behavioral evaluation harness | manual dogfooding에서 반복 failure가 확인됨 |
| P2 | CI validation | 둘 이상의 contributor가 skill을 수정 |
| P3 | Asset usage·provenance analytics | maintenance decision에 usage evidence가 필요 |
| P3 | IDE extension 또는 custom OpenSpec schema | filesystem skill과 config로 부족 |

## Not Now

- 전체 agent action logging
- token·cost dashboard
- Review `approved` 없는 automatic archive
- OpenSpec 밖의 두 번째 planning artifact
- single workflow가 검증되기 전 multi-agent infrastructure

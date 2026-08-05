---
title: "Subagent Delegation Decision 보고서"
description: "HMDA EDA 작업에서 Data Builder delegation 여부를 callable registry, agent asset 적합성, 직접 실행 결과를 기준으로 분석한 보고서"
date: 2026-07-31
---

# Subagent Delegation Decision Report

## Executive Summary

> [!IMPORTANT]
> 당시 HMDA EDA 작업에서 `Data Builder`에 위임하지 않은 직접적인 실행 이유는
> 그 시점의 세션에 노출된 callable agent 목록에 `Data Builder`가 없고
> `explorer`만 있었기 때문이다. 그러나 workspace에 `Data Builder` agent asset
> 파일은 이미 존재했고, 작업 내용도 그 agent의 mission과 상당히 일치했다.
> 따라서 “사용할 수 없어서 못 했다”는 설명은 runtime 관점에서는 맞지만,
> “작업 적합성을 충분히 인식하고 delegation을 검토했다”는 의미에서는 부족하다.

이번 보고서는 다음 두 사실을 분리한다.

1. **Agent asset가 workspace에 존재했는가?**
1. **그 agent를 현재 세션에서 실제로 호출할 수 있었는가?**

이 둘을 혼동하면 VS Code Copilot의 custom agent routing을 잘못 이해하게 된다.

## Decision

| Question | Answer |
| --- | --- |
| Workspace에 `Data Builder`가 있었는가? | 있었다. `.github/agents/data-builder.agent.md`에 정의되어 있었다. |
| 당시 callable registry에 노출됐는가? | 당시 conversation context의 `<agents>` 목록에는 `explorer`만 있었다. |
| 당시 실제로 호출했는가? | 호출하지 않았다. |
| 작업이 `Data Builder` 범위에 맞았는가? | 매우 잘 맞았다. |
| 직접 작업이 기술적으로 가능했는가? | 가능했다. |
| delegation하지 않은 판단이 최선이었는가? | 결과는 성공했지만 routing 판단은 개선 여지가 있다. |
| 현재 registry에서도 같은가? | 아니다. 현재 customization update에는 `Data Builder`가 callable agent로 노출되어 있다. |

## What The Data Builder Agent Was Designed For

`Data Builder`의 mission은 Data Analyst의 관찰을 실제 artifact로 바꾸는 것이다.
정의된 in-scope 항목은 이번 작업과 다음처럼 직접 겹친다.

| Data Builder scope | 이번 HMDA EDA 작업 |
| --- | --- |
| Marimo/Jupyter EDA notebook 수정·실행 | `notebooks/eda_mo.py`를 shared entrypoint로 전환 |
| Python 분석 코드와 query helper 편집 | `hmda_data/eda.py` 구현 |
| DuckDB/SQL query 작성 | aggregate query와 fail-fast reader 작성 |
| metadata와 analysis documentation 갱신 | EDA reference와 completion report 작성 |
| sample로 빠른 반복 후 실행·검증 | deterministic fixture, focused tests, memory smoke |
| 재현 가능한 분석 흐름 반영 | fixture manifest와 memory runner 구현 |

또한 agent 규칙은 다음을 요구한다.

- 편집 전 대상, input source, output artifact 고정
- 작은 sample 또는 제한 파티션으로 먼저 구현
- notebook, SQL, model을 실제 실행
- 원본 CSV와 production data를 변경하지 않음
- 편집 직후 좁은 check 실행
- full scan 여부와 남은 한계를 명시

실제 수행 내용은 이 규칙들과 대부분 일치했다. 문제는 작업 수행 방식보다
**그 수행을 담당할 적절한 custom agent로 routing하지 않았다는 점**이다.

## Why Delegation Did Not Happen

### 1. Runtime registry와 workspace asset를 구분했다

당시 system context에 제공된 callable agent 목록은 다음과 같았다.

- `explorer`

`Data Builder` 파일은 workspace에 존재했지만, 당시 `runSubagent`로 지정할 수
있는 agent 목록에는 포함되어 있지 않았다. 따라서 당시 tool surface만 기준으로
보면 `Data Builder`를 실제로 호출할 수 없었다.

이 판단은 다음 경우에는 타당하다.

- custom agent file이 있지만 현재 VS Code session이 reload되지 않은 경우
- agent frontmatter가 있으나 registry에 반영되지 않은 경우
- customizations update 이전의 대화 context인 경우

즉, “파일이 있다”와 “이번 turn에서 callable하다”는 같은 의미가 아니다.

### 2. 작업 경로가 명확해 직접 구현을 선택했다

작업 초기에 다음 경로가 빠르게 고정됐다.

```text
OpenSpec tasks
  -> characterization test
  -> shared EDA entrypoint
  -> Marimo integration
  -> representative fixture
  -> memory runner
  -> validation and archive
```

직접 tool 사용으로 이 경로를 수행할 수 있었고, live Marimo notebook은 활성
kernel의 source of truth를 따라야 했다. 그래서 직접 구현이 기술적으로
불가능하거나 위험한 상황은 아니었다.

### 3. `Data Builder`의 존재를 routing에 충분히 반영하지 못했다

여기가 핵심적인 판단 부족이다. 당시 agent asset 파일을 더 일찍 검색하고,
workspace custom agent가 registry에 올라왔는지 확인했다면 다음 중 하나를 할 수
있었다.

- Data Builder에 구현 작업을 위임
- Data Builder에 notebook·fixture·문서 artifact를 위임하고 main agent가
  OpenSpec·검증·archive를 담당
- Data Builder를 호출할 수 없다는 사실을 명시적으로 기록

실제 작업 중에는 `explorer`만 callable하다는 사실을 확인한 뒤 direct work를
계속했지만, “이 작업은 Data Builder에 적합하다”는 판단을 별도 기록하지 않았다.
그 결과 나중에 사용자는 asset 존재와 실제 사용 여부 사이의 차이를 다시 질문해야
했다.

## VS Code Copilot Routing Model

### Workspace agent file

`.github/agents/data-builder.agent.md`는 workspace custom agent 정의다. 이 파일은
다음 정보를 제공한다.

- `name`: `Data Builder`
- `description`: 분석 artifact를 만드는 상황에서의 선택 기준
- `tools`: 사용할 수 있는 tool 범위
- `user-invocable: true`: 사용자가 agent picker에서 선택할 수 있는 표식
- `disable-model-invocation: false`: 모델이 조건에 맞으면 자동 선택할 수 있는 표식
- `agents: [explorer]`: Data Builder가 필요할 때 추가로 explorer에 위임할 수 있는 관계

하지만 이 파일의 존재만으로 모든 기존 session에서 즉시 callable하다고 단정할 수
없다. VS Code가 customizations를 로드하고 현재 agent registry에 반영해야 한다.

### Current registry versus historical registry

현재 customizations update에서는 다음 agent가 노출된다.

- `Data Builder`
- `explorer`
- `reviewer`
- `Explore`

따라서 **현재 같은 작업을 새로 시작한다면 `Data Builder`를 호출할 수 있다.**
이 사실은 당시의 historical context와 다르다. 이전 작업 당시의 판단은 당시
노출된 registry에는 근거가 있었지만, workspace asset을 적극적으로 활용하지
못한 routing 누락도 있었다.

### Hook message is not delegation

`.codex/hooks.json`의 다음 message는 delegation을 실행하지 않는다.

```text
Use agent skill: `/caveman lite`, `/ponytail full`
```

이것은 SessionStart 시 skill 사용을 안내하는 shell `echo`다.

- custom agent를 선택하지 않는다.
- `Data Builder`를 실행하지 않는다.
- `explorer`를 호출하지 않는다.
- skill과 subagent를 자동으로 연결하지 않는다.

Skill, custom agent, subagent와 hook은 서로 다른 customization primitive다.

## What Should Have Been Delegated

현재 registry에 `Data Builder`가 있었다면 아래 범위를 위임하는 것이 합리적이었다.

### Delegation candidate

```text
Data Builder에게 위임:
- notebooks/eda_mo.py의 shared analyze_hmda_csv 연결
- hmda_data/eda.py의 reusable read-only aggregate entrypoint
- deterministic fixture와 memory worker artifact
- focused correctness tests
- EDA reference documentation
```

### Main agent responsibilities

```text
Main agent가 유지:
- OpenSpec proposal/design/spec/tasks 해석
- cross-file contract 조정
- Marimo live-kernel 상태 확인
- systemd hard-limit baseline의 최종 판정
- OpenSpec main spec sync와 archive
- 최종 validation과 commit
```

이렇게 분리하면 Data Builder는 artifact construction에 집중하고, main agent는
계약·경계·최종 통합을 담당한다. Data Builder의 `agents: [explorer]` 설정을
활용하면 필요한 read-only 탐색을 그 agent 내부에서 추가 위임할 수도 있다.

## Why Direct Execution Was Still Defensible

직접 수행이 완전히 잘못된 것은 아니다.

- 작업 범위가 한 repository 안에 있었고
- 변경 대상이 명확했으며
- Marimo live kernel과 직접 상호작용해야 했고
- 첫 edit 후 focused validation을 즉시 실행했으며
- 최종 결과가 test, type check, hook, OpenSpec strict validation을 통과했다.

특히 subagent는 별도의 context를 사용하고 단일 결과를 반환하므로, live notebook
state와 여러 파일의 연속적인 implementation feedback이 중요한 이 작업에서는
직접 수행이 더 짧을 수도 있었다.

다만 “직접 수행이 가능했다”와 “적합한 agent가 없었다”는 다른 주장이다. 후자의
주장은 당시 callable registry가 제한되어 있었다는 범위 안에서만 정확하다.

## Evaluation Of The Previous Decision

| Aspect | Evaluation |
| --- | --- |
| Technical outcome | 성공. 기능, test, archive와 commit까지 완료했다. |
| Runtime awareness | 당시 callable agent 목록이 제한되어 있었음을 인지했다. |
| Workspace customization awareness | Data Builder file의 존재와 적용 가능성을 일찍 routing하지 못했다. |
| Delegation quality | 위임 없이 직접 처리했다. 품질은 높았지만 delegation 기회를 사용하지 않았다. |
| Reporting quality | “사용 가능한 agent가 explorer뿐”이라고만 설명해 historical registry와 workspace asset의 차이를 충분히 설명하지 못했다. |
| Corrective understanding | 현재 registry에는 Data Builder가 노출되어 있음을 확인했고, 다음에는 적합성·호출 가능성·직접 수행의 trade-off를 분리해 보고해야 한다. |

## Recommended Routing Policy

앞으로 유사한 작업에서는 다음 순서를 사용한다.

1. 사용자 요청과 변경 대상에서 적용 가능한 custom agent를 식별한다.
1. workspace `.github/agents/*.agent.md`의 정의와 current callable registry를 각각 확인한다.
1. `agent available`과 `agent suitable`을 별도로 기록한다.
1. artifact construction이 중심이면 `Data Builder`를 우선 delegation 후보로 둔다.
1. read-only 탐색만 필요하면 `explorer`를 사용한다.
1. main agent는 cross-cutting contract, live state, final validation과 commit을 소유한다.
1. 위임하지 않을 경우 다음 세 가지를 한 줄로 기록한다.
   - 왜 적합한가
   - 왜 현재 호출할 수 없는가 또는 왜 직접 수행하는가
   - 직접 수행 시 어떤 validation으로 품질을 보장하는가

## Final Judgment

당시 `Data Builder`를 사용하지 않은 이유는 **작업이 부적합해서가 아니라,
당시 session의 callable registry에 노출되지 않았고 직접 구현 경로가 열려 있었기
때문**이다.

그러나 workspace agent asset가 존재했고 작업 범위가 Data Builder의 mission과
강하게 일치했으므로, agent routing 관점에서는 **부분적으로 놓친 delegation
기회**였다. 현재 registry에서는 Data Builder를 호출할 수 있으므로, 동일한
작업을 다시 한다면 artifact construction을 Data Builder에 위임하고 main agent가
통합·검증·archive를 맡는 방식이 더 Copilot다운 workflow다.

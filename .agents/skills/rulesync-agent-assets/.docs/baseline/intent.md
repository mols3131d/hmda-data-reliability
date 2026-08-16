# Intent

이 문서는 `rulesync-agent-assets`가 시간이 지나도 보존해야 하는 목적과 범위를 정의한다.
구현, Rulesync CLI 세부사항, 특정 프로젝트의 현재 파일 배치는 이 문서의 관심사가 아니다.

## Purpose

하나의 명확한 source authority를 유지하면서 agent customization asset을 여러 coding-agent
harness에서 사용할 수 있게 한다. 포맷 변환 자체는 Rulesync에 위임하고, Skill은 어떤
source를 어떤 범위로 어떤 안전 조건 아래 이식할지를 책임진다.

## Goals

1. 하나의 Skill이 두 source model을 모두 지원한다.
   - Rulesync canonical source에서 여러 harness로 fan-out한다.
   - 하나의 native harness를 source로 유지하며 다른 harness로 bridge한다.
2. target이 기존 source를 그대로 사용할 수 있으면 변환하지 않는다.
3. caller 또는 project가 선택한 source of truth를 보존한다.
4. 요청된 target과 asset 종류만 최소 범위로 다룬다.
5. 변환 성공과 semantic parity를 구분하고 compatibility gap을 드러낸다.
6. Rulesync의 upstream 지원을 활용하고 별도 compiler를 중복 구현하지 않는다.
7. 생성 결과와 검증 근거를 caller가 판단할 수 있을 만큼 명확하게 남긴다.

## Scope

이 Skill의 범위는 Rulesync가 지원하는 cross-harness agent customization asset의
재사용, 생성, 변환과 그 결과 검증이다. 대표적인 asset category는 rules, subagents,
skills, commands, hooks, permissions, checks와 MCP configuration이다.

Project scope를 기본 경계로 본다. User-global configuration은 caller가 명시적으로
요구한 별도 범위다.

이 Skill은 orchestration layer다. Source 선택, target 범위, 안전한 실행, compatibility
evidence와 validation을 소유한다. Format parsing, normalization, mapping과 serialization은
Rulesync backend가 소유한다.

## Non-goals

- 모든 harness를 포괄하는 새 canonical schema를 발명하지 않는다.
- Rulesync의 parser, serializer 또는 compatibility matrix를 복제하지 않는다.
- 모든 프로젝트에 `.rulesync/`를 source of truth로 강제하지 않는다.
- native harness를 source로 선택한 프로젝트를 canonical workflow로 자동 migration하지
  않는다.
- target의 표현력 차이를 숨기거나 완전 호환으로 과장하지 않는다.
- 변환을 이유로 source asset을 몰래 rename, copy, relocate 또는 normalize하지 않는다.
- install, upgrade, cleanup, deletion 또는 global configuration mutation을 부수 효과로
  수행하지 않는다.
- 특정 프로젝트의 source preference나 파일 배치를 generic Skill의 본질로 승격하지
  않는다.

## Essence

구현이 바뀌더라도 다음은 유지되어야 한다.

- **One authority:** 한 작업에는 어느 asset이 source인지 명확해야 한다.
- **Least transformation:** 재사용이 가능하면 재사용하고, 필요한 만큼만 변환한다.
- **Two source models:** canonical fan-out과 native bridge를 모두 first-class로 지원한다.
- **Backend delegation:** 변환 지식은 가능한 한 Rulesync가 소유한다.
- **Visible loss:** 발견되지 않거나 표현할 수 없는 의미는 조용히 버리지 않는다.
- **Evidence before confidence:** 생성 여부와 semantic compatibility를 구분해 검증한다.

이 원칙을 의도적으로 변경하는 수정은 단순 refactor가 아니다. 같은 변경에서 baseline을
명시적으로 갱신하고, 변경된 제품 계약으로 검토되어야 한다.

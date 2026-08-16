# Decisions

이 문서는 `rulesync-agent-assets`의 durable design decision과 변경 조건을 기록한다.
구현 세부사항이나 일시적인 upstream 상태가 아니라, 이후 수정에서 근거 없이 되돌리면
안 되는 설계 선택을 보존한다.

## D1. Rulesync is the translation backend

**Decision:** Cross-harness format translation은 Rulesync에 위임한다.

**Rationale:** Harness별 schema, discovery path와 capability 변화 추적은 독립적인
유지보수 비용이 크다. 이미 이 문제를 소유하는 backend를 활용하는 것이 KISS와 DRY에
맞다.

**Change when:** Rulesync가 필요한 핵심 source model 또는 target을 지속적으로 지원하지
못하고, 그 gap이 실제 사용에서 반복적으로 확인될 때 다시 검토한다.

## D2. Both source models are first-class

**Decision:** Canonical fan-out과 native bridge를 하나의 Skill에서 동등하게 지원한다.

**Rationale:** 어떤 repository는 공용 canonical source를 원하고, 다른 repository는 특정
harness의 native asset을 authoritative source로 유지해야 한다. 하나의 방식을 강제하면
다른 사용 사례가 불필요한 migration을 떠안는다.

**Change when:** 제품 방향 자체가 단일 source model만 지원하도록 명시적으로 변경될 때만
baseline과 함께 변경한다.

## D3. Reuse precedes conversion

**Decision:** Target이 이미 같은 portable source를 소비할 수 있으면 변환하지 않는다.

**Rationale:** 생성물이 늘어날수록 drift와 ownership ambiguity가 늘어난다. Backend를
호출하지 않는 것이 가장 단순하고 정확한 경로일 수 있다.

**Change when:** Direct reuse가 runtime discovery나 semantic behavior를 안정적으로 보장하지
못한다는 근거가 있을 때 해당 asset category에 한해 예외를 정의한다.

## D4. Source authority is external to the Skill

**Decision:** Source of truth는 caller의 명시, repository policy 또는 이미 확립된 ownership이
결정한다. Generic Skill이 특정 harness나 `.rulesync/`를 우선하지 않는다.

**Rationale:** Portability Skill이 project architecture를 몰래 결정하면 책임이 뒤섞인다.

**Change when:** 없음. 특정 project default는 project profile에서 정의한다.

## D5. Generated output is derived

**Decision:** 변환으로 생성된 target asset은 authoritative source가 아니라 derived
artifact로 취급한다.

**Rationale:** Source와 generated target을 동시에 수동 관리하면 양방향 drift가 생긴다.

**Change when:** 특정 project가 명시적으로 ownership transfer를 수행하는 별도 migration을
채택할 때만 그 project 범위에서 바뀔 수 있다.

## D6. Conversion success is not semantic parity

**Decision:** File generation 성공과 runtime semantic compatibility를 구분한다.

**Rationale:** Harness는 같은 개념을 다르게 표현하거나 일부 기능을 지원하지 않을 수 있다.
Omission, approximation, simulation과 discovery failure를 숨기면 결과가 실제보다 강하게
보인다.

**Change when:** 없음. Backend가 완전한 parity를 검증할 수 있는 특정 feature가 생기더라도
그 검증 근거를 명시해야 한다.

## D7. Preview is the mutation gate

**Decision:** Rulesync write는 가능한 dry-run/preview 결과를 먼저 확인한 뒤 적용한다.

**Rationale:** Cross-harness generation은 여러 파일과 config를 동시에 건드릴 수 있으므로
예상 범위 확인이 mutation보다 먼저 와야 한다.

**Change when:** Backend에 preview가 없는 operation만 명시적 예외가 될 수 있으며, 그 경우
대체 검증 경계를 정의해야 한다.

## D8. No speculative wrapper or parallel schema

**Decision:** Concrete Rulesync limitation이 확인되기 전에는 custom wrapper, adapter,
parallel canonical schema를 만들지 않는다.

**Rationale:** Rulesync와 겹치는 abstraction은 유지보수와 upstream tracking을 다시 우리
책임으로 가져온다.

**Change when:** 반복되는 backend gap이 작은 project policy만으로 해결되지 않고, 실제
자동화가 duplication과 오류를 줄인다는 근거가 생길 때 추가한다.

## D9. Documentation has separate audiences

**Decision:** 문서 책임을 다음처럼 분리한다.

- `SKILL.md`: runtime agent가 따라야 하는 실행 계약
- `references/*`: 실행 중 조건부로 필요한 backend/project detail
- `README.md`: Skill caller가 알아야 하는 호출 계약
- `.docs/baseline/*`: maintainer가 보존해야 하는 목적, 요구사항과 결정

**Rationale:** 서로 다른 독자가 같은 문서를 읽게 하면 trigger context가 불어나고 같은
정보가 여러 위치에 복제된다.

**Change when:** 문서 소비 방식 자체가 바뀌는 경우에만 구조를 조정하되 audience ownership은
유지한다.

## D10. Frontmatter follows the common Skill contract

**Decision:** Frontmatter 역할은 다음과 같이 유지한다.

- `description`: activation context와 사용 조건
- `compatibility`: dependencies, runtime prerequisites와 호환 조건
- `metadata`: 식별용 부가 정보

현재 `metadata`에는 `author`, `version`만 둔다. 호환성이나 backend 전제를 metadata에
중복 기록하지 않는다.

**Rationale:** 공용 Agent Skills frontmatter의 semantic role을 따르고, 같은 사실을 여러
field에 복제하지 않기 위해서다.

**Change when:** 공용 Skill spec 또는 repository validator가 변경되면 새 계약에 맞춰
검토한다.

## Change Discipline

Baseline decision을 깨는 변경은 refactor로 취급하지 않는다. 같은 변경에서 관련 intent와
requirements를 검토하고 필요한 baseline 수정, caller-facing 영향과 migration 여부를 함께
명시한다.

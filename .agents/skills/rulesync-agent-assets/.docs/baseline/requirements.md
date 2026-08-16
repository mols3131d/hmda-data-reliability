# Requirements

이 문서는 `rulesync-agent-assets`의 구현이 계속 만족해야 하는 durable requirement를 정의한다.
Rulesync의 현재 CLI option, target identifier, harness별 파일 경로처럼 upstream 변화에 민감한
정보는 baseline requirement가 아니다.

## Functional Requirements

### R1. Source authority

각 작업은 하나의 authoritative source를 식별해야 한다. Caller의 명시적 선택과 project
policy를 우선하며, 서로 다른 source가 경쟁하는 상태에서 임의로 하나를 선택하지 않는다.

### R2. Reuse before transformation

Target이 기존 source를 올바르게 소비할 수 있으면 새 asset을 생성하지 않아야 한다.
Rulesync 사용 자체가 목적이 되어서는 안 된다.

### R3. Canonical fan-out

Rulesync canonical source가 authoritative한 경우 하나의 source에서 하나 이상의 target
harness용 native asset을 생성할 수 있어야 한다.

### R4. Native bridge

하나의 harness native asset이 authoritative한 경우 그 source를 유지하면서 하나 이상의
다른 harness용 asset을 생성할 수 있어야 한다. 단순 bridge를 위해 canonical source
채택을 강제하지 않는다.

### R5. Minimal scope

Target, asset category와 project/global scope는 요청과 project policy가 요구하는 최소
범위로 제한해야 한다. 명시적 이유 없이 all-target, all-feature 또는 global mutation으로
확장하지 않는다.

### R6. Preview before mutation

Rulesync가 파일을 변경하는 경로는 backend가 제공하는 preview를 먼저 사용해야 한다.
Preview에서 예상 밖 output, 누락 source, warning 또는 unsupported behavior를 확인한 뒤에만
실제 write를 수행한다.

### R7. Source preservation

Compatibility를 만들기 위해 authoritative source를 암묵적으로 rename, copy, relocate,
normalize 또는 rewrite하지 않는다. Source layout 변경이 필요하면 별도 의도된 변경으로
취급한다.

### R8. Compatibility transparency

File generation 성공을 semantic parity의 증거로 취급하지 않는다. Omitted, approximated,
simulated, unsupported 또는 undiscovered behavior는 caller가 판단할 수 있게 드러내야 한다.

### R9. Backend delegation

Parsing, normalization, harness mapping과 serialization은 가능한 한 Rulesync에 위임한다.
Concrete backend gap이 확인되기 전에는 parallel schema, custom adapter 또는 wrapper
compiler를 추가하지 않는다.

### R10. Validation evidence

작업 결과에는 실제 생성된 target, 확인된 compatibility gap과 실제 수행한 validation이
구분되어야 한다. 실행하지 않은 검증을 성공한 것처럼 보고하지 않는다.

## Quality Requirements

### Q1. KISS

가장 작은 유효 route를 선택한다. Reuse가 가능하면 reuse, canonical source가 이미 있으면
fan-out, native source를 유지해야 하면 bridge를 사용한다. 새로운 abstraction은 실제 반복
문제가 확인된 뒤에만 추가한다.

### Q2. DRY

공통 routing과 safety policy는 하나의 Skill이 소유한다. Project-specific default와 gap은
project profile이 소유한다. Rulesync CLI와 capability 정보는 backend reference가 소유한다.
같은 규범을 여러 문서에 복제하지 않는다.

### Q3. SRP

- Skill: route, scope, safety, compatibility evidence, completion contract
- Rulesync: format translation mechanics
- Project profile: project-specific source preference와 discovery gap
- README: caller-facing usage contract
- Baseline: maintainer-facing invariant와 design intent

한 영역의 정보를 다른 영역으로 이동시켜 책임을 섞지 않는다.

### Q4. Progressive disclosure

Skill activation에 항상 필요한 정보만 `SKILL.md`에 둔다. Backend와 project detail은 필요한
경우에만 reference에서 읽는다. Maintainer baseline과 caller documentation은 runtime agent
instruction으로 사용하지 않는다.

### Q5. Portability

Generic Skill은 특정 harness나 특정 프로젝트를 source of truth로 가정하지 않는다. 지원
harness 목록과 세부 capability는 installed Rulesync version에 따라 바뀔 수 있어야 한다.

## Acceptance Invariants

다음 중 하나라도 깨지면 본질적 regression으로 본다.

- canonical fan-out과 native bridge 중 하나가 second-class 또는 unsupported가 된다.
- 기존 source를 직접 재사용할 수 있는데도 변환을 강제한다.
- source authority가 caller/project가 아니라 Skill 내부 선호로 결정된다.
- compatibility loss가 조용히 누락된다.
- Rulesync backend와 경쟁하는 별도 변환 체계가 근거 없이 생긴다.
- write 전에 확인 가능한 preview를 건너뛴다.
- caller-visible 결과에서 생성 성공과 semantic compatibility를 구분할 수 없다.

이 requirement를 의도적으로 변경하려면 구현 수정과 함께 baseline을 갱신하고 contract
change로 검토한다.

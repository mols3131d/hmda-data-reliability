# Acceptance Criteria

## Structure

| ID | Criterion |
| --- | --- |
| S1 | directory 이름이 `pivot-openspec-rpi`이고 valid `SKILL.md`를 포함한다 |
| S2 | frontmatter에는 `name`과 `description`만 존재한다 |
| S3 | description에 기능, positive trigger, anti-trigger가 있다 |
| S4 | `SKILL.md`는 500 line 미만이며 one-level resource로 직접 link한다 |
| S5 | relative link는 skill root 내부에서 resolve된다 |
| S6 | 불필요한 `README.md`, changelog, installation guide를 만들지 않는다 |

## Behavior

| ID | Criterion |
| --- | --- |
| B1 | Research는 추가 조사 전에 항상 기존 evidence를 평가한다 |
| B2 | evidence가 충분하면 새 조사 없이 Research를 완료할 수 있다 |
| B3 | Research status는 `draft`, `in_progress`, `completed`, `blocked`, `superseded` 중 하나다 |
| B4 | proposal·requirements·design·tasks·archive state는 OpenSpec만 소유한다 |
| B5 | ROR artifact는 OpenSpec change directory 밖에 위치한다 |
| B6 | Review는 독립 evidence를 사용하고 `pending`, `in_progress`, `approved`, `changes_requested`, `blocked` status를 기록한다 |
| B7 | `changes_requested`는 owner phase를 지정하고 fresh Review를 요구한다 |
| B8 | Review status가 `approved`가 아니면 archive하지 않는다 |
| B9 | human interruption은 intent conflict, material choice, unsafe side effect, missing access로 제한한다 |
| B10 | final output에 실제 validation 결과와 remaining risk가 보인다 |
| B11 | 실행 방식과 무관하게 동일한 artifact·status·routing contract를 사용한다 |
| B12 | phase 간 handoff는 transcript나 private reasoning 대신 durable evidence를 사용한다 |
| B13 | Research는 change와 독립적인 repository-unique `research-id`를 사용한다 |
| B14 | Research artifact는 `openspec/research/{research-id}/research.md`에 위치한다 |
| B15 | ROR artifact는 `openspec-rpi` front matter로 title, description, category, status, related artifact, tags를 관리한다 |
| B16 | Research, OpenSpec, Implement, Review는 각자의 입력 artifact가 유효하면 독립적으로 시작할 수 있다 |
| B17 | 시작 phase의 필수 artifact가 없거나 충돌하면 해당 artifact owner phase로 route하며, 유효한 artifact를 다시 만들지 않는다 |
| B18 | P는 설치된 OpenSpec workflow를 그대로 따르며, RPI는 OpenSpec의 entry condition, schema, lifecycle, command, 완료·archive 조건을 변경하거나 추가 gate로 제한하지 않는다 |
| B19 | Research와 Review는 선택적 decorator artifact이며, OpenSpec change의 entry·completion·archive gate가 아니다 |

## Portability

| ID | Criterion |
| --- | --- |
| P1 | skill 내부 path는 skill root 기준 relative path다 |
| P2 | 전체 skill directory를 Windows와 WSL에서 link할 수 있다 |
| P3 | core execution은 IDE 전용 plugin 또는 custom OpenSpec schema에 의존하지 않는다 |

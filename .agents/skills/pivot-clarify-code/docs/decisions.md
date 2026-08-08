# Clarify Code 결정 기록

## 채택

| 결정 | 이유 | 영향 |
| --- | --- | --- |
| `pivot-clarify-code` namespace 사용 | Project Pivot 전용 skill을 기존 `pivot-*` 계열과 맞춤 | `prj-clarify-code`를 rename |
| description은 사용자 intent와 near-miss boundary를 직접 표현 | discovery 단계에서는 `name`과 `description`이 주요 routing signal | clarify 요청은 넓게 포착하고 feature, review, performance, architecture 요청은 제외 |
| 공통 guardrail은 repository instructions가 소유 | 항상 적용되는 규칙과 선택적 workflow를 분리 | skill은 diagnosis, intervention, validation에 집중 |
| 오해 비용이 가장 큰 병목 하나를 먼저 해소 | 전면 정리와 cosmetic cleanup을 방지 | destructive side effect, gate, ordering, invariant를 단순 복잡성보다 우선 |
| explicit caller와 framework/runtime entrypoint를 모두 usage surface로 취급 | 등록 기반 호출과 public contract 보호 | caller-visible rename·move·extraction을 제한 |
| code/name → docstring/comment → extraction 순으로 최소 해법 선택 | prose와 helper 증가로 생기는 이해 부채 방지 | caller contract와 code-local rationale만 필요한 위치에 설명 |
| 넓은 정책은 canonical owner, 호출에 필요한 의미는 API에 projection | DRY와 API 사용성을 함께 유지 | destructive side effect, overwrite, precondition 등은 local contract로 유지 가능 |
| observable behavior를 좁은 before/after validation으로 보존 | API 외 exception, state, side effect, registration drift도 보호 | 기존 safeguard를 우선하고 필요한 경우에만 characterization test 사용 |
| public interface는 `target`, `scope`, `validation`만 제공 | caller/maintainer 관점은 diagnosis 내부 판단 | 불필요한 `focus` argument 제거 |
| reference는 load condition과 함께 one-level로 연결 | eager loading과 reference 탐색 비용을 줄임 | diagnosis, documentation, validation을 필요한 경우에만 읽음 |

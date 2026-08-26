# Project Guidance

`Always`는 모든 작업에서 읽고, `As needed`는 현재 작업에 관련될 때 읽는다.

| Load | Document | Scope |
| --- | --- | --- |
| Always | [`docs/VISION.md`](docs/VISION.md) | 장기 방향, trust model과 AI delegation 원칙 |
| Always | [`docs/language.md`](docs/language.md) | 언어 정책 |
| As needed | [`DEVELOPMENT.md`](DEVELOPMENT.md) | 개발 환경, active tool, package layout과 code convention |
| As needed | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | 시스템 구조, 실행 경계와 domain ownership |
| As needed | [`docs/mvp.md`](docs/mvp.md) | 현재 MVP 목표, scope와 acceptance |

## Review Independence

Code-facing implementation, test 또는 runtime/config behavior를 변경한 agent는 작업 완료를 선언하기 전에 가능한 경우 별도 subagent context의 `review-lead`에 bounded review를 위임한다.

- 구현 agent의 self-review는 independent review를 대체하지 않는다.
- `review-lead`에는 target, 현재 revision 또는 observable state, intended behavior, scope와 이미 수행한 validation만 최소한으로 전달한다.
- Material finding을 수정한 뒤 review가 여전히 필요하면 새 `review-lead` invocation으로 다시 검토한다.
- `review-lead` 또는 nested subagent invocation을 사용할 수 없으면 independent review를 수행했다고 주장하지 않고 coverage gap을 보고한다.

# Development Documents

이 디렉터리는 `spec-driven-tdd` schema 자체를 개발하고 검토하기 위한 문서를 보관한다.

| Document | Purpose |
| --- | --- |
| `architecture.md` | workflow, artifact 책임, parsing contract와 configuration boundary |
| `baseline/DIRECTIVE.md` | 개선 중에도 보존해야 하는 요구사항, 결정사항과 불변 조건 |

## Maintenance Rule

- 사용자용 간단한 설명은 루트 `README.md`에 둔다.
- 설계 근거와 유지보수 규칙은 `docs/`에 둔다.
- 장기적으로 바뀌면 안 되는 취지와 계약은 `docs/baseline/`에 둔다.
- 구현 세부나 일시적 조사 기록을 baseline에 넣지 않는다.
- OpenSpec runtime/version을 의미 있게 갱신할 때 built-in `spec-driven`의 metadata, validation, artifact completion과 archive contract 변화를 확인하고 현재 schema에 필요한 runtime semantics만 선별 반영한다. Upstream 문구나 구조를 그대로 동기화하지 않는다.

# Project Rules

- 데이터 상태와 reliability 판단은 재현 가능한 deterministic evidence를 기준으로 한다. Pipeline success나 AI/LLM output만으로 trusted state, incident resolution 또는 validation success를 주장하지 않는다. Trust model의 authority는 [`docs/VISION.md`](docs/VISION.md)다.
- AI/agent는 자신의 delegation boundary나 mutation authority를 스스로 확대하지 않는다. Advisory output과 `RemediationDraft`는 실행 권한이 아니며, state-changing recovery는 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)의 validated proposal → external approval → re-validation boundary를 보존한다.
- 언어 정책은 [`docs/language.md`](docs/language.md)를 따른다.

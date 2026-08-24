# Rulesync

Repository Agent instruction policy는 [`docs/development/agent-instructions.md`](../docs/development/agent-instructions.md)를 따른다.

## Chatbot route

`scripts/generate_agent_routes.py`는 glob이 있는 non-root Rule을 chatbot route index에 투영한다. 특정 vendor capability에만 유효한 Rule은 frontmatter에 `route: false`를 두어 Rulesync projection은 유지하고 chatbot route에서만 제외한다.

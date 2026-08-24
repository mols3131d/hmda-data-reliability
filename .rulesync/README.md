# Rulesync

Repository Agent instruction policy는 [`docs/development/agent-instructions.md`](../docs/development/agent-instructions.md)를 따른다.

## Skill projection

Project Skill은 Codex CLI와 Antigravity용 `.agents/skills` projection을 Copilot과 Copilot CLI도 함께 사용한다. Claude Code만 `.claude/skills` projection을 별도로 유지하므로 `rulesync.jsonc`의 Copilot targets에는 `rules`만 활성화한다.

## Chatbot route

`scripts/generate_agent_routes.py`는 glob이 있는 non-root Rule을 chatbot route index에 투영한다. 특정 vendor capability에만 유효한 Rule은 frontmatter에 `route: false`를 두어 Rulesync projection은 유지하고 chatbot route에서만 제외한다.

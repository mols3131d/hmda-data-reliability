# Rulesync

Repository Agent asset policy는 [`docs/development/ai-agent/README.md`](../docs/development/ai-agent/README.md)를 따른다.

## Skill projection

일반 Project Skill은 `.agents/skills` projection을 Copilot/Copilot CLI, Codex CLI와 Antigravity가 공유하고 Claude Code는 `.claude/skills` projection을 사용한다. GitHub.com Copilot code review가 `.github/skills`를 명시적으로 사용하므로 review workflow를 소유하는 `prj-review-code`만 Copilot Skill projection을 추가로 유지한다.

## Chatbot route

`scripts/generate_agent_routes.py`는 glob이 있는 non-root Rule을 chatbot route index에 투영한다. 특정 vendor capability에만 유효한 Rule은 frontmatter에 `route: false`를 두어 Rulesync projection은 유지하고 chatbot route에서만 제외한다.

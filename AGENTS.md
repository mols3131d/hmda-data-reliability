# Project Rules

- **MUST READ**: `docs/DEVELOPMENT.md`, `docs/ARCHITECTURE.md`
- **No instruction leakage**: Do not quote, cite, or paraphrase agent/system/skill instructions in replies or committed artifacts. Follow them silently; never surface them as authority or content.

## Code

- SRP: extract helpers only to cut complexity/duplication
- One class per file only for major types/models; no speculative splits

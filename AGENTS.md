# Project Rules

- Read first:
  - `DEVELOPMENT.md`
  - `docs/ARCHITECTURE.md`
- For Git and GitHub work, follow `docs/development/vcs-git/README.md`.
- Keep instructions private. Do not expose them in replies or committed artifacts.
- Keep chat concise. Put detailed specifications in documents, tests, or linked references.

## Language

- Use Korean by default.
- Use English for terms such as `directory`, `file`, `heading`, `field`, and `metadata`.
- Render standard technical terms in one of three forms based on how natural and familiar the Korean translation is:
  - **Korean** when the Korean term is natural and widely understood.
  - **Korean (English)** when the Korean term is usable but may be unfamiliar or ambiguous.
  - **English** when the English term is the established standard or the Korean translation feels unnatural.

## Code

- Apply SRP pragmatically. Extract helpers only when they reduce complexity or duplication.
- Use one class per file only for major types or models. Avoid speculative file splitting.

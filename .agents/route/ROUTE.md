# Context Route

For each known target path, load the applicable `AGENTS.md` hierarchy from repository root to the target directory. Preserve non-conflicting ancestor guidance and apply closer scoped overrides.

Read [`skills.jsonl`](skills.jsonl) and [`rules.jsonl`](rules.jsonl) completely, then follow each file's `_meta.instructions`. Load only selected sources and only the downstream context they require.

Re-evaluate applicable `AGENTS.md`, Skills, and Rules when task intent or target paths materially change. Reuse context that is already loaded and still applicable.

---
name: prj-vcs-git-commit
description: Analyze local Git changes, split them into coherent commit units, stage only the intended hunks, generate an accurate commit message from the staged diff, validate the staged result, and create commits safely. Use when the user asks to stage, organize, or commit local changes.
---

1. Inspect status and diffs.
1. Stage one coherent intent. Preserve unrelated and existing staged changes.
1. Use patch staging only when a file contains mixed intentions.
1. Review the staged diff.
1. Write the message from the staged diff, following `.gitmessage`.
1. Commit and report the result.

Ask only when the commit boundary is genuinely ambiguous.
Do not push, amend, rebase, reset destructively, or bypass hooks unless requested.

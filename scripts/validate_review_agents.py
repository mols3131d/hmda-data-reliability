#!/usr/bin/env python3
"""Validate the repository review-agent delegation topology."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_ROOT = REPO_ROOT / ".github" / "agents"
SETTINGS = REPO_ROOT / ".vscode" / "settings.json"

LEAD = "review-lead"
SPECIALISTS = ("review-quality", "review-adversarial")


def frontmatter(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"missing frontmatter: {path.relative_to(REPO_ROOT)}")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(
            f"unterminated frontmatter: {path.relative_to(REPO_ROOT)}"
        ) from exc

    value = yaml.safe_load("\n".join(lines[1:end])) or {}
    if not isinstance(value, dict):
        raise ValueError(f"frontmatter must be a mapping: {path.relative_to(REPO_ROOT)}")
    return value


def agent_meta(name: str) -> dict[str, Any]:
    path = AGENTS_ROOT / f"{name}.agent.md"
    if not path.is_file():
        raise ValueError(f"missing review agent: {path.relative_to(REPO_ROOT)}")
    meta = frontmatter(path)
    if meta.get("name") != name:
        raise ValueError(f"agent name mismatch: {path.relative_to(REPO_ROOT)}")
    return meta


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate() -> None:
    lead = agent_meta(LEAD)
    require(lead.get("user-invocable") is False, "review-lead must be subagent-only")
    require(
        lead.get("disable-model-invocation") is not True,
        "review-lead must remain available for implementation agents to delegate",
    )
    require(
        lead.get("agents") == list(SPECIALISTS),
        "review-lead must explicitly allow exactly review-quality and review-adversarial",
    )
    require("agent" in (lead.get("tools") or []), "review-lead requires the agent tool")

    for name in SPECIALISTS:
        meta = agent_meta(name)
        require(meta.get("user-invocable") is False, f"{name} must be hidden from users")
        require(
            meta.get("disable-model-invocation") is True,
            f"{name} must reject general model invocation and rely on review-lead allowlisting",
        )
        require(meta.get("agents") == [], f"{name} must not invoke other agents")
        require("agent" not in (meta.get("tools") or []), f"{name} must not have agent tool")

    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    require(
        settings.get("chat.subagents.allowInvocationsFromSubagents") is True,
        "nested subagent invocation must be enabled for review-lead delegation",
    )


def main() -> int:
    try:
        validate()
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as error:
        print(f"review-agent validation failed: {error}")
        return 1

    print("review-agent topology valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate the repository review-agent delegation topology and capability boundaries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_ROOT = REPO_ROOT / ".github" / "agents"
SETTINGS = REPO_ROOT / ".vscode" / "settings.json"

LEAD = "review-lead"
QUALITY = "review-quality"
ADVERSARIAL = "review-adversarial"
SPECIALISTS = (QUALITY, ADVERSARIAL)
EXPECTED_TOOLS = {
    LEAD: {"read", "search", "agent"},
    QUALITY: {
        "read",
        "search",
        "execute/runTests",
        "execute/testFailure",
        "vscodeGeneral/usages",
        "vscodeGeneral/runTests",
        "vscodeGeneral/testFailure",
    },
    ADVERSARIAL: {"read", "search"},
}


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


def agent_tools(name: str, meta: dict[str, Any]) -> set[str]:
    value = meta.get("tools") or []
    require(isinstance(value, list), f"{name} tools must be a list")
    require(
        all(isinstance(tool, str) for tool in value),
        f"{name} tools must be strings",
    )
    return set(value)


def validate_review_agent_common(name: str, meta: dict[str, Any]) -> None:
    require(meta.get("target") == "vscode", f"{name} must target vscode")
    require(meta.get("user-invocable") is False, f"{name} must be subagent-only")
    require(
        agent_tools(name, meta) == EXPECTED_TOOLS[name],
        f"{name} tools must match its least-privilege review role",
    )


def validate() -> None:
    lead = agent_meta(LEAD)
    validate_review_agent_common(LEAD, lead)
    require(
        lead.get("disable-model-invocation") is not True,
        "review-lead must remain available for implementation agents to delegate",
    )
    require(
        lead.get("agents") == list(SPECIALISTS),
        "review-lead must explicitly allow exactly review-quality and review-adversarial",
    )

    for name in SPECIALISTS:
        meta = agent_meta(name)
        validate_review_agent_common(name, meta)
        require(
            meta.get("disable-model-invocation") is True,
            f"{name} must reject general model invocation and rely on review-lead allowlisting",
        )
        require(meta.get("agents") == [], f"{name} must not invoke other agents")

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

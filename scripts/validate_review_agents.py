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
QUALITY_EXECUTE_TOOLS = {"execute/runTests", "execute/testFailure"}


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


def tools(meta: dict[str, Any]) -> set[str]:
    value = meta.get("tools") or []
    require(isinstance(value, list), "agent tools must be a list")
    require(all(isinstance(tool, str) for tool in value), "agent tools must be strings")
    return set(value)


def has_tool_family(agent_tools: set[str], family: str) -> bool:
    return any(tool == family or tool.startswith(f"{family}/") for tool in agent_tools)


def validate_review_agent_common(name: str, meta: dict[str, Any]) -> set[str]:
    require(meta.get("target") == "vscode", f"{name} must target vscode")
    require(meta.get("user-invocable") is False, f"{name} must be subagent-only")
    agent_tools = tools(meta)
    require(
        not has_tool_family(agent_tools, "edit"),
        f"{name} must not expose workspace edit capability",
    )
    return agent_tools


def validate() -> None:
    lead = agent_meta(LEAD)
    lead_tools = validate_review_agent_common(LEAD, lead)
    require(
        lead.get("disable-model-invocation") is not True,
        "review-lead must remain available for implementation agents to delegate",
    )
    require(
        lead.get("agents") == list(SPECIALISTS),
        "review-lead must explicitly allow exactly review-quality and review-adversarial",
    )
    require("agent" in lead_tools, "review-lead requires the agent tool")
    require(
        not has_tool_family(lead_tools, "execute"),
        "review-lead must not expose execution capability",
    )

    quality = agent_meta(QUALITY)
    quality_tools = validate_review_agent_common(QUALITY, quality)
    require(
        quality.get("disable-model-invocation") is True,
        "review-quality must reject general model invocation and rely on review-lead allowlisting",
    )
    require(quality.get("agents") == [], "review-quality must not invoke other agents")
    require("agent" not in quality_tools, "review-quality must not have agent tool")
    require("execute" not in quality_tools, "review-quality must not expose general execute")
    unsupported_execute = {
        tool
        for tool in quality_tools
        if tool.startswith("execute/") and tool not in QUALITY_EXECUTE_TOOLS
    }
    require(
        not unsupported_execute,
        "review-quality may use only test-specific execute tools: "
        + ", ".join(sorted(unsupported_execute)),
    )

    adversarial = agent_meta(ADVERSARIAL)
    adversarial_tools = validate_review_agent_common(ADVERSARIAL, adversarial)
    require(
        adversarial.get("disable-model-invocation") is True,
        "review-adversarial must reject general model invocation and rely on review-lead allowlisting",
    )
    require(
        adversarial.get("agents") == [],
        "review-adversarial must not invoke other agents",
    )
    require("agent" not in adversarial_tools, "review-adversarial must not have agent tool")
    require(
        not has_tool_family(adversarial_tools, "execute"),
        "review-adversarial must not expose execution capability",
    )

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

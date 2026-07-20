from typing import Any


def req(t: type = str, **kwargs: Any) -> dict[str, Any]:
    return {"type": t, "required": True, **kwargs}


def opt(t: type = str, default: Any = "", **kwargs: Any) -> dict[str, Any]:
    return {"type": t, "required": False, "default": default, **kwargs}


SUMMARY_SCHEMA: dict[str, Any] = {
    "frontmatter": {
        "title": req(),
        "date": req(),
        "type": req(default="code-review-summary"),
    },
    "sections": ("Summary", "Findings"),
}

FINDING_SCHEMA: dict[str, Any] = {
    "frontmatter": {
        "title": req(),
        "description": opt(),
        "type": req(default="code-review-finding"),
        "severity": opt(default="nit", allowed_values=("bug", "risk", "nit", "q")),
        "status": opt(default="open", allowed_values=("open", "resolved", "dismissed")),
    },
    "sections": (
        "Summary",
        "Observation",
        "Impact",
        "Recommendation",
        "Verification",
    ),
}

TEMPLATE_SCHEMAS: dict[str, dict[str, Any]] = {
    "code-review-summary": SUMMARY_SCHEMA,
    "code-review-finding": FINDING_SCHEMA,
}

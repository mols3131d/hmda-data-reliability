"""Chatbot route generation paths and source errors."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_ROOT = REPO_ROOT / ".rulesync" / "skills"
RULES_ROOT = REPO_ROOT / ".rulesync" / "rules"
ROUTE_ROOT = REPO_ROOT / ".agents" / "route"
RULESYNC_CONFIG = REPO_ROOT / "rulesync.jsonc"
RULESYNC_LOCK = REPO_ROOT / "rulesync.lock"
SKILLS_LOCK = REPO_ROOT / "skills-lock.json"


class RouteGenerationError(RuntimeError):
    """Raised when route source metadata cannot be converted into a valid index."""

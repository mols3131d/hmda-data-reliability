"""Review-owned prompt preflight settings."""

from __future__ import annotations

from pydantic import Field

from hmda_reliability.reliability.contracts.base import ReliabilityContract


class ReviewAISettings(ReliabilityContract):
    """Bound review prompt rendering before provider invocation."""

    max_prompt_bytes: int = Field(default=65_536, gt=0, le=1_048_576)

    def sanitized_configuration(self) -> dict[str, int]:
        """Return review configuration safe for invocation evidence."""

        return {"max_prompt_bytes": self.max_prompt_bytes}

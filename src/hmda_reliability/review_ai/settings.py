"""Review 전용 프롬프트 사전 검사 설정 모듈."""

from __future__ import annotations

from pydantic import Field

from hmda_reliability.reliability.contracts.base import ReliabilityContract


class ReviewAISettings(ReliabilityContract):
    """Provider 호출 전 review 프롬프트 렌더링 한도를 제한하는 설정."""

    max_prompt_bytes: int = Field(default=65_536, gt=0, le=1_048_576)

    def sanitized_configuration(self) -> dict[str, int]:
        """호출 evidence 기록을 위한 정제된 review 설정을 반환한다."""

        return {"max_prompt_bytes": self.max_prompt_bytes}

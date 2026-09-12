"""Review 전용 프롬프트 사전 검사 설정 모듈.

Provider 호출 전 렌더링된 표준 프롬프트의 최대 허용 바이트를 제한하여
예기치 않은 페이로드 폭주 및 비용/토큰 한도 초과를 방어한다.
"""

from __future__ import annotations

from pydantic import Field

from hmda_reliability.reliability.contracts.base import ReliabilityContract


class ReviewAISettings(ReliabilityContract):
    """Provider 호출 전 review 프롬프트 렌더링 한도를 제한하는 설정.

    Attributes:
        max_prompt_bytes: 렌더링된 UTF-8 JSON 대화 메시지 목록의 최대 허용 바이트 수
            (기본값: 64KiB = 65,536 bytes, 최대 1MiB = 1,048,576 bytes).
    """

    max_prompt_bytes: int = Field(default=65_536, gt=0, le=1_048_576)

    def sanitized_configuration(self) -> dict[str, int]:
        """호출 evidence 기록을 위한 정제된 review 설정을 반환한다.

        `AgenticInvocationEvidence`에 포함되어 감사 및 재생에 활용된다.
        """

        return {"max_prompt_bytes": self.max_prompt_bytes}

"""고정 단계 실행의 시간 예산. 전송 timeout과 별도로 적용한다."""

from pydantic import Field

from hmda_reliability.reliability.contracts.base import ReliabilityContract


class StagedExecutionSettings(ReliabilityContract):
    """후속 실행과 결과 채택을 제한하는 협력적 시간 예산.

    동기 provider 호출을 deadline 시각에 강제 중단하지 않는다.
    """

    stage_budget_seconds: float = Field(default=360, gt=0, le=7200)
    workflow_budget_seconds: float = Field(default=1200, gt=0, le=21_600)

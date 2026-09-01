"""신뢰성 기본 계약 모델 모듈."""

from pydantic import BaseModel, ConfigDict


class ReliabilityContract(BaseModel):
    """불변 및 엄격한 설정을 강제하는 신뢰성 계약 기본 클래스."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)

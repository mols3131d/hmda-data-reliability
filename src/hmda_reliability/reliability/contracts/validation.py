"""계약 유효성 검증 유틸리티 모듈."""

from pydantic import ValidationError

from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.reliability.errors import ContractValidationError


def validate_contract[ContractT: ReliabilityContract](
    contract_type: type[ContractT],
    payload: dict[str, object],
) -> ContractT:
    """페이로드를 검증하여 지정된 신뢰성 계약 모델 객체로 변환한다."""
    try:
        return contract_type.model_validate(payload)
    except ValidationError as error:
        raise ContractValidationError.from_validation_error(
            contract_name=contract_type.__name__,
            error=error,
        ) from error

"""Validation utilities for contracts."""

from pydantic import ValidationError

from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.reliability.errors import ContractValidationError


def validate_contract[ContractT: ReliabilityContract](
    contract_type: type[ContractT],
    payload: dict[str, object],
) -> ContractT:
    try:
        return contract_type.model_validate(payload)
    except ValidationError as error:
        raise ContractValidationError.from_validation_error(
            contract_name=contract_type.__name__,
            error=error,
        ) from error

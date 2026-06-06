"""Reliability domain exceptions."""

from __future__ import annotations

from pydantic import ValidationError


class ReliabilityError(Exception):
    """Reliability application error base class."""


class ContractValidationError(ReliabilityError):
    """Contract validation failed."""

    def __init__(self, contract_name: str, details: list[str]) -> None:
        self.contract_name = contract_name
        self.details = details
        message = f"{contract_name} contract validation failed"
        super().__init__(message)

    @classmethod
    def from_validation_error(
        cls,
        contract_name: str,
        error: ValidationError,
    ) -> ContractValidationError:
        details = [
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
            for item in error.errors()
        ]
        return cls(contract_name=contract_name, details=details)


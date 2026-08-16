"""Exact table-schema recovery validation result."""

from typing import Literal

from pydantic import model_validator

from project_pivot.reliability.contracts import (
    ProfileSnapshot,
    ReliabilityContract,
    TableStateIdentity,
)


class SchemaRecoveryValidationResult(ReliabilityContract):
    """Mutation-aware exact table state and aligned profile evidence."""

    approval_id: str
    incident_id: str
    table_name: str
    profile_snapshot: ProfileSnapshot
    approved_before_state: TableStateIdentity
    expected_after_state: TableStateIdentity
    actual_state: TableStateIdentity
    mutation_state: Literal["table_replaced", "already_restored"]
    reconciliation_action: Literal["replace_table", "resume_verification"]
    validation_passed: bool
    executed_actions: tuple[str, ...]

    @model_validator(mode="after")
    def _validate_exact_result(self) -> "SchemaRecoveryValidationResult":
        states = (
            self.approved_before_state,
            self.expected_after_state,
            self.actual_state,
        )
        if any(state.table_name != self.table_name for state in states):
            raise ValueError(
                "schema recovery result states는 target table과 같아야 합니다."
            )
        if self.validation_passed and self.actual_state != self.expected_after_state:
            raise ValueError(
                "validated actual state는 expected after state와 같아야 합니다."
            )
        expected_path = {
            "table_replaced": (
                "replace_table",
                ("replace_table", "rerun_profile_snapshot"),
            ),
            "already_restored": (
                "resume_verification",
                ("rerun_profile_snapshot",),
            ),
        }[self.mutation_state]
        if (self.reconciliation_action, self.executed_actions) != expected_path:
            raise ValueError(
                "mutation state와 reconciliation/action evidence가 맞지 않습니다."
            )
        return self

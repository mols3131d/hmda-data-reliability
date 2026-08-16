"""Complete table schema/content identity contract."""

from pydantic import Field, model_validator

from project_pivot.hmda_data import PartitionContentIdentity
from project_pivot.reliability.contracts.base import ReliabilityContract


class TableStateIdentity(ReliabilityContract):
    """Name/type schema와 non-overlapping year population의 exact identity."""

    table_name: str = Field(min_length=1)
    schema_hash: str = Field(min_length=1)
    row_count: int = Field(ge=0)
    partition_identities: tuple[PartitionContentIdentity, ...]

    @model_validator(mode="after")
    def _validate_complete_population(self) -> "TableStateIdentity":
        years = [identity.source_year for identity in self.partition_identities]
        if len(set(years)) != len(years):
            raise ValueError(
                "partition_identities는 duplicate source_year를 허용하지 않습니다."
            )
        if years != sorted(years):
            raise ValueError(
                "partition_identities는 source_year 오름차순이어야 합니다."
            )
        if any(
            identity.table_name != self.table_name
            for identity in self.partition_identities
        ):
            raise ValueError(
                "partition identity table_name은 table state와 같아야 합니다."
            )
        if any(
            identity.source_file is not None for identity in self.partition_identities
        ):
            raise ValueError("partition identity는 year 전체 scope여야 합니다.")
        partition_row_count = sum(
            identity.row_count for identity in self.partition_identities
        )
        if partition_row_count != self.row_count:
            raise ValueError(
                "partition row count 합계는 table row_count와 같아야 합니다."
            )
        return self

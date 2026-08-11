"""HMDA 원천 데이터 적재 API."""

from project_pivot.hmda_data.ingestion._common import (
    HMDA_LOANS_TABLE,
    REQUIRED_HMDA_COLUMNS,
    validate_required_columns,
)
from project_pivot.hmda_data.ingestion.discovery import discover_hmda_files
from project_pivot.hmda_data.ingestion.full_load import load_hmda_loans
from project_pivot.hmda_data.ingestion.identity import (
    PartitionContentIdentity,
    partition_content_identity,
)
from project_pivot.hmda_data.ingestion.partition import load_hmda_loans_partition

__all__ = [
    "HMDA_LOANS_TABLE",
    "PartitionContentIdentity",
    "REQUIRED_HMDA_COLUMNS",
    "discover_hmda_files",
    "load_hmda_loans",
    "load_hmda_loans_partition",
    "partition_content_identity",
    "validate_required_columns",
]

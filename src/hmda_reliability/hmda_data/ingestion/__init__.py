"""HMDA 원천을 Bronze table로 적재하는 public API.

Full load와 partition load는 append가 아니라 replace semantics를 사용한다.
"""

from hmda_reliability.hmda_data.ingestion._common import (
    HMDA_LOANS_TABLE,
    REQUIRED_HMDA_COLUMNS,
    validate_required_columns,
)
from hmda_reliability.hmda_data.ingestion.discovery import discover_hmda_files
from hmda_reliability.hmda_data.ingestion.full_load import load_hmda_loans
from hmda_reliability.hmda_data.ingestion.identity import (
    PartitionContentIdentity,
    partition_content_identity,
    partition_max_ingested_at,
)
from hmda_reliability.hmda_data.ingestion.partition import load_hmda_loans_partition

__all__ = [
    "HMDA_LOANS_TABLE",
    "PartitionContentIdentity",
    "REQUIRED_HMDA_COLUMNS",
    "discover_hmda_files",
    "load_hmda_loans",
    "load_hmda_loans_partition",
    "partition_content_identity",
    "partition_max_ingested_at",
    "validate_required_columns",
]

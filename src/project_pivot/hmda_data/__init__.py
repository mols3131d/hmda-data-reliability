"""HMDA 원천의 Bronze 적재, descriptive EDA, 합성 결함 생성 API.

실행 조합, dbt 변환, reliability 판정은 이 domain이 소유하지 않는다.
"""

from project_pivot.hmda_data.eda import analyze_hmda_csv
from project_pivot.hmda_data.ingestion import (
    HMDA_LOANS_TABLE,
    REQUIRED_HMDA_COLUMNS,
    PartitionContentIdentity,
    discover_hmda_files,
    load_hmda_loans,
    load_hmda_loans_partition,
    partition_content_identity,
    validate_required_columns,
)
from project_pivot.hmda_data.synthetic import (
    freshness_delay,
    null_spike,
    row_count_drop,
    schema_drift,
)

__all__ = [
    "HMDA_LOANS_TABLE",
    "PartitionContentIdentity",
    "REQUIRED_HMDA_COLUMNS",
    "analyze_hmda_csv",
    "discover_hmda_files",
    "freshness_delay",
    "load_hmda_loans",
    "load_hmda_loans_partition",
    "null_spike",
    "partition_content_identity",
    "row_count_drop",
    "schema_drift",
    "validate_required_columns",
]

select
    cast(activity_year as integer) as activity_year,
    cast(state_code as varchar) as state_code,
    cast(county_code as varchar) as county_code,
    cast(loan_purpose as integer) as loan_purpose,
    cast(action_taken as integer) as action_taken,
    try_cast(loan_amount as double) as loan_amount,
    try_cast(income as double) as income,
    cast(source_file as varchar) as source_file,
    cast(source_year as integer) as source_year
from {{ source('raw', 'hmda_loans') }}
